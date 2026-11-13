"""Install the procedural asset pack ("core_v1") into a library folder and merge it into library_index.json.

  python3 engine/assetgen/build.py                      # into the active library (common.library_dir())
  python3 engine/assetgen/build.py --library PATH --only 06_props,05_scenes
  python3 engine/assetgen/build.py --dry-run            # validate + count, write nothing

Rules: deterministic output; existing assets that are not part of this pack (seed library, forged, curated) are never
touched; an id clash with such an asset skips the pack asset and is reported. Pack assets that no longer exist in the
generator are removed from the index on the next build.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "assetgen"  # noqa: A001

import common  # noqa: E402
import schemas  # noqa: E402
from assetgen import audio, fxassets, kit, rigs, scenes  # noqa: E402
from assetgen import props_a, props_b, props_c  # noqa: E402,F401  (registration side effects)
from assetgen.registry import PROPS  # noqa: E402

PACK = "core_v1"
MAX_TAGS = 6
MAX_SVG_BYTES = 60_000


def _validate_svg(text: str) -> str:
    import forge
    return forge.validate_svg(text)


def _tags(tags: List[str]) -> List[str]:
    out: List[str] = []
    for t in tags:
        if t and t not in out:
            out.append(t)
    return out[:MAX_TAGS] or ["general"]


def _scope(tags: List[str], default: str = "specific") -> str:
    return "global" if (not tags or tags == ["general"] or "general" in tags) else default


def plan() -> List[Dict[str, Any]]:
    """Every pack asset as {id, category, scope, tags, ext, write(path), extra}."""
    items: List[Dict[str, Any]] = []

    def add_json(cat: str, it: Dict[str, Any], scope: Optional[str] = None, **extra):
        items.append({"id": it["id"], "category": cat, "scope": scope or it.get("scope") or _scope(it["tags"]), "tags": _tags(it["tags"]),
                      "ext": ".json", "data": json.dumps(it["json"], indent=1, ensure_ascii=False), **extra})

    for it in rigs.characters():
        voice = next((v for v in fxassets.voices() if v["id"] == it["json"]["default_voice_profile_id"]), None)
        add_json("01_characters", it, it["scope"], default_voice_id=(voice or {}).get("gemini_voice_name"))
    for it in rigs.poses():
        add_json("02_poses", it, "global")
    for it in rigs.expressions():
        add_json("03_expressions", it, "global")
    for it in rigs.motions():
        add_json("04_motions", it, "global")
    for sc in scenes.SCENES:
        d = scenes.Doc(sc["id"])
        sc["build"](d)
        items.append({"id": sc["id"], "category": "05_scenes", "scope": sc["scope"], "tags": _tags(sc["tags"]), "ext": ".svg", "data": d.svg(),
                      "meta": {"character_anchor": sc["anchor"]}})
    for p in PROPS:
        items.append({"id": p["id"], "category": "06_props", "scope": p["scope"], "tags": _tags(p["tags"]), "ext": ".svg", "data": kit.svg(p["build"]())})
    for it in fxassets.widgets():
        add_json("07_widgets", it)
    for it in fxassets.overlays():
        add_json("08_overlays", it)
    for it in fxassets.transitions():
        add_json("09_transitions", it, "global")
    for it in fxassets.caption_styles():
        add_json("10_caption_styles", it, "global")
    for it in fxassets.themes():
        add_json("11_themes", it)
    for it in fxassets.voices():
        add_json("12_voices", it, "global", gemini_voice_name=it["gemini_voice_name"])
    for bid, tags, spec in audio.BGM_SPECS:
        items.append({"id": bid, "category": "13_bgm", "scope": "global", "tags": _tags(tags.split()), "ext": ".ogg",
                      "audio": (lambda spec=spec, bid=bid: audio.make_bgm(spec, bid)), "meta": {"bpm": spec["bpm"], "loop": True}})
    for sid, tags, fn in audio.sfx_bank():
        items.append({"id": sid, "category": "14_sfx", "scope": "global", "tags": _tags(tags.split()), "ext": ".wav",
                      "audio": (lambda fn=fn, sid=sid: audio.norm(fn(audio._rng(sid))))})
    return items


def _write_wav(path: Path, x, sr: int) -> None:
    import wave

    import numpy as np
    arr = np.atleast_2d(x)
    pcm = (np.clip(arr, -1, 1) * 32767).astype("<i2").T.copy()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(arr.shape[0])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def _to_ogg(wav: Path, ogg: Path) -> None:
    common.run([common.ffmpeg_bin(), "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "3", str(ogg)])


def build(library: Optional[Path] = None, only: Optional[List[str]] = None, dry_run: bool = False, progress: Optional[Callable[[str], None]] = None
          ) -> Dict[str, Any]:
    lib = Path(library) if library else common.library_dir()
    index = schemas.load_library_index(lib)
    existing = {a.id: a for a in index.assets}
    say = progress or (lambda m: None)
    items = plan()
    if only:
        items = [i for i in items if i["category"] in only]
    seen: Dict[str, str] = {}
    dupes = []
    for it in items:
        if it["id"] in seen:
            dupes.append(f"{it['id']} ({seen[it['id']]} / {it['category']})")
        seen[it["id"]] = it["category"]
    if dupes:
        raise ValueError(f"duplicate ids inside the pack: {dupes[:10]}")
    skipped, written, errors = [], 0, []
    keep_ids = {it["id"] for it in items}
    new_entries: List[schemas.LibraryAsset] = []
    for n, it in enumerate(items):
        old = existing.get(it["id"])
        if old is not None and (old.meta or {}).get("pack") != PACK:
            skipped.append(f"{it['category']}:{it['id']}")
            continue
        rel = f"{it['category']}/{it['id']}{it['ext']}"
        try:
            if it["ext"] == ".svg":
                if len(it["data"].encode()) > MAX_SVG_BYTES:
                    raise ValueError(f"svg too large ({len(it['data'].encode())} bytes)")
                _validate_svg(it["data"])
            if not dry_run:
                path = lib / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                if "audio" in it:
                    x = it["audio"]()
                    if it["ext"] == ".ogg":
                        tmp = common.tmpdir() / f"{it['id']}.wav"
                        _write_wav(tmp, x, audio.SR)
                        _to_ogg(tmp, path)
                        tmp.unlink(missing_ok=True)
                    else:
                        _write_wav(path, x, audio.SR)
                else:
                    path.write_text(it["data"], encoding="utf-8")
                written += 1
            meta = {"pack": PACK, **(it.get("meta") or {})}
            entry = {"id": it["id"], "category": it["category"], "scope": it["scope"], "niche_tags": it["tags"], "file_path": rel, "meta": meta}
            if old is not None:   # keep generated thumbs/previews/usage across rebuilds
                entry.update({k: getattr(old, k) for k in ("thumb_path", "usage_count", "perceptual_hash") if getattr(old, k, None) is not None})
                if getattr(old, "preview_path", None):
                    entry["preview_path"] = old.preview_path
            for k in ("default_voice_id", "gemini_voice_name"):
                if it.get(k):
                    entry[k] = it[k]
            new_entries.append(schemas.LibraryAsset.model_validate(entry))
        except Exception as e:  # noqa: BLE001 - report every broken asset, keep going
            errors.append({"id": it["id"], "error": str(e)[:200]})
        if n % 50 == 0:
            say(f"pack {n}/{len(items)}")
    if errors:
        raise ValueError(f"{len(errors)} pack assets failed validation: {errors[:5]}")
    removed = []
    if not only:
        removed = [a.id for a in index.assets if (a.meta or {}).get("pack") == PACK and a.id not in keep_ids]
    built_ids = {e.id for e in new_entries}
    others = [a for a in index.assets if a.id not in built_ids and a.id not in removed]
    index.assets = others + new_entries
    index.updated_at_utc = datetime.now(timezone.utc)
    if not dry_run:
        for rid in removed:
            for ext in (".json", ".svg", ".wav", ".ogg"):
                for cat in schemas.CATEGORIES:
                    (lib / cat / f"{rid}{ext}").unlink(missing_ok=True)
        schemas.save_json(lib / "library_index.json", index)
    counts: Dict[str, int] = {}
    for e in new_entries:
        counts[e.category] = counts.get(e.category, 0) + 1
    return {"pack": PACK, "library": str(lib), "pack_assets": len(new_entries), "written": written, "skipped_existing": skipped,
            "removed_stale": removed, "by_category": dict(sorted(counts.items())), "library_total": len(index.assets)}


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library", type=Path)
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    res = build(a.library, [c for c in a.only.split(",") if c] or None, a.dry_run, progress=lambda m: print(m, file=sys.stderr))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
