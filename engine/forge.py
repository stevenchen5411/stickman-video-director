#!/usr/bin/env python3
"""AI Asset Forge: synthesize SVG/JSON/WAV assets, render 256x256 pycairo thumbnails, 85% pHash dedup.

CLI:
  python3 engine/forge.py --rebuild-thumbs [--library DIR] [--only-missing]
  python3 engine/forge.py --forge 06_props:magnifying_glass --brief "..." [--scope specific --tags a,b]
  python3 engine/forge.py --check-dupes
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import common
import schemas

log = common.log
THUMB_SIZE = 256
THUMB_CATS = {"01_characters", "02_poses", "03_expressions", "04_motions", "05_scenes", "06_props",
              "07_widgets", "08_overlays", "09_transitions", "10_caption_styles", "11_themes"}
DEDUP_CATS = {"05_scenes", "06_props", "07_widgets", "08_overlays"}   # visually distinctive categories
SVG_CATS = {"05_scenes", "06_props", "08_overlays"}
AUDIO_CATS = {"12_voices", "13_bgm", "14_sfx"}
MAX_SVG_BYTES = 60_000
SR = 44100


# --------------------------------------------------------------------------- perceptual hash
def phash_gray(gray32: np.ndarray) -> str:
    """64-bit pHash of a 32x32 grayscale array -> 16 hex chars (DCT, median of 8x8 low-freq block)."""
    n = 32
    k = np.arange(n)
    dct = np.cos(np.pi * (2 * k[None, :] + 1) * k[:, None] / (2 * n))
    low = (dct @ gray32.astype(np.float64) @ dct.T)[:8, :8]
    bits = (low > np.median(low.flatten()[1:])).flatten()
    val = 0
    for b in bits:
        val = (val << 1) | int(b)
    return f"{val:016x}"


def phash_image(path: Path) -> str:
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    g = bg.convert("L").resize((32, 32), Image.LANCZOS)
    return phash_gray(np.asarray(g))


def hash_similarity(a: Optional[str], b: Optional[str]) -> float:
    if not a or not b or len(a) != 16 or len(b) != 16:
        return 0.0
    return 1.0 - bin(int(a, 16) ^ int(b, 16)).count("1") / 64.0


def find_duplicate(index: schemas.LibraryIndex, category: str, new_hash: str,
                   threshold: float = schemas.PHASH_DEDUP_THRESHOLD, ignore_id: Optional[str] = None
                   ) -> Optional[Tuple[str, float]]:
    best: Optional[Tuple[str, float]] = None
    for a in index.by_category(category):
        if a.id == ignore_id:
            continue
        s = hash_similarity(new_hash, a.perceptual_hash)
        if s >= threshold and (best is None or s > best[1]):
            best = (a.id, s)
    return best


# --------------------------------------------------------------------------- thumbnails
def _renderer():
    import render_cairo  # needs pycairo (+cairosvg for SVG assets)
    return render_cairo


def rebuild_thumbs(library: Optional[Path] = None, only_missing: bool = False, progress=None) -> Dict[str, Any]:
    """Still thumbnails for every asset + animated previews for moving ones (see previews.py)."""
    import previews
    return previews.build_all(library, only_missing, progress=progress)


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- SVG validation
_BAD_SVG = re.compile(r"<\s*script|foreignObject|<!DOCTYPE|<!ENTITY|\son\w+\s*=|javascript:", re.I)
_HREF = re.compile(r"""href\s*=\s*["']([^"']*)["']""", re.I)


def validate_svg(text: str) -> str:
    """Return cleaned SVG or raise ValueError. Rejects scripts, external refs, oversize, bad XML."""
    text = text.strip()
    text = re.sub(r"^```(?:svg|xml)?\s*|\s*```$", "", text, flags=re.S).strip()
    if len(text.encode()) > MAX_SVG_BYTES:
        raise ValueError("svg too large")
    if _BAD_SVG.search(text):
        raise ValueError("svg contains forbidden content")
    for h in _HREF.findall(text):
        if not h.startswith("#"):
            raise ValueError("svg has external href")
    root = ET.fromstring(text)
    if not root.tag.endswith("svg"):
        raise ValueError("root is not <svg>")
    if "viewBox" not in root.attrib:
        raise ValueError("svg needs a viewBox")
    return text


# --------------------------------------------------------------------------- procedural fallbacks
def _hue(seed: str) -> int:
    return int(hashlib.sha1(seed.encode()).hexdigest()[:4], 16) % 360


def fallback_svg(category: str, aid: str, tags: List[str]) -> str:
    h = _hue(aid)
    label = (aid.replace("_", " ").split() or ["?"])[0][:10].upper()
    if category == "05_scenes":
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="hsl({h},45%,18%)"/><stop offset="1" stop-color="hsl({(h + 40) % 360},40%,32%)"/></linearGradient></defs>'
                f'<g id="back"><rect width="1080" height="1920" fill="url(#g)"/></g><g id="mid"><circle cx="540" cy="780" r="360" fill="hsl({h},60%,60%)" opacity="0.12"/></g>'
                f'<g id="ground"><rect y="1480" width="1080" height="440" fill="hsl({h},40%,10%)"/></g></svg>')
    if category == "08_overlays":
        pts = " ".join(f"{540 + (320 + 120 * (i % 2)) * np.cos(i * np.pi / 8):.0f},{960 + (320 + 120 * (i % 2)) * np.sin(i * np.pi / 8):.0f}" for i in range(16))
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920"><polygon points="{pts}" fill="hsl({h},90%,60%)" opacity="0.85"/></svg>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><circle cx="128" cy="128" r="96" fill="hsl({h},65%,55%)" '
            f'stroke="#0f172a" stroke-width="8"/><text x="128" y="148" font-family="DejaVu Sans" font-size="40" font-weight="bold" '
            f'text-anchor="middle" fill="#0f172a">{label}</text></svg>')


def _exemplar(lib: Path, index: schemas.LibraryIndex, category: str) -> Dict[str, Any]:
    for a in index.by_category(category):
        if a.file_path.endswith(".json"):
            return schemas.load_json(lib / a.file_path)
    return {}


# --------------------------------------------------------------------------- audio synthesis
def _write_wav(path: Path, data: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.atleast_2d(data)
    pcm = (np.clip(arr, -1, 1) * 32767).astype("<i2").T.copy()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(arr.shape[0])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def synth_sfx(spec: Dict[str, Any], seed: str) -> np.ndarray:
    """spec: {kind: tick|thud|whoosh|pop|ding|glitch|noise, freq, duration, decay}; duration capped < 1.5 s."""
    rng = np.random.default_rng(int(hashlib.sha1(seed.encode()).hexdigest()[:8], 16))
    kind = spec.get("kind", "pop")
    dur = float(min(1.4, max(0.05, spec.get("duration", 0.3))))
    f = float(min(8000, max(40, spec.get("freq", 600))))
    decay = float(max(0.01, spec.get("decay", dur / 4)))
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t / decay) * np.minimum(1, t / 0.003)
    if kind == "tick":
        sig = np.sin(2 * np.pi * f * t) * 0.7 + rng.standard_normal(n) * 0.3
    elif kind == "thud":
        sig = np.sin(2 * np.pi * np.cumsum(f * 0.1 + f * 0.1 * np.exp(-t / 0.05)) / SR)
    elif kind == "whoosh":
        env = np.sin(np.pi * t / t[-1]) ** 2
        sig = np.convolve(rng.standard_normal(n), np.ones(6) / 6, mode="same") + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 0.5 + 4 * f * (t / t[-1]) ** 2) / SR)
    elif kind == "ding":
        sig = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)
    elif kind == "glitch":
        steps = np.repeat(rng.choice([f * 0.5, f, f * 1.5, f * 2], size=9), n // 9 + 1)[:n]
        sig = np.sign(np.sin(2 * np.pi * np.cumsum(steps) / SR)) * 0.5
    elif kind == "noise":
        sig = rng.standard_normal(n)
    else:  # pop
        sig = np.sin(2 * np.pi * np.cumsum(f * 0.3 + f * np.exp(-t / 0.02)) / SR)
    out = sig * env
    return out * (0.8 / (np.max(np.abs(out)) or 1.0))


def synth_bgm(bpm: float, root_hz: float, mood: str, dur: float = 16.0) -> np.ndarray:
    """Seamless stereo loop: sine pad (integer cycles per loop) + pulse. Returns shape (2, n)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    snap = lambda f: round(f * dur) / dur  # noqa: E731
    minor = mood in ("tense", "dark", "sad")
    ratios = [1, 1.1892 if minor else 1.2599, 1.4983]
    pad = sum(np.sin(2 * np.pi * snap(root_hz * r) * t) for r in ratios) * (0.7 + 0.3 * np.sin(2 * np.pi * t / dur * 2))
    beat = 60.0 / bpm
    pulse = np.zeros(n)
    k = int(0.18 * SR)
    kt = np.arange(k) / SR
    thump = np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-kt / 0.03)) / SR) * np.exp(-kt / 0.08)
    for i in range(int(dur / beat)):
        s = int(i * beat * SR)
        idx = (s + np.arange(k)) % n
        np.add.at(pulse, idx, thump * (0.9 if i % 4 == 0 else 0.5))
    mix = pad * 0.25 + pulse * 0.4
    mix = mix * (0.7 / (np.max(np.abs(mix)) or 1.0))
    return np.vstack([mix, np.roll(mix, 211)])


def _to_ogg(wav: Path, ogg: Path) -> None:
    ogg.parent.mkdir(parents=True, exist_ok=True)
    common.run([common.ffmpeg_bin(), "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "4", str(ogg)])


# --------------------------------------------------------------------------- LLM synthesis
_SYSTEM = ("You design assets for a procedural stickman video renderer. Reply with ONE JSON object and nothing else. "
           "Put the answer fields (for example svg, anchors, asset) at the TOP LEVEL of that object; do not repeat the task or rules.")


LAST_ANCHORS: Dict[str, Any] = {}
PREFER: Optional[str] = None      # provider to try first (set per forge call, e.g. "gemini")


def _ask(prompt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        import llm
        data, _ = llm.call_json(_SYSTEM, json.dumps(prompt), prefer=PREFER)
        if isinstance(data, dict) and isinstance(data.get("output"), dict):   # web models echo the prompt layout: unwrap it
            data = {**{k: v for k, v in data.items() if k != "output"}, **data["output"]}
        return data
    except Exception as e:  # noqa: BLE001
        log.info("forge: no AI synthesis (%s)", str(e)[:100])
        return None


def _ai_svg(category: str, aid: str, brief: str, tags: List[str]) -> Optional[str]:
    vb = "0 0 256 256" if category == "06_props" else "0 0 1080 1920"
    extra = ("Group layers as <g id=\"back\">, <g id=\"mid\">, <g id=\"ground\">. " if category == "05_scenes" else "")
    data = _ask({"task": f"Write a flat-vector SVG for asset '{aid}' ({category}). Brief: {brief}. Tags: {tags}.",
                 "rules": [f"viewBox must be \"{vb}\"; solid fills/strokes/gradients only; no text-heavy art, no scripts, "
                           "no external references, under 8KB. " + extra,
                           "Style: bold flat shapes, thick dark outlines (stroke-width 6-8) for props, high contrast."],
                 "output": {"svg": "<svg ...>...</svg>",
                            "anchors": {"seat": [128, 150]} if category == "06_props" else {}},
                 "anchors_help": "optional named attach points in the 256x256 viewBox where a character touches the prop: "
                                 "seat (pelvis rests here), floor (feet stand here), inside (torso/hips sit inside), hand (hands grip here)."})
    if not data or not isinstance(data.get("svg"), str):
        return None
    LAST_ANCHORS.clear()
    if isinstance(data.get("anchors"), dict):
        for k, v in data["anchors"].items():
            if isinstance(k, str) and isinstance(v, list) and len(v) == 2 and all(isinstance(n, (int, float)) for n in v):
                LAST_ANCHORS[k[:20]] = [round(float(max(0, min(256, v[0]))), 1), round(float(max(0, min(256, v[1]))), 1)]
    try:
        return validate_svg(data["svg"])
    except Exception as e:  # noqa: BLE001
        log.warning("forge: AI svg rejected: %s", e)
        return None


def _ai_json(lib: Path, index: schemas.LibraryIndex, category: str, aid: str, brief: str, tags: List[str]
             ) -> Optional[Dict[str, Any]]:
    ex = _exemplar(lib, index, category)
    if not ex:
        return None
    data = _ask({"task": f"Create a NEW '{category}' asset id '{aid}'. Brief: {brief}. Tags: {tags}.",
                 "rules": ["Follow the exemplar's exact keys, nesting, value types and `format` string.",
                           "Change values meaningfully so the result is visually/behaviourally different from the exemplar."]
                 + (["Joint angles are degrees from straight DOWN for hips/shoulders (0 = hanging down, +/-90 = horizontal, 180 = up); "
                     "knee bends the shin back; torso_lean tilts the body from vertical; neck tilts the head. Feet are auto-grounded, "
                     "so a seated pose is hips about 85-90 and knees about 85-95 with the torso upright; a slump/sad pose leans the torso and neck forward and drops the arms; "
                     "mirror l_/r_ values sensibly; keep every key from the exemplar."] if category == "02_poses" else []),
                 "exemplar": ex, "output": {"asset": "<same structure as exemplar>"}})
    asset = (data or {}).get("asset")
    if isinstance(asset, dict) and asset.get("format") == ex.get("format") and set(asset) >= (set(ex) - {"id"}):
        return asset
    return None


# --------------------------------------------------------------------------- forging
def _register(index: schemas.LibraryIndex, entry: Dict[str, Any]) -> None:
    index.assets.append(schemas.LibraryAsset.model_validate(entry))
    index.updated_at_utc = _now()


def forge_asset(category: str, aid: str, brief: str = "", scope: str = "global", tags: Optional[List[str]] = None,
                library: Optional[Path] = None, use_ai: bool = True, prefer: Optional[str] = None) -> Dict[str, Any]:
    """Create one asset. Returns {status: created|exists|duplicate, id, ...}. Never raises on AI failure."""
    global PREFER
    PREFER = prefer
    lib = Path(library) if library else common.library_dir()
    if category not in schemas.CATEGORIES:
        raise ValueError(f"unknown category {category}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]*", aid):
        raise ValueError(f"invalid asset id {aid!r}")
    index = schemas.load_library_index(lib)
    if index.get(aid):
        return {"status": "exists", "id": aid}
    tags = tags or ["general"]
    brief = brief or aid.replace("_", " ")
    entry: Dict[str, Any] = {"id": aid, "category": category, "scope": scope, "niche_tags": tags, "usage_count": 0}
    written: List[Path] = []
    ai_used = False

    if category in SVG_CATS:
        svg = _ai_svg(category, aid, brief, tags) if use_ai else None
        ai_used = svg is not None
        svg = svg or fallback_svg(category, aid, tags)
        rel = f"{category}/{aid}.svg"
        (lib / category).mkdir(parents=True, exist_ok=True)
        (lib / rel).write_text(svg + "\n", encoding="utf-8")
        written.append(lib / rel)
        if category == "06_props" and ai_used and LAST_ANCHORS:
            entry["meta"] = {"anchors": dict(LAST_ANCHORS), "anchor_viewbox": 256}
    elif category == "14_sfx":
        spec = (_ask({"task": f"Describe a short sound effect '{aid}'. Brief: {brief}",
                      "output": {"kind": "tick|thud|whoosh|pop|ding|glitch|noise", "freq": 600, "duration": 0.3, "decay": 0.1}})
                if use_ai else None) or {}
        data = synth_sfx(spec, aid)
        rel = f"{category}/{aid}.wav"
        _write_wav(lib / rel, data, SR)
        written.append(lib / rel)
        entry["meta"] = {"duration_sec": round(len(data) / SR, 3), "sample_rate": SR}
    elif category == "13_bgm":
        spec = (_ask({"task": f"Describe a looping instrumental bed '{aid}'. Brief: {brief}",
                      "output": {"bpm": 90, "root_hz": 110, "mood": "calm|tense|upbeat|dark"}}) if use_ai else None) or {}
        bpm = float(min(160, max(50, spec.get("bpm", 90))))
        mood = spec.get("mood") if spec.get("mood") in ("calm", "tense", "upbeat", "dark") else "calm"
        tmp = common.tmpdir() / f"forge_{aid}.wav"
        _write_wav(tmp, synth_bgm(bpm, float(min(220, max(55, spec.get("root_hz", 110)))), mood), SR)
        rel = f"{category}/{aid}.ogg"
        _to_ogg(tmp, lib / rel)
        tmp.unlink(missing_ok=True)
        written.append(lib / rel)
        entry["meta"] = {"bpm": bpm, "mood": mood, "loop_sec": 16.0, "loop": True}
    elif category == "12_voices":
        import tts_expressive
        vname = next((v for v in schemas.GEMINI_VOICES if v.lower() in aid), schemas.GEMINI_VOICES[_hue(aid) % 5])
        rel = f"{category}/{aid}.json"
        prev = f"{category}/{aid}_preview.wav"
        persona = {"id": aid, "format": "voice_persona/v1", "type": "prebuilt", "gemini_voice_name": vname,
                   "tts_model": "gemini-3.8-flash-tts", "default_style": brief[:200], "pace_multiplier": 1.0,
                   "preview_audio_path": prev, "preview_is_placeholder": True}
        (lib / category).mkdir(parents=True, exist_ok=True)
        (lib / rel).write_text(json.dumps(persona, indent=2) + "\n", encoding="utf-8")
        _write_wav(lib / prev, tts_expressive.placeholder_speech("preview", vname, 1.2)[0], tts_expressive.SR)
        written += [lib / rel, lib / prev]
        entry.update({"gemini_voice_name": vname, "preview_audio_path": prev})
    else:  # JSON categories (characters, poses, expressions, motions, widgets, transitions, captions, themes)
        asset = _ai_json(lib, index, category, aid, brief, tags) if use_ai else None
        ai_used = asset is not None
        if asset is None:
            asset = dict(_exemplar(lib, index, category))
            asset.pop("id", None)
            if category == "01_characters":
                asset["name"] = aid.split("_")[0].title()
                asset["colors"] = {**asset.get("colors", {}), "accent": f"#{hashlib.sha1(aid.encode()).hexdigest()[:6]}"}
            asset["procedural_fallback"] = True
        rel = f"{category}/{aid}.json"
        (lib / category).mkdir(parents=True, exist_ok=True)
        (lib / rel).write_text(json.dumps({"id": aid, **asset}, indent=2) + "\n", encoding="utf-8")
        written.append(lib / rel)
        if category == "01_characters":
            entry["default_voice_id"] = asset.get("default_voice_id")

    entry["file_path"] = rel
    entry["perceptual_hash"] = hashlib.sha1((lib / rel).read_bytes()).hexdigest()[:12]
    if category in THUMB_CATS:
        entry["thumb_path"] = f".thumbs/{aid}.png"
        try:
            thumb = lib / ".thumbs" / f"{aid}.png"
            thumb.parent.mkdir(parents=True, exist_ok=True)
            if category in SVG_CATS and rel.endswith(".svg"):
                # not registered in the index yet, so the index-based renderer would draw a generic placeholder for it
                import cairosvg
                cairosvg.svg2png(bytestring=(lib / rel).read_bytes(), write_to=str(thumb), output_width=THUMB_SIZE,
                                 output_height=THUMB_SIZE, background_color="#ffffff")
            else:
                _renderer().render_asset_thumbnail(lib, entry, thumb, THUMB_SIZE)
            h = phash_image(thumb)
            if category in DEDUP_CATS and not (category == "08_overlays" and rel.endswith(".json")):
                dup = find_duplicate(index, category, h)
                if dup:
                    for p in written + [thumb]:
                        p.unlink(missing_ok=True)
                    log.info("forge: %s is %.0f%% similar to %s; reusing it", aid, dup[1] * 100, dup[0])
                    return {"status": "duplicate", "id": aid, "duplicate_of": dup[0], "similarity": round(dup[1], 3)}
            entry["perceptual_hash"] = h
        except ImportError:
            log.info("forge: pycairo/cairosvg unavailable; thumbnail deferred to --rebuild-thumbs")
            entry.pop("thumb_path", None)
        except Exception as e:  # noqa: BLE001
            log.warning("forge: thumbnail failed for %s: %s", aid, e)
    _register(index, entry)
    schemas.save_json(lib / "library_index.json", index)
    return {"status": "created", "id": aid, "category": category, "ai": ai_used}


def forge_missing(missing: List[str], niche: str = "general", library: Optional[Path] = None,
                  use_ai: bool = True) -> List[Dict[str, Any]]:
    """`missing` items are 'category:id'. Returns per-item results; duplicates are reported, not created."""
    results = []
    for item in missing:
        cat, _, aid = item.partition(":")
        try:
            tag = re.sub(r"[^a-z0-9]+", "_", niche.lower()).strip("_") or "general"
            results.append(forge_asset(cat, aid, f"asset for a '{niche}' video", scope="specific",
                                       tags=[tag], library=library, use_ai=use_ai))
        except Exception as e:  # noqa: BLE001
            log.warning("forge %s failed: %s", item, e)
            results.append({"status": "failed", "id": aid, "error": str(e)[:200]})
    return results


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rebuild-thumbs", action="store_true")
    ap.add_argument("--only-missing", action="store_true")
    ap.add_argument("--forge", metavar="CATEGORY:ID")
    ap.add_argument("--brief", default="")
    ap.add_argument("--scope", default="global", choices=["global", "specific"])
    ap.add_argument("--tags", default="general")
    ap.add_argument("--no-ai", action="store_true")
    ap.add_argument("--check-dupes", action="store_true")
    ap.add_argument("--library")
    a = ap.parse_args(argv)
    lib = Path(a.library) if a.library else None
    rc = 0
    if a.rebuild_thumbs:
        r = rebuild_thumbs(lib, a.only_missing)
        print(f"thumbnails rendered: {r['rendered']}, failed: {len(r['failed'])}, near-duplicates: {len(r['near_duplicates'])}")
        for f in r["failed"]:
            print("  FAIL", f)
        for d in r["near_duplicates"]:
            print("  DUP ", d)
        rc |= 1 if r["failed"] else 0
    if a.forge:
        cat, _, aid = a.forge.partition(":")
        print(json.dumps(forge_asset(cat, aid, a.brief, a.scope, a.tags.split(","), lib, not a.no_ai)))
    if a.check_dupes:
        index = schemas.load_library_index(lib or common.library_dir())
        for cat in DEDUP_CATS:
            items = index.by_category(cat)
            for i, x in enumerate(items):
                for y in items[i + 1:]:
                    s = hash_similarity(x.perceptual_hash, y.perceptual_hash)
                    if s >= schemas.PHASH_DEDUP_THRESHOLD:
                        print(f"{cat}: {x.id} ~ {y.id} ({s:.0%})")
    if not (a.rebuild_thumbs or a.forge or a.check_dupes):
        ap.print_help()
    return rc


if __name__ == "__main__":
    sys.exit(main())
