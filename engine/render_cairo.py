#!/usr/bin/env python3
"""Procedural stickman renderer: pycairo compositor -> raw RGBA frames -> FFmpeg stdin (zero-disk video pipe).

Audio-first: TTS -> mastering -> exact scene frame spans from the real vocal timeline -> frames. Per-frame PNGs are
never written; frames are composited in RAM and streamed to `ffmpeg -f rawvideo -pix_fmt rgba`.

Modes: --keyframes-only (one JPG per scene + cover), --draft-480p (480x854 @30, Termux), --hd-1080p60 (CI).
CLI: python3 engine/render_cairo.py --package PATH (--keyframes-only | --draft-480p | --hd-1080p60) --out DIR
Also exposes render_asset_thumbnail() used by forge.py (256x256 library thumbnails).
"""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cairo
import numpy as np

import audio_master
import common
import layout
import schemas

log = common.log

MODES = {"keyframes": (480, 30), "draft": (480, 30), "hd": (1080, 60)}   # (short side px, fps)
DEFAULT_THEME = {"bg": "#0f172a", "surface": "#1e293b", "line": "#e2e8f0", "text": "#f8fafc",
                 "accent": "#22d3ee", "accent2": "#f472b6", "highlight": "#facc15", "danger": "#f87171"}
VISEME_BY_LETTER = {"a": "A", "e": "E", "i": "E", "y": "E", "o": "O", "u": "O", "w": "O", "b": "M", "m": "M", "p": "M"}


def dims_for(aspect: str, mode: str) -> Tuple[int, int, int]:
    short, fps = MODES[mode]
    even = lambda v: int(round(v / 2.0)) * 2  # noqa: E731
    if aspect == "16:9":
        return even(short * 16 / 9), short, fps
    if aspect == "1:1":
        return short, short, fps
    return short, even(short * 16 / 9), fps


# =========================================================================== math / easing
def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def ease(name: str, u: float) -> float:
    u = clamp(u)
    if name == "ease_in":
        return u * u
    if name == "ease_out":
        return 1 - (1 - u) ** 2
    if name == "ease_in_out":
        return u * u * (3 - 2 * u)
    if name == "expo_out":
        return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)
    if name == "expo_in":
        return 0.0 if u <= 0 else 2 ** (10 * (u - 1))
    if name == "sine":
        return 0.5 - 0.5 * math.cos(math.pi * u)
    return u


def spring_step(t: float, stiffness: float = 260.0, damping: float = 14.0) -> float:
    """Unit step response of a damped spring (overshoots then settles to 1)."""
    if t <= 0:
        return 0.0
    w = math.sqrt(stiffness)
    z = damping / (2 * w)
    if z < 1:
        wd = w * math.sqrt(1 - z * z)
        return 1 - math.exp(-z * w * t) * (math.cos(wd * t) + (z * w / wd) * math.sin(wd * t))
    return 1 - math.exp(-w * t) * (1 + w * t)


def eval_track(keys: List[List[Any]], t: float, spring: Dict[str, float]) -> float:
    if not keys:
        return 0.0
    if t <= keys[0][0]:
        return float(keys[0][1])
    for k0, k1 in zip(keys, keys[1:]):
        if t < k1[0]:
            span = max(1e-6, k1[0] - k0[0])
            kind = k1[2] if len(k1) > 2 else "linear"
            p = spring_step(t - k0[0], spring.get("stiffness", 260), spring.get("damping", 14)) \
                if kind == "spring" else ease(kind, (t - k0[0]) / span)
            return float(k0[1]) + (float(k1[1]) - float(k0[1])) * p
    return float(keys[-1][1])


def eval_motion(motion: Optional[Dict[str, Any]], t: float) -> Dict[str, float]:
    st = {"camera.scale": 1.0, "camera.x": 0.0, "camera.y": 0.0, "camera.rot": 0.0, "character.x": 0.0,
          "character.y": 0.0, "character.rot": 0.0, "character.scale": 1.0, "torso.scale_y": 1.0, "object.scale": 1.0}
    if not motion:
        return st
    dur = max(1e-3, float(motion.get("duration_sec", 1.0)))
    tt = (t % dur) if motion.get("loop") else min(t, dur)
    for tr in motion.get("tracks", []):
        st[tr["target"]] = eval_track(tr["keys"], tt, motion.get("spring", {}))
    return st


# =========================================================================== colour / theme
def hex_rgba(c: Any, theme: Dict[str, str]) -> Tuple[float, float, float, float]:
    if isinstance(c, str) and c.startswith("theme."):
        c = theme.get(c[6:], "#ff00ff")
    if not isinstance(c, str) or not c.startswith("#"):
        return (1.0, 0.0, 1.0, 1.0)
    h = c[1:]
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) not in (6, 8):
        return (1.0, 0.0, 1.0, 1.0)
    vals = [int(h[i:i + 2], 16) / 255.0 for i in range(0, len(h), 2)]
    return (vals[0], vals[1], vals[2], vals[3] if len(vals) == 4 else 1.0)


def setc(ctx, c: Any, theme: Dict[str, str], alpha: float = 1.0) -> None:
    r, g, b, a = hex_rgba(c, theme)
    ctx.set_source_rgba(r, g, b, a * alpha)


# =========================================================================== library access
class Assets:
    """Cached access to library assets; every lookup is failure-tolerant (callers fall back to visual aids)."""

    def __init__(self, lib: Path, size: Tuple[int, int]):
        self.lib = Path(lib)
        self.index = schemas.load_library_index(self.lib)
        self.size = size
        self._json: Dict[str, Optional[Dict[str, Any]]] = {}
        self._surf: Dict[Tuple[str, int, int], Any] = {}

    def entry(self, aid: Optional[str], cat: str):
        return self.index.get(aid, cat) if aid else None

    def json(self, aid: Optional[str], cat: str) -> Optional[Dict[str, Any]]:
        key = f"{cat}:{aid}"
        if key not in self._json:
            e = self.entry(aid, cat)
            try:
                self._json[key] = schemas.load_json(self.lib / e.file_path) if e and e.file_path.endswith(".json") else None
            except Exception as ex:  # noqa: BLE001
                log.warning("asset %s unreadable: %s", key, ex)
                self._json[key] = None
        return self._json[key]

    def is_svg(self, aid: Optional[str], cat: str) -> bool:
        e = self.entry(aid, cat)
        return bool(e and e.file_path.endswith(".svg"))

    def svg(self, aid: Optional[str], cat: str, w: int, h: int):
        e = self.entry(aid, cat)
        if not e or not e.file_path.endswith(".svg"):
            return None
        key = (e.id, w, h)
        if key not in self._surf:
            self._surf[key] = svg_file_to_surface(self.lib / e.file_path, w, h)
        return self._surf[key]


def svg_viewbox_ratio(text: str) -> float:
    m = re.search(r'viewBox\s*=\s*"[\s,]*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', text)
    return float(m.group(1)) / float(m.group(2)) if m else 1.0


def svg_file_to_surface(path: Path, w: int, h: int):
    """Rasterize an SVG to a cairo surface that fits inside w x h (aspect preserved)."""
    import cairosvg  # lazy: only needed for SVG assets
    data = Path(path).read_bytes()
    ratio = svg_viewbox_ratio(data.decode("utf-8", "replace"))
    ow, oh = (w, max(1, int(round(w / ratio)))) if w / h <= ratio else (max(1, int(round(h * ratio))), h)
    png = cairosvg.svg2png(bytestring=data, output_width=ow, output_height=oh)
    return cairo.ImageSurface.create_from_png(io.BytesIO(png))


def draw_surface(ctx, surf, x: float, y: float, w: float, h: float, alpha: float = 1.0) -> None:
    sw, sh = surf.get_width(), surf.get_height()
    ctx.save()
    ctx.translate(x, y)
    safe_scale(ctx, w / sw, h / sh)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


# =========================================================================== primitives
def rrect(ctx, x: float, y: float, w: float, h: float, r: float) -> None:
    r = min(r, w / 2, h / 2)
    ctx.new_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def set_font(ctx, name: str, size: float) -> None:
    bold = "bold" in name.lower()
    family = re.sub(r"\s*bold\s*", " ", name, flags=re.I).strip() or "sans-serif"
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(max(0.5, float(size)))


def text_width(ctx, s: str) -> float:
    return ctx.text_extents(s).x_advance


def draw_text(ctx, s: str, x: float, y: float, theme, fill: Any, stroke: Any = None, stroke_w: float = 0.0,
              alpha: float = 1.0) -> None:
    ctx.move_to(x, y)
    if stroke and stroke_w > 0:
        ctx.text_path(s)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_width(stroke_w)
        setc(ctx, stroke, theme, alpha)
        ctx.stroke_preserve()
        setc(ctx, fill, theme, alpha)
        ctx.fill()
    else:
        setc(ctx, fill, theme, alpha)
        ctx.show_text(s)


def line(ctx, x0, y0, x1, y1, w, color, theme, alpha=1.0) -> None:
    setc(ctx, color, theme, alpha)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()


def circle(ctx, x, y, r, theme, fill=None, stroke=None, sw=0.0, alpha=1.0) -> None:
    ctx.new_path()
    ctx.arc(x, y, max(0.1, r), 0, 2 * math.pi)
    if fill is not None:
        setc(ctx, fill, theme, alpha)
        ctx.fill_preserve() if stroke else ctx.fill()
    if stroke:
        setc(ctx, stroke, theme, alpha)
        ctx.set_line_width(sw)
        ctx.stroke()
    ctx.new_path()


# =========================================================================== stickman rig
def _dir(angle_deg: float) -> Tuple[float, float]:
    a = math.radians(angle_deg)
    return (-math.sin(a), math.cos(a))          # 0 deg = straight down; +angle swings toward screen-left


def _up(angle_deg: float) -> Tuple[float, float]:
    a = math.radians(angle_deg)
    return (math.sin(a), -math.cos(a))          # 0 deg = straight up; +angle leans right


def safe_scale(ctx, sx: float, sy: Optional[float] = None) -> None:
    """ctx.scale that never makes the matrix singular (a 0 scale raises in pycairo)."""
    sy = sx if sy is None else sy
    ctx.scale(math.copysign(max(abs(sx), 1e-3), sx or 1.0), math.copysign(max(abs(sy), 1e-3), sy or 1.0))


DEFAULT_POSE = {"torso_lean": 0, "neck": 0, "l_shoulder": 8, "l_elbow": 5, "r_shoulder": -8, "r_elbow": -5,
                "l_hip": 4, "l_knee": 0, "r_hip": -4, "r_knee": 0}
DEFAULT_RIG = {"head_radius": 0.085, "neck": 0.03, "torso": 0.26, "upper_arm": 0.14, "forearm": 0.13,
               "thigh": 0.18, "shin": 0.18, "line_width": 0.012, "hand_radius": 0.016}


def rig_points(rig: Dict[str, float], pose: Dict[str, float], U: float, anchor: Tuple[float, float],
               torso_scale: float = 1.0, ground: bool = True) -> Dict[str, Tuple[float, float]]:
    j = {**DEFAULT_POSE, **pose}
    ax, ay = anchor
    pel = (ax, ay - (rig["thigh"] + rig["shin"]) * U)
    up = _up(j["torso_lean"])
    torso = rig["torso"] * torso_scale * U
    neck_base = (pel[0] + up[0] * torso, pel[1] + up[1] * torso)
    head_dir = _up(j["torso_lean"] + j["neck"])
    head = (neck_base[0] + head_dir[0] * (rig["neck"] + rig["head_radius"]) * U,
            neck_base[1] + head_dir[1] * (rig["neck"] + rig["head_radius"]) * U)
    sh = (neck_base[0], neck_base[1] + 0.02 * U)
    pts: Dict[str, Tuple[float, float]] = {"pelvis": pel, "neck_base": neck_base, "head": head}
    for side, s in (("l", 1), ("r", -1)):
        d1 = _dir(j[f"{side}_shoulder"])
        elbow = (sh[0] + d1[0] * rig["upper_arm"] * U, sh[1] + d1[1] * rig["upper_arm"] * U)
        d2 = _dir(j[f"{side}_shoulder"] + j[f"{side}_elbow"])
        hand = (elbow[0] + d2[0] * rig["forearm"] * U, elbow[1] + d2[1] * rig["forearm"] * U)
        hip = (pel[0] + s * 0.02 * U * -1, pel[1])
        d3 = _dir(j[f"{side}_hip"])
        knee = (hip[0] + d3[0] * rig["thigh"] * U, hip[1] + d3[1] * rig["thigh"] * U)
        d4 = _dir(j[f"{side}_hip"] - s * j[f"{side}_knee"])   # signed: negative bends the other way
        foot = (knee[0] + d4[0] * rig["shin"] * U, knee[1] + d4[1] * rig["shin"] * U)
        pts.update({f"{side}_shoulder": sh, f"{side}_elbow": elbow, f"{side}_hand": hand,
                    f"{side}_hip": hip, f"{side}_knee": knee, f"{side}_foot": foot})
    if ground:  # bent legs (squat, sit, lunge) keep the feet on the floor instead of floating
        dy = ay - max(pts["l_foot"][1], pts["r_foot"][1])
        if abs(dy) > 1e-6:
            pts = {k: (v[0], v[1] + dy) for k, v in pts.items()}
    return pts


def draw_mouth(ctx, cx, cy, r, shape: Any, theme, color) -> None:
    ctx.set_line_width(max(1.5, r * 0.09))
    setc(ctx, color, theme)
    if isinstance(shape, dict):                          # viseme {open, width}
        w, o = shape.get("width", 0.5) * r * 0.9, shape.get("open", 0.0) * r * 0.5
        if o < r * 0.04:
            line(ctx, cx - w / 2, cy, cx + w / 2, cy, max(1.5, r * 0.09), color, theme)
        else:
            ctx.save()
            ctx.translate(cx, cy)
            safe_scale(ctx, max(0.1, w / 2), max(0.1, o))
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            setc(ctx, color, theme)
            ctx.fill()
        return
    if shape == "smirk_right":
        ctx.move_to(cx - r * 0.3, cy)
        ctx.curve_to(cx, cy + r * 0.05, cx + r * 0.2, cy, cx + r * 0.4, cy - r * 0.18)
        ctx.stroke()
    elif shape == "open_small":
        ctx.save(); ctx.translate(cx, cy); safe_scale(ctx, r * 0.14, r * 0.2); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.fill()
    elif shape == "wobble":
        ctx.move_to(cx - r * 0.35, cy)
        ctx.curve_to(cx - r * 0.15, cy - r * 0.12, cx + r * 0.05, cy + r * 0.12, cx + r * 0.35, cy)
        ctx.stroke()
    elif shape == "grit":
        rrect(ctx, cx - r * 0.35, cy - r * 0.1, r * 0.7, r * 0.2, r * 0.05)
        ctx.stroke()
        line(ctx, cx, cy - r * 0.1, cx, cy + r * 0.1, max(1.0, r * 0.05), color, theme)
    else:
        line(ctx, cx - r * 0.28, cy, cx + r * 0.28, cy, max(1.5, r * 0.09), color, theme)


def draw_face(ctx, cx, cy, r, expr: Dict[str, Any], mouth: Any, look_t: float, theme, color, skin: str = "#0f172a") -> None:
    """Eyes (round/happy/x/heart/star/wink/... + automatic blinking), brows, extras and mouth (see render_fx)."""
    render_fx.draw_face_ext(ctx, cx, cy, r, expr, mouth, look_t, theme, color, skin)


def draw_character(ctx, char: Dict[str, Any], pose: Dict[str, Any], expr: Dict[str, Any], mouth: Any, theme,
                   U: float, anchor: Tuple[float, float], torso_scale: float = 1.0, t: float = 0.0) -> None:
    rig = {**DEFAULT_RIG, **char.get("rig", {})}
    cols = char.get("colors", {})
    line_c, fill_c, accent = cols.get("line", "#f1f5f9"), cols.get("fill", "#0f172a"), cols.get("accent", "#22d3ee")
    joints = {**DEFAULT_POSE, **(pose.get("joints", {}) or {})}
    pts = rig_points(rig, joints, U, anchor, torso_scale, ground=not pose.get("airborne", False))
    lw = max(2.0, rig["line_width"] * U)
    head_r = rig["head_radius"] * U
    accs = render_fx.accessory_list(char)
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    render_fx.draw_body_accessories(ctx, accs, pts, rig, U, theme, head_r, line_c, t)
    bones = (("neck_base", "pelvis"), ("l_shoulder", "l_elbow"), ("l_elbow", "l_hand"), ("r_shoulder", "r_elbow"),
             ("r_elbow", "r_hand"), ("l_hip", "l_knee"), ("l_knee", "l_foot"), ("r_hip", "r_knee"), ("r_knee", "r_foot"))
    halo = cols.get("outline", "#0f172a")
    for a, b in bones:   # soft dark under-stroke keeps light limbs readable on bright backdrops
        line(ctx, *pts[a], *pts[b], lw * 1.9, halo, theme, 0.45)
    for a, b in bones:
        line(ctx, *pts[a], *pts[b], lw, line_c, theme)
    for k in ("l_hand", "r_hand"):
        circle(ctx, *pts[k], rig["hand_radius"] * U, theme, fill=line_c)
    for k in ("l_foot", "r_foot"):
        circle(ctx, *pts[k], rig["hand_radius"] * U * 0.9, theme, fill=accent)
    circle(ctx, *pts["head"], head_r, theme, fill=fill_c, stroke=line_c, sw=lw)
    head_angle = joints["torso_lean"] + joints["neck"]
    ctx.save()
    ctx.translate(*pts["head"])
    ctx.rotate(math.radians(head_angle))
    draw_face(ctx, 0.0, 0.0, head_r, expr, mouth, t, theme, line_c, fill_c)
    ctx.restore()
    render_fx.draw_head_accessories(ctx, accs, pts["head"], head_r, head_angle, theme, line_c, t)
    ctx.restore()
    pts["_head_r"] = head_r  # type: ignore[assignment]
    return pts  # type: ignore[return-value]


def viseme_at(words: List[Dict[str, Any]], t: float, visemes: Dict[str, Any]) -> Dict[str, Any]:
    rest = visemes.get("rest", {"open": 0.0, "width": 0.5})
    for w in words:
        if w["start"] <= t < w["end"]:
            letters = re.sub(r"[^a-z]", "", w["word"].lower())
            if not letters:
                return rest
            pos = int((t - w["start"]) / max(1e-3, w["end"] - w["start"]) * len(letters))
            v = VISEME_BY_LETTER.get(letters[min(pos, len(letters) - 1)])
            if v is None:
                return {"open": 0.25, "width": 0.6}
            base = visemes.get(v, rest)
            wob = 0.85 + 0.15 * math.sin(t * 28)
            return {"open": base["open"] * wob, "width": base["width"]}
    return rest


# =========================================================================== backgrounds, widgets, overlays
def draw_prims(ctx, prims: List[Dict[str, Any]], W: float, H: float, theme) -> None:
    for p in prims:
        k = p.get("type")
        if k == "rect":
            ctx.rectangle(p["x"] * W, p["y"] * H, p["w"] * W, p["h"] * H)
            setc(ctx, p.get("fill", "#888888"), theme)
            ctx.fill()
        elif k == "circle":
            circle(ctx, p["x"] * W, p["y"] * H, p["r"] * min(W, H), theme, fill=p.get("fill", "#888888"))
        elif k == "poly":
            pts = p["points"]
            ctx.move_to(pts[0][0] * W, pts[0][1] * H)
            for x, y in pts[1:]:
                ctx.line_to(x * W, y * H)
            ctx.close_path()
            setc(ctx, p.get("fill", "#888888"), theme)
            ctx.fill()
        elif k == "line":
            line(ctx, p["x1"] * W, p["y1"] * H, p["x2"] * W, p["y2"] * H, p.get("width", 3), p.get("stroke", "#000000"), theme)


def draw_background(ctx, assets: Assets, scene_id: Optional[str], W: int, H: int, theme, cam_x: float) -> Tuple[float, float]:
    """Returns the character anchor (x, ground_y) in px."""
    setc(ctx, theme.get("bg", "#0f172a"), theme)
    ctx.paint()
    anchor = (0.5, 0.78)
    try:
        sj = assets.json(scene_id, "05_scenes")
        if sj:
            anchor = tuple(sj.get("character_anchor", anchor))  # type: ignore[assignment]
            for layer, par in (("back", 0.3), ("mid", 0.6), ("ground", 1.0)):
                ctx.save()
                ctx.translate(-cam_x * W * par * 0.5, 0)
                draw_prims(ctx, sj.get("layers", {}).get(layer, []), W, H, theme)
                ctx.restore()
        elif assets.is_svg(scene_id, "05_scenes"):
            meta_anchor = (assets.entry(scene_id, "05_scenes").meta or {}).get("character_anchor")
            if isinstance(meta_anchor, (list, tuple)) and len(meta_anchor) == 2:
                anchor = (float(meta_anchor[0]), float(meta_anchor[1]))
            surf = assets.svg(scene_id, "05_scenes", W, H)
            if surf:
                s = max(W / surf.get_width(), H / surf.get_height())
                draw_surface(ctx, surf, (W - surf.get_width() * s) / 2, (H - surf.get_height() * s) / 2,
                             surf.get_width() * s, surf.get_height() * s)
    except Exception as e:  # noqa: BLE001 - a broken background must never crash a render
        log.warning("background %s failed: %s", scene_id, e)
    return anchor[0] * W, anchor[1] * H


def draw_card(ctx, x, y, w, h, theme, alpha=0.92) -> None:
    rrect(ctx, x, y, w, h, min(w, h) * 0.08)
    setc(ctx, theme.get("surface", "#1e293b"), theme, alpha)
    ctx.fill_preserve()
    setc(ctx, theme.get("accent", "#22d3ee"), theme, 0.9)
    ctx.set_line_width(max(2, min(w, h) * 0.015))
    ctx.stroke()


def draw_callout(ctx, x, y, w, h, title: str, subtitle: Optional[str], theme, t: float) -> None:
    p = ease("expo_out", t / 0.35)
    ctx.save()
    ctx.translate(x + w / 2, y + h / 2)
    safe_scale(ctx, 0.85 + 0.15 * p, 0.85 + 0.15 * p)
    draw_card(ctx, -w / 2, -h / 2, w, h, theme, 0.95 * p)
    fs = min(h * 0.3, w / max(6, len(title)) * 1.7)
    set_font(ctx, "DejaVu Sans Bold", fs)
    draw_text(ctx, title, -text_width(ctx, title) / 2, fs * (0.1 if subtitle else 0.35), theme, theme.get("text"), alpha=p)
    if subtitle:
        set_font(ctx, "DejaVu Sans", fs * 0.55)
        draw_text(ctx, subtitle, -text_width(ctx, subtitle) / 2, fs * 0.9, theme, theme.get("accent"), alpha=p)
    ctx.restore()


def draw_bars(ctx, x, y, w, h, labels: List[str], values: List[float], theme, t: float, hi: Optional[int] = None,
              stagger: float = 0.09, show_values: bool = True) -> None:
    draw_card(ctx, x, y, w, h, theme)
    n = max(1, len(values))
    vmax = max(values) if values else 1.0
    bw = w * 0.8 / n
    base = y + h * 0.82
    for i, v in enumerate(values):
        p = ease("expo_out", clamp((t - i * stagger) / 0.5))
        bh = (h * 0.6) * (v / vmax) * p
        bx = x + w * 0.1 + i * bw + bw * 0.12
        ctx.rectangle(bx, base - bh, bw * 0.76, bh)
        setc(ctx, theme.get("danger" if i == hi else "accent"), theme)
        ctx.fill()
        set_font(ctx, "DejaVu Sans Bold", h * 0.08)
        if i < len(labels):
            draw_text(ctx, str(labels[i]), bx + bw * 0.38 - text_width(ctx, str(labels[i])) / 2, base + h * 0.1, theme, theme.get("text"))
        if show_values and p > 0.8:
            s = f"{v:g}"
            draw_text(ctx, s, bx + bw * 0.38 - text_width(ctx, s) / 2, base - bh - h * 0.02, theme, theme.get("text"))


def draw_widget(ctx, wj: Dict[str, Any], x, y, w, h, theme, t: float) -> None:
    kind, data = wj.get("type"), wj.get("data", {})
    if kind == "bar_chart":
        draw_bars(ctx, x, y, w, h, data.get("labels", []), [float(v) for v in data.get("values", [])], theme, t,
                  wj.get("highlight_index"), wj.get("stagger_ms", 90) / 1000.0, wj.get("style", {}).get("show_values", True))
    elif kind == "comparison_card":
        p = ease("expo_out", t / 0.4)
        for i, side in enumerate(("left", "right")):
            cw = w * 0.47
            cx = x + i * (w - cw) + (1 - p) * (-1 if i == 0 else 1) * w * 0.3
            draw_card(ctx, cx, y, cw, h, theme, 0.92 * p)
            set_font(ctx, "DejaVu Sans Bold", h * 0.14)
            title = data.get(side, {}).get("title", "")
            draw_text(ctx, title, cx + cw / 2 - text_width(ctx, title) / 2, y + h * 0.25, theme, theme.get("highlight"), alpha=p)
            set_font(ctx, "DejaVu Sans", h * 0.1)
            for j, b in enumerate(data.get(side, {}).get("bullets", [])[:4]):
                draw_text(ctx, "• " + str(b), cx + cw * 0.08, y + h * (0.48 + j * 0.15), theme, theme.get("text"), alpha=p)
    elif kind == "funnel":
        stages = data.get("stages", [])
        n = max(1, len(stages))
        top = max([s.get("value", 1) for s in stages] + [1])
        for i, s in enumerate(stages):
            p = ease("expo_out", clamp((t - i * 0.15) / 0.4))
            bw = w * (0.35 + 0.65 * s.get("value", 1) / top) * p
            by = y + i * h / n
            rrect(ctx, x + (w - bw) / 2, by + 2, bw, h / n - 4, 8)
            setc(ctx, theme.get("accent" if i % 2 == 0 else "accent2"), theme, 0.9)
            ctx.fill()
            set_font(ctx, "DejaVu Sans Bold", h / n * 0.34)
            label = f"{s.get('label', '')} {s.get('value', '')}"
            draw_text(ctx, label, x + (w - text_width(ctx, label)) / 2, by + h / n * 0.62, theme, theme.get("bg"), alpha=p)
    elif not render_fx.draw_widget_ext(ctx, wj, x, y, w, h, theme, t):
        raise ValueError(f"unknown widget type {kind}")


def draw_overlay(ctx, assets: Assets, oid: Optional[str], W: int, H: int, theme, t: float,
                 head: Tuple[float, float], head_r: float) -> None:
    if not oid:
        return
    oj = assets.json(oid, "08_overlays")
    if oj:
        kind = oj.get("kind")
        mo = oj.get("motion", {})
        life = max(0.2, mo.get("lifetime_sec", 1.0))
        if kind == "particles":
            part = oj.get("particle", {})
            r = part.get("size", 0.018) * min(W, H)
            dx, dy = mo.get("direction", [0.5, -1.0])
            g = mo.get("gravity", 0.9)
            for i in range(int(oj.get("count", 3))):
                u = ((t / life) + i / max(1, oj.get("count", 3))) % 1.0
                px = head[0] + head_r * (0.9 + 0.25 * i) * (1 if i % 2 else -1) + dx * u * head_r
                py = head[1] - head_r * 0.2 + (dy * u + g * u * u) * head_r * 1.6
                circle(ctx, px, py, r, theme, fill=part.get("color", "#7dd3fc"), alpha=1 - u * 0.8)
        elif kind == "floating_text":
            set_font(ctx, "DejaVu Sans Bold", oj.get("size", 0.05) * min(W, H))
            for i in range(int(oj.get("count", 3))):
                u = ((t / life) + i / 3) % 1.0
                px = head[0] + (i - 1) * head_r * 1.2
                py = head[1] - head_r * 1.5 - u * head_r * 0.8 + math.sin(t * 6 + i) * mo.get("bob", 0.01) * H
                draw_text(ctx, oj.get("text", "?"), px, py, theme, oj.get("color", "theme.highlight"), alpha=1 - u * 0.7)
        else:
            render_fx.draw_overlay_ext(ctx, oj, W, H, theme, t, head, head_r, assets)
        return
    entry = assets.entry(oid, "08_overlays")
    fullscreen = "speed_lines" in oid or bool(entry and entry.meta.get("placement") == "fullscreen")
    if not fullscreen:  # a badge beside the head instead of a giant centred burst that hides the character
        size = int(min(W, H) * float((entry.meta.get("size") if entry else None) or 0.26))
        surf = assets.svg(oid, "08_overlays", size, size)
        if surf:
            pop = clamp(spring_step(t, 320, 15), 0, 1.3)
            cx = min(max(head[0] + head_r * 1.3 + size * 0.4, size * 0.55), W - size * 0.55)
            cy = max(head[1] - head_r * 1.2 - size * 0.2 + math.sin(t * 3) * size * 0.03, size * 0.55)
            ctx.save()
            ctx.translate(cx, cy)
            safe_scale(ctx, max(0.01, pop), max(0.01, pop))
            ctx.rotate(math.sin(t * 2.5) * 0.08)
            sw, sh = surf.get_width(), surf.get_height()
            draw_surface(ctx, surf, -sw / 2, -sh / 2, sw, sh)
            ctx.restore()
        return
    surf = assets.svg(oid, "08_overlays", W, H)
    if surf:

        pop = min(1.0, spring_step(t, 300, 16))
        ctx.save()
        ctx.translate(W / 2, H / 2)
        if "speed_lines" in oid:
            ctx.rotate(t * 0.35)
        safe_scale(ctx, max(0.2, pop), max(0.2, pop))
        sw, sh = surf.get_width(), surf.get_height()
        sc = max(W / sw, H / sh) * (1.1 if "speed_lines" in oid else 0.5)
        draw_surface(ctx, surf, -sw * sc / 2, -sh * sc / 2, sw * sc, sh * sc, 0.8 * min(1, t / 0.08))
        ctx.restore()


# =========================================================================== transitions & captions
def draw_with_transition(ctx, tr: Optional[Dict[str, Any]], t: float, W: int, H: int, draw_fn) -> None:
    dur = float(tr.get("duration_sec", 0.3)) if tr else 0.0
    if not tr or t >= dur:
        draw_fn()
        return
    u = ease(tr.get("easing", "ease_in_out"), t / dur)
    kind = tr.get("type")
    if kind == "whip_pan":
        sign = 1 if tr.get("direction", "left") == "left" else -1
        ctx.push_group()
        draw_fn()
        pat = ctx.pop_group()
        ghosts = (0.0, 0.06, 0.12) if tr.get("motion_blur") else (0.0,)
        for gi, gd in enumerate(ghosts):
            ctx.save()
            ctx.translate(sign * (1 - u + gd * (1 - u)) * W, 0)
            ctx.set_source(pat)
            ctx.paint_with_alpha(1.0 if gi == 0 else 0.3)
            ctx.restore()
    elif kind == "zoom":
        s = tr.get("from_scale", 1.0) + (tr.get("to_scale", 1.6) - tr.get("from_scale", 1.0)) * (1 - u)
        ctx.save()
        ctx.translate(W / 2, H / 2)
        safe_scale(ctx, s, s)
        ctx.translate(-W / 2, -H / 2)
        draw_fn()
        ctx.restore()
        if tr.get("flash"):
            ctx.set_source_rgba(1, 1, 1, 0.5 * (1 - u))
            ctx.paint()
    elif kind == "wipe":
        ang = math.radians(tr.get("angle_deg", 35))
        edge = u * (W + H * math.tan(ang))
        ctx.save()
        ctx.move_to(0, 0)
        ctx.line_to(edge, 0)
        ctx.line_to(edge - H * math.tan(ang), H)
        ctx.line_to(0, H)
        ctx.close_path()
        ctx.clip()
        draw_fn()
        ctx.restore()
    elif render_fx.draw_transition_ext(ctx, tr, kind, u, t, W, H, draw_fn):
        pass
    else:  # fade
        ctx.push_group()
        draw_fn()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(u)


def draw_captions(ctx, style: Dict[str, Any], words: List[Dict[str, Any]], t: float, W: int, H: int, theme) -> None:
    if not words:
        return
    per = max(1, int(style.get("max_words_per_line", 3)))
    groups = [words[i:i + per] for i in range(0, len(words), per)]
    cur = None
    for g in groups:
        if t >= g[0]["start"] - 0.05:
            cur = g
    if cur is None or t > words[-1]["end"] + 0.6:
        return
    size = style.get("size_ratio", 0.06) * min(W, H) * 1.45
    set_font(ctx, style.get("font", "DejaVu Sans Bold"), size)
    case = style.get("case", "sentence")
    texts = [w["word"].upper() if case == "upper" else w["word"] for w in cur]
    space = text_width(ctx, " ")
    total = sum(text_width(ctx, s) for s in texts) + space * (len(texts) - 1)
    if total > W * 0.92:
        size *= W * 0.92 / total
        set_font(ctx, style.get("font", "DejaVu Sans Bold"), size)
        space = text_width(ctx, " ")
        total = sum(text_width(ctx, s) for s in texts) + space * (len(texts) - 1)
    x = (W - total) / 2
    y = style.get("position_y", 0.7) * H
    bg = style.get("background")
    if bg:
        rrect(ctx, x - size * 0.4, y - size * 1.0, total + size * 0.8, size * 1.5, size * 0.3)
        setc(ctx, bg.get("color", "#000000"), theme, bg.get("opacity", 0.5))
        ctx.fill()
    act = style.get("active_word", {})
    stroke = style.get("stroke")
    for w, s in zip(cur, texts):
        active = w["start"] <= t < w["end"] + 0.04
        pop = 1.0
        if active and act.get("pop_ms", 0) > 0:
            pop = 1.0 + (act.get("scale_pop", 1.0) - 1.0) * math.sin(math.pi * clamp((t - w["start"]) / (act["pop_ms"] / 1000.0)))
        wd = text_width(ctx, s)
        ctx.save()
        ctx.translate(x + wd / 2, y)
        safe_scale(ctx, pop, pop)
        box = act.get("box")
        if active and isinstance(box, dict):
            rrect(ctx, -wd / 2 - size * 0.18, -size * 0.92, wd + size * 0.36, size * 1.22, size * float(box.get("radius", 0.25)))
            setc(ctx, box.get("color", "theme.accent"), theme, float(box.get("opacity", 1.0)))
            ctx.fill()
        shadow = style.get("shadow")
        if isinstance(shadow, dict):
            draw_text(ctx, s, -wd / 2 + size * float(shadow.get("dx", 0.06)), size * float(shadow.get("dy", 0.08)), theme,
                      shadow.get("color", "#000000"), alpha=float(shadow.get("opacity", 0.6)))
        draw_text(ctx, s, -wd / 2, 0, theme, act.get("color", "#fff") if active else style.get("inactive_color", "#fff"),
                  stroke.get("color") if stroke else None, (stroke.get("width_ratio", 0.01) * min(W, H) * 1.4) if stroke else 0)
        ctx.restore()
        x += wd + space


# =========================================================================== scene composition
def _wrap(ctx, words: List[str], max_w: float) -> List[List[int]]:
    """Greedy word wrap -> lists of word indexes per line."""
    lines: List[List[int]] = [[]]
    space = text_width(ctx, " ")
    cur = 0.0
    for i, w in enumerate(words):
        ww = text_width(ctx, w)
        if lines[-1] and cur + space + ww > max_w:
            lines.append([])
            cur = 0.0
        cur += (space if lines[-1] else 0.0) + ww
        lines[-1].append(i)
    return lines


def say_presence(say: Optional[Dict[str, Any]], t: float) -> float:
    """0..1 envelope of the stickman talking (ramps in before the line, lingers after it)."""
    if not say:
        return 0.0
    a, b = say["start"] - 0.1, say["end"] + 0.4
    return clamp((t - a) / 0.2) * clamp((b - t) / 0.25)


def draw_speech_bubble(ctx, say: Dict[str, Any], t: float, head: Tuple[float, float], head_r: float,
                       W: int, H: int, theme) -> None:
    """Comic speech bubble above the stickman's head; words appear as he says them."""
    t0, t1 = say["start"], say["end"]
    if t < t0 - 0.05 or t > t1 + 0.6:
        return
    words = [w["word"] for w in say["words"]] or say["text"].split()
    size = 0.044 * H
    set_font(ctx, "DejaVu Sans Bold", size)
    max_w = W * 0.72
    lines = _wrap(ctx, words, max_w)
    space = text_width(ctx, " ")
    lw = [sum(text_width(ctx, words[i]) for i in ln) + space * (len(ln) - 1) for ln in lines]
    pad = size * 0.7
    bw, bh = max(lw) + 2 * pad, len(lines) * size * 1.3 + 2 * pad - size * 0.2
    hx, hy = head
    tail_len = size * 1.1
    bx = min(max(hx - bw / 2, W * 0.04), W * 0.96 - bw)
    by = max(H * 0.04, hy - head_r * 1.35 - tail_len - bh)
    tip = (min(max(hx, bx + pad), bx + bw - pad), by + bh + tail_len)
    p = clamp(spring_step(t - (t0 - 0.05), 300, 15), 0.0, 1.25)
    fade = 1.0 - clamp((t - (t1 + 0.35)) / 0.25)
    bob = 2.0 * math.sin(t * 3.2)
    ctx.save()
    ctx.translate(tip[0], tip[1] + bob)
    safe_scale(ctx, max(0.01, p), max(0.01, p))
    ctx.translate(-tip[0], -tip[1])
    ctx.push_group()
    # tail first, then body, so the outline merges
    tx = tip[0]
    ctx.new_path()
    ctx.move_to(tx - size * 0.55, by + bh - 2)
    ctx.line_to(tip[0] + size * 0.05, tip[1])
    ctx.line_to(tx + size * 0.55, by + bh - 2)
    ctx.close_path()
    setc(ctx, "#ffffff", theme)
    ctx.fill_preserve()
    setc(ctx, "#0f172a", theme)
    ctx.set_line_width(max(2.0, size * 0.09))
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    rrect(ctx, bx, by, bw, bh, size * 0.8)
    setc(ctx, "#ffffff", theme)
    ctx.fill_preserve()
    setc(ctx, "#0f172a", theme)
    ctx.set_line_width(max(2.0, size * 0.09))
    ctx.stroke()
    # cover the seam between tail and body
    ctx.new_path()
    ctx.move_to(tx - size * 0.55 + 2, by + bh)
    ctx.line_to(tx + size * 0.55 - 2, by + bh)
    ctx.set_line_width(max(2.0, size * 0.09) + 1.0)
    setc(ctx, "#ffffff", theme)
    ctx.stroke()
    set_font(ctx, "DejaVu Sans Bold", size)
    y = by + pad + size * 0.85
    for ln, wid in zip(lines, lw):
        x = bx + (bw - wid) / 2
        for i in ln:
            seg = say["words"][i] if i < len(say["words"]) else None
            wd = text_width(ctx, words[i])
            if seg is None or t >= seg["start"] - 0.02:
                active = seg is not None and seg["start"] <= t < seg["end"] + 0.04
                draw_text(ctx, words[i], x, y, theme, "#ea580c" if active else "#0f172a")
            x += wd + space
        y += size * 1.3
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(clamp(fade))
    ctx.restore()


class SceneCtx:
    """Everything resolved once per scene (assets, motion, words)."""

    def __init__(self, pkg: schemas.AnalysisPackage, sc, tl: Dict[str, Any], assets: Assets, theme, caption):
        self.sc, self.tl, self.assets, self.theme, self.caption = sc, tl, assets, theme, caption
        self.char = assets.json(sc.character.character_id, "01_characters") or {"rig": DEFAULT_RIG}
        self.pose = assets.json(sc.character.pose_id, "02_poses") or {"joints": {}}
        self.expr = assets.json(sc.character.expression_id, "03_expressions") or {}
        self.motion = assets.json(sc.character.motion_id, "04_motions")
        self.visemes = (assets.json("viseme_default", "03_expressions") or {}).get("visemes", {})
        self.trans = assets.json(sc.environment.transition_in_id, "09_transitions")
        self.words = tl["words"]
        self.say = tl.get("say")
        sp = getattr(sc, "speech", None)
        self.say_expr = assets.json(sp.expression_id, "03_expressions") if (sp and sp.expression_id) else None
        # with a distinct stickman voice the narrator is a voice-over: he only lip-syncs his own lines
        self.lipsync_narration = not any(getattr(x, "speech", None) for x in pkg.scenes)
        # the bubble carries his words, so the bottom captions step aside while he talks
        self.cap_hidden: Optional[Tuple[float, float]] = None
        if self.say:
            a, b = self.say["start"] - 0.05, self.say["end"] + 0.6
            if self.words and self.words[0]["start"] > self.say["start"]:  # narration follows his line
                b = min(b, self.words[0]["start"] - 0.05)
            self.cap_hidden = (a, b)
        self.prev_joints: Optional[Dict[str, float]] = None   # set by build_scene_ctxs: pose springs from here
        self.layout: Optional[layout.Layout] = None
        self._lay_key: Optional[tuple] = None

    def solve_layout(self, W: int, H: int, ax: float, ay: float) -> "layout.Layout":
        """Zones for caption / widget / prop from the character's target pose (stable for the whole scene)."""
        key = (W, H, round(ax, 1), round(ay, 1))
        if self._lay_key != key:
            rig = {**DEFAULT_RIG, **self.char.get("rig", {})}
            joints = {**DEFAULT_POSE, **(self.pose.get("joints") or {})}
            U = 0.44 * H
            pts = rig_points(rig, joints, U, (ax, ay), 1.0, ground=not self.pose.get("airborne", False))
            va = self.sc.visual_aid
            self.layout = layout.solve(W, H, pts, rig["head_radius"] * U, max(2.0, rig["line_width"] * U),
                                       caption_style=self.caption, has_widget=bool(va.widget_id),
                                       has_prop=bool(va.prop_id))
            self._lay_key = key
        return self.layout  # type: ignore[return-value]


def scene_joints(s: "SceneCtx", t: float, ms: Dict[str, float], speaking: bool) -> Dict[str, float]:
    """The pose actually drawn at scene time t: springs in from the previous scene's pose, breathes, sways,
    nods while talking, plus any `pose.<joint>` gesture tracks from the scene's motion."""
    target = {**DEFAULT_POSE, **(s.pose.get("joints") or {})}
    prev = {**DEFAULT_POSE, **(s.prev_joints or {})}
    p = spring_step(t, 170, 15) if prev != target else 1.0
    j = {k: prev.get(k, 0.0) + (float(v) - prev.get(k, 0.0)) * p for k, v in target.items()}
    j["l_shoulder"] += 2.0 * math.sin(t * 1.9)
    j["r_shoulder"] -= 2.0 * math.sin(t * 1.9 + 0.7)
    j["neck"] += 1.5 * math.sin(t * 1.3)
    if speaking:
        j["neck"] += 4.0 * math.sin(t * 7.5)
    for k, v in ms.items():
        if k.startswith("pose."):
            j[k[5:]] = j.get(k[5:], 0.0) + v
    return j


def draw_visual_aid(ctx, s: SceneCtx, W: int, H: int, t: float, lay: "layout.Layout", obj_scale: float = 1.0) -> None:
    va, theme, a = s.sc.visual_aid, s.theme, s.assets
    fb = va.fallback_visual_aid
    drew = False
    if va.widget_id:
        try:
            wj = a.json(va.widget_id, "07_widgets")
            if wj:
                wr = lay.widget or layout.Rect(W * 0.07, H * 0.07, W * 0.86, H * 0.24)
                draw_widget(ctx, render_fx.widget_with_story(wj, fb), wr.x, wr.y, wr.w, wr.h, theme, t)
                drew = True
        except Exception as e:  # noqa: BLE001
            log.warning("widget %s failed: %s", va.widget_id, e)
    if va.prop_id:
        try:
            slot = lay.prop or layout.Rect(W * 0.58, H * 0.38, min(W, H) * 0.28, min(W, H) * 0.28)
            box = int(slot.w)
            surf = a.svg(va.prop_id, "06_props", box, box)
            if surf:
                p = clamp(spring_step(t - 0.12, 240, 13), 0, 1.3)
                # pivot on the edge next to the character, so the pop-in grows away from the body
                pivot_x = slot.r if lay.prop_side == "left" else slot.x
                ctx.save()
                ctx.translate(pivot_x, slot.y + slot.h / 2 + math.sin(t * 2.2) * H * 0.006)   # gentle float
                ctx.rotate(math.sin(t * 1.7) * 0.035)
                safe_scale(ctx, max(0.01, p * obj_scale), max(0.01, p * obj_scale))
                draw_surface(ctx, surf, slot.x - pivot_x, -slot.h / 2, box, box, clamp(t / 0.1))
                ctx.restore()
                drew = True
        except Exception as e:  # noqa: BLE001
            log.warning("prop %s failed: %s", va.prop_id, e)
    if not drew:
        if fb.type == "chart_bar" and fb.values:
            draw_bars(ctx, W * 0.1, H * 0.08, W * 0.8, H * 0.24, fb.labels or [""] * len(fb.values), fb.values, theme, t)
        else:
            draw_callout(ctx, W * 0.08, H * 0.1, W * 0.84, H * 0.16, fb.title, fb.subtitle, theme, t)


def draw_scene(ctx, s: SceneCtx, W: int, H: int, t: float) -> None:
    """Composite one frame of scene-local time `t` (seconds since the scene's start)."""
    ms = eval_motion(s.motion, t)
    theme = s.theme

    def content() -> None:
        ctx.save()
        cs = ms["camera.scale"]
        ctx.translate(W / 2 + ms["camera.x"] * W, H / 2 + ms["camera.y"] * H)
        safe_scale(ctx, cs, cs)
        if ms["camera.rot"]:
            ctx.rotate(math.radians(ms["camera.rot"]))
        ctx.translate(-W / 2, -H / 2)
        ax, ay = draw_background(ctx, s.assets, s.sc.environment.scene_id, W, H, theme, ms["camera.x"])
        lay = s.solve_layout(W, H, ax, ay)
        presence = say_presence(s.say, t)
        if presence > 0.01:  # the prop/card steps back while the stickman talks, so the bubble reads cleanly
            ctx.push_group()
            draw_visual_aid(ctx, s, W, H, t, lay, ms["object.scale"])
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(1.0 - 0.85 * presence)
        else:
            draw_visual_aid(ctx, s, W, H, t, lay, ms["object.scale"])
        U = 0.44 * H
        rest = s.expr.get("mouth_rest", "flat")
        speaking = bool(s.say) and s.say["start"] - 0.03 <= t <= s.say["end"] + 0.05
        if speaking and s.visemes:
            mouth = viseme_at(s.say["words"], t, s.visemes)
        elif s.lipsync_narration and s.visemes and s.words and t <= s.tl["speech_sec"]:
            mouth = viseme_at(s.words, t, s.visemes)
        else:
            mouth = rest
        breath = 1.0 + 0.012 * math.sin(t * 2.6) + (0.02 * math.sin(t * 9.0) if speaking else 0.0)
        cx, cy = ax + ms["character.x"] * W, ay + ms["character.y"] * H + lay.char_dy
        rot, csc = ms["character.rot"], ms["character.scale"]
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(math.radians(rot))
        safe_scale(ctx, csc, csc)
        ctx.translate(-cx, -cy)
        pts = draw_character(ctx, s.char, {"joints": scene_joints(s, t, ms, speaking), "airborne": s.pose.get("airborne")},
                             (s.say_expr if (speaking and s.say_expr) else s.expr), mouth, theme, U, (cx, cy),
                             ms["torso.scale_y"] * breath, t)
        ctx.restore()
        hx, hy = pts["head"][0] - cx, pts["head"][1] - cy  # type: ignore[index]
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        head = (cx + (hx * cr - hy * sr) * csc, cy + (hx * sr + hy * cr) * csc)
        head_r = pts["_head_r"] * csc  # type: ignore[operator]
        draw_overlay(ctx, s.assets, s.sc.visual_aid.overlay_id, W, H, theme, t, head, head_r)
        if s.say:
            draw_speech_bubble(ctx, s.say, t, head, head_r, W, H, theme)
        ctx.restore()

    draw_with_transition(ctx, s.trans, t, W, H, content)
    if s.caption and not (s.cap_hidden and s.cap_hidden[0] <= t <= s.cap_hidden[1]):
        cap = s.caption
        if s.layout is not None and s.layout.caption_y is not None:
            cap = {**s.caption, "position_y": s.layout.caption_y / H}
        draw_captions(ctx, cap, s.words, t, W, H, theme)


def draw_cover_text(ctx, text: str, W: int, H: int, theme) -> None:
    words = text.split()
    lines = [" ".join(words[:3]), " ".join(words[3:])] if len(words) > 3 else [text]
    size = min(W, H) * 0.12
    set_font(ctx, "DejaVu Sans Bold", size)
    y = H * 0.13
    for i, ln in enumerate(l for l in lines if l):
        fs = size
        if text_width(ctx, ln) > W * 0.92:
            fs = size * W * 0.92 / text_width(ctx, ln)
            set_font(ctx, "DejaVu Sans Bold", fs)
        draw_text(ctx, ln, (W - text_width(ctx, ln)) / 2, y, theme, theme.get("highlight") if i else "#ffffff",
                  "#000000", size * 0.14)
        set_font(ctx, "DejaVu Sans Bold", size)
        y += size * 1.1


# =========================================================================== surfaces / output
def surface_rgba_bytes(surface, W: int, H: int) -> bytes:
    """cairo ARGB32 (BGRA in memory) -> RGBA bytes (opaque frames, so no un-premultiply needed)."""
    surface.flush()
    arr = np.frombuffer(surface.get_data(), dtype=np.uint8).reshape(H, surface.get_stride() // 4, 4)[:, :W]
    return np.ascontiguousarray(arr[:, :, [2, 1, 0, 3]]).tobytes()


def surface_to_jpg(surface, W: int, H: int, path: Path, quality: int = 92) -> None:
    from PIL import Image
    im = Image.frombytes("RGBA", (W, H), surface_rgba_bytes(surface, W, H)).convert("RGB")
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "JPEG", quality=quality)


def build_scene_ctxs(pkg: schemas.AnalysisPackage, timeline: Dict[str, Any], assets: Assets) -> List[SceneCtx]:
    theme = {**DEFAULT_THEME, **((assets.json(pkg.render_config.theme_id, "11_themes") or {}).get("palette", {}))}
    caption = assets.json(pkg.render_config.caption_style_id, "10_caption_styles")
    ctxs = [SceneCtx(pkg, sc, tl, assets, theme, caption) for sc, tl in zip(pkg.scenes, timeline["scenes"])]
    for prev, cur in zip(ctxs, ctxs[1:]):
        cur.prev_joints = prev.pose.get("joints") or {}
    return ctxs


def ffmpeg_cmd(W: int, H: int, fps: int, master: Path, out: Path, total_sec: float, mode: str) -> List[str]:
    return [common.ffmpeg_bin(), "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
            "-i", str(master), "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast" if mode != "hd" else "medium",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]


def layout_report(scenes: List[SceneCtx], ctx, W: int, H: int) -> List[Dict[str, Any]]:
    """QA pass: solve every scene's layout and list residual overlaps (caption/prop/widget vs the character)."""
    rep: List[Dict[str, Any]] = []
    for i, s in enumerate(scenes):
        try:
            ctx.save()
            ax, ay = draw_background(ctx, s.assets, s.sc.environment.scene_id, W, H, s.theme, 0.0)
            ctx.restore()
            lay = s.solve_layout(W, H, ax, ay)
            issues = layout.check(lay)
            if issues or lay.notes:
                rep.append({"scene": i, "issues": issues, "notes": lay.notes})
            for msg in issues:
                log.warning("layout: scene %d: %s", i, msg)
        except Exception as e:  # noqa: BLE001 - QA must never block a render
            log.warning("layout QA scene %d failed: %s", i, e)
    return rep


def render_video(pkg: schemas.AnalysisPackage, timeline: Dict[str, Any], master: Path, out: Path,
                 mode: str, assets: Assets, progress=None) -> Dict[str, Any]:
    W, H, fps = dims_for(pkg.render_config.aspect_ratio, mode)
    assets.size = (W, H)
    spans = audio_master.frame_spans(timeline, fps)
    scenes = build_scene_ctxs(pkg, timeline, assets)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    errlog = common.tmpdir() / f"ffmpeg_{pkg.package_id}.log"
    total_frames = spans[-1][1]
    lay_issues = layout_report(scenes, ctx, W, H)
    with open(errlog, "wb") as ef:
        proc = subprocess.Popen(ffmpeg_cmd(W, H, fps, master, out, timeline["total_sec"], mode),
                                stdin=subprocess.PIPE, stderr=ef)
        try:
            for sctx, (f0, f1) in zip(scenes, spans):
                t0 = sctx.tl["start_sec"]
                for f in range(f0, f1):
                    ctx.save()
                    draw_scene(ctx, sctx, W, H, max(0.0, f / fps - t0))
                    ctx.restore()
                    proc.stdin.write(surface_rgba_bytes(surface, W, H))
                    if progress and f % fps == 0:
                        progress(f / total_frames)
            proc.stdin.close()
        except BrokenPipeError:
            pass
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed ({rc}): {errlog.read_text(errors='replace')[-600:]}")
    errlog.unlink(missing_ok=True)
    return {"video": str(out), "frames": total_frames, "fps": fps, "size": [W, H], "layout_issues": lay_issues}


def render_stills(pkg: schemas.AnalysisPackage, timeline: Dict[str, Any], out_dir: Path, mode: str,
                  assets: Assets) -> Dict[str, Any]:
    W, H, _ = dims_for(pkg.render_config.aspect_ratio, mode)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    scenes = build_scene_ctxs(pkg, timeline, assets)
    paths: Dict[str, str] = {}
    for sctx in scenes:
        ctx.save()
        draw_scene(ctx, sctx, W, H, min(sctx.tl["speech_sec"] * 0.55, 3.0))
        ctx.restore()
        p = out_dir / f"{sctx.sc.id}.jpg"
        surface_to_jpg(surface, W, H, p)
        paths[sctx.sc.id] = str(p)
    cover_id = pkg.viral_packaging.cover_scene_id
    cs = next(s for s in scenes if s.sc.id == cover_id)
    ctx.save()
    draw_scene(ctx, cs, W, H, min(cs.tl["speech_sec"] * 0.55, 3.0))
    ctx.restore()
    draw_cover_text(ctx, pkg.viral_packaging.cover_text_hook, W, H, cs.theme)
    cover = out_dir / "cover.jpg"
    surface_to_jpg(surface, W, H, cover)
    return {"scenes": paths, "cover": str(cover)}


# =========================================================================== orchestration
def render_package(package_path: Path, mode: str, out_dir: Path, placeholder_tts: Optional[bool] = None,
                   library: Optional[Path] = None, progress=None) -> Dict[str, Any]:
    import tts_expressive
    pkg = schemas.load_package(package_path)
    lib = Path(library) if library else common.library_dir()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / ".work" / pkg.package_id
    work.mkdir(parents=True, exist_ok=True)
    assets = Assets(lib, (0, 0))
    if mode == "keyframes" and placeholder_tts is None:
        placeholder_tts = True                      # keyframes never spend TTS quota
    tts_expressive.synthesize_package(pkg, work, placeholder_tts, lib)
    if mode == "keyframes":
        timeline, _, _ = audio_master.build_timeline(pkg, work / "audio")
        res = render_stills(pkg, timeline, out_dir / f"{pkg.package_id}_keyframes", mode, assets)
        return {"mode": mode, **res}
    mastered = audio_master.master_package(pkg, work / "audio", work, lib)
    suffix = "" if mode == "hd" else "_draft"
    video = out_dir / f"{pkg.package_id}{suffix}.mp4"
    res = render_video(pkg, mastered["timeline"], Path(mastered["master"]), video, mode, assets, progress)
    stills = render_stills(pkg, mastered["timeline"], work / "stills", mode, assets)
    cover = out_dir / f"{pkg.package_id}_cover.jpg"
    Path(stills["cover"]).replace(cover)
    return {"mode": mode, "video": res["video"], "cover": str(cover), "frames": res["frames"],
            "fps": res["fps"], "size": res["size"], "duration_sec": mastered["timeline"]["total_sec"],
            "layout_issues": res.get("layout_issues", [])}


# =========================================================================== library thumbnails
def render_asset_thumbnail(lib: Path, entry: Dict[str, Any], out_png: Path, size: int = 256, assets: Optional["Assets"] = None) -> None:
    """Render a 256x256 preview for any visual library asset (forge.py / previews.py; pass `assets` to reuse a loaded index)."""
    lib = Path(lib)
    if assets is None:
        assets = Assets(lib, (size, size))
    index = assets.index
    cat, aid = entry["category"], entry["id"]
    theme = dict(DEFAULT_THEME)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surf)
    setc(ctx, "#16213a", theme)
    ctx.paint()
    S = size

    def char_with(pose_json, expr_json, char_json=None):
        ch = char_json or next((assets.json(a.id, "01_characters") for a in index.by_category("01_characters")), None) \
            or {"rig": DEFAULT_RIG}
        draw_character(ctx, ch, pose_json or {"joints": {}}, expr_json or {}, (expr_json or {}).get("mouth_rest", "flat"),
                       theme, S * 0.98, (S * 0.5, S * 0.97))

    if cat == "01_characters":
        char_with(assets.json("standing_neutral", "02_poses"), assets.json("neutral", "03_expressions"), assets.json(aid, cat))
    elif cat == "02_poses":
        char_with(assets.json(aid, cat), assets.json("neutral", "03_expressions"))
    elif cat == "03_expressions":
        ej = assets.json(aid, cat) or {}
        if ej.get("format") == "viseme_set/v1":
            for i, k in enumerate(("rest", "A", "E", "O", "M")):
                draw_mouth(ctx, S * (0.18 + 0.16 * i), S * 0.5, S * 0.12, ej["visemes"][k], theme, "#f1f5f9")
        else:
            circle(ctx, S * 0.5, S * 0.52, S * 0.36, theme, fill="#0f172a", stroke="#f1f5f9", sw=S * 0.02)
            draw_face(ctx, S * 0.5, S * 0.52, S * 0.36, ej, ej.get("mouth_rest", "flat"), 0.0, theme, "#f1f5f9")
    elif cat == "04_motions":
        mj = assets.json(aid, cat) or {}
        setc(ctx, "#334155", theme)
        ctx.rectangle(S * 0.1, S * 0.15, S * 0.8, S * 0.7)
        ctx.stroke()
        tr = (mj.get("tracks") or [{"keys": [[0, 0], [1, 1]]}])[0]
        dur = max(1e-3, mj.get("duration_sec", 1.0))
        vals = [eval_track(tr["keys"], dur * i / 60, mj.get("spring", {})) for i in range(61)]
        lo, hi = min(vals), max(vals)
        setc(ctx, "#22d3ee", theme)
        ctx.set_line_width(S * 0.02)
        for i, v in enumerate(vals):
            x, y = S * (0.1 + 0.8 * i / 60), S * (0.85 - 0.7 * ((v - lo) / (hi - lo) if hi > lo else 0.5))
            ctx.line_to(x, y) if i else ctx.move_to(x, y)
        ctx.stroke()
    elif cat in ("05_scenes", "06_props", "08_overlays"):
        if assets.is_svg(aid, cat):
            sf = assets.svg(aid, cat, S, S)
            draw_surface(ctx, sf, (S - sf.get_width()) / 2, (S - sf.get_height()) / 2, sf.get_width(), sf.get_height())
        elif cat == "05_scenes":
            ctx.save(); ctx.translate(S * 0.2, 0); draw_background(ctx, assets, aid, int(S * 0.6), S, theme, 0.0); ctx.restore()
        else:
            draw_overlay(ctx, assets, aid, S, S, theme, 0.5, (S * 0.5, S * 0.5), S * 0.12)
            circle(ctx, S * 0.5, S * 0.5, S * 0.12, theme, stroke="#f1f5f9", sw=3)
    elif cat == "07_widgets":
        draw_widget(ctx, assets.json(aid, cat) or {}, S * 0.06, S * 0.2, S * 0.88, S * 0.6, theme, 2.0)
    elif cat == "09_transitions":
        tj = assets.json(aid, cat) or {}
        for i, col in enumerate(("#22d3ee", "#f472b6")):
            rrect(ctx, S * (0.08 + 0.46 * i), S * 0.3, S * 0.38, S * 0.4, S * 0.04)
            setc(ctx, col, theme)
            ctx.fill()
        set_font(ctx, "DejaVu Sans Bold", S * 0.075)
        draw_text(ctx, str(tj.get("type", aid))[:14], S * 0.5 - text_width(ctx, str(tj.get("type", aid))[:14]) / 2, S * 0.88, theme, "#f1f5f9")
        line(ctx, S * 0.35, S * 0.5, S * 0.65, S * 0.5, S * 0.03, "#ffffff", theme)
    elif cat == "10_caption_styles":
        cj = assets.json(aid, cat) or {}
        words = [{"word": "WORD", "start": 0.0, "end": 0.5}, {"word": "POP", "start": 0.5, "end": 1.0},
                 {"word": "NOW", "start": 1.0, "end": 1.5}]
        draw_captions(ctx, {**cj, "position_y": 0.55, "size_ratio": cj.get("size_ratio", 0.06) * 1.4}, words, 0.7, S, S, theme)
    elif cat == "11_themes":
        pal = (assets.json(aid, cat) or {}).get("palette", DEFAULT_THEME)
        for i, (k, v) in enumerate(list(pal.items())[:8]):
            rrect(ctx, S * (0.08 + 0.22 * (i % 4)), S * (0.2 + 0.36 * (i // 4)), S * 0.18, S * 0.3, S * 0.03)
            setc(ctx, v, theme)
            ctx.fill()
    else:
        raise ValueError(f"no thumbnail renderer for {cat}")
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    surf.write_to_png(str(out_png))


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--keyframes-only", action="store_true")
    g.add_argument("--draft-480p", action="store_true")
    g.add_argument("--hd-1080p60", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--placeholder-tts", action="store_true", help="skip Gemini TTS, use the offline placeholder voice")
    a = ap.parse_args(argv)
    mode = "keyframes" if a.keyframes_only else "draft" if a.draft_480p else "hd"
    last = [-1]

    def prog(p: float) -> None:
        pct = int(p * 100)
        if pct // 10 != last[0] // 10:
            print(f"render {pct}%", flush=True)
        last[0] = pct

    res = render_package(Path(a.package), mode, Path(a.out), True if a.placeholder_tts else None, progress=prog)
    print(json.dumps(res, indent=2))
    return 0


import render_fx  # noqa: E402  (extensions; imported last because it reuses the primitives above)

if __name__ == "__main__":
    sys.exit(main())
