"""Library previews: a still thumbnail for every asset and a short animated WebP for assets that move.

Files live next to the library: .thumbs/<id>.png (256 px) and .previews/<id>.webp (240 px, ~12 fps). The app shows the
still and plays the WebP once when tapped. Audio assets get a waveform still; the app plays the audio file itself.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

import common
import schemas

log = common.log

THUMB = 256
PREV = 240
FPS = 12
ANIMATED = {"01_characters", "02_poses", "03_expressions", "04_motions", "07_widgets", "08_overlays", "09_transitions", "10_caption_styles"}
AUDIO = {"12_voices", "13_bgm", "14_sfx"}
BG = "#16213a"


def _rc():
    import render_cairo
    return render_cairo


def _surface_to_image(surf, w: int, h: int):
    from PIL import Image
    surf.flush()
    return Image.frombuffer("RGBA", (w, h), bytes(surf.get_data()), "raw", "BGRA", surf.get_stride(), 1).convert("RGB")


# --------------------------------------------------------------------------- drawing one frame of any asset
class Ctx:
    def __init__(self, lib: Path, index: schemas.LibraryIndex):
        rc = _rc()
        self.rc = rc
        self.lib = Path(lib)
        self.index = index
        self.assets = rc.Assets(self.lib, (THUMB, THUMB))
        self.assets.index = index
        self.theme = dict(rc.DEFAULT_THEME)
        first_char = next((a.id for a in index.by_category("01_characters")), None)
        self.char = (self.assets.json("nova_scientist", "01_characters") or (self.assets.json(first_char, "01_characters") if first_char else None)
                     or {"rig": rc.DEFAULT_RIG})
        self.pose = self.assets.json("stand_relaxed", "02_poses") or self.assets.json("standing_neutral", "02_poses") or {"joints": {}}
        self.face = self.assets.json("smile_soft", "03_expressions") or self.assets.json("neutral", "03_expressions") or {}
        self.visemes = (self.assets.json("viseme_default", "03_expressions") or {}).get("visemes", {})


def _stage(c: Ctx, ctx, S: int, grid: bool = False) -> None:
    rc = c.rc
    rc.setc(ctx, BG, c.theme)
    ctx.paint()
    if grid:
        for i in range(1, 8):
            rc.line(ctx, S * i / 8, 0, S * i / 8, S, 1, "#22304f", c.theme)
            rc.line(ctx, 0, S * i / 8, S, S * i / 8, 1, "#22304f", c.theme)
    ctx.rectangle(0, S * 0.9, S, S * 0.1)
    rc.setc(ctx, "#0f172a", c.theme)
    ctx.fill()


def _stickman(c: Ctx, ctx, S: int, joints: Dict[str, float], t: float, expr=None, char=None, mouth=None, ms=None, airborne=False,
              scale: float = 1.0) -> Dict[str, Any]:
    rc = c.rc
    ms = ms or {}
    U = S * 0.86 * scale
    ax, ay = S * 0.5 + ms.get("character.x", 0) * S, S * 0.9 + ms.get("character.y", 0) * S
    rot, sc = ms.get("character.rot", 0.0), ms.get("character.scale", 1.0)
    ctx.save()
    ctx.translate(ax, ay)
    ctx.rotate(math.radians(rot))
    rc.safe_scale(ctx, sc, sc)
    ctx.translate(-ax, -ay)
    e = expr if expr is not None else c.face
    pts = rc.draw_character(ctx, char or c.char, {"joints": joints, "airborne": airborne}, e, mouth if mouth is not None else e.get("mouth_rest", "smile"),
                            c.theme, U, (ax, ay), ms.get("torso.scale_y", 1.0), t)
    ctx.restore()
    hx, hy = pts["head"][0] - ax, pts["head"][1] - ay
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return {"head": (ax + (hx * cr - hy * sr) * sc, ay + (hx * sr + hy * cr) * sc), "head_r": pts["_head_r"] * sc}


def _joints(c: Ctx, pose: Optional[Dict[str, Any]], extra: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    rc = c.rc
    j = {**rc.DEFAULT_POSE, **((pose or {}).get("joints") or {})}
    for k, v in (extra or {}).items():
        if k.startswith("pose."):
            j[k[5:]] = j.get(k[5:], 0.0) + v
    return j


def draw_frame(c: Ctx, ctx, entry: schemas.LibraryAsset, S: int, t: float) -> None:
    """Draw asset `entry` at preview time t (seconds) onto a SxS context."""
    rc = c.rc
    cat, aid, a = entry.category, entry.id, c.assets
    if cat == "01_characters":
        _stage(c, ctx, S)
        wave_m = a.json("wave_right", "04_motions")
        ms = rc.eval_motion(wave_m, max(0.0, t - 0.3)) if wave_m and t > 0.3 else {}
        _stickman(c, ctx, S, _joints(c, c.pose, ms), t, char=a.json(aid, cat) or c.char)
    elif cat == "02_poses":
        _stage(c, ctx, S)
        pose = a.json(aid, cat) or {"joints": {}}
        p = rc.clamp(rc.spring_step(t - 0.15, 170, 13), 0, 1.3)
        base, tgt = {**rc.DEFAULT_POSE}, {**rc.DEFAULT_POSE, **pose.get("joints", {})}
        j = {k: base[k] + (tgt[k] - base[k]) * p for k in tgt}
        _stickman(c, ctx, S, j, t, airborne=bool(pose.get("airborne")))
    elif cat == "03_expressions":
        ej = a.json(aid, cat) or {}
        rc.setc(ctx, BG, c.theme)
        ctx.paint()
        if ej.get("format") == "viseme_set/v1":
            keys = ["rest", "A", "E", "O", "M"]
            k = keys[int(t * 6) % len(keys)]
            rc.circle(ctx, S * 0.5, S * 0.52, S * 0.36, c.theme, fill="#0f172a", stroke="#f1f5f9", sw=S * 0.02)
            rc.draw_face(ctx, S * 0.5, S * 0.52, S * 0.36, {"eyes": {"open": 0.85}}, ej["visemes"].get(k, {}), t, c.theme, "#f1f5f9")
            rc.set_font(ctx, "DejaVu Sans Bold", S * 0.08)
            rc.draw_text(ctx, k, S * 0.08, S * 0.14, c.theme, "#94a3b8")
        else:
            talk = t < 1.0 and c.visemes
            mouth = (rc.viseme_at([{"word": "hello", "start": 0.0, "end": 0.95}], t, c.visemes) if talk else ej.get("mouth_rest", "flat"))
            rc.circle(ctx, S * 0.5, S * 0.52, S * 0.36, c.theme, fill="#0f172a", stroke="#f1f5f9", sw=S * 0.02)
            rc.draw_face(ctx, S * 0.5, S * 0.52, S * 0.36, ej, mouth, t + 2.3, c.theme, "#f1f5f9")
    elif cat == "04_motions":
        mj = a.json(aid, cat) or {}
        ms = rc.eval_motion(mj, t)
        ctx.save()
        cs = ms.get("camera.scale", 1.0)
        ctx.translate(S / 2 + ms.get("camera.x", 0) * S, S / 2 + ms.get("camera.y", 0) * S)
        rc.safe_scale(ctx, cs, cs)
        if ms.get("camera.rot"):
            ctx.rotate(math.radians(ms["camera.rot"]))
        ctx.translate(-S / 2, -S / 2)
        _stage(c, ctx, S, grid=True)
        _stickman(c, ctx, S, _joints(c, c.pose, ms), t, ms=ms)
        ctx.restore()
    elif cat == "07_widgets":
        rc.setc(ctx, BG, c.theme)
        ctx.paint()
        rc.draw_widget(ctx, a.json(aid, cat) or {}, S * 0.05, S * 0.18, S * 0.9, S * 0.62, c.theme, t)
    elif cat == "08_overlays":
        _stage(c, ctx, S)
        info = _stickman(c, ctx, S, _joints(c, c.pose), t, scale=0.66)
        rc.draw_overlay(ctx, a, aid, S, S, c.theme, t, info["head"], info["head_r"])
    elif cat == "09_transitions":
        tj = a.json(aid, cat) or {}
        dur = float(tj.get("duration_sec", 0.3))

        def scene(col, label):
            def f():
                rc.setc(ctx, col, c.theme)
                ctx.paint()
                rc.set_font(ctx, "DejaVu Sans Bold", S * 0.22)
                rc.draw_text(ctx, label, S / 2 - rc.text_width(ctx, label) / 2, S * 0.6, c.theme, "#0f172a")
            return f
        if t < 0.35:
            scene("#f472b6", "A")()
        else:
            scene("#f472b6", "A")()
            rc.draw_with_transition(ctx, tj, t - 0.35, S, S, scene("#22d3ee", "B"))
        if t >= 0.35 + dur + 0.6:
            scene("#22d3ee", "B")()
    elif cat == "10_caption_styles":
        cj = a.json(aid, cat) or {}
        rc.setc(ctx, BG, c.theme)
        ctx.paint()
        words = [{"word": w, "start": i * 0.32, "end": i * 0.32 + 0.3} for i, w in enumerate("THIS IS HOW IT POPS".split())]
        rc.draw_captions(ctx, {**cj, "position_y": 0.55, "size_ratio": cj.get("size_ratio", 0.06) * 1.3}, words, t, S, S, c.theme)
    else:
        raise ValueError(f"no animated preview for {cat}")


def preview_duration(c: Ctx, entry: schemas.LibraryAsset) -> float:
    cat = entry.category
    if cat == "04_motions":
        mj = c.assets.json(entry.id, cat) or {}
        d = float(mj.get("duration_sec", 1.0))
        if mj.get("loop"):
            return min(2.5, max(1.2, d * max(1, round(1.6 / max(d, 0.1)))))
        return min(2.5, d + 0.6)
    if cat == "09_transitions":
        return 0.35 + float((c.assets.json(entry.id, cat) or {}).get("duration_sec", 0.3)) + 0.6
    return {"01_characters": 2.0, "02_poses": 1.3, "03_expressions": 1.6, "07_widgets": 2.2, "08_overlays": 1.8, "10_caption_styles": 1.9}.get(cat, 1.5)


def write_preview(c: Ctx, entry: schemas.LibraryAsset, out: Path, size: int = PREV, fps: int = FPS) -> int:
    rc = c.rc
    import cairo
    dur = preview_duration(c, entry)
    n = max(2, int(round(dur * fps)))
    frames = []
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    for i in range(n):
        ctx = cairo.Context(surf)
        draw_frame(c, ctx, entry, size, i / fps)
        frames.append(_surface_to_image(surf, size, size))
        del ctx
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, "WEBP", save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, quality=72, method=4)
    _ = rc
    return n


# --------------------------------------------------------------------------- stills
def _audio_samples(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as w:
            raw = w.readframes(w.getnframes())
            x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
            return x[:: w.getnchannels()]
    import audio_master
    return audio_master.decode(path, 8000, 1).astype(np.float32)


def _waveform(c: Ctx, ctx, S: int, entry: schemas.LibraryAsset) -> None:
    rc = c.rc
    rc.setc(ctx, BG, c.theme)
    ctx.paint()
    col = "#a78bfa" if entry.category == "13_bgm" else "#22d3ee"
    try:
        x = _audio_samples(c.lib / entry.file_path)
    except Exception:  # noqa: BLE001
        x = np.zeros(1000)
    bars = 48
    chunk = max(1, len(x) // bars)
    peaks = [float(np.max(np.abs(x[i * chunk:(i + 1) * chunk]))) if len(x[i * chunk:(i + 1) * chunk]) else 0.0 for i in range(bars)]
    m = max(peaks) or 1.0
    for i, p in enumerate(peaks):
        h = max(2.0, S * 0.5 * p / m)
        rc.rrect(ctx, S * 0.08 + i * S * 0.84 / bars, S * 0.5 - h / 2, S * 0.84 / bars * 0.65, h, 1.5)
        rc.setc(ctx, col, c.theme)
        ctx.fill()
    rc.set_font(ctx, "DejaVu Sans Bold", S * 0.075)
    label = "MUSIC" if entry.category == "13_bgm" else "SFX"
    rc.draw_text(ctx, label, S * 0.08, S * 0.16, c.theme, col)
    secs = len(x) / (8000.0 if entry.category == "13_bgm" else 44100.0)
    rc.draw_text(ctx, f"{secs:.1f}s", S * 0.92 - rc.text_width(ctx, f"{secs:.1f}s"), S * 0.16, c.theme, "#94a3b8")
    rc.draw_text(ctx, "▶", S * 0.46, S * 0.9, c.theme, "#f8fafc")


def _voice_card(c: Ctx, ctx, S: int, entry: schemas.LibraryAsset) -> None:
    rc = c.rc
    rc.setc(ctx, BG, c.theme)
    ctx.paint()
    vj = c.assets.json(entry.id, entry.category) or {}
    rc.rrect(ctx, S * 0.4, S * 0.12, S * 0.2, S * 0.36, S * 0.1)
    rc.setc(ctx, "#f472b6", c.theme)
    ctx.fill()
    ctx.new_path()
    ctx.arc(S * 0.5, S * 0.36, S * 0.17, 0, math.pi)
    rc.setc(ctx, "#f8fafc", c.theme)
    ctx.set_line_width(S * 0.025)
    ctx.stroke()
    rc.line(ctx, S * 0.5, S * 0.53, S * 0.5, S * 0.6, S * 0.025, "#f8fafc", c.theme)
    name = str(vj.get("gemini_voice_name") or entry.gemini_voice_name or entry.id)
    rc.set_font(ctx, "DejaVu Sans Bold", S * 0.1)
    rc.draw_text(ctx, name, S / 2 - rc.text_width(ctx, name) / 2, S * 0.75, c.theme, "#f8fafc")
    style = str(vj.get("voice_character") or "")
    rc.set_font(ctx, "DejaVu Sans", S * 0.065)
    rc.draw_text(ctx, style, S / 2 - rc.text_width(ctx, style) / 2, S * 0.86, c.theme, "#94a3b8")


def write_thumb(c: Ctx, entry: schemas.LibraryAsset, out: Path, size: int = THUMB) -> None:
    import cairo
    rc = c.rc
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surf)
    cat = entry.category
    if cat in ("13_bgm", "14_sfx"):
        _waveform(c, ctx, size, entry)
    elif cat == "12_voices":
        _voice_card(c, ctx, size, entry)
    elif cat in ANIMATED:
        t = {"01_characters": 0.0, "02_poses": 1.2, "03_expressions": 1.3, "07_widgets": 2.2, "08_overlays": 0.7, "10_caption_styles": 0.75}.get(cat)
        if cat == "04_motions":
            t = preview_duration(c, entry) * 0.35
        elif cat == "09_transitions":
            tj = c.assets.json(entry.id, cat) or {}
            t = 0.35 + float(tj.get("duration_sec", 0.3)) * 0.5
        draw_frame(c, ctx, entry, size, t)
    else:
        rc.render_asset_thumbnail(c.lib, entry.model_dump(), out, size, assets=c.assets)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    surf.write_to_png(str(out))


# --------------------------------------------------------------------------- batch
def build_all(library: Optional[Path] = None, only_missing: bool = False, ids: Optional[List[str]] = None,
              progress: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    import forge
    lib = Path(library) if library else common.library_dir()
    index = schemas.load_library_index(lib)
    c = Ctx(lib, index)
    say = progress or (lambda m: None)
    thumbs_dir, prev_dir = lib / ".thumbs", lib / ".previews"
    done_t = done_p = 0
    failed: List[Dict[str, str]] = []
    todo = [a for a in index.assets if (ids is None or a.id in ids)]
    for n, a in enumerate(todo):
        tp, pp = thumbs_dir / f"{a.id}.png", prev_dir / f"{a.id}.webp"
        try:
            if not (only_missing and tp.is_file()):
                write_thumb(c, a, tp)
                if a.category in forge.THUMB_CATS and not (a.category == "08_overlays" and a.file_path.endswith(".json")):
                    a.perceptual_hash = forge.phash_image(tp)
                elif a.category == "08_overlays":
                    a.perceptual_hash = None   # JSON overlays share the same stickman still: no visual dedup
                done_t += 1
            a.thumb_path = f".thumbs/{a.id}.png"
            if a.category in ANIMATED:
                if not (only_missing and pp.is_file()):
                    write_preview(c, a, pp)
                    done_p += 1
                a.preview_path = f".previews/{a.id}.webp"
        except Exception as e:  # noqa: BLE001 - one bad asset must not stop the batch
            failed.append({"id": a.id, "error": str(e)[:200]})
            log.warning("preview failed for %s: %s", a.id, e)
        if n % 25 == 0:
            say(f"previews {n}/{len(todo)}")
        if n % 150 == 149:
            schemas.save_json(lib / "library_index.json", index)
    dupes = []
    for cat in forge.DEDUP_CATS:
        items = [x for x in index.by_category(cat) if x.perceptual_hash]
        for i, x in enumerate(items):
            for y in items[i + 1:]:
                s = forge.hash_similarity(x.perceptual_hash, y.perceptual_hash)
                if s >= schemas.PHASH_DEDUP_THRESHOLD:
                    dupes.append({"a": x.id, "b": y.id, "similarity": round(s, 3)})
    from datetime import datetime, timezone
    index.updated_at_utc = datetime.now(timezone.utc)
    schemas.save_json(lib / "library_index.json", index)
    return {"rendered": done_t, "previews": done_p, "failed": failed, "near_duplicates": dupes[:50], "near_duplicate_count": len(dupes)}
