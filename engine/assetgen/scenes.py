"""Backdrops (05_scenes): 1080x1920 SVG compositions. Ground line at y=1500 so the stickman stands on it.

Design rules: muted, mid/dark tones so white stick lines and props pop; keep the centre (x 300-900, y 650-1500)
uncluttered; detail lives at the edges and in the distance."""
from __future__ import annotations

import math
import random
from typing import Any, Callable, Dict, List, Optional, Tuple

from .kit import *  # noqa: F401,F403

W, H, GY = 1080, 1920, 1500
SCENES: List[Dict[str, Any]] = []
_IDS: set = set()


class Doc:
    """Collects defs (gradients) and body elements for one scene."""

    def __init__(self, seed: str):
        self.defs: List[str] = []
        self.body: List[str] = []
        self.rng = random.Random(seed)
        self.n = 0

    def grad(self, stops, x1=0, y1=0, x2=0, y2=1) -> str:
        self.n += 1
        gid = f"g{self.n}"
        self.defs.append(linear_grad(gid, stops, x1, y1, x2, y2))
        return f"url(#{gid})"

    def rgrad(self, stops, cx=0.5, cy=0.5, r=0.5, ops=None) -> str:
        self.n += 1
        gid = f"r{self.n}"
        self.defs.append(radial_grad(gid, stops, cx, cy, r, ops))
        return f"url(#{gid})"

    def add(self, *els) -> None:
        for e in els:
            if isinstance(e, (list, tuple)):
                self.body.extend(e)
            else:
                self.body.append(e)

    def svg(self) -> str:
        return svg(self.body, W, H, self.defs)


def S(sid: str, tags: str, build: Callable[[Doc], None], anchor: Tuple[float, float] = (0.6, 0.78), scope: str = "") -> None:
    if sid in _IDS:
        raise ValueError(f"duplicate scene {sid}")
    _IDS.add(sid)
    tl = tags.split()
    SCENES.append({"id": sid, "tags": [t for t in tl if t != "general"] or ["general"],
                   "scope": scope or ("global" if "general" in tl else "specific"), "build": build, "anchor": list(anchor)})


# =========================================================================== building blocks
SKIES = {
    "day": ("#38bdf8", "#bae6fd"), "noon": ("#0ea5e9", "#7dd3fc"), "sunset": ("#7c3aed", "#fb923c"), "dusk": ("#1e1b4b", "#be185d"),
    "night": ("#020617", "#1e293b"), "dawn": ("#fda4af", "#fde68a"), "overcast": ("#64748b", "#cbd5e1"), "storm": ("#1f2937", "#475569"),
}
NIGHTISH = {"night", "dusk", "storm"}


def sky(d: Doc, kind: str, y1: float = GY) -> None:
    a, b = SKIES[kind]
    d.add(rect(0, 0, W, y1 + 4, d.grad([(0, a), (1, b)]), 0, None))
    if kind in ("night", "dusk"):
        stars(d, 70 if kind == "night" else 30, 0, y1 * 0.7)


def stars(d: Doc, n: int, y0: float, y1: float, col: str = "#f8fafc") -> None:
    for _ in range(n):
        x, y = d.rng.uniform(0, W), d.rng.uniform(y0, y1)
        d.add(circle(round(x), round(y), round(d.rng.choice((1.5, 2, 2.5, 3.5)), 1), col, None, op=round(d.rng.uniform(0.35, 0.95), 2)))


def sun(d: Doc, x, y, r, col="#fde68a", glow=True) -> None:
    if glow:
        d.add(circle(x, y, r * 2.2, d.rgrad([(0, col), (1, col)], ops=[0.45, 0.0]), None))
    d.add(circle(x, y, r, col, None))


def moon(d: Doc, x, y, r) -> None:
    d.add(circle(x, y, r * 2.4, d.rgrad([(0, "#e2e8f0"), (1, "#e2e8f0")], ops=[0.25, 0.0]), None), circle(x, y, r, "#f1f5f9", None),
          circle(x - r * 0.3, y - r * 0.2, r * 0.18, "#cbd5e1", None), circle(x + r * 0.25, y + r * 0.3, r * 0.12, "#cbd5e1", None))


def clouds(d: Doc, n: int, y0: float, y1: float, col="#ffffff", op=0.85, size=(50, 95)) -> None:
    for _ in range(n):
        x, y, s = d.rng.uniform(-40, W + 40), d.rng.uniform(y0, y1), d.rng.uniform(*size)
        d.add(path(cloud_d(round(x), round(y), round(s)), col, None, op=op))


def ground(d: Doc, col: str, y: float = GY, col2: Optional[str] = None) -> None:
    d.add(rect(0, y, W, H - y, d.grad([(0, col), (1, col2 or darken(col, 0.6))]), 0, None))


def mountains(d: Doc, base: float, col: str, peaks: int, hmin: float, hmax: float, snow: bool = False) -> None:
    pts = [(0, base)]
    xs = sorted(d.rng.uniform(0, W) for _ in range(peaks))
    for i, x in enumerate(xs):
        pts.append((x, base - d.rng.uniform(hmin, hmax)))
        if i < len(xs) - 1:
            pts.append(((x + xs[i + 1]) / 2, base - d.rng.uniform(hmin * 0.3, hmin * 0.7)))
    pts += [(W, base - hmin * 0.4), (W, base + 4), (0, base + 4)]
    d.add(poly(pts, col, None))
    if snow:
        for i in range(1, len(pts) - 3, 2):
            x, y = pts[i]
            if base - y > hmin:
                d.add(poly([(x, y), (x + 40, y + 60), (x + 14, y + 52), (x - 10, y + 66), (x - 38, y + 58)], "#f1f5f9", None, op=0.9))


def hills(d: Doc, base: float, col: str, amp: float = 60, n: int = 3) -> None:
    pts = " ".join(f"Q{(i + 0.5) * W / n:.0f},{base - amp * (1 if i % 2 == 0 else 0.4):.0f} {(i + 1) * W / n:.0f},{base:.0f}" for i in range(n))
    d.add(path(f"M0,{base} {pts} L{W},{H} L0,{H} Z", col, None))


def skyline(d: Doc, base: float, col: str, hmin: float, hmax: float, lit: Optional[str] = None, density: float = 0.35, wmin=70, wmax=150) -> None:
    x = -20
    while x < W:
        w = d.rng.uniform(wmin, wmax)
        h = d.rng.uniform(hmin, hmax)
        d.add(rect(round(x), round(base - h), round(w), round(h + 2), col, 0, None))
        if lit:
            for wy in range(int(base - h + 24), int(base - 20), 34):
                for wx in range(int(x + 14), int(x + w - 18), 26):
                    if d.rng.random() < density:
                        d.add(rect(wx, wy, 12, 16, lit, 0, None, op=round(d.rng.uniform(0.5, 0.95), 2)))
        if d.rng.random() < 0.25:
            d.add(rect(round(x + w / 2 - 3), round(base - h - 50), 6, 50, col, 0, None))
        x += w + d.rng.uniform(4, 18)


def pine_row(d: Doc, base: float, col: str, n: int, hmin: float, hmax: float, x0: float = -40, x1: float = W + 40) -> None:
    for _ in range(n):
        x, h = d.rng.uniform(x0, x1), d.rng.uniform(hmin, hmax)
        d.add(poly([(x, base - h), (x + h * 0.28, base), (x - h * 0.28, base)], col, None))


def round_tree(d: Doc, x: float, base: float, h: float, crown: str, trunk: str = "#3f2a1d") -> None:
    d.add(rect(x - h * 0.05, base - h * 0.55, h * 0.1, h * 0.56, trunk, 0, None),
          path(cloud_d(round(x), round(base - h * 0.72), round(h * 0.34)), crown, None))


def lamp_post(d: Doc, x: float, base: float, on: bool) -> None:
    d.add(rect(x - 6, base - 360, 12, 360, "#1e293b", 0, None), rect(x - 34, base - 380, 68, 26, "#334155", 8, None))
    if on:
        d.add(circle(x, base - 340, 110, d.rgrad([(0, "#fde68a"), (1, "#fde68a")], ops=[0.45, 0.0]), None))


def window_frame(d: Doc, x, y, w, h, kind: str, frame="#cbd5e1") -> None:
    a, b = SKIES[kind]
    d.add(rect(x, y, w, h, d.grad([(0, a), (1, b)]), 6, frame, 14))
    if kind in NIGHTISH:
        for _ in range(6):
            d.add(circle(round(x + d.rng.uniform(20, w - 20)), round(y + d.rng.uniform(20, h * 0.6)), 2.5, "#f8fafc", None, op=0.8))
    else:
        d.add(path(cloud_d(round(x + w * 0.35), round(y + h * 0.3), round(w * 0.12)), "#ffffff", None, op=0.8))
    d.add(line(x + w / 2, y, x + w / 2, y + h, frame, 10), line(x, y + h / 2, x + w, y + h / 2, frame, 10))


def room(d: Doc, wall: str, floor: str, floor_y: float = 1330, wall2: Optional[str] = None, planks: bool = True, tiles: bool = False,
         baseboard: str = "#0f172a") -> None:
    d.add(rect(0, 0, W, floor_y, d.grad([(0, wall2 or lighten(wall, 0.08)), (1, darken(wall, 0.85))]), 0, None))
    d.add(rect(0, floor_y, W, H - floor_y, d.grad([(0, floor), (1, darken(floor, 0.55))]), 0, None))
    d.add(rect(0, floor_y - 16, W, 18, baseboard, 0, None, op=0.6))
    if planks:
        for i, yy in enumerate(range(int(floor_y + 70), H, 90)):
            d.add(line(0, yy, W, yy, darken(floor, 0.75), 4, op=0.6))
            for xx in range(-100 + (i % 2) * 140, W, 280):
                d.add(line(xx, yy - 90 if yy - 90 > floor_y else floor_y, xx, yy, darken(floor, 0.75), 3, op=0.5))
    if tiles:
        for yy in range(int(floor_y + 80), H, 110):
            d.add(line(0, yy, W, yy, darken(floor, 0.8), 3, op=0.5))
        for xx in range(0, W + 1, 135):
            d.add(line(W / 2 + (xx - W / 2) * 0.6, floor_y, xx + (xx - W / 2) * 0.5, H, darken(floor, 0.8), 3, op=0.5))


def vignette(d: Doc, strength: float = 0.45) -> None:
    d.add(rect(0, 0, W, H, d.rgrad([(0, "#000000"), (1, "#000000")], 0.5, 0.45, 0.75, [0.0, strength]), 0, None))


# simple furniture silhouettes (flat, low contrast, edges of frame)
def desk(d: Doc, x, y, w=420, col="#7c5a3c", monitor=True, screen="#0ea5e9") -> None:
    d.add(rect(x, y, w, 26, col, 4, None), rect(x + 20, y + 26, 24, 170, darken(col, 0.8), 0, None), rect(x + w - 44, y + 26, 24, 170, darken(col, 0.8), 0, None))
    if monitor:
        d.add(rect(x + w * 0.3, y - 190, w * 0.48, 150, "#1e293b", 10, None), rect(x + w * 0.3 + 12, y - 178, w * 0.48 - 24, 126, screen, 4, None, op=0.85),
              rect(x + w * 0.52, y - 40, 18, 40, "#334155", 0, None))


def shelf(d: Doc, x, y, w, rows=3, col="#5b4636", books=True) -> None:
    for r in range(rows):
        yy = y + r * 150
        d.add(rect(x, yy + 120, w, 16, col, 2, None))
        if books:
            xx = x + 10
            while xx < x + w - 30:
                bw = d.rng.uniform(16, 32)
                bh = d.rng.uniform(70, 115)
                d.add(rect(round(xx), round(yy + 120 - bh), round(bw), round(bh), d.rng.choice(["#b91c1c", "#1d4ed8", "#15803d", "#a16207", "#6d28d9", "#0f766e", "#be185d"]), 2, None, op=0.85))
                xx += bw + d.rng.uniform(2, 8)


def frame_art(d: Doc, x, y, w, h, inner: str) -> None:
    d.add(rect(x, y, w, h, "#d6a76c", 6, None), rect(x + 12, y + 12, w - 24, h - 24, inner, 2, None),
          poly([(x + 12, y + h - 12), (x + w * 0.4, y + h * 0.45), (x + w * 0.65, y + h * 0.7), (x + w - 12, y + h * 0.4), (x + w - 12, y + h - 12)], darken(inner, 0.6), None, op=0.8))


def wall_clock(d: Doc, x, y, r=60) -> None:
    d.add(circle(x, y, r, "#f8fafc", "#334155", 10), line(x, y, x, y - r * 0.6, "#0f172a", 8), line(x, y, x + r * 0.45, y + r * 0.2, "#0f172a", 6))


def plant(d: Doc, x, base, s=1.0) -> None:
    d.add(path(f"M{x - 50 * s},{base - 110 * s} L{x + 50 * s},{base - 110 * s} L{x + 38 * s},{base} L{x - 38 * s},{base} Z", "#c2410c", None))
    for dx, h in ((-40, 190), (0, 250), (40, 200), (-20, 230), (24, 220)):
        d.add(ellipse(x + dx * s, base - (110 + h * 0.55) * s, 22 * s, h * 0.5 * s, "#15803d", None, op=0.95, transform=f"rotate({dx * 0.6} {x + dx * s} {base - (110 + h * 0.55) * s})"))


def chart_screen(d: Doc, x, y, w, h, up=True, candles=False) -> None:
    d.add(rect(x, y, w, h, "#0b1220", 10, "#334155", 8))
    if candles:
        for i in range(8):
            cx = x + 30 + i * (w - 60) / 7
            base = y + h * (0.75 - 0.5 * i / 7 if up else 0.25 + 0.5 * i / 7)
            c = "#22c55e" if (d.rng.random() < (0.7 if up else 0.3)) else "#ef4444"
            hh = d.rng.uniform(20, 50)
            d.add(line(cx, base - hh, cx, base + hh * 0.6, c, 3), rect(cx - 8, base - hh * 0.6, 16, hh * 0.9, c, 2, None))
    else:
        pts = [(x + 20 + i * (w - 40) / 9, y + h * (0.8 - 0.6 * (i / 9) if up else 0.2 + 0.6 * (i / 9)) + d.rng.uniform(-18, 18)) for i in range(10)]
        d.add(pline(pts, "#22c55e" if up else "#ef4444", 6))


# =========================================================================== OUTDOOR
def _city(kind):
    def b(d: Doc):
        sky(d, kind)
        if kind in ("day", "noon"):
            sun(d, 860, 260, 70)
            clouds(d, 5, 150, 600)
        elif kind == "sunset":
            sun(d, 540, 1150, 130, "#fdba74")
        else:
            moon(d, 820, 280, 55)
        far = {"day": "#7dd3fc", "noon": "#7dd3fc", "sunset": "#6d28d9", "night": "#1e293b"}[kind]
        near = {"day": "#334155", "noon": "#334155", "sunset": "#3b0764", "night": "#0f172a"}[kind]
        skyline(d, GY, lighten(far, 0.0), 300, 700, None)
        skyline(d, GY, near, 160, 520, "#fde68a" if kind in ("night", "sunset") else "#bae6fd", 0.35 if kind != "day" else 0.18)
        ground(d, "#1f2937" if kind != "day" else "#475569")
        d.add(rect(0, GY + 120, W, 14, "#facc15", 0, None, op=0.5))
        vignette(d, 0.35)
    return b


for k in ("day", "sunset", "night"):
    S(f"city_skyline_{k}", "general city business", _city(k))


def _street(night):
    def b(d: Doc):
        sky(d, "night" if night else "day")
        skyline(d, 1180, "#1e293b" if night else "#94a3b8", 300, 600, "#fde68a" if night else None, 0.3)
        for x, w, c in ((-40, 380, "#7c2d12"), (720, 420, "#1e3a8a")):
            d.add(rect(x, 520, w, 980, darken(c, 0.6) if night else c, 0, None))
            for wy in range(580, 1380, 120):
                for wx in range(x + 40, x + w - 60, 110):
                    d.add(rect(wx, wy, 60, 80, "#fde68a" if (night and d.rng.random() < 0.5) else "#bae6fd", 4, None, op=0.85))
        ground(d, "#334155" if not night else "#111827")
        d.add(rect(0, GY, W, 60, "#94a3b8" if not night else "#374151", 0, None))
        for x in range(40, W, 200):
            d.add(rect(x, GY + 230, 110, 14, "#f8fafc", 0, None, op=0.6))
        lamp_post(d, 120, GY, night)
        lamp_post(d, 960, GY, night)
        vignette(d, 0.4)
    return b


S("city_street_day", "general city", _street(False))
S("city_street_night", "general city mystery", _street(True))


def _suburb(night):
    def b(d: Doc):
        sky(d, "night" if night else "day")
        moon(d, 840, 300, 50) if night else sun(d, 860, 280, 64)
        hills(d, 1200, "#166534" if not night else "#052e16", 80, 2)
        for x, c in ((-60, "#fca5a5"), (330, "#fde68a"), (720, "#93c5fd")):
            col = darken(c, 0.45) if night else c
            d.add(rect(x, 1030, 330, 470, col, 0, None), poly([(x - 30, 1040), (x + 165, 860), (x + 360, 1040)], darken(col, 0.7), None),
                  rect(x + 130, 1300, 80, 200, darken(col, 0.6), 4, None))
            for wx in (x + 40, x + 230):
                d.add(rect(wx, 1120, 70, 80, "#fde68a" if night else "#e0f2fe", 4, None))
        ground(d, "#4d7c0f" if not night else "#14532d")
        d.add(rect(0, GY + 40, W, 120, "#94a3b8" if not night else "#334155", 0, None))
        vignette(d, 0.3)
    return b


S("suburb_street_day", "general home family", _suburb(False))
S("suburb_street_night", "general home family", _suburb(True))


def _park(autumn):
    def b(d: Doc):
        sky(d, "day")
        clouds(d, 4, 160, 520)
        hills(d, 1250, "#86efac" if not autumn else "#fcd34d", 90, 2)
        crown = "#16a34a" if not autumn else "#ea580c"
        for x, h in ((80, 620), (230, 480), (900, 640), (1030, 500)):
            round_tree(d, x, GY, h, crown if x % 2 else darken(crown, 0.85))
        ground(d, "#4ade80" if not autumn else "#ca8a04")
        d.add(rect(80, GY - 120, 260, 22, "#92400e", 4, None), rect(80, GY - 180, 260, 18, "#92400e", 4, None),
              rect(100, GY - 98, 16, 98, "#451a03", 0, None), rect(300, GY - 98, 16, 98, "#451a03", 0, None))
        path_d = f"M300,{H} C420,1700 520,1580 560,{GY} L640,{GY} C660,1580 760,1700 880,{H} Z"
        d.add(path(path_d, "#e7e5e4", None, op=0.6))
        vignette(d, 0.25)
    return b


S("park_day", "general nature", _park(False))
S("park_autumn", "general nature", _park(True))


def _forest(night):
    def b(d: Doc):
        sky(d, "night" if night else "dawn")
        if night:
            moon(d, 780, 300, 60)
        for base, col, n, hm in ((1250, "#1e3a2f" if night else "#4d7c0f", 22, (380, 620)), (1400, "#0f2a1f" if night else "#3f6212", 16, (450, 750)),
                                 (GY, "#052e16" if night else "#14532d", 8, (700, 1050))):
            pine_row(d, base, col, n, *hm)
        ground(d, "#14532d" if not night else "#052e16")
        if night:
            for _ in range(14):
                d.add(circle(round(d.rng.uniform(40, W - 40)), round(d.rng.uniform(900, 1450)), 5, "#fde047", None, op=0.85))
        vignette(d, 0.45)
    return b


S("forest_day", "nature adventure", _forest(False))
S("forest_night", "nature mystery spooky", _forest(True))


def _beach(kind):
    def b(d: Doc):
        sky(d, kind, 1150)
        sun(d, 540 if kind == "sunset" else 820, 1080 if kind == "sunset" else 300, 120 if kind == "sunset" else 70, "#fdba74" if kind == "sunset" else "#fde68a")
        clouds(d, 3, 200, 600, op=0.7)
        d.add(rect(0, 1150, W, 300, d.grad([(0, "#0369a1" if kind != "sunset" else "#7c3aed"), (1, "#38bdf8" if kind != "sunset" else "#f472b6")]), 0, None))
        for y in range(1190, 1440, 50):
            d.add(path(f"M0,{y} " + " ".join(f"Q{x + 45},{y - 12} {x + 90},{y}" for x in range(0, W, 90)), "none", "#e0f2fe", 4, op=0.4))
        d.add(path(f"M0,1450 C300,1400 700,1470 1080,1420 L1080,{H} L0,{H} Z", "#fcd34d" if kind != "sunset" else "#d6a76c", None))
        d.add(path("M960,1450 C966,1300 950,1150 990,1020", "none", "#78350f", 22))
        for a in (-60, -20, 20, 60, 100):
            d.add(ellipse(990, 1010, 120, 26, "#15803d", None, transform=f"rotate({a} 990 1010) translate(80 0)"))
        vignette(d, 0.25)
    return b


S("beach_day", "travel nature ocean", _beach("day"))
S("beach_sunset", "travel nature ocean love", _beach("sunset"))


def _mountains(kind, snow=False):
    def b(d: Doc):
        sky(d, kind)
        if kind == "sunset":
            sun(d, 300, 900, 110, "#fdba74")
        elif kind not in NIGHTISH:
            clouds(d, 4, 180, 560, op=0.8)
        else:
            moon(d, 800, 320, 55)
        cols = {"day": ("#94a3b8", "#64748b", "#475569"), "sunset": ("#a78bfa", "#7c3aed", "#4c1d95"), "night": ("#334155", "#1e293b", "#0f172a"),
                "dawn": ("#f9a8d4", "#c084fc", "#7e22ce")}[kind]
        mountains(d, 1250, cols[0], 4, 350, 650, snow)
        mountains(d, 1380, cols[1], 5, 220, 450, snow)
        hills(d, GY, cols[2], 60, 2)
        ground(d, darken(cols[2], 0.9) if not snow else "#e2e8f0", GY, None if not snow else "#94a3b8")
        vignette(d, 0.3)
    return b


S("mountains_day", "nature travel adventure", _mountains("day"))
S("mountains_sunset", "nature travel motivation", _mountains("sunset"))
S("mountains_snow", "nature travel weather", _mountains("day", True))
S("mountains_night", "nature mystery", _mountains("night"))


def _desert(night):
    def b(d: Doc):
        sky(d, "night" if night else "noon")
        moon(d, 820, 300, 60) if night else sun(d, 800, 300, 90, "#fef08a")
        for base, col in ((1250, "#d97706" if not night else "#44403c"), (1380, "#f59e0b" if not night else "#57534e"), (GY, "#fbbf24" if not night else "#78716c")):
            d.add(path(f"M0,{base} C250,{base - 90} 500,{base + 40} 760,{base - 60} C900,{base - 100} 1000,{base - 20} 1080,{base - 40} L1080,{H} L0,{H} Z", col, None))
        ground(d, "#fcd34d" if not night else "#78716c")
        for x, h in ((140, 300), (930, 220)):
            c = "#15803d" if not night else "#1c1917"
            d.add(rect(x - 22, GY - h, 44, h, c, 22, None), path(f"M{x - 22},{GY - h * 0.5} L{x - 70},{GY - h * 0.5} L{x - 70},{GY - h * 0.8}", "none", c, 30))
        vignette(d, 0.3)
    return b


S("desert_day", "nature travel adventure", _desert(False))
S("desert_night", "nature mystery adventure", _desert(True))


def _farm(kind):
    def b(d: Doc):
        sky(d, kind)
        sun(d, 300 if kind == "sunset" else 860, 1000 if kind == "sunset" else 260, 90, "#fdba74" if kind == "sunset" else "#fde68a")
        hills(d, 1280, "#65a30d" if kind == "day" else "#854d0e", 70, 3)
        d.add(rect(700, 980, 300, 300, "#b91c1c" if kind == "day" else "#7f1d1d", 0, None), poly([(680, 990), (850, 860), (1020, 990)], "#7f1d1d", None),
              rect(800, 1140, 100, 140, "#f8fafc", 0, None))
        for i in range(12):
            d.add(rect(i * 95, 1360, 14, 120, "#a16207", 0, None))
        d.add(rect(0, 1390, W, 12, "#a16207", 0, None), rect(0, 1440, W, 12, "#a16207", 0, None))
        ground(d, "#84cc16" if kind == "day" else "#a16207")
        vignette(d, 0.25)
    return b


S("farm_day", "agriculture nature food", _farm("day"))
S("farm_sunset", "agriculture nature", _farm("sunset"))


def _ocean(night):
    def b(d: Doc):
        sky(d, "night" if night else "day", 1100)
        moon(d, 760, 400, 60) if night else (sun(d, 820, 320, 70), clouds(d, 4, 200, 600))
        d.add(rect(0, 1100, W, H - 1100, d.grad([(0, "#1e3a8a" if night else "#0284c7"), (1, "#020617" if night else "#075985")]), 0, None))
        for y in range(1130, H, 70):
            d.add(path(f"M0,{y} " + " ".join(f"Q{x + 50},{y - 14} {x + 100},{y}" for x in range(0, W, 100)), "none", "#bae6fd", 4, op=0.25))
        if night:
            d.add(rect(700, 1110, 120, 500, d.grad([(0, "#f1f5f9"), (1, "#f1f5f9")]), 0, None, op=0.12))
        vignette(d, 0.35)
    return b


S("ocean_day", "nature ocean travel", _ocean(False))
S("ocean_night", "nature ocean mystery", _ocean(True))


def _jungle(d: Doc):
    sky(d, "day")
    for base, col in ((1200, "#166534"), (1350, "#15803d"), (GY, "#14532d")):
        for _ in range(9):
            x = d.rng.uniform(-80, W + 80)
            d.add(path(cloud_d(round(x), round(base - d.rng.uniform(150, 400)), round(d.rng.uniform(120, 220))), col, None))
    for x in (60, 1000):
        d.add(path(f"M{x},0 C{x + 40},400 {x - 40},800 {x + 20},1300", "none", "#365314", 14))
        for y in range(100, 1300, 160):
            d.add(ellipse(x + 30, y, 40, 18, "#4d7c0f", None, transform=f"rotate(30 {x + 30} {y})"))
    ground(d, "#365314")
    vignette(d, 0.45)


S("jungle_day", "nature adventure animals", _jungle)


def _savanna(d: Doc):
    sky(d, "sunset")
    sun(d, 540, 1150, 170, "#fb923c")
    d.add(rect(0, 1250, W, H - 1250, "#78350f", 0, None))
    for x, s in ((180, 1.0), (850, 0.75)):
        d.add(path(f"M{x},{1260} L{x + 10 * s},{1000} ", "none", "#1c1917", 22 * s),
              path(f"M{x - 220 * s},{960} C{x - 100 * s},{900} {x + 100 * s},{900} {x + 240 * s},{960} C{x + 120 * s},{990} {x - 120 * s},{990} {x - 220 * s},{960} Z", "#1c1917", None))
    ground(d, "#92400e", 1260)
    vignette(d, 0.35)


S("savanna_sunset", "nature animals travel", _savanna)


def _snow_village(d: Doc):
    sky(d, "night")
    moon(d, 820, 300, 60)
    hills(d, 1200, "#cbd5e1", 80, 2)
    for x, c in ((60, "#7c2d12"), (380, "#1e3a8a"), (760, "#14532d")):
        d.add(rect(x, 1130, 260, 280, c, 0, None), poly([(x - 30, 1140), (x + 130, 990), (x + 290, 1140)], "#f1f5f9", None),
              rect(x + 40, 1210, 60, 70, "#fde68a", 4, None), rect(x + 160, 1210, 60, 70, "#fde68a", 4, None))
    ground(d, "#f1f5f9", 1400, "#94a3b8")
    for _ in range(60):
        d.add(circle(round(d.rng.uniform(0, W)), round(d.rng.uniform(0, 1500)), round(d.rng.uniform(3, 7)), "#ffffff", None, op=0.8))
    vignette(d, 0.3)


S("snowy_village_night", "holiday weather home", _snow_village, (0.6, 0.78))


def _volcano(d: Doc):
    sky(d, "dusk")
    d.add(poly([(80, GY), (440, 700), (640, 700), (1000, GY)], "#292524", None), poly([(440, 700), (640, 700), (600, 780), (480, 780)], "#f97316", None))
    for i in range(6):
        d.add(path(cloud_d(540 + d.rng.uniform(-100, 100), 600 - i * 80, 90 + i * 12), "#57534e", None, op=0.85))
    d.add(path("M520,780 C500,950 560,1100 520,1300 L560,1300 C600,1100 560,950 580,780 Z", "#f97316", None, op=0.9))
    ground(d, "#1c1917")
    vignette(d, 0.4)


S("volcano_eruption", "nature science danger", _volcano)


def _lake(d: Doc):
    sky(d, "dawn", 1150)
    sun(d, 540, 1100, 90, "#fef3c7")
    mountains(d, 1150, "#a78bfa", 4, 250, 450)
    d.add(rect(0, 1150, W, 350, d.grad([(0, "#c4b5fd"), (1, "#7dd3fc")]), 0, None))
    for y in range(1170, 1480, 40):
        d.add(line(d.rng.uniform(100, 500), y, d.rng.uniform(600, 1000), y, "#ffffff", 3, op=0.4))
    pine_row(d, GY, "#14532d", 6, 300, 520, -60, 260)
    pine_row(d, GY, "#14532d", 5, 300, 520, 860, 1140)
    ground(d, "#166534")
    vignette(d, 0.3)


S("lake_dawn", "nature calm mental_health", _lake)


def _rooftop(d: Doc):
    sky(d, "night")
    moon(d, 860, 320, 50)
    skyline(d, 1300, "#1e293b", 300, 700, "#fde68a", 0.3)
    ground(d, "#334155", 1300, "#111827")
    d.add(rect(0, 1300, W, 40, "#475569", 0, None), rect(820, 1050, 180, 250, "#475569", 0, None), circle(910, 1040, 60, "#64748b", None))
    vignette(d, 0.4)


S("rooftop_night", "city mystery storytelling", _rooftop)


def _highway(d: Doc):
    sky(d, "day")
    sun(d, 840, 260, 70)
    hills(d, 1150, "#65a30d", 60, 2)
    d.add(poly([(470, 1150), (610, 1150), (1080, H), (0, H)], "#334155", None))
    for i in range(6):
        y0 = 1180 + i * 130
        d.add(poly([(538 - 3 - i * 4, y0), (542 + 3 + i * 4, y0), (544 + 6 + i * 6, y0 + 60 + i * 10), (536 - 6 - i * 6, y0 + 60 + i * 10)], "#facc15", None))
    ground(d, "#4d7c0f", 1150)
    d.add(poly([(470, 1150), (610, 1150), (1080, H), (0, H)], "#334155", None))
    for i in range(6):
        y0 = 1180 + i * 130
        d.add(poly([(537 - i * 4, y0), (543 + i * 4, y0), (550 + i * 6, y0 + 60 + i * 10), (530 - i * 6, y0 + 60 + i * 10)], "#facc15", None))
    vignette(d, 0.3)


S("highway_road", "transport travel adventure", _highway, (0.62, 0.86))


def _bridge(d: Doc):
    sky(d, "sunset")
    sun(d, 760, 1000, 110, "#fdba74")
    d.add(rect(0, 1150, W, H - 1150, d.grad([(0, "#7c3aed"), (1, "#1e1b4b")]), 0, None))
    for x in (220, 860):
        d.add(rect(x - 30, 500, 60, 820, "#1e1b4b", 0, None))
    d.add(path("M-20,720 Q540,1150 1100,720", "none", "#1e1b4b", 14), rect(0, 1300, W, 40, "#1e1b4b", 0, None))
    for x in range(260, 840, 50):
        y = 720 + (1 - ((x - 540) / 560) ** 2) * 0 + 430 * (1 - ((x - 540) / 540) ** 2) * 0.55
        d.add(line(x, y, x, 1300, "#1e1b4b", 4))
    ground(d, "#312e81", GY)
    vignette(d, 0.35)


S("bridge_sunset", "city travel transport", _bridge)


def _harbor(d: Doc):
    sky(d, "day", 1200)
    clouds(d, 4, 180, 600)
    d.add(rect(0, 1200, W, 300, "#0369a1", 0, None))
    for x, c in ((80, "#ef4444"), (560, "#2563eb")):
        d.add(path(f"M{x},1180 L{x + 420},1180 L{x + 380},1260 L{x + 40},1260 Z", c, None))
        for i in range(4):
            d.add(rect(x + 60 + i * 80, 1120, 70, 60, ["#f59e0b", "#22c55e", "#3b82f6", "#a855f7"][i], 2, None))
    d.add(rect(880, 700, 26, 500, "#facc15", 0, None), rect(700, 700, 300, 22, "#facc15", 0, None))
    ground(d, "#64748b")
    vignette(d, 0.3)


S("harbor_port", "logistics transport business ocean", _harbor)


def _stadium(d: Doc):
    sky(d, "night", 1000)
    for x in (120, 960):
        d.add(rect(x - 6, 200, 12, 600, "#334155", 0, None), rect(x - 90, 160, 180, 70, "#e2e8f0", 8, None),
              poly([(x - 90, 230), (x + 90, 230), (x + 300 * (1 if x < 500 else -1), 1400), (x - 100 * (1 if x < 500 else -1), 1400)], "#fef9c3", None, op=0.08))
    d.add(rect(0, 800, W, 300, "#1e293b", 0, None))
    for y in range(820, 1080, 40):
        for x in range(0, W, 30):
            d.add(circle(x + d.rng.uniform(0, 20), y + d.rng.uniform(0, 16), 8, d.rng.choice(["#ef4444", "#3b82f6", "#facc15", "#f8fafc", "#22c55e"]), None, op=0.7))
    ground(d, "#15803d", 1100, "#14532d")
    for x in range(0, W, 180):
        d.add(rect(x, 1100, 90, H - 1100, "#16a34a", 0, None, op=0.5))
    d.add(line(0, 1300, W, 1300, "#f8fafc", 8, op=0.8))
    vignette(d, 0.35)


S("stadium_night", "sports entertainment", _stadium, (0.6, 0.8))


def _school_yard(d: Doc):
    sky(d, "day")
    clouds(d, 3, 200, 500)
    d.add(rect(100, 760, 880, 600, "#f87171", 0, None), poly([(60, 780), (540, 560), (1020, 780)], "#7f1d1d", None), rect(470, 620, 140, 140, "#f8fafc", 70, None),
          circle(540, 690, 50, "#f8fafc", "#0f172a", 6), line(540, 690, 540, 655, "#0f172a", 6), line(540, 690, 565, 700, "#0f172a", 5))
    for x in range(160, 960, 160):
        d.add(rect(x, 880, 90, 110, "#bae6fd", 4, None), rect(x, 1080, 90, 110, "#bae6fd", 4, None))
    d.add(rect(480, 1180, 120, 180, "#7c2d12", 4, None), rect(380, 470, 8, 160, "#334155", 0, None), rect(388, 470, 100, 60, "#2563eb", 0, None))
    ground(d, "#a3a3a3", 1360)
    vignette(d, 0.25)


S("school_yard", "education kids", _school_yard)


def _construction(d: Doc):
    sky(d, "day")
    sun(d, 860, 260, 60)
    for i in range(5):
        d.add(rect(80, 600 + i * 150, 600, 10, "#f59e0b", 0, None))
    for x in (80, 380, 680):
        d.add(rect(x, 600, 14, 900, "#f59e0b", 0, None))
    d.add(rect(880, 300, 24, 1200, "#facc15", 0, None), rect(560, 300, 500, 22, "#facc15", 0, None), line(700, 322, 700, 700, "#1e293b", 4),
          rect(670, 700, 60, 50, "#64748b", 0, None))
    ground(d, "#a16207")
    for x in range(0, W, 120):
        d.add(poly([(x, GY), (x + 60, GY), (x + 30, GY - 60)], "#f97316", None, op=0.0))
    vignette(d, 0.3)


S("construction_site", "construction industry", _construction)


def _space(variant):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, d.grad([(0, "#020617"), (1, "#1e1b4b" if variant != "nebula" else "#3b0764")]), 0, None))
        stars(d, 160, 0, H)
        if variant == "nebula":
            for _ in range(6):
                d.add(circle(round(d.rng.uniform(100, 1000)), round(d.rng.uniform(200, 1400)), round(d.rng.uniform(200, 400)),
                             d.rgrad([(0, d.rng.choice(["#a855f7", "#ec4899", "#3b82f6"])), (1, "#000000")], ops=[0.35, 0.0]), None))
        if variant == "planets":
            d.add(circle(200, 400, 120, "#f59e0b", None), ellipse(200, 410, 220, 40, "none", "#fde68a", 12, transform="rotate(-15 200 410)"),
                  circle(900, 900, 70, "#ef4444", None), circle(780, 280, 30, "#94a3b8", None))
        if variant == "orbit":
            d.add(circle(540, 2300, 1100, d.grad([(0, "#2563eb"), (1, "#0c4a6e")]), None), path("M-60,1320 C200,1250 400,1280 600,1240 C760,1210 900,1250 1140,1210", "none", "#22c55e", 40, op=0.6),
                  circle(540, 2300, 1120, "none", "#7dd3fc", 18, op=0.4))
        if variant == "stars":
            d.add(circle(860, 300, 40, "#f8fafc", None, op=0.9))
    return b


S("space_stars", "space science", _space("stars"), (0.6, 0.8))
S("space_planets", "space science education", _space("planets"), (0.6, 0.8))
S("galaxy_nebula", "space science mystery", _space("nebula"), (0.6, 0.8))
S("earth_orbit", "space science environment", _space("orbit"), (0.6, 0.64))


def _surface(kind):
    def b(d: Doc):
        top, bot = ("#020617", "#1e293b") if kind == "moon" else ("#7c2d12", "#fb923c")
        d.add(rect(0, 0, W, 1300, d.grad([(0, top), (1, bot)]), 0, None))
        stars(d, 90 if kind == "moon" else 10, 0, 1000)
        if kind == "moon":
            d.add(circle(820, 380, 120, d.grad([(0, "#2563eb"), (1, "#0f766e")]), None))
        else:
            sun(d, 300, 400, 50, "#fef3c7")
        gcol = "#94a3b8" if kind == "moon" else "#c2410c"
        d.add(path(f"M0,1280 C300,1230 700,1330 1080,1270 L1080,{H} L0,{H} Z", gcol, None))
        for _ in range(9):
            x, y, r = d.rng.uniform(0, W), d.rng.uniform(1350, 1850), d.rng.uniform(30, 90)
            d.add(ellipse(round(x), round(y), round(r), round(r * 0.3), darken(gcol, 0.75), None))
        if kind == "mars":
            d.add(poly([(700, 1290), (880, 1100), (1080, 1280)], "#9a3412", None))
    return b


S("moon_surface", "space science adventure", _surface("moon"))
S("mars_surface", "space science adventure", _surface("mars"))


def _underwater(deep):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, d.grad([(0, "#0e7490" if not deep else "#082f49"), (1, "#083344" if not deep else "#020617")]), 0, None))
        for i in range(6):
            d.add(poly([(100 + i * 180, 0), (180 + i * 180, 0), (60 + i * 190, 1400), (20 + i * 190, 1400)], "#a5f3fc", None, op=0.06 if not deep else 0.03))
        for _ in range(30):
            d.add(circle(round(d.rng.uniform(0, W)), round(d.rng.uniform(100, 1400)), round(d.rng.uniform(4, 14)), "none", "#e0f2fe", 3, op=0.5))
        if not deep:
            for x, c in ((80, "#f472b6"), (200, "#fb923c"), (900, "#a78bfa"), (1000, "#f472b6")):
                for k in range(4):
                    d.add(ellipse(x + k * 20 - 30, GY - 80 - k * 50, 24, 90, c, None, op=0.85, transform=f"rotate({k * 15 - 20} {x} {GY})"))
        else:
            for _ in range(10):
                d.add(circle(round(d.rng.uniform(0, W)), round(d.rng.uniform(300, 1400)), 5, "#67e8f9", None, op=0.8))
        ground(d, "#fde68a" if not deep else "#1e293b")
    return b


S("underwater_reef", "ocean nature animals", _underwater(False))
S("deep_sea", "ocean mystery science", _underwater(True))


def _cave(d: Doc):
    d.add(rect(0, 0, W, H, "#1c1917", 0, None))
    d.add(path("M0,0 L1080,0 L1080,500 C900,700 800,350 600,520 C450,650 300,400 0,600 Z", "#0c0a09", None))
    for x in range(40, W, 120):
        d.add(poly([(x, 0), (x + 40, 0), (x + 20, d.rng.uniform(150, 380))], "#292524", None))
    d.add(circle(540, 1100, 600, d.rgrad([(0, "#f59e0b"), (1, "#000000")], ops=[0.25, 0.0]), None))
    ground(d, "#292524")
    vignette(d, 0.55)


S("cave_dark", "adventure mystery history", _cave)


def _rainy_night(d: Doc):
    sky(d, "storm")
    skyline(d, 1200, "#0f172a", 300, 650, "#fde68a", 0.25)
    ground(d, "#111827")
    lamp_post(d, 160, GY, True)
    for _ in range(140):
        x, y = d.rng.uniform(0, W), d.rng.uniform(0, H)
        d.add(line(round(x), round(y), round(x - 10), round(y + 40), "#93c5fd", 2, op=0.35))
    for x in (160, 700):
        d.add(ellipse(x, GY + 120, 140, 18, "#fde68a", None, op=0.15))
    vignette(d, 0.45)


S("rainy_street_night", "city mystery weather sad", _rainy_night)


def _stormy_sea(d: Doc):
    sky(d, "storm", 1150)
    d.add(poly(bolt_pts(300, 500, 180), "#fef08a", None, op=0.9))
    d.add(rect(0, 1150, W, H - 1150, d.grad([(0, "#1e3a8a"), (1, "#020617")]), 0, None))
    for y in range(1150, H, 90):
        d.add(path(f"M0,{y} " + " ".join(f"Q{x + 60},{y - 50} {x + 120},{y}" for x in range(0, W, 120)), "none", "#e0f2fe", 6, op=0.3))
    vignette(d, 0.5)


S("stormy_sea", "ocean weather danger adventure", _stormy_sea)


def _pyramids(d: Doc):
    sky(d, "noon")
    sun(d, 860, 260, 80, "#fef9c3")
    for x, s, c in ((80, 1.0, "#d6a76c"), (560, 0.7, "#c08a4a")):
        d.add(poly([(x, 1300), (x + 320 * s, 1300 - 420 * s), (x + 640 * s, 1300)], c, None), poly([(x + 320 * s, 1300 - 420 * s), (x + 640 * s, 1300), (x + 380 * s, 1300)], darken(c, 0.85), None))
    ground(d, "#fcd34d", 1300)
    vignette(d, 0.25)


S("pyramids_desert", "history travel archaeology", _pyramids, (0.6, 0.8))


def _colosseum(d: Doc):
    sky(d, "day")
    d.add(path("M60,1300 L60,700 C300,620 780,620 1020,700 L1020,1300 Z", "#d6a76c", None))
    for r in range(3):
        for i in range(8):
            d.add(rect(100 + i * 115, 760 + r * 170, 70, 120, "#78350f", 34, None, op=0.8))
    d.add(poly([(820, 650), (1020, 700), (1020, 1000), (900, 900)], "#bae6fd", None))
    ground(d, "#e7c18a", 1300)
    vignette(d, 0.25)


S("colosseum_ruins", "history travel", _colosseum, (0.6, 0.8))


def _castle(d: Doc):
    sky(d, "dusk")
    moon(d, 820, 280, 50)
    hills(d, 1300, "#1e1b4b", 160, 1)
    d.add(rect(300, 650, 480, 500, "#334155", 0, None))
    for x in (250, 730):
        d.add(rect(x, 520, 100, 630, "#475569", 0, None), poly([(x - 10, 530), (x + 50, 400), (x + 110, 530)], "#7f1d1d", None))
    for x in range(300, 780, 60):
        d.add(rect(x, 620, 36, 40, "#334155", 0, None))
    d.add(path("M480,1150 L480,1000 C480,940 600,940 600,1000 L600,1150 Z", "#1e293b", None))
    for x, y in ((360, 800), (680, 800), (520, 760)):
        d.add(rect(x, y, 36, 60, "#fde68a", 18, None))
    ground(d, "#1e1b4b", 1300)
    vignette(d, 0.4)


S("castle_hill", "history storytelling magic", _castle, (0.6, 0.8))


def _greek(d: Doc):
    sky(d, "day")
    d.add(poly([(140, 700), (540, 520), (940, 700)], "#e7e5e4", None), rect(140, 700, 800, 50, "#d6d3d1", 0, None))
    for x in range(170, 940, 110):
        d.add(rect(x, 750, 60, 520, "#f5f5f4", 0, None), line(x + 20, 760, x + 20, 1260, "#d6d3d1", 4), line(x + 40, 760, x + 40, 1260, "#d6d3d1", 4))
    d.add(rect(110, 1270, 860, 40, "#d6d3d1", 0, None))
    ground(d, "#a8a29e", 1310)
    vignette(d, 0.25)


S("greek_temple", "history education", _greek, (0.6, 0.8))


def _wild_west(d: Doc):
    sky(d, "sunset")
    sun(d, 540, 1000, 120, "#fdba74")
    for x, w, h in ((-20, 300, 600), (310, 260, 520), (760, 340, 640)):
        d.add(rect(x, GY - h, w, h, "#78350f", 0, None), rect(x, GY - h - 60, w, 60, "#451a03", 0, None), rect(x + 30, GY - h + 80, w - 60, 40, "#fde68a", 0, None, op=0.3))
    ground(d, "#c2410c")
    vignette(d, 0.35)


S("wild_west_town", "history storytelling adventure", _wild_west)


def _prehistoric(d: Doc):
    sky(d, "dawn")
    d.add(poly([(600, 1250), (800, 700), (1000, 1250)], "#57534e", None))
    for x in (60, 240, 900):
        d.add(path(f"M{x},{GY} L{x + 10},{GY - 500}", "none", "#365314", 20))
        for a in range(-60, 70, 30):
            d.add(ellipse(x + 10, GY - 500, 150, 22, "#4d7c0f", None, transform=f"rotate({a} {x + 10} {GY - 500}) translate(90 0)"))
    ground(d, "#4d7c0f")
    vignette(d, 0.3)


S("prehistoric_jungle", "history science animals kids", _prehistoric)


def _medieval(d: Doc):
    sky(d, "day")
    hills(d, 1250, "#4d7c0f", 100, 2)
    for x, c in ((40, "#d6a76c"), (380, "#e7c18a"), (720, "#d6a76c")):
        d.add(rect(x, 1050, 300, 300, c, 0, None), poly([(x - 20, 1060), (x + 150, 920), (x + 320, 1060)], "#78350f", None))
        for i in range(3):
            d.add(line(x, 1100 + i * 80, x + 300, 1100 + i * 80, "#78350f", 6))
    ground(d, "#a16207", 1350)
    vignette(d, 0.3)


S("medieval_village", "history storytelling", _medieval, (0.6, 0.8))


def _airport(d: Doc):
    sky(d, "day")
    clouds(d, 3, 200, 500)
    d.add(path("M200,500 L300,520 L600,470 L640,480 L560,520 L800,560 L760,580 L520,550 L460,610 L420,600 L470,545 L300,560 Z", "#f8fafc", None))
    ground(d, "#475569", 1250)
    for x in range(0, W, 220):
        d.add(rect(x, 1500, 120, 18, "#f8fafc", 0, None))
    d.add(rect(0, 1250, W, 30, "#facc15", 0, None, op=0.5))
    vignette(d, 0.25)


S("airport_runway", "travel transport", _airport)


def _train_platform(d: Doc):
    room(d, "#334155", "#9ca3af", 1300, planks=False, tiles=True)
    d.add(rect(0, 500, W, 520, "#b91c1c", 30, None))
    for x in range(40, W, 200):
        d.add(rect(x, 560, 150, 160, "#bae6fd", 10, None))
    d.add(rect(0, 1240, W, 30, "#facc15", 0, None), rect(380, 180, 320, 90, "#0f172a", 10, None), text(540, 245, "PLATFORM 3", 46, "#facc15"))
    vignette(d, 0.35)


S("train_platform", "travel transport city", _train_platform)


def _bus_stop(d: Doc):
    sky(d, "overcast")
    skyline(d, 1250, "#64748b", 300, 600, None)
    ground(d, "#6b7280")
    d.add(rect(60, 900, 20, 600, "#334155", 0, None), rect(60, 880, 360, 30, "#334155", 0, None), rect(80, 910, 320, 360, "#bae6fd", 0, None, op=0.3),
          rect(100, 1380, 280, 20, "#1e293b", 0, None))
    vignette(d, 0.3)


S("bus_stop", "city transport", _bus_stop)


def _campsite(d: Doc):
    sky(d, "night")
    moon(d, 800, 300, 60)
    pine_row(d, 1300, "#052e16", 18, 400, 700)
    ground(d, "#14532d", 1300)
    d.add(poly([(80, 1450), (260, 1150), (440, 1450)], "#f97316", None), poly([(200, 1450), (260, 1250), (320, 1450)], "#7c2d12", None))
    d.add(circle(760, 1420, 220, d.rgrad([(0, "#f97316"), (1, "#f97316")], ops=[0.4, 0.0]), None))
    vignette(d, 0.5)


S("campsite_night", "adventure nature storytelling", _campsite)


def _garden(d: Doc):
    sky(d, "day")
    sun(d, 860, 260, 60)
    for i in range(12):
        d.add(rect(i * 92, 1120, 70, 380, "#fef3c7", 6, None))
    d.add(rect(0, 1180, W, 18, "#fef3c7", 0, None), rect(0, 1340, W, 18, "#fef3c7", 0, None))
    for x in (90, 200, 880, 990):
        d.add(circle(x, 1430, 50, "#16a34a", None), circle(x, 1400, 18, d.rng.choice(["#f43f5e", "#facc15", "#a855f7"]), None))
    ground(d, "#65a30d")
    vignette(d, 0.25)


S("garden_backyard", "home nature family", _garden)


def _blossom(d: Doc):
    sky(d, "dawn")
    for x in (120, 950):
        d.add(path(f"M{x},{GY} C{x + 20},1200 {x - 40},900 {x + 30},700", "none", "#44403c", 30))
        for _ in range(14):
            d.add(circle(round(x + d.rng.uniform(-200, 200)), round(d.rng.uniform(500, 900)), round(d.rng.uniform(60, 110)), "#fbcfe8", None, op=0.9))
    for _ in range(40):
        d.add(ellipse(round(d.rng.uniform(0, W)), round(d.rng.uniform(300, 1500)), 8, 5, "#f9a8d4", None, op=0.8))
    ground(d, "#86efac")
    vignette(d, 0.2)


S("cherry_blossom_park", "nature love calm", _blossom)


def _waterfall(d: Doc):
    sky(d, "day")
    d.add(poly([(0, 300), (400, 400), (420, GY), (0, GY)], "#57534e", None), poly([(1080, 300), (700, 400), (680, GY), (1080, GY)], "#57534e", None))
    d.add(rect(420, 400, 260, 1100, d.grad([(0, "#bae6fd"), (1, "#38bdf8")]), 0, None))
    for x in range(430, 680, 40):
        d.add(line(x, 400, x, 1480, "#f0f9ff", 6, op=0.5))
    d.add(ellipse(550, GY, 300, 60, "#f0f9ff", None, op=0.6))
    ground(d, "#166534")
    vignette(d, 0.3)


S("waterfall_cliff", "nature travel adventure", _waterfall, (0.75, 0.78))


def _graveyard(d: Doc):
    sky(d, "night")
    moon(d, 760, 320, 90)
    hills(d, 1300, "#1e1b4b", 120, 1)
    for x, h in ((120, 200), (330, 160), (780, 220), (960, 170)):
        d.add(path(f"M{x - 60},{GY} L{x - 60},{GY - h + 60} C{x - 60},{GY - h - 10} {x + 60},{GY - h - 10} {x + 60},{GY - h + 60} L{x + 60},{GY} Z", "#475569", None))
    d.add(path("M600,900 C620,1000 560,1100 600,1300", "none", "#0f172a", 24), path("M600,1000 L700,920 M600,1060 L520,980", "none", "#0f172a", 14))
    ground(d, "#1e1b4b")
    for _ in range(5):
        d.add(ellipse(round(d.rng.uniform(0, W)), round(d.rng.uniform(1350, 1500)), 260, 40, "#cbd5e1", None, op=0.12))
    vignette(d, 0.45)


S("graveyard_spooky", "spooky holiday mystery", _graveyard)


def _haunted(d: Doc):
    sky(d, "dusk")
    moon(d, 820, 280, 80)
    d.add(rect(220, 700, 640, 800, "#1e1b4b", 0, None), poly([(180, 720), (540, 420), (900, 720)], "#0f0a2e", None), rect(680, 480, 80, 220, "#1e1b4b", 0, None))
    for x, y in ((290, 820), (690, 820), (290, 1080), (690, 1080)):
        d.add(rect(x, y, 100, 140, "#fde047", 4, None, op=0.75))
    d.add(path("M480,1500 L480,1300 C480,1240 600,1240 600,1300 L600,1500 Z", "#0f0a2e", None))
    ground(d, "#0f0a2e")
    vignette(d, 0.5)


S("haunted_house", "spooky holiday mystery storytelling", _haunted)


def _festival(d: Doc):
    sky(d, "night")
    for row in range(3):
        y0 = 300 + row * 220
        d.add(path(f"M-20,{y0} Q540,{y0 + 140} 1100,{y0}", "none", "#334155", 4))
        for i in range(9):
            x = 40 + i * 125
            y = y0 + 140 * (1 - ((x - 540) / 560) ** 2) * 0.6 + 30
            d.add(ellipse(x, y, 34, 44, d.rng.choice(["#ef4444", "#f97316", "#facc15"]), None), circle(x, y, 70, d.rgrad([(0, "#fdba74"), (1, "#fdba74")], ops=[0.35, 0.0]), None))
    ground(d, "#1e1b4b")
    vignette(d, 0.35)


S("festival_lanterns", "holiday celebration culture", _festival)


def _track(d: Doc):
    sky(d, "day")
    d.add(rect(0, 900, W, 300, "#1e293b", 0, None))
    for y in range(920, 1180, 40):
        for x in range(0, W, 26):
            d.add(circle(x + d.rng.uniform(0, 10), y + d.rng.uniform(0, 10), 7, d.rng.choice(["#ef4444", "#3b82f6", "#facc15", "#f8fafc"]), None, op=0.6))
    ground(d, "#b45309", 1200, "#7c2d12")
    for y in (1280, 1400, 1520, 1640):
        d.add(line(0, y, W, y, "#f8fafc", 6, op=0.8))
    for i in range(10):
        d.add(rect(i * 108, 1460, 54, 40, "#f8fafc" if i % 2 else "#0f172a", 0, None))
    vignette(d, 0.25)


S("running_track", "sports fitness winner", _track)


def _countryside(d: Doc):
    sky(d, "day")
    clouds(d, 5, 150, 600)
    hills(d, 1150, "#84cc16", 120, 2)
    hills(d, 1300, "#65a30d", 80, 3)
    d.add(path(f"M480,1150 C500,1250 380,1350 300,{H} L780,{H} C700,1350 580,1250 560,1150 Z", "#d6d3d1", None))
    round_tree(d, 160, 1250, 260, "#15803d")
    round_tree(d, 920, 1300, 300, "#16a34a")
    ground(d, "#4d7c0f", 1600)
    vignette(d, 0.2)


S("countryside_road", "nature travel agriculture", _countryside)


def _arctic(d: Doc):
    sky(d, "day")
    d.add(path("M0,800 C200,780 400,820 600,760 C800,720 1000,800 1080,780 L1080,1100 L0,1100 Z", "#22c55e", None, op=0.0))
    for x, w, h in ((60, 300, 400), (700, 360, 300)):
        d.add(poly([(x, 1200), (x + w * 0.3, 1200 - h), (x + w * 0.7, 1200 - h * 0.8), (x + w, 1200)], "#e0f2fe", None))
    d.add(rect(0, 1200, W, 300, "#0ea5e9", 0, None))
    ground(d, "#f8fafc", 1350, "#bae6fd")
    vignette(d, 0.2)


S("arctic_ice", "nature weather environment animals", _arctic)


def _canyon(d: Doc):
    sky(d, "noon")
    for i, (c, y) in enumerate((("#c2410c", 800), ("#9a3412", 1000), ("#7c2d12", 1200))):
        d.add(path(f"M0,{y} L200,{y - 60} L320,{y - 60} L380,{y + 20} L700,{y + 10} L760,{y - 80} L1080,{y - 70} L1080,{H} L0,{H} Z", c, None))
    ground(d, "#ea580c", GY, "#9a3412")
    vignette(d, 0.3)


S("canyon_red_rocks", "nature travel adventure", _canyon)


def _island(d: Doc):
    sky(d, "day", 1200)
    sun(d, 840, 260, 80)
    d.add(rect(0, 1200, W, H - 1200, d.grad([(0, "#06b6d4"), (1, "#0e7490")]), 0, None))
    d.add(ellipse(540, 1420, 520, 120, "#fde68a", None))
    for x in (300, 780):
        d.add(path(f"M{x},1400 C{x + 10},1250 {x - 10},1100 {x + 30},950", "none", "#78350f", 20))
        for a in (-50, -10, 30, 70, 110):
            d.add(ellipse(x + 30, 950, 120, 22, "#16a34a", None, transform=f"rotate({a} {x + 30} 950) translate(80 0)"))
    vignette(d, 0.2)


S("tropical_island", "travel ocean nature", _island, (0.55, 0.76))


# =========================================================================== INDOOR
def _bedroom(night):
    def b(d: Doc):
        room(d, "#4c1d95" if night else "#6d28d9", "#78350f")
        window_frame(d, 620, 300, 360, 420, "night" if night else "day")
        d.add(rect(40, 1150, 500, 200, "#1d4ed8", 20, None), rect(30, 1020, 40, 340, "#78350f", 6, None), rect(80, 1110, 160, 70, "#f8fafc", 30, None),
              rect(200, 1140, 340, 210, "#3b82f6", 10, None))
        frame_art(d, 120, 420, 240, 180, "#fbbf24")
        if night:
            d.add(rect(0, 0, W, H, "#020617", 0, None, op=0.35), circle(800, 510, 260, d.rgrad([(0, "#bfdbfe"), (1, "#bfdbfe")], ops=[0.18, 0.0]), None))
        vignette(d, 0.35)
    return b


S("bedroom_day", "home sleep family", _bedroom(False))
S("bedroom_night", "home sleep mental_health", _bedroom(True))


def _living(night):
    def b(d: Doc):
        room(d, "#0f766e" if not night else "#134e4a", "#a16207")
        window_frame(d, 80, 300, 320, 400, "night" if night else "day")
        d.add(rect(560, 1120, 480, 160, "#f97316", 30, None), rect(560, 1040, 480, 120, "#ea580c", 30, None), rect(540, 1120, 60, 200, "#ea580c", 20, None),
              rect(1000, 1120, 60, 200, "#ea580c", 20, None))
        frame_art(d, 640, 420, 340, 240, "#38bdf8")
        plant(d, 470, 1330, 0.9)
        if night:
            d.add(rect(0, 0, W, H, "#020617", 0, None, op=0.35), circle(240, 900, 200, d.rgrad([(0, "#fde68a"), (1, "#fde68a")], ops=[0.25, 0.0]), None))
        vignette(d, 0.3)
    return b


S("living_room_day", "home family", _living(False))
S("living_room_night", "home family relaxation", _living(True))


def _kitchen(d: Doc):
    room(d, "#fef3c7", "#d6d3d1", 1330, planks=False, tiles=True)
    d.add(rect(0, 1000, 1080, 340, "#e7e5e4", 0, None), rect(0, 980, 1080, 30, "#78716c", 0, None))
    for x in range(20, W, 270):
        d.add(rect(x, 1030, 240, 290, "#fafaf9", 8, "#a8a29e", 4), circle(x + 210, 1170, 8, "#78716c", None))
    for x in range(20, W, 270):
        d.add(rect(x, 260, 240, 300, "#fafaf9", 8, "#a8a29e", 4))
    d.add(rect(700, 860, 160, 120, "#ef4444", 20, None), rect(680, 840, 200, 30, "#b91c1c", 8, None))
    vignette(d, 0.25)


S("kitchen_home", "food cooking home family", _kitchen)


def _home_office(d: Doc):
    room(d, "#1e3a8a", "#78350f")
    window_frame(d, 640, 280, 340, 400, "day")
    desk(d, 40, 1080, 480)
    shelf(d, 40, 300, 360, 2)
    plant(d, 960, 1330, 0.8)
    vignette(d, 0.3)


S("home_office", "office productivity remote_work tech", _home_office)


def _open_office(d: Doc):
    room(d, "#e2e8f0", "#94a3b8", 1300, planks=False, tiles=True)
    for x in range(-40, W, 360):
        d.add(rect(x + 20, 200, 300, 500, "#bae6fd", 8, "#94a3b8", 10))
    desk(d, -60, 1080, 420, "#cbd5e1", True, "#22d3ee")
    desk(d, 700, 1080, 420, "#cbd5e1", True, "#a78bfa")
    plant(d, 560, 1300, 0.7)
    vignette(d, 0.2)


S("office_open_plan", "office business career", _open_office)


def _cubicle(d: Doc):
    room(d, "#64748b", "#475569", 1300, planks=False)
    d.add(rect(0, 860, 420, 440, "#94a3b8", 6, None), rect(700, 860, 380, 440, "#94a3b8", 6, None))
    desk(d, 0, 1080, 380, "#cbd5e1", True, "#0ea5e9")
    d.add(rect(60, 900, 80, 60, "#fde047", 2, None), rect(160, 920, 70, 60, "#f9a8d4", 2, None))
    d.add(rect(300, 120, 480, 30, "#f8fafc", 0, None, op=0.8), rect(300, 220, 480, 30, "#f8fafc", 0, None, op=0.8))
    vignette(d, 0.35)


S("office_cubicle", "office productivity career", _cubicle)


def _boardroom(d: Doc):
    room(d, "#1e293b", "#334155", 1300, planks=False)
    d.add(rect(160, 260, 760, 440, "#0b1220", 12, "#475569", 12))
    for i, h in enumerate((120, 200, 160, 280, 340)):
        d.add(rect(240 + i * 130, 640 - h, 80, h, ["#38bdf8", "#22d3ee", "#a78bfa", "#f472b6", "#22c55e"][i], 4, None))
    d.add(path("M60,1300 L1020,1300 L900,1180 L180,1180 Z", "#78350f", None))
    for x in (230, 400, 680, 850):
        d.add(rect(x, 1080, 60, 100, "#0f172a", 12, None))
    vignette(d, 0.35)


S("boardroom_meeting", "business management office", _boardroom)


def _garage(d: Doc):
    room(d, "#57534e", "#44403c", 1300, planks=False)
    d.add(rect(60, 200, 960, 600, "#78716c", 6, None))
    for y in range(240, 800, 70):
        d.add(line(60, y, 1020, y, "#57534e", 8))
    desk(d, 40, 1080, 460, "#a16207", True, "#22c55e")
    d.add(rect(700, 900, 300, 400, "#ef4444", 10, None), rect(720, 920, 260, 60, "#b91c1c", 4, None))
    vignette(d, 0.4)


S("startup_garage", "startup business tech", _garage)


def _classroom(d: Doc):
    room(d, "#fde68a", "#a16207")
    d.add(rect(100, 260, 880, 480, "#14532d", 10, "#78350f", 18), text(540, 470, "2 + 2 = 4", 90, "#f8fafc", family="DejaVu Sans Mono"),
          path("M200,600 C320,560 420,640 540,590", "none", "#f8fafc", 6, op=0.7))
    wall_clock(d, 900, 160, 55)
    for x in (40, 780):
        d.add(rect(x, 1150, 260, 30, "#92400e", 4, None), rect(x + 20, 1180, 20, 150, "#451a03", 0, None), rect(x + 220, 1180, 20, 150, "#451a03", 0, None))
    vignette(d, 0.25)


S("classroom", "education kids", _classroom)


def _lecture(d: Doc):
    room(d, "#312e81", "#1e1b4b", 1250, planks=False)
    d.add(rect(80, 180, 920, 520, "#e2e8f0", 8, None), rect(110, 210, 860, 460, "#0f172a", 4, None))
    for i in range(5):
        d.add(rect(160 + i * 160, 600 - 50 * i, 100, 50 * i + 20, "#38bdf8", 4, None))
    for row in range(3):
        y = 1300 + row * 160
        d.add(rect(0, y, W, 30, "#4338ca", 0, None))
    vignette(d, 0.4)


S("lecture_hall", "education business", _lecture, (0.6, 0.66))


def _library(d: Doc):
    room(d, "#451a03", "#78350f")
    shelf(d, 0, 140, 380, 6)
    shelf(d, 700, 140, 380, 6)
    d.add(rect(420, 300, 240, 400, "#fde68a", 120, None, op=0.25))
    vignette(d, 0.4)


S("library_books", "education history storytelling", _library)


def _lab(d: Doc):
    room(d, "#e0f2fe", "#cbd5e1", 1300, planks=False, tiles=True)
    d.add(rect(0, 1000, W, 40, "#334155", 0, None), rect(0, 1040, W, 260, "#64748b", 0, None))
    for x, c in ((60, "#22c55e"), (160, "#3b82f6"), (850, "#a855f7"), (950, "#f97316")):
        d.add(rect(x, 860, 50, 140, "#e0f2fe", 20, "#94a3b8", 5), rect(x + 6, 930, 38, 66, c, 16, None))
    d.add(rect(300, 220, 480, 300, "#0b1220", 10, "#475569", 10), path("M330,450 C400,300 460,500 540,360 C600,260 680,420 750,300", "none", "#22d3ee", 8))
    d.add(rect(820, 300, 200, 400, "#f8fafc", 8, "#94a3b8", 6))
    vignette(d, 0.25)


S("science_lab", "science chemistry biology health", _lab)


def _hospital(d: Doc):
    room(d, "#ccfbf1", "#e2e8f0", 1300, planks=False, tiles=True)
    d.add(rect(40, 1050, 520, 120, "#f8fafc", 20, "#94a3b8", 6), rect(40, 940, 40, 360, "#94a3b8", 6, None), rect(80, 1000, 160, 60, "#bfdbfe", 30, None),
          rect(200, 1060, 360, 100, "#60a5fa", 10, None))
    d.add(rect(800, 600, 16, 700, "#94a3b8", 0, None), rect(760, 600, 100, 140, "#e0f2fe", 20, "#94a3b8", 5))
    d.add(rect(640, 260, 300, 200, "#0b1220", 10, "#64748b", 8), pline([(660, 360), (720, 360), (745, 300), (775, 420), (800, 360), (920, 360)], "#22c55e", 6))
    d.add(rect(120, 300, 140, 140, "#ef4444", 14, None), rect(170, 320, 40, 100, "#f8fafc", 0, None), rect(140, 350, 100, 40, "#f8fafc", 0, None))
    vignette(d, 0.2)


S("hospital_room", "health medical", _hospital)


def _operating(d: Doc):
    room(d, "#134e4a", "#0f766e", 1300, planks=False, tiles=True)
    d.add(ellipse(540, 240, 260, 90, "#e2e8f0", None), circle(540, 240, 600, d.rgrad([(0, "#f0fdfa"), (1, "#f0fdfa")], ops=[0.3, 0.0]), None))
    d.add(rect(80, 1150, 920, 80, "#e2e8f0", 10, None), rect(500, 1230, 80, 120, "#64748b", 0, None))
    d.add(rect(820, 600, 200, 300, "#0b1220", 10, "#475569", 6), pline([(840, 750), (880, 750), (900, 700), (920, 800), (940, 750), (1000, 750)], "#22c55e", 6))
    vignette(d, 0.35)


S("operating_room", "health medical", _operating)


def _pharmacy(d: Doc):
    room(d, "#f0fdf4", "#d1d5db", 1300, planks=False, tiles=True)
    for x in (0, 720):
        for r in range(5):
            d.add(rect(x, 200 + r * 170, 360, 14, "#94a3b8", 0, None))
            for i in range(6):
                d.add(rect(x + 20 + i * 56, 200 + r * 170 - 70, 40, 70, d.rng.choice(["#f97316", "#3b82f6", "#22c55e", "#f8fafc", "#ef4444"]), 6, None))
    d.add(rect(380, 1000, 320, 300, "#22c55e", 10, None), rect(500, 1050, 80, 200, "#f8fafc", 0, None), rect(440, 1110, 200, 80, "#f8fafc", 0, None))
    vignette(d, 0.2)


S("pharmacy_store", "health medicine shopping", _pharmacy)


def _server(d: Doc):
    room(d, "#0b1220", "#1e293b", 1300, planks=False, tiles=True)
    for x in (0, 230, 620, 850):
        d.add(rect(x + 10, 200, 210, 1100, "#111827", 8, "#334155", 6))
        for y in range(240, 1260, 60):
            d.add(rect(x + 30, y, 170, 40, "#1f2937", 4, None), circle(x + 50, y + 20, 6, d.rng.choice(["#22c55e", "#22c55e", "#3b82f6", "#ef4444"]), None))
    d.add(rect(0, 0, W, H, d.grad([(0, "#22d3ee"), (1, "#000000")]), 0, None, op=0.08))
    vignette(d, 0.45)


S("server_room", "tech data infrastructure security", _server)


def _trading(d: Doc):
    room(d, "#0b1220", "#111827", 1300, planks=False)
    for i, (x, y) in enumerate(((60, 260), (400, 200), (740, 260), (60, 640), (740, 640))):
        chart_screen(d, x, y, 290, 220 if i < 3 else 200, i % 3 != 1, candles=i % 2 == 0)
    d.add(rect(0, 1080, W, 40, "#1f2937", 0, None))
    d.add(rect(0, 0, W, H, d.rgrad([(0, "#22c55e"), (1, "#000000")], ops=[0.08, 0.0]), 0, None))
    vignette(d, 0.4)


S("trading_floor", "finance trading investing crypto", _trading)


def _crypto_desk(d: Doc):
    room(d, "#1e1b4b", "#0f0a2e", 1300, planks=False)
    for x in range(0, W, 120):
        d.add(line(x, 0, x, 1300, "#a855f7", 2, op=0.15))
    chart_screen(d, 80, 260, 420, 300, True, True)
    chart_screen(d, 580, 260, 420, 300, False, True)
    d.add(rect(80, 1060, 920, 36, "#4c1d95", 6, None))
    d.add(circle(200, 760, 70, "#f59e0b", None), btc_glyph(200, 760, 80, "#f8fafc", None))
    d.add(circle(880, 760, 70, "#6366f1", None), text(880, 790, "◆", 80, "#f8fafc"))
    vignette(d, 0.45)


S("crypto_desk", "crypto finance trading web3", _crypto_desk)


def _bank_lobby(d: Doc):
    room(d, "#e7e5e4", "#a8a29e", 1300, planks=False, tiles=True)
    for x in range(90, W, 230):
        d.add(rect(x, 200, 80, 1100, "#f5f5f4", 0, "#d6d3d1", 6))
    d.add(rect(0, 1000, W, 300, "#78350f", 0, None), rect(0, 980, W, 30, "#451a03", 0, None), text(540, 160, "BANK", 90, "#a16207"))
    vignette(d, 0.25)


S("bank_lobby", "finance banking business", _bank_lobby)


def _vault(d: Doc):
    room(d, "#334155", "#1e293b", 1300, planks=False)
    d.add(circle(540, 700, 420, "#94a3b8", "#475569", 30), circle(540, 700, 330, "#cbd5e1", None), circle(540, 700, 90, "#64748b", None))
    for a in range(0, 360, 60):
        d.add(line(540, 700, 540 + 250 * math.cos(math.radians(a)), 700 + 250 * math.sin(math.radians(a)), "#64748b", 26))
    for x in (40, 860):
        for y in (1150, 1210, 1270):
            d.add(poly([(x, y + 40), (x + 30, y), (x + 150, y), (x + 180, y + 40)], "#fbbf24", None))
    vignette(d, 0.45)


S("bank_vault", "finance security", _vault, (0.62, 0.8))


def _courtroom(d: Doc):
    room(d, "#78350f", "#451a03")
    d.add(rect(240, 700, 600, 400, "#92400e", 8, None), rect(200, 680, 680, 40, "#451a03", 0, None), rect(400, 220, 280, 280, "#d6a76c", 140, None))
    d.add(path("M540,260 L540,460 M440,300 L640,300", "none", "#78350f", 10), path("M430,300 L410,380 L470,380 Z M650,300 L630,380 L690,380 Z", "#78350f", None))
    for x in range(0, W, 120):
        d.add(rect(x, 1150, 20, 180, "#451a03", 0, None))
    d.add(rect(0, 1140, W, 26, "#451a03", 0, None))
    vignette(d, 0.4)


S("courtroom", "law", _courtroom)


def _newsroom(d: Doc):
    room(d, "#0c4a6e", "#082f49", 1300, planks=False)
    d.add(rect(60, 180, 960, 540, "#0ea5e9", 10, None), path(cloud_d(300, 400, 80), "#e0f2fe", None, op=0.6),
          rect(60, 620, 960, 100, "#b91c1c", 0, None), text(540, 690, "BREAKING NEWS", 64, "#f8fafc"))
    d.add(path("M140,1300 L940,1300 L860,1100 L220,1100 Z", "#1e293b", None))
    vignette(d, 0.35)


S("newsroom_tv", "media communication storytelling", _newsroom)


def _podcast(d: Doc):
    room(d, "#3b0764", "#1e1b4b", 1300, planks=False)
    for x in range(0, W, 90):
        for y in range(120, 900, 90):
            d.add(poly([(x, y), (x + 45, y - 30), (x + 90, y), (x + 45, y + 30)], "#4c1d95" if (x + y) % 180 else "#581c87", None))
    d.add(rect(300, 140, 480, 120, "#ef4444", 20, None), text(540, 225, "ON AIR", 70, "#f8fafc"))
    d.add(rect(0, 1100, W, 40, "#7c3aed", 0, None))
    vignette(d, 0.45)


S("podcast_studio", "media podcast communication music", _podcast)


def _stage(kind):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, "#0b0b12", 0, None))
        if kind == "concert":
            for x, c in ((180, "#a855f7"), (540, "#22d3ee"), (900, "#f472b6")):
                d.add(poly([(x - 30, 0), (x + 30, 0), (x + 260, 1400), (x - 260, 1400)], c, None, op=0.14))
            for y in range(1550, H, 50):
                for x in range(0, W, 40):
                    d.add(circle(x + d.rng.uniform(0, 30), y + d.rng.uniform(0, 30), 22, "#111827", None))
        else:
            d.add(path("M0,0 L300,0 C260,500 200,1000 120,1400 L0,1400 Z", "#7f1d1d", None), path("M1080,0 L780,0 C820,500 880,1000 960,1400 L1080,1400 Z", "#7f1d1d", None),
                  rect(0, 0, W, 120, "#991b1b", 0, None), poly([(500, 120), (580, 120), (780, 1400), (300, 1400)], "#fef9c3", None, op=0.12))
        d.add(rect(0, 1400, W, 130, "#3f3f46" if kind == "concert" else "#78350f", 0, None))
        vignette(d, 0.4)
    return b


S("concert_stage", "music entertainment celebration", _stage("concert"), (0.55, 0.74))
S("theater_stage", "art entertainment storytelling", _stage("theater"), (0.55, 0.74))


def _cinema(d: Doc):
    d.add(rect(0, 0, W, H, "#0f0a0a", 0, None), rect(80, 160, 920, 520, "#e5e7eb", 6, None, op=0.92), circle(540, 420, 500, d.rgrad([(0, "#f8fafc"), (1, "#000")], ops=[0.25, 0.0]), None))
    for row in range(4):
        y = 1150 + row * 170
        for x in range(-20, W, 110):
            d.add(rect(x, y, 96, 130, "#7f1d1d", 30, None))
    vignette(d, 0.5)


S("cinema_hall", "entertainment media", _cinema, (0.55, 0.62))


def _art_studio(d: Doc):
    room(d, "#fef3c7", "#d6a76c")
    window_frame(d, 620, 220, 380, 480, "day")
    d.add(poly([(140, 1330), (260, 700), (380, 1330)], "none", "#78350f", 14), rect(150, 700, 230, 300, "#f8fafc", 4, "#78350f", 8))
    for i, c in enumerate(("#ef4444", "#3b82f6", "#facc15")):
        d.add(circle(210 + i * 60, 820 + i * 40, 40, c, None, op=0.8))
    for _ in range(12):
        d.add(circle(round(d.rng.uniform(0, W)), round(d.rng.uniform(1350, 1880)), round(d.rng.uniform(8, 20)), d.rng.choice(["#ef4444", "#3b82f6", "#facc15", "#22c55e"]), None, op=0.7))
    vignette(d, 0.25)


S("art_studio", "art creativity", _art_studio)


def _museum(d: Doc):
    room(d, "#f5f5f4", "#a8a29e", 1300, planks=False, tiles=True)
    frame_art(d, 60, 360, 300, 380, "#0ea5e9")
    frame_art(d, 720, 360, 300, 380, "#f59e0b")
    d.add(rect(430, 1050, 220, 250, "#e7e5e4", 4, "#a8a29e", 6), path("M540,1050 C480,980 500,880 540,850 C580,880 600,980 540,1050 Z", "#a8a29e", None))
    d.add(line(120, 1200, 960, 1200, "#991b1b", 6, op=0.0))
    vignette(d, 0.25)


S("museum_gallery", "art history education", _museum)


def _gym(d: Doc):
    room(d, "#1f2937", "#111827", 1300, planks=False)
    d.add(rect(0, 200, W, 600, "#374151", 0, None))
    for x in range(60, W, 240):
        d.add(rect(x, 260, 160, 480, "#94a3b8", 6, None, op=0.25))
    d.add(rect(0, 1100, 340, 20, "#64748b", 0, None))
    for x in (30, 120, 210, 300):
        d.add(rect(x - 24, 1040, 48, 60, "#111827", 10, "#ef4444", 5))
    d.add(rect(720, 960, 320, 30, "#9ca3af", 6, None), rect(720, 900, 40, 150, "#ef4444", 6, None), rect(1000, 900, 40, 150, "#ef4444", 6, None))
    vignette(d, 0.45)


S("gym_weights", "fitness sports health", _gym)


def _yoga(d: Doc):
    room(d, "#fdf2f8", "#d6a76c")
    window_frame(d, 160, 220, 760, 600, "dawn", "#fbcfe8")
    plant(d, 100, 1330, 1.0)
    plant(d, 980, 1330, 0.8)
    d.add(rect(300, 1450, 480, 70, "#a78bfa", 20, None))
    vignette(d, 0.15)


S("yoga_studio", "mental_health fitness self_improvement", _yoga)


def _rest_kitchen(d: Doc):
    room(d, "#e5e7eb", "#9ca3af", 1300, planks=False, tiles=True)
    d.add(rect(0, 1000, W, 300, "#d1d5db", 0, None), rect(0, 980, W, 30, "#6b7280", 0, None))
    for x in range(40, W, 200):
        d.add(rect(x, 300, 150, 18, "#6b7280", 0, None))
        for k in range(3):
            d.add(circle(x + 25 + k * 50, 290, 22, "#9ca3af", None))
    d.add(rect(120, 880, 200, 100, "#475569", 10, None), circle(220, 870, 140, d.rgrad([(0, "#f97316"), (1, "#f97316")], ops=[0.25, 0.0]), None))
    vignette(d, 0.3)


S("restaurant_kitchen", "food cooking business", _rest_kitchen)


def _cafe(d: Doc):
    room(d, "#7c2d12", "#451a03")
    d.add(rect(0, 1000, W, 300, "#92400e", 0, None), rect(0, 980, W, 30, "#451a03", 0, None))
    d.add(rect(120, 200, 840, 300, "#1c1917", 10, None), text(540, 300, "MENU", 60, "#fef3c7"))
    for i in range(3):
        d.add(line(200, 360 + i * 40, 600, 360 + i * 40, "#fef3c7", 6, op=0.6), line(700, 360 + i * 40, 880, 360 + i * 40, "#fef3c7", 6, op=0.6))
    for x in (200, 540, 880):
        d.add(line(x, 0, x, 120, "#1c1917", 4), ellipse(x, 140, 60, 30, "#fbbf24", None), circle(x, 170, 120, d.rgrad([(0, "#fde68a"), (1, "#fde68a")], ops=[0.3, 0.0]), None))
    vignette(d, 0.4)


S("cafe_counter", "food business relaxation", _cafe)


def _supermarket(d: Doc):
    room(d, "#f8fafc", "#e5e7eb", 1300, planks=False, tiles=True)
    for x in (0, 720):
        for r in range(5):
            y = 260 + r * 200
            d.add(rect(x, y + 120, 360, 16, "#94a3b8", 0, None))
            for i in range(7):
                d.add(rect(x + 10 + i * 50, y + 40, 40, 80, d.rng.choice(["#ef4444", "#f97316", "#22c55e", "#3b82f6", "#facc15", "#a855f7"]), 6, None))
    d.add(rect(0, 120, W, 60, "#22c55e", 0, None), text(540, 165, "FRESH MARKET", 40, "#f8fafc"))
    vignette(d, 0.2)


S("supermarket_aisle", "shopping food business", _supermarket)


def _warehouse(d: Doc):
    room(d, "#57534e", "#78716c", 1300, planks=False)
    for x in (0, 760):
        for r in range(4):
            y = 260 + r * 260
            d.add(rect(x, y + 220, 320, 20, "#f97316", 0, None))
            for i in range(3):
                d.add(rect(x + 10 + i * 100, y + 100, 90, 120, "#d6a76c", 4, "#92400e", 4))
    d.add(rect(0, 1240, W, 16, "#facc15", 0, None, op=0.7))
    vignette(d, 0.4)


S("warehouse_shelves", "logistics business shopping industry", _warehouse)


def _factory_floor(d: Doc):
    room(d, "#374151", "#4b5563", 1300, planks=False)
    for x in range(0, W, 180):
        d.add(line(x, 0, x + 90, 200, "#6b7280", 10))
    d.add(rect(0, 1050, W, 90, "#1f2937", 0, None))
    for x in range(30, W, 140):
        d.add(circle(x, 1095, 30, "#6b7280", None), rect(x - 40, 960, 80, 90, "#f59e0b", 6, None))
    for x in (120, 900):
        d.add(poly([(x + 40 * math.cos(math.radians(i * 22.5)) * (1 if i % 2 else 1.35), 600 + 40 * math.sin(math.radians(i * 22.5)) * (1 if i % 2 else 1.35)) for i in range(16)], "#9ca3af", None))
    vignette(d, 0.4)


S("factory_floor", "industry construction business", _factory_floor)


def _workshop(d: Doc):
    room(d, "#78350f", "#57534e", 1300, planks=False)
    d.add(rect(60, 240, 960, 560, "#a16207", 8, None))
    for i in range(16):
        d.add(circle(120 + (i % 8) * 120, 320 + (i // 8) * 200, 12, "#451a03", None))
    for x, h in ((120, 150), (300, 110), (480, 170), (660, 130), (840, 160)):
        d.add(rect(x, 340, 30, h, "#64748b", 6, None))
    d.add(rect(0, 1050, W, 40, "#451a03", 0, None))
    vignette(d, 0.4)


S("workshop_tools", "construction tools industry", _workshop)


def _mission(d: Doc):
    room(d, "#0b1220", "#111827", 1300, planks=False)
    d.add(rect(60, 160, 960, 520, "#020617", 10, "#334155", 10))
    stars(d, 40, 180, 660)
    d.add(path("M120,600 C300,300 600,250 900,420", "none", "#22d3ee", 6, stroke_dasharray="18 12"), circle(900, 420, 20, "#f97316", None))
    for row in range(2):
        for x in range(0, W, 180):
            d.add(rect(x + 10, 1000 + row * 160, 160, 100, "#1f2937", 8, None), rect(x + 30, 1015 + row * 160, 120, 60, "#0ea5e9", 4, None, op=0.6))
    vignette(d, 0.45)


S("mission_control", "space science tech", _mission)


def _spaceship(d: Doc):
    d.add(rect(0, 0, W, H, "#0f172a", 0, None), path("M0,0 L1080,0 L1080,300 C800,200 280,200 0,300 Z", "#1e293b", None))
    d.add(path("M140,260 C300,180 780,180 940,260 L900,900 C700,960 380,960 180,900 Z", "#020617", "#475569", 14))
    stars(d, 70, 260, 900)
    d.add(circle(760, 520, 90, "#2563eb", None))
    d.add(rect(0, 1100, W, 200, "#1e293b", 0, None))
    for x in range(40, W, 160):
        d.add(rect(x, 1130, 110, 50, d.rng.choice(["#22d3ee", "#22c55e", "#f97316"]), 6, None, op=0.7))
    vignette(d, 0.4)


S("spaceship_bridge", "space science tech adventure", _spaceship)


def _greenhouse(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#bbf7d0"), (1, "#86efac")]), 0, None))
    for x in range(0, W, 135):
        d.add(line(x, 0, x, GY, "#f8fafc", 10, op=0.8))
    for y in range(0, GY, 220):
        d.add(line(0, y, W, y, "#f8fafc", 8, op=0.7))
    for x in (60, 200, 880, 1000):
        plant(d, x, 1450, 0.9)
    ground(d, "#78350f")
    vignette(d, 0.2)


S("greenhouse", "agriculture nature science", _greenhouse)


def _bathroom(d: Doc):
    room(d, "#e0f2fe", "#bae6fd", 1300, planks=False, tiles=True)
    for y in range(200, 1300, 100):
        d.add(line(0, y, W, y, "#bae6fd", 3))
    d.add(rect(700, 300, 280, 360, "#f0f9ff", 10, "#94a3b8", 10), rect(660, 900, 360, 120, "#f8fafc", 30, "#94a3b8", 6),
          rect(40, 1000, 420, 220, "#f8fafc", 60, "#94a3b8", 8))
    vignette(d, 0.2)


S("bathroom_home", "home health", _bathroom)


def _playroom(d: Doc):
    room(d, "#fef9c3", "#fca5a5")
    for x, c in ((120, "#ef4444"), (200, "#3b82f6"), (160, "#22c55e")):
        d.add(rect(x, 1180 - (40 if c == "#22c55e" else 0), 90, 90, c, 8, None))
    d.add(circle(900, 1260, 70, "#f472b6", None), circle(900, 1260, 70, "none", "#f8fafc", 10))
    for i, c in enumerate(("#ef4444", "#f97316", "#facc15", "#22c55e", "#3b82f6")):
        d.add(path(arc_d(540, 700, 300 - i * 30, 180, 360), "none", c, 26, op=0.7))
    vignette(d, 0.15)


S("kids_playroom", "kids family education", _playroom)


# =========================================================================== ABSTRACT / STUDIO
def _studio(c1, c2, spot=True):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, d.grad([(0, c1), (1, c2)]), 0, None))
        if spot:
            d.add(ellipse(540, 900, 520, 620, d.rgrad([(0, "#ffffff"), (1, "#ffffff")], ops=[0.16, 0.0]), None))
        d.add(ellipse(540, GY + 10, 380, 50, "#000000", None, op=0.25))
        vignette(d, 0.35)
    return b


for name, a, b_ in (("blue", "#1e3a8a", "#0c4a6e"), ("purple", "#4c1d95", "#1e1b4b"), ("teal", "#115e59", "#042f2e"), ("orange", "#c2410c", "#7c2d12"),
                    ("pink", "#be185d", "#500724"), ("green", "#166534", "#052e16"), ("red", "#991b1b", "#450a0a"), ("dark", "#1f2937", "#030712"),
                    ("cream", "#fef3c7", "#d6a76c"), ("sky", "#0284c7", "#0369a1")):
    S(f"studio_{name}", "general", _studio(a, b_))


def _grid(neon):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, "#0b1020" if neon else "#1d4ed8", 0, None))
        col = "#22d3ee" if neon else "#bfdbfe"
        for x in range(0, W + 1, 60):
            d.add(line(x, 0, x, H, col, 2, op=0.18))
        for y in range(0, H + 1, 60):
            d.add(line(0, y, W, y, col, 2, op=0.18))
        if neon:
            d.add(rect(0, GY, W, H - GY, "#0b1020", 0, None))
            for i in range(14):
                y = GY + (i ** 1.6) * 6
                d.add(line(0, y, W, y, "#f472b6", 3, op=0.6))
            for x in range(-1200, 2400, 120):
                d.add(line(540, GY, x, H, "#f472b6", 3, op=0.5))
        vignette(d, 0.4)
    return b


S("neon_grid", "tech gaming general", _grid(True))
S("blueprint_grid", "engineering construction science general", _grid(False))


def _chalk(d: Doc):
    d.add(rect(0, 0, W, H, "#14532d", 0, None))
    for _ in range(40):
        d.add(line(d.rng.uniform(0, W), d.rng.uniform(0, H), d.rng.uniform(0, W), d.rng.uniform(0, H), "#f8fafc", 2, op=0.04))
    for s, x, y in (("π", 140, 300), ("x²", 880, 260), ("∑", 160, 900), ("√", 900, 820), ("?", 520, 220)):
        d.add(text(x, y, s, 110, "#f8fafc", op=0.35))
    d.add(rect(0, 1720, W, 200, "#78350f", 0, None))
    vignette(d, 0.4)


S("chalkboard_bg", "education science general", _chalk)


def _paper(d: Doc):
    d.add(rect(0, 0, W, H, "#fefce8", 0, None))
    for y in range(160, H, 64):
        d.add(line(0, y, W, y, "#93c5fd", 3, op=0.7))
    d.add(line(150, 0, 150, H, "#f87171", 4))
    for y in (300, 900, 1500):
        d.add(circle(60, y, 26, "#e5e7eb", None))
    vignette(d, 0.15)


S("notebook_paper", "education productivity general", _paper)


def _cork(d: Doc):
    d.add(rect(0, 0, W, H, "#b45309", 0, None))
    for _ in range(400):
        d.add(circle(round(d.rng.uniform(0, W)), round(d.rng.uniform(0, H)), 3, "#78350f", None, op=0.4))
    for x, y, c, r in ((80, 200, "#fde047", -6), (760, 260, "#f9a8d4", 5), (120, 1000, "#a5f3fc", 4), (780, 1050, "#bbf7d0", -5)):
        d.add(rect(x, y, 240, 240, c, 2, None, transform=f"rotate({r} {x + 120} {y + 120})"), circle(x + 120, y + 16, 14, "#ef4444", None))
    d.add(path("M200,320 C400,500 600,400 880,380 M240,1120 C500,900 700,1000 900,1170", "none", "#ef4444", 5))
    vignette(d, 0.3)


S("cork_board", "mystery productivity storytelling general", _cork)


def _halftone(c1, c2):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, c1, 0, None))
        for y in range(0, H, 64):
            for x in range(0, W, 64):
                r = 5 + 18 * (1 - abs(y - 960) / 960)
                d.add(circle(x + (32 if (y // 64) % 2 else 0), y, round(r), c2, None, op=0.35))
        vignette(d, 0.3)
    return b


S("comic_halftone_yellow", "comedy general", _halftone("#facc15", "#f97316"))
S("comic_halftone_blue", "comedy general", _halftone("#38bdf8", "#1d4ed8"))


def _rays(c1, c2):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, c1, 0, None))
        for i in range(0, 24, 2):
            a0, a1 = math.radians(i * 15), math.radians((i + 1) * 15)
            d.add(poly([(540, 900), (540 + 2400 * math.cos(a0), 900 + 2400 * math.sin(a0)), (540 + 2400 * math.cos(a1), 900 + 2400 * math.sin(a1))], c2, None))
        vignette(d, 0.35)
    return b


S("sunburst_gold", "celebration winner general", _rays("#f59e0b", "#fbbf24"))
S("sunburst_red", "comedy general", _rays("#dc2626", "#ef4444"))
S("sunburst_purple", "celebration general", _rays("#6d28d9", "#7c3aed"))


def _bokeh(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#1e1b4b"), (1, "#0f172a")]), 0, None))
    for _ in range(40):
        c = d.rng.choice(["#f472b6", "#fde68a", "#22d3ee", "#a78bfa"])
        d.add(circle(round(d.rng.uniform(0, W)), round(d.rng.uniform(0, 1400)), round(d.rng.uniform(30, 110)), c, None, op=round(d.rng.uniform(0.08, 0.28), 2)))
    vignette(d, 0.35)


S("bokeh_lights", "celebration love general", _bokeh)


def _matrix(d: Doc):
    d.add(rect(0, 0, W, H, "#020617", 0, None))
    for x in range(20, W, 46):
        y0 = d.rng.uniform(-400, 600)
        for k in range(d.rng.randint(8, 26)):
            d.add(text(x, round(y0 + k * 44), d.rng.choice("0123456789ABCDEF<>/{}"), 34, "#22c55e", family="DejaVu Sans Mono", op=round(max(0.1, 1 - k / 26), 2)))
    vignette(d, 0.4)


S("matrix_code", "tech coding security", _matrix)


def _circuit(d: Doc):
    d.add(rect(0, 0, W, H, "#052e16", 0, None))
    for _ in range(60):
        x, y = d.rng.uniform(0, W), d.rng.uniform(0, H)
        dx = d.rng.choice([-1, 1]) * d.rng.uniform(80, 260)
        dy = d.rng.choice([-1, 1]) * d.rng.uniform(80, 260)
        d.add(pline([(x, y), (x + dx, y), (x + dx, y + dy)], "#22c55e", 4, op=0.35), circle(round(x + dx), round(y + dy), 8, "#fbbf24", None, op=0.6))
    d.add(rect(390, 760, 300, 300, "#111827", 16, "#22c55e", 6))
    vignette(d, 0.4)


S("circuit_board", "tech ai computing", _circuit)


def _network(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#0f172a"), (1, "#1e1b4b")]), 0, None))
    pts = [(d.rng.uniform(0, W), d.rng.uniform(0, 1450)) for _ in range(28)]
    for i, (x, y) in enumerate(pts):
        for (x2, y2) in pts[i + 1:]:
            if math.hypot(x - x2, y - y2) < 300:
                d.add(line(round(x), round(y), round(x2), round(y2), "#38bdf8", 2, op=0.35))
    for x, y in pts:
        d.add(circle(round(x), round(y), 9, "#a78bfa", None))
    vignette(d, 0.4)


S("network_nodes", "tech ai web3 crypto social_media", _network)


def _split(c1, c2):
    def b(d: Doc):
        d.add(rect(0, 0, W / 2, H, c1, 0, None), rect(W / 2, 0, W / 2, H, c2, 0, None))
        d.add(poly([(W / 2 - 40, 0), (W / 2 + 40, 0), (W / 2 - 40, H), (W / 2 - 120, H)], "#f8fafc", None, op=0.0))
        d.add(circle(W / 2, 330, 110, "#f8fafc", None), text(W / 2, 375, "VS", 110, "#0f172a"))
        vignette(d, 0.3)
    return b


S("split_versus", "general comparison", _split("#1d4ed8", "#b91c1c"))
S("split_before_after", "general comparison self_improvement", _split("#475569", "#16a34a"))


def _vapor(d: Doc):
    d.add(rect(0, 0, W, GY, d.grad([(0, "#1e1b4b"), (0.6, "#be185d"), (1, "#f97316")]), 0, None))
    sun(d, 540, 1150, 260, "#fbbf24", False)
    for i, y in enumerate(range(1000, 1420, 60)):
        d.add(rect(0, y, W, 14 + i * 3, "#be185d", 0, None))
    d.add(rect(0, GY, W, H - GY, "#0b1020", 0, None))
    for i in range(12):
        d.add(line(0, GY + (i ** 1.6) * 6, W, GY + (i ** 1.6) * 6, "#22d3ee", 3, op=0.6))
    for x in range(-1200, 2400, 140):
        d.add(line(540, GY, x, H, "#22d3ee", 3, op=0.5))


S("vaporwave_sunset", "music gaming general", _vapor)


def _world_map(d: Doc):
    d.add(rect(0, 0, W, H, "#0c4a6e", 0, None))
    for y in range(0, H, 120):
        d.add(line(0, y, W, y, "#38bdf8", 2, op=0.15))
    for x in range(0, W, 120):
        d.add(line(x, 0, x, H, "#38bdf8", 2, op=0.15))
    for cx, cy, rx, ry in ((260, 500, 200, 170), (300, 900, 120, 230), (640, 480, 180, 140), (680, 900, 140, 200), (900, 620, 140, 120), (900, 1150, 100, 60)):
        d.add(ellipse(cx, cy, rx, ry, "#0d9488", None, op=0.8))
    vignette(d, 0.35)


S("world_map_bg", "travel history business general", _world_map)


def _newspaper(d: Doc):
    d.add(rect(0, 0, W, H, "#f5f5f4", 0, None), rect(40, 60, 1000, 140, "#1c1917", 0, None), text(540, 160, "THE DAILY STICK", 80, "#f5f5f4", family="DejaVu Serif"))
    for col in range(3):
        for k in range(26):
            d.add(line(60 + col * 340, 260 + k * 46, 360 + col * 340, 260 + k * 46, "#a8a29e", 6, op=0.7))
    d.add(rect(60, 600, 640, 420, "#d6d3d1", 0, None))
    vignette(d, 0.2)


S("newspaper_bg", "media history storytelling general", _newspaper)


def _money_bg(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#14532d"), (1, "#052e16")]), 0, None))
    for _ in range(36):
        d.add(text(round(d.rng.uniform(0, W)), round(d.rng.uniform(60, H)), "$", round(d.rng.uniform(50, 140)), "#22c55e", op=round(d.rng.uniform(0.1, 0.35), 2)))
    vignette(d, 0.4)


S("money_pattern", "finance money general", _money_bg)


def _chart_bg(up):
    def b(d: Doc):
        d.add(rect(0, 0, W, H, "#0b1220", 0, None))
        for y in range(200, 1500, 140):
            d.add(line(0, y, W, y, "#1e293b", 3))
        pts = [(x, (1300 - x * 0.9 if up else 300 + x * 0.9) + d.rng.uniform(-90, 90)) for x in range(0, W + 1, 90)]
        d.add(pline(pts, "#22c55e" if up else "#ef4444", 10, op=0.6))
        vignette(d, 0.4)
    return b


S("chart_bull_bg", "finance trading investing growth", _chart_bg(True))
S("chart_bear_bg", "finance trading investing decline", _chart_bg(False))


def _dna_bg(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#1e1b4b"), (1, "#0c4a6e")]), 0, None))
    for k, x0 in enumerate((180, 900)):
        for i in range(40):
            y = i * 48
            a = i * 0.4 + k
            x1, x2 = x0 + 90 * math.sin(a), x0 - 90 * math.sin(a)
            d.add(line(round(x1), y, round(x2), y, "#64748b", 3, op=0.4), circle(round(x1), y, 9, "#f472b6", None, op=0.6), circle(round(x2), y, 9, "#38bdf8", None, op=0.6))
    vignette(d, 0.35)


S("dna_bg", "science biology health", _dna_bg)


def _cells_bg(d: Doc):
    d.add(rect(0, 0, W, H, "#7f1d1d", 0, None))
    for _ in range(28):
        x, y, r = d.rng.uniform(0, W), d.rng.uniform(0, H), d.rng.uniform(40, 90)
        d.add(ellipse(round(x), round(y), round(r), round(r * 0.7), "#ef4444", None, op=0.7), ellipse(round(x), round(y), round(r * 0.45), round(r * 0.3), "#b91c1c", None, op=0.8))
    vignette(d, 0.45)


S("bloodstream_cells", "health medical biology science", _cells_bg)


def _microscope_view(d: Doc):
    d.add(rect(0, 0, W, H, "#000000", 0, None), circle(540, 900, 520, "#ecfccb", None))
    for _ in range(14):
        x, y = d.rng.uniform(140, 940), d.rng.uniform(500, 1300)
        d.add(ellipse(round(x), round(y), 70, 44, "#a3e635", "#4d7c0f", 5, op=0.85), circle(round(x + 10), round(y), 16, "#65a30d", None))
    d.add(circle(540, 900, 520, "none", "#1f2937", 30))


S("microscope_view", "science biology health", _microscope_view, (0.6, 0.86))


def _brain_bg(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#2e1065"), (1, "#831843")]), 0, None))
    pts = [(d.rng.uniform(0, W), d.rng.uniform(0, 1450)) for _ in range(24)]
    for i, (x, y) in enumerate(pts):
        for (x2, y2) in pts[i + 1:]:
            if math.hypot(x - x2, y - y2) < 260:
                d.add(path(f"M{x:.0f},{y:.0f} Q{(x + x2) / 2 + 40:.0f},{(y + y2) / 2 - 40:.0f} {x2:.0f},{y2:.0f}", "none", "#f9a8d4", 3, op=0.4))
        d.add(circle(round(x), round(y), 10, "#fde68a", None, op=0.8))
    vignette(d, 0.4)


S("neurons_bg", "psychology science mental_health ai", _brain_bg)


def _stage_spot(d: Doc):
    d.add(rect(0, 0, W, H, "#09090b", 0, None), poly([(450, 0), (630, 0), (900, GY), (180, GY)], "#fef9c3", None, op=0.14),
          ellipse(540, GY, 380, 60, "#fef9c3", None, op=0.22), rect(0, GY, W, H - GY, "#18181b", 0, None))


S("spotlight_stage", "entertainment motivation storytelling general", _stage_spot, (0.5, 0.78))


def _clouds_dream(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#c4b5fd"), (1, "#fbcfe8")]), 0, None))
    clouds(d, 14, 0, H, "#ffffff", 0.75, (90, 180))
    stars(d, 30, 0, 1200, "#fef9c3")


S("dreamy_clouds", "sleep mental_health magic general", _clouds_dream, (0.6, 0.8))


def _inside_phone(d: Doc):
    d.add(rect(0, 0, W, H, "#1e293b", 0, None), rect(140, 60, 800, 1800, "#0f172a", 80, "#475569", 20))
    for i in range(6):
        d.add(rect(220, 240 + i * 230, 640, 190, "#1e293b", 26, None), circle(310, 335 + i * 230, 50, d.rng.choice(["#f43f5e", "#3b82f6", "#22c55e", "#f59e0b"]), None),
              rect(390, 300 + i * 230, 380, 26, "#475569", 10, None), rect(390, 350 + i * 230, 260, 22, "#334155", 10, None))


S("inside_phone_feed", "social_media tech addiction marketing", _inside_phone, (0.55, 0.82))


def _timeline_bg(d: Doc):
    d.add(rect(0, 0, W, H, d.grad([(0, "#0f172a"), (1, "#1e293b")]), 0, None), line(80, 400, 1000, 400, "#94a3b8", 8))
    for i, yr in enumerate(("1900", "1950", "2000", "2050")):
        x = 120 + i * 280
        d.add(circle(x, 400, 22, "#f59e0b", None), text(x, 340, yr, 44, "#e2e8f0"))
    vignette(d, 0.3)


S("timeline_history_bg", "history education storytelling", _timeline_bg)
