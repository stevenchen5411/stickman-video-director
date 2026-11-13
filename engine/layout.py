#!/usr/bin/env python3
"""Layout solver: one place decides where captions, widgets and props go so they never collide with the
character, whatever the scene anchor, aspect ratio or caption style.

Pure geometry (no cairo). The renderer feeds it the character's rig points for the scene's target pose and gets
back rectangles. `check()` is the same geometry used as a QA: it lists any residual overlap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Pt = Tuple[float, float]

GAP = 0.012            # clearance between zones, in frame heights
SAFE_BOTTOM = 0.93     # nothing readable below this
SAFE_SIDE = 0.03
MAX_LIFT = 0.10        # most the character may be lifted to make room for the caption (frame heights)
MIN_WIDGET_H = 0.14
PROP_FRAC = 0.28       # prop box edge, as a fraction of min(W, H)


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def r(self) -> float:
        return self.x + self.w

    @property
    def b(self) -> float:
        return self.y + self.h

    def overlap(self, o: "Rect") -> float:
        ox = min(self.r, o.r) - max(self.x, o.x)
        oy = min(self.b, o.b) - max(self.y, o.y)
        return ox * oy if ox > 0 and oy > 0 else 0.0

    def shifted(self, dy: float) -> "Rect":
        return Rect(self.x, self.y + dy, self.w, self.h)


@dataclass
class Layout:
    W: int
    H: int
    char: Rect                       # character extent (after any lift)
    head: Rect                       # head bounding box (after any lift)
    char_dy: float = 0.0             # px the character is lifted (negative = up)
    caption_y: Optional[float] = None
    caption: Optional[Rect] = None
    widget: Optional[Rect] = None
    prop: Optional[Rect] = None
    prop_side: str = ""
    notes: List[str] = field(default_factory=list)


def char_extent(pts: Dict[str, Any], head_r: float, pad: float) -> Tuple[Rect, Rect]:
    keys = [k for k in pts if not k.startswith("_")]
    xs = [pts[k][0] for k in keys]
    ys = [pts[k][1] for k in keys]
    hx, hy = pts["head"]
    x0, x1 = min(xs + [hx - head_r]) - pad, max(xs + [hx + head_r]) + pad
    y0, y1 = min(ys + [hy - head_r]) - pad, max(ys) + pad
    return Rect(x0, y0, x1 - x0, y1 - y0), Rect(hx - head_r, hy - head_r, 2 * head_r, 2 * head_r)


def caption_size(style: Optional[Dict[str, Any]], W: int, H: int) -> float:
    return float((style or {}).get("size_ratio", 0.06)) * min(W, H) * 1.45


def solve(W: int, H: int, pts: Dict[str, Any], head_r: float, lw: float, *,
          caption_style: Optional[Dict[str, Any]] = None, has_widget: bool = False, has_prop: bool = False) -> Layout:
    char, head = char_extent(pts, head_r, lw * 1.2)
    gap = GAP * H
    lay = Layout(W, H, char, head)

    # ---- caption: keep the style's own height unless it would sit on the character
    if caption_style:
        size = caption_size(caption_style, W, H)
        y = float(caption_style.get("position_y", 0.7)) * H
        top_off, bot_off = size * 1.0, size * 0.5          # text box spans [y - size, y + 0.5 size]
        y_max = SAFE_BOTTOM * H - bot_off

        def hits(yy: float) -> bool:
            return (yy - top_off) < char.b + gap * 0.5 and (yy + bot_off) > char.y - gap * 0.5

        if hits(y):
            below = char.b + gap + top_off
            if below <= y_max:
                y = below
                lay.notes.append("caption moved below the feet")
            else:
                lift = min(MAX_LIFT * H, below - y_max)
                lay.char_dy = -lift
                char, head = char.shifted(-lift), head.shifted(-lift)
                lay.char, lay.head = char, head
                y = min(y_max, char.b + gap + top_off)
                lay.notes.append(f"character lifted {lift:.0f}px for the caption")
        lay.caption_y = y
        lay.caption = Rect(0.04 * W, y - top_off, 0.92 * W, top_off + bot_off)

    # ---- widget: top band, never lower than the head
    if has_widget:
        x, y0, w = W * 0.07, H * 0.07, W * 0.86
        h = H * 0.24
        room = head.y - gap - y0
        if room < h:
            h = max(MIN_WIDGET_H * H, room)
            lay.notes.append("widget shortened above the head")
        lay.widget = Rect(x, y0, w, h)

    # ---- prop: beside the body at torso height, on the roomier side
    if has_prop:
        b = PROP_FRAC * min(W, H)
        left_room = char.x - gap - SAFE_SIDE * W
        right_room = (1 - SAFE_SIDE) * W - (char.r + gap)
        side, room = ("left", left_room) if left_room >= right_room else ("right", right_room)
        bb = max(0.0, min(b, room))
        if bb < 0.55 * b:
            lay.notes.append("little room beside the character; prop shrunk")
        bb = max(bb, 0.4 * b)
        x = char.x - gap - bb if side == "left" else char.r + gap
        yc = (pts["neck_base"][1] + pts["pelvis"][1]) / 2 + lay.char_dy
        y = yc - bb / 2
        top_lim = (lay.widget.b + gap) if lay.widget else 0.04 * H
        y = max(top_lim, min(y, char.b - bb))
        lay.prop, lay.prop_side = Rect(x, y, bb, bb), side
    return lay


def check(lay: Layout) -> List[str]:
    """Residual problems after solving (empty list = clean)."""
    W, H = lay.W, lay.H
    out: List[str] = []
    if lay.caption and lay.caption.overlap(lay.char) > 0:
        out.append("caption overlaps the character")
    if lay.caption and lay.caption.b > H:
        out.append("caption outside the frame")
    if lay.prop:
        if lay.prop.overlap(lay.char) > 0:
            out.append("prop overlaps the character")
        if lay.prop.x < 0 or lay.prop.r > W or lay.prop.y < 0 or lay.prop.b > H:
            out.append("prop outside the frame")
        if lay.caption and lay.prop.overlap(lay.caption) > 0:
            out.append("prop overlaps the caption")
        if lay.widget and lay.prop.overlap(lay.widget) > 0:
            out.append("prop overlaps the widget")
    if lay.widget and lay.widget.overlap(lay.head) > 0:
        out.append("widget overlaps the head")
    return out
