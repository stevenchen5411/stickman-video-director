"""Tiny SVG builder used by the asset pack: flat illustration style, dark outline, soft highlights."""
from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence, Tuple, Union

OUT = "#0f172a"
SW = 7  # default outline width on a 256 canvas

# curated palette
WHITE, PAPER, SILVER, GRAY, GRAY_D, SLATE, INK = "#f8fafc", "#f1f5f9", "#cbd5e1", "#94a3b8", "#64748b", "#334155", "#1e293b"
RED, RED_D, ROSE, PINK, ORANGE, AMBER, YELLOW, GOLD = "#ef4444", "#b91c1c", "#f43f5e", "#ec4899", "#f97316", "#f59e0b", "#facc15", "#fbbf24"
LIME, GREEN, GREEN_D, EMERALD, TEAL, CYAN, SKY, BLUE, BLUE_D = ("#84cc16", "#22c55e", "#15803d", "#10b981", "#14b8a6",
                                                               "#22d3ee", "#38bdf8", "#3b82f6", "#1d4ed8")
INDIGO, VIOLET, PURPLE, BROWN, BROWN_L, TAN, CREAM, SAND = ("#6366f1", "#8b5cf6", "#a855f7", "#92400e", "#b45309",
                                                           "#d6a76c", "#fef3c7", "#fde68a")
GLASS = "#bae6fd"

El = str


def _a(**kw) -> str:
    out = []
    for k, v in kw.items():
        if v is None:
            continue
        k = k.rstrip("_").replace("_", "-")
        if isinstance(v, float):
            v = f"{v:.1f}".rstrip("0").rstrip(".")
        out.append(f'{k}="{v}"')
    return " ".join(out)


def _st(fill, stroke, sw, op=None, extra=None):
    d = dict(fill=fill or "none", stroke=stroke or None, stroke_width=sw if stroke else None,
             stroke_linejoin="round" if stroke else None, stroke_linecap="round" if stroke else None, opacity=op)
    if extra:
        d.update(extra)
    return d


def rect(x, y, w, h, fill, rx=0, stroke=OUT, sw=SW, op=None, **kw) -> El:
    return f"<rect {_a(x=x, y=y, width=w, height=h, rx=rx or None, **_st(fill, stroke, sw, op), **kw)}/>"


def circle(cx, cy, r, fill, stroke=OUT, sw=SW, op=None, **kw) -> El:
    return f"<circle {_a(cx=cx, cy=cy, r=r, **_st(fill, stroke, sw, op), **kw)}/>"


def ellipse(cx, cy, rx, ry, fill, stroke=OUT, sw=SW, op=None, **kw) -> El:
    return f"<ellipse {_a(cx=cx, cy=cy, rx=rx, ry=ry, **_st(fill, stroke, sw, op), **kw)}/>"


def path(d, fill, stroke=OUT, sw=SW, op=None, **kw) -> El:
    return f"<path {_a(d=d, **_st(fill, stroke, sw, op), **kw)}/>"


def poly(points: Sequence[Tuple[float, float]], fill, stroke=OUT, sw=SW, op=None, **kw) -> El:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f"<polygon {_a(points=pts, **_st(fill, stroke, sw, op), **kw)}/>"


def pline(points: Sequence[Tuple[float, float]], stroke=OUT, sw=SW, op=None, **kw) -> El:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f"<polyline {_a(points=pts, **_st(None, stroke, sw, op), **kw)}/>"


def line(x1, y1, x2, y2, stroke=OUT, sw=SW, op=None, **kw) -> El:
    return f"<line {_a(x1=x1, y1=y1, x2=x2, y2=y2, **_st(None, stroke, sw, op), **kw)}/>"


def text(x, y, s, size, fill=OUT, weight="bold", anchor="middle", family="DejaVu Sans", op=None, stroke=None, sw=None) -> El:
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    attrs = _a(x=x, y=y, font_size=size, font_family=family, font_weight=weight, text_anchor=anchor, fill=fill,
               opacity=op, stroke=stroke, stroke_width=sw, paint_order="stroke" if stroke else None)
    return f"<text {attrs}>{s}</text>"


def g(children: Iterable[El], transform: Optional[str] = None, op=None) -> El:
    return f"<g {_a(transform=transform, opacity=op)}>{''.join(children)}</g>"


def hl(d, op=0.35) -> El:
    """Soft white highlight (no outline)."""
    return path(d, WHITE, None, 0, op)


def hl_ellipse(cx, cy, rx, ry, op=0.35, rot=0) -> El:
    return ellipse(cx, cy, rx, ry, WHITE, None, 0, op, transform=f"rotate({rot} {cx} {cy})" if rot else None)


def shade(d, op=0.18) -> El:
    return path(d, "#000000", None, 0, op)


def linear_grad(gid, stops: List[Tuple[float, str]], x1=0, y1=0, x2=0, y2=1) -> El:
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def radial_grad(gid, stops: List[Tuple[float, str]], cx=0.5, cy=0.5, r=0.5, op_stops: Optional[List[float]] = None) -> El:
    s = "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{op_stops[i]}"' if op_stops else "") + "/>"
                for i, (o, c) in enumerate(stops))
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'


def svg(children: Iterable[El], w=256, h=256, defs: Iterable[El] = ()) -> str:
    d = "".join(defs)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            + (f"<defs>{d}</defs>" if d else "") + "".join(children) + "</svg>")


# --------------------------------------------------------------------------- geometry helpers
def star_pts(cx, cy, ro, ri, n=5, rot=-90.0) -> List[Tuple[float, float]]:
    out = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = math.radians(rot + i * 180.0 / n)
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def reg_pts(cx, cy, r, n, rot=-90.0) -> List[Tuple[float, float]]:
    return [(cx + r * math.cos(math.radians(rot + i * 360.0 / n)), cy + r * math.sin(math.radians(rot + i * 360.0 / n)))
            for i in range(n)]


def heart_d(cx, cy, s) -> str:
    return (f"M{cx},{cy + s * 0.9} C{cx - s * 1.3},{cy + s * 0.1} {cx - s * 0.8},{cy - s} {cx},{cy - s * 0.35} "
            f"C{cx + s * 0.8},{cy - s} {cx + s * 1.3},{cy + s * 0.1} {cx},{cy + s * 0.9} Z")


def drop_d(cx, cy, s) -> str:
    return (f"M{cx},{cy - s} C{cx + s * 0.9},{cy + s * 0.1} {cx + s * 0.62},{cy + s * 0.75} {cx},{cy + s * 0.75} "
            f"C{cx - s * 0.62},{cy + s * 0.75} {cx - s * 0.9},{cy + s * 0.1} {cx},{cy - s} Z")


def arc_d(cx, cy, r, a0, a1) -> str:
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f}"


def pie_d(cx, cy, r, a0, a1) -> str:
    return f"M{cx},{cy} L" + arc_d(cx, cy, r, a0, a1)[1:] + " Z"


def cloud_d(cx, cy, s) -> str:
    return (f"M{cx - s * 1.0},{cy + s * 0.45} C{cx - s * 1.5},{cy + s * 0.45} {cx - s * 1.5},{cy - s * 0.25} {cx - s * 0.95},{cy - s * 0.2} "
            f"C{cx - s * 0.9},{cy - s * 0.75} {cx - s * 0.1},{cy - s * 0.85} {cx + s * 0.1},{cy - s * 0.35} "
            f"C{cx + s * 0.4},{cy - s * 0.7} {cx + s * 1.05},{cy - s * 0.5} {cx + s * 0.95},{cy - s * 0.05} "
            f"C{cx + s * 1.45},{cy - s * 0.05} {cx + s * 1.45},{cy + s * 0.45} {cx + s * 0.95},{cy + s * 0.45} Z")


def bolt_pts(cx, cy, s) -> List[Tuple[float, float]]:
    return [(cx + s * 0.15, cy - s), (cx - s * 0.5, cy + s * 0.12), (cx - s * 0.02, cy + s * 0.12),
            (cx - s * 0.22, cy + s), (cx + s * 0.52, cy - s * 0.18), (cx + s * 0.05, cy - s * 0.18)]


def arrow_pts(x0, y0, x1, y1, w=26, head=46) -> List[Tuple[float, float]]:
    """Thick block arrow from (x0,y0) to (x1,y1)."""
    ang = math.atan2(y1 - y0, x1 - x0)
    L = math.hypot(x1 - x0, y1 - y0)
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (x0 + u * ca - v * sa, y0 + u * sa + v * ca)
    return [P(0, -w / 2), P(L - head, -w / 2), P(L - head, -head * 0.75), P(L, 0), P(L - head, head * 0.75),
            P(L - head, w / 2), P(0, w / 2)]


def darken(hexc: str, f: float = 0.75) -> str:
    h = hexc.lstrip("#")
    r, g_, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * f), int(g_ * f), int(b * f))


def lighten(hexc: str, f: float = 0.35) -> str:
    h = hexc.lstrip("#")
    r, g_, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r + (255 - r) * f), int(g_ + (255 - g_) * f), int(b + (255 - b) * f))


Num = Union[int, float]


def btc_glyph(cx, cy, size, fill="#ffffff", stroke=OUT) -> str:
    """Bitcoin-style B (letter B with two short bars) without relying on the U+20BF font glyph."""
    sw = max(2.0, size * 0.07)
    return g([text(cx, cy + size * 0.36, "B", size, fill, stroke=stroke, sw=sw * 0.6),
              line(cx - size * 0.1, cy - size * 0.5, cx - size * 0.1, cy - size * 0.36, fill, sw),
              line(cx + size * 0.08, cy - size * 0.5, cx + size * 0.08, cy - size * 0.36, fill, sw),
              line(cx - size * 0.1, cy + size * 0.36, cx - size * 0.1, cy + size * 0.5, fill, sw),
              line(cx + size * 0.08, cy + size * 0.36, cx + size * 0.08, cy + size * 0.5, fill, sw)])
