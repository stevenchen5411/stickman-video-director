"""Renderer extensions: character outfits/hats/hair, expressive faces, extra widget, overlay and transition kinds.

Imported at the bottom of render_cairo (which owns the drawing primitives). Every entry point is defensive:
unknown kinds return False so the caller can fall back, and nothing here raises on odd asset data.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Tuple

import cairo

import render_cairo as rc

Pt = Tuple[float, float]


# =========================================================================== small helpers
def _c(theme, c, default="#94a3b8"):
    return c if c else default


def _fill_stroke(ctx, fill, stroke, lw, theme, alpha: float = 1.0) -> None:
    if fill:
        rc.setc(ctx, fill, theme, alpha)
        ctx.fill_preserve() if stroke else ctx.fill()
    if stroke:
        rc.setc(ctx, stroke, theme, alpha)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()


def _poly(ctx, pts: List[Pt]) -> None:
    ctx.new_path()
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def _ellipse(ctx, cx, cy, rx, ry) -> None:
    ctx.save()
    ctx.translate(cx, cy)
    rc.safe_scale(ctx, max(1e-3, rx), max(1e-3, ry))
    ctx.new_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def _star(ctx, cx, cy, r_out, r_in, n=5, rot=-math.pi / 2) -> None:
    ctx.new_path()
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        (ctx.line_to if i else ctx.move_to)(cx + r * math.cos(a), cy + r * math.sin(a))
    ctx.close_path()


def _heart(ctx, cx, cy, s) -> None:
    ctx.new_path()
    ctx.move_to(cx, cy + s * 0.9)
    ctx.curve_to(cx - s * 1.3, cy + s * 0.1, cx - s * 0.8, cy - s * 1.0, cx, cy - s * 0.35)
    ctx.curve_to(cx + s * 0.8, cy - s * 1.0, cx + s * 1.3, cy + s * 0.1, cx, cy + s * 0.9)
    ctx.close_path()


def _drop(ctx, cx, cy, s) -> None:
    ctx.new_path()
    ctx.move_to(cx, cy - s)
    ctx.curve_to(cx + s * 0.9, cy + s * 0.1, cx + s * 0.6, cy + s * 0.75, cx, cy + s * 0.75)
    ctx.curve_to(cx - s * 0.6, cy + s * 0.75, cx - s * 0.9, cy + s * 0.1, cx, cy - s)
    ctx.close_path()


def _bolt(ctx, cx, cy, s) -> None:
    _poly(ctx, [(cx + s * 0.15, cy - s), (cx - s * 0.45, cy + s * 0.1), (cx - s * 0.02, cy + s * 0.1),
                (cx - s * 0.2, cy + s), (cx + s * 0.5, cy - s * 0.15), (cx + s * 0.05, cy - s * 0.15)])


def fit_font(ctx, text: str, max_w: float, size: float, font: str = "DejaVu Sans Bold", min_size: float = 6.0) -> float:
    rc.set_font(ctx, font, size)
    w = rc.text_width(ctx, text)
    if w > max_w > 0:
        size = max(min_size, size * max_w / w)
        rc.set_font(ctx, font, size)
    return size


def text_c(ctx, s: str, cx: float, y: float, theme, fill, max_w: float, size: float, font="DejaVu Sans Bold",
           alpha: float = 1.0, stroke=None, stroke_w: float = 0.0) -> float:
    """Centred single-line text that shrinks to fit max_w. Returns the font size used."""
    s = str(s)
    size = fit_font(ctx, s, max_w, size, font)
    rc.draw_text(ctx, s, cx - rc.text_width(ctx, s) / 2, y, theme, fill, stroke, stroke_w, alpha)
    return size


def wrap_lines(ctx, s: str, max_w: float, max_lines: int = 3) -> List[str]:
    words, lines, cur = str(s).split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and rc.text_width(ctx, trial) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,") + "…"
    return lines


# =========================================================================== characters: outfits, hats, hair
BACK_KINDS = {"cape", "backpack", "hair_long", "hair_ponytail", "labcoat", "hoodie", "tank", "suit", "dress", "robe",
              "trench_coat", "vest_safety", "apron", "scrubs", "jersey", "overalls", "tshirt", "tie", "bowtie", "scarf",
              "stethoscope", "lanyard", "medal", "belt", "necklace", "toolbelt", "sash", "jacket"}
GARMENTS = ["cape", "backpack", "hair_long", "hair_ponytail", "labcoat", "trench_coat", "robe", "hoodie", "jacket", "suit",
            "tshirt", "tank", "scrubs", "jersey", "dress", "overalls", "apron", "vest_safety", "toolbelt", "belt", "sash",
            "scarf", "tie", "bowtie", "necklace", "stethoscope", "lanyard", "medal"]


def accessory_list(char: Dict[str, Any]) -> List[Dict[str, Any]]:
    """New `accessories` list plus the legacy single `accessory` dict (type/glasses/headband)."""
    out: List[Dict[str, Any]] = []
    acc = char.get("accessory") or {}
    if acc.get("type"):
        out.append({"type": acc["type"], "color": acc.get("color")})
    out += [a for a in (char.get("accessories") or []) if isinstance(a, dict) and a.get("type")]
    if acc.get("glasses"):
        out.append({"type": "glasses", "color": (char.get("colors") or {}).get("accent", "#22d3ee")})
    if acc.get("headband"):
        out.append({"type": "headband", "color": "#f8fafc"})
    return out


def _torso(pts) -> Tuple[Pt, Pt, Pt, Pt, float]:
    t, p = pts["neck_base"], pts["pelvis"]
    ax, ay = p[0] - t[0], p[1] - t[1]
    L = math.hypot(ax, ay) or 1.0
    u = (ax / L, ay / L)
    return t, p, u, (-u[1], u[0]), L


def _quad(top: Pt, bot: Pt, u: Pt, n: Pt, wt: float, wb: float, t0: float = 0.0, b0: float = 0.0) -> List[Pt]:
    tc = (top[0] + u[0] * t0, top[1] + u[1] * t0)
    bc = (bot[0] + u[0] * b0, bot[1] + u[1] * b0)
    return [(tc[0] + n[0] * wt / 2, tc[1] + n[1] * wt / 2), (tc[0] - n[0] * wt / 2, tc[1] - n[1] * wt / 2),
            (bc[0] - n[0] * wb / 2, bc[1] - n[1] * wb / 2), (bc[0] + n[0] * wb / 2, bc[1] + n[1] * wb / 2)]


def _along(a: Pt, u: Pt, n: Pt, du: float, dn: float = 0.0) -> Pt:
    return (a[0] + u[0] * du + n[0] * dn, a[1] + u[1] * du + n[1] * dn)


def draw_body_accessories(ctx, accs, pts, rig, U, theme, head_r, line_c, t: float = 0.0) -> None:
    """Garments and body items, drawn before the limbs so arms read on top."""
    top, bot, u, n, L = _torso(pts)
    lw = max(1.5, rig["line_width"] * U * 0.55)
    kinds = {a["type"]: a for a in accs if a.get("type") in BACK_KINDS}
    for kind in GARMENTS:
        a = kinds.get(kind)
        if not a:
            continue
        col = a.get("color") or "#64748b"
        col2 = a.get("color2") or "#f8fafc"
        try:
            _BODY[kind](ctx, top, bot, u, n, L, U, head_r, col, col2, lw, line_c, theme, pts, t)
        except Exception:  # noqa: BLE001 - a broken accessory must never break a frame
            continue


def _g_coat(ext, wt, wb):
    def f(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
        _poly(ctx, _quad(top, bot, u, n, wt * U, wb * U, -0.005 * U, ext * U))
        _fill_stroke(ctx, col, lc, lw, th)
        # lapels / opening line
        a, b = _along(top, u, n, 0.0), _along(top, u, n, L * 0.45)
        rc.line(ctx, a[0] - n[0] * wt * U * 0.25, a[1] - n[1] * wt * U * 0.25, b[0], b[1], lw, lc, th)
        rc.line(ctx, a[0] + n[0] * wt * U * 0.25, a[1] + n[1] * wt * U * 0.25, b[0], b[1], lw, lc, th)
        c = _along(bot, u, n, ext * U)
        rc.line(ctx, b[0], b[1], c[0], c[1], lw * 0.8, lc, th)
    return f


def _g_plain(wt, wb, ext=0.0, neck="round"):
    def f(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
        _poly(ctx, _quad(top, bot, u, n, wt * U, wb * U, 0.0, ext * U))
        _fill_stroke(ctx, col, lc, lw, th)
        if neck == "v":
            a, b, c = _along(top, u, n, 0, wt * U * 0.3), _along(top, u, n, L * 0.25), _along(top, u, n, 0, -wt * U * 0.3)
            ctx.new_path(); ctx.move_to(*a); ctx.line_to(*b); ctx.line_to(*c)
            rc.setc(ctx, lc, th); ctx.set_line_width(lw); ctx.stroke()
    return f


def _g_hoodie(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    hx, hy = pts["head"]
    _ellipse(ctx, hx, hy + hr * 0.15, hr * 1.25, hr * 1.18)
    _fill_stroke(ctx, col, lc, lw, th)
    _poly(ctx, _quad(top, bot, u, n, 0.1 * U, 0.095 * U, -0.01 * U, 0.015 * U))
    _fill_stroke(ctx, col, lc, lw, th)
    p = _along(top, u, n, L * 0.62)
    rc.rrect(ctx, p[0] - 0.035 * U, p[1] - 0.015 * U, 0.07 * U, 0.03 * U, 0.01 * U)
    _fill_stroke(ctx, None, lc, lw * 0.8, th)


def _g_suit(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    _poly(ctx, _quad(top, bot, u, n, 0.105 * U, 0.095 * U, -0.005 * U, 0.03 * U))
    _fill_stroke(ctx, col, lc, lw, th)
    a, b, c = _along(top, u, n, 0, 0.03 * U), _along(top, u, n, L * 0.42), _along(top, u, n, 0, -0.03 * U)
    _poly(ctx, [a, b, c])
    _fill_stroke(ctx, col2, None, lw, th)
    for i in range(2):
        p = _along(top, u, n, L * (0.6 + 0.15 * i), 0.012 * U)
        rc.circle(ctx, p[0], p[1], 0.006 * U, th, fill=lc)


def _g_dress(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    _poly(ctx, _quad(top, bot, u, n, 0.08 * U, 0.075 * U, 0.0, -L * 0.35))
    _fill_stroke(ctx, col, lc, lw, th)
    waist = _along(top, u, n, L * 0.62)
    sway = math.sin(t * 2.4) * 0.006 * U
    _poly(ctx, _quad(waist, bot, u, n, 0.075 * U, 0.2 * U, 0.0, 0.11 * U))
    pp = _quad(waist, bot, u, n, 0.075 * U, 0.2 * U, 0.0, 0.11 * U)
    pp[2] = (pp[2][0] + sway, pp[2][1]); pp[3] = (pp[3][0] + sway, pp[3][1])
    _poly(ctx, pp)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.line(ctx, *_along(waist, u, n, 0, 0.04 * U), *_along(waist, u, n, 0, -0.04 * U), lw * 1.6, col2, th)


def _g_cape(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    w = math.sin(t * 3.0) * 0.012 * U
    a, b = _along(top, u, n, 0.005 * U, 0.05 * U), _along(top, u, n, 0.005 * U, -0.05 * U)
    c, d = _along(bot, u, n, 0.2 * U, -0.13 * U - w), _along(bot, u, n, 0.2 * U, 0.13 * U - w)
    ctx.new_path(); ctx.move_to(*a); ctx.line_to(*b)
    ctx.curve_to(b[0] - n[0] * 0.05 * U, b[1] + 0.1 * U, c[0], c[1] - 0.08 * U, c[0], c[1])
    ctx.line_to(*d)
    ctx.curve_to(d[0], d[1] - 0.08 * U, a[0] + n[0] * 0.05 * U, a[1] + 0.1 * U, a[0], a[1])
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw, th)


def _g_backpack(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    c = _along(top, u, n, L * 0.42, 0.07 * U)
    rc.rrect(ctx, c[0] - 0.045 * U, c[1] - 0.075 * U, 0.09 * U, 0.15 * U, 0.025 * U)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.rrect(ctx, c[0] - 0.03 * U, c[1] + 0.005 * U, 0.06 * U, 0.05 * U, 0.012 * U)
    _fill_stroke(ctx, col2, lc, lw * 0.8, th)
    a, b = _along(top, u, n, 0.0, 0.015 * U), _along(top, u, n, L * 0.55, 0.02 * U)
    rc.line(ctx, a[0], a[1], b[0], b[1], lw * 1.6, col, th)


def _g_hair_long_back(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    hx, hy = pts["head"]
    ctx.new_path()
    ctx.move_to(hx - hr * 1.12, hy)
    ctx.curve_to(hx - hr * 1.2, hy + hr * 1.6, hx - hr * 0.9, hy + hr * 2.1, hx - hr * 0.6, hy + hr * 2.2)
    ctx.line_to(hx + hr * 0.6, hy + hr * 2.2)
    ctx.curve_to(hx + hr * 0.9, hy + hr * 2.1, hx + hr * 1.2, hy + hr * 1.6, hx + hr * 1.12, hy)
    ctx.arc_negative(hx, hy, hr * 1.12, 0, math.pi)
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw * 0.55, th)


def _g_ponytail_back(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    hx, hy = pts["head"]
    sw = math.sin(t * 3.2) * hr * 0.12
    ctx.new_path()
    ctx.move_to(hx + hr * 0.75, hy - hr * 0.55)
    ctx.curve_to(hx + hr * 1.9 + sw, hy - hr * 0.6, hx + hr * 1.7 + sw, hy + hr * 1.0, hx + hr * 1.25 + sw, hy + hr * 1.6)
    ctx.curve_to(hx + hr * 1.35 + sw, hy + hr * 0.7, hx + hr * 1.3, hy - hr * 0.1, hx + hr * 0.95, hy - hr * 0.2)
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw * 0.55, th)


def _g_tie(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    a = _along(top, u, n, 0.012 * U)
    pts4 = [_along(a, u, n, 0, 0.012 * U), _along(a, u, n, 0.02 * U, 0.008 * U), _along(a, u, n, L * 0.5, 0.016 * U),
            _along(a, u, n, L * 0.58), _along(a, u, n, L * 0.5, -0.016 * U), _along(a, u, n, 0.02 * U, -0.008 * U),
            _along(a, u, n, 0, -0.012 * U)]
    _poly(ctx, pts4)
    _fill_stroke(ctx, col, lc, lw * 0.7, th)


def _g_bowtie(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    c = _along(top, u, n, 0.012 * U)
    for s in (1, -1):
        _poly(ctx, [c, _along(c, u, n, -0.016 * U, s * 0.03 * U), _along(c, u, n, 0.016 * U, s * 0.03 * U)])
        _fill_stroke(ctx, col, lc, lw * 0.7, th)
    rc.circle(ctx, c[0], c[1], 0.007 * U, th, fill=col, stroke=lc, sw=lw * 0.6)


def _g_scarf(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    a, b = _along(top, u, n, 0.004 * U, 0.04 * U), _along(top, u, n, 0.004 * U, -0.04 * U)
    rc.line(ctx, a[0], a[1], b[0], b[1], 0.03 * U, col, th)
    sw = math.sin(t * 3.0) * 0.006 * U
    e = _along(top, u, n, 0.1 * U, -0.03 * U)
    rc.line(ctx, b[0], b[1], e[0] + sw, e[1], 0.022 * U, col, th)


def _g_vest(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    _poly(ctx, _quad(top, bot, u, n, 0.1 * U, 0.095 * U, 0.01 * U, -0.02 * U))
    _fill_stroke(ctx, col, lc, lw, th)
    for f in (0.45, 0.7):
        a, b = _along(top, u, n, L * f, 0.048 * U), _along(top, u, n, L * f, -0.048 * U)
        rc.line(ctx, a[0], a[1], b[0], b[1], 0.014 * U, col2, th)


def _g_apron(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    _poly(ctx, _quad(_along(top, u, n, L * 0.2), bot, u, n, 0.07 * U, 0.1 * U, 0.0, 0.1 * U))
    _fill_stroke(ctx, col, lc, lw, th)
    a, b = _along(top, u, n, L * 0.2, 0.035 * U), _along(top, u, n, L * 0.2, -0.035 * U)
    ctx.new_path(); ctx.move_to(*a); ctx.line_to(*_along(top, u, n, -0.005 * U)); ctx.line_to(*b)
    rc.setc(ctx, lc, th); ctx.set_line_width(lw); ctx.stroke()
    p = _along(top, u, n, L * 0.72)
    rc.rrect(ctx, p[0] - 0.03 * U, p[1] - 0.012 * U, 0.06 * U, 0.03 * U, 0.008 * U)
    _fill_stroke(ctx, col2, lc, lw * 0.7, th)


def _g_jersey(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    _poly(ctx, _quad(top, bot, u, n, 0.1 * U, 0.09 * U, 0.0, 0.0))
    _fill_stroke(ctx, col, lc, lw, th)
    c = _along(top, u, n, L * 0.52)
    rc.set_font(ctx, "DejaVu Sans Bold", 0.06 * U)
    num = "10"
    rc.draw_text(ctx, num, c[0] - rc.text_width(ctx, num) / 2, c[1] + 0.02 * U, th, col2)


def _g_overalls(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    _poly(ctx, _quad(_along(top, u, n, L * 0.4), bot, u, n, 0.075 * U, 0.095 * U, 0.0, 0.02 * U))
    _fill_stroke(ctx, col, lc, lw, th)
    for s in (1, -1):
        a, b = _along(top, u, n, 0.0, s * 0.03 * U), _along(top, u, n, L * 0.4, s * 0.03 * U)
        rc.line(ctx, a[0], a[1], b[0], b[1], 0.012 * U, col, th)
        rc.circle(ctx, b[0], b[1], 0.007 * U, th, fill=col2)


def _g_belt(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    a, b = _along(bot, u, n, -0.01 * U, 0.05 * U), _along(bot, u, n, -0.01 * U, -0.05 * U)
    rc.line(ctx, a[0], a[1], b[0], b[1], 0.016 * U, col, th)
    c = _along(bot, u, n, -0.01 * U)
    rc.rrect(ctx, c[0] - 0.012 * U, c[1] - 0.01 * U, 0.024 * U, 0.02 * U, 0.003 * U)
    _fill_stroke(ctx, col2, lc, lw * 0.5, th)


def _g_toolbelt(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    _g_belt(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t)
    for s in (1, -1):
        c = _along(bot, u, n, 0.02 * U, s * 0.05 * U)
        rc.rrect(ctx, c[0] - 0.016 * U, c[1] - 0.012 * U, 0.032 * U, 0.038 * U, 0.006 * U)
        _fill_stroke(ctx, col, lc, lw * 0.7, th)


def _g_sash(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    a, b = _along(top, u, n, 0.0, 0.045 * U), _along(bot, u, n, -0.01 * U, -0.05 * U)
    rc.line(ctx, a[0], a[1], b[0], b[1], 0.026 * U, col, th)


def _g_necklace(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    a, c, b = _along(top, u, n, 0.0, 0.03 * U), _along(top, u, n, L * 0.22), _along(top, u, n, 0.0, -0.03 * U)
    ctx.new_path(); ctx.move_to(*a); ctx.curve_to(a[0], c[1], b[0], c[1], b[0], b[1])
    rc.setc(ctx, col, th); ctx.set_line_width(lw * 0.7); ctx.stroke()
    rc.circle(ctx, c[0], c[1] + 0.008 * U, 0.012 * U, th, fill=col2, stroke=col, sw=lw * 0.5)


def _g_stethoscope(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    a, b = _along(top, u, n, -0.004 * U, 0.035 * U), _along(top, u, n, -0.004 * U, -0.035 * U)
    tip = _along(top, u, n, L * 0.45, 0.02 * U)
    ctx.new_path(); ctx.move_to(*a)
    ctx.curve_to(a[0], a[1] + 0.09 * U, b[0], b[1] + 0.09 * U, b[0], b[1])
    rc.setc(ctx, col, th); ctx.set_line_width(lw * 1.1); ctx.stroke()
    mid = _along(top, u, n, 0.065 * U, 0.0)
    ctx.new_path(); ctx.move_to(*mid); ctx.curve_to(mid[0], mid[1] + 0.04 * U, tip[0], tip[1] - 0.04 * U, tip[0], tip[1])
    ctx.stroke()
    rc.circle(ctx, tip[0], tip[1], 0.014 * U, th, fill=col2, stroke=col, sw=lw)


def _g_lanyard(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    c = _along(top, u, n, L * 0.4)
    for s in (1, -1):
        a = _along(top, u, n, 0.0, s * 0.025 * U)
        rc.line(ctx, a[0], a[1], c[0], c[1], lw * 0.8, col, th)
    rc.rrect(ctx, c[0] - 0.02 * U, c[1], 0.04 * U, 0.05 * U, 0.006 * U)
    _fill_stroke(ctx, col2, lc, lw * 0.6, th)
    rc.line(ctx, c[0] - 0.01 * U, c[1] + 0.035 * U, c[0] + 0.01 * U, c[1] + 0.035 * U, lw * 0.5, col, th)


def _g_medal(ctx, top, bot, u, n, L, U, hr, col, col2, lw, lc, th, pts, t):
    c = _along(top, u, n, L * 0.35)
    for s in (1, -1):
        a = _along(top, u, n, 0.0, s * 0.03 * U)
        rc.line(ctx, a[0], a[1], c[0], c[1], 0.012 * U, col2, th)
    rc.circle(ctx, c[0], c[1] + 0.018 * U, 0.022 * U, th, fill=col, stroke=lc, sw=lw * 0.6)
    _star(ctx, c[0], c[1] + 0.018 * U, 0.012 * U, 0.005 * U)
    _fill_stroke(ctx, "#ffffff", None, 0, th, 0.8)


_BODY: Dict[str, Callable] = {
    "labcoat": _g_coat(0.11, 0.085, 0.12), "trench_coat": _g_coat(0.11, 0.1, 0.16), "robe": _g_coat(0.2, 0.09, 0.12),
    "jacket": _g_coat(0.0, 0.1, 0.095), "hoodie": _g_hoodie, "suit": _g_suit, "dress": _g_dress, "cape": _g_cape,
    "backpack": _g_backpack, "hair_long": _g_hair_long_back, "hair_ponytail": _g_ponytail_back,
    "tshirt": _g_plain(0.1, 0.09), "tank": _g_plain(0.07, 0.075), "scrubs": _g_plain(0.1, 0.095, 0.01, "v"),
    "jersey": _g_jersey, "overalls": _g_overalls, "apron": _g_apron, "vest_safety": _g_vest, "belt": _g_belt,
    "toolbelt": _g_toolbelt, "sash": _g_sash, "scarf": _g_scarf, "tie": _g_tie, "bowtie": _g_bowtie,
    "necklace": _g_necklace, "stethoscope": _g_stethoscope, "lanyard": _g_lanyard, "medal": _g_medal,
}
# robe/jacket proportions: (ext below pelvis, top width, bottom width)
_BODY["robe"] = _g_coat(0.2, 0.1, 0.13)
_BODY["jacket"] = _g_coat(0.02, 0.105, 0.1)


def draw_head_accessories(ctx, accs, head: Pt, r: float, angle_deg: float, theme, line_c, t: float = 0.0) -> None:
    """Hats, hair, glasses, facial hair: drawn in head-local coords (r = head radius, up = -y)."""
    items = [a for a in accs if a.get("type") in _HEAD]
    if not items:
        return
    ctx.save()
    ctx.translate(*head)
    ctx.rotate(math.radians(angle_deg))
    lw = max(1.2, r * 0.09)
    for a in sorted(items, key=lambda a: _HEAD_ORDER.get(a["type"], 5)):
        try:
            _HEAD[a["type"]](ctx, r, a.get("color") or "#64748b", a.get("color2") or "#f8fafc", lw, line_c, theme, t)
        except Exception:  # noqa: BLE001
            continue
    ctx.restore()


def _dome(ctx, r, k=1.04, y0=0.0):
    ctx.new_path()
    ctx.arc(0, y0, r * k, math.pi, 2 * math.pi)
    ctx.close_path()


def _h_cap(ctx, r, col, col2, lw, lc, th, t):
    _dome(ctx, r, 1.06, -r * 0.12)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.rrect(ctx, r * 0.1, -r * 0.2, r * 1.35, r * 0.18, r * 0.08)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.circle(ctx, 0, -r * 1.16, r * 0.1, th, fill=col2)


def _h_beanie(ctx, r, col, col2, lw, lc, th, t):
    _dome(ctx, r, 1.07, -r * 0.25)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.rrect(ctx, -r * 1.12, -r * 0.4, r * 2.24, r * 0.32, r * 0.1)
    _fill_stroke(ctx, col2, lc, lw, th)
    rc.circle(ctx, 0, -r * 1.42, r * 0.2, th, fill=col2, stroke=lc, sw=lw)


def _h_top_hat(ctx, r, col, col2, lw, lc, th, t):
    rc.rrect(ctx, -r * 0.68, -r * 2.05, r * 1.36, r * 1.4, r * 0.08)
    _fill_stroke(ctx, col, lc, lw, th)
    ctx.rectangle(-r * 0.68, -r * 0.95, r * 1.36, r * 0.22)
    _fill_stroke(ctx, col2, None, lw, th)
    rc.rrect(ctx, -r * 1.25, -r * 0.78, r * 2.5, r * 0.2, r * 0.1)
    _fill_stroke(ctx, col, lc, lw, th)


def _h_fedora(ctx, r, col, col2, lw, lc, th, t):
    _poly(ctx, [(-r * 0.75, -r * 0.7), (-r * 0.6, -r * 1.5), (0, -r * 1.3), (r * 0.6, -r * 1.5), (r * 0.75, -r * 0.7)])
    _fill_stroke(ctx, col, lc, lw, th)
    ctx.rectangle(-r * 0.74, -r * 0.92, r * 1.48, r * 0.18)
    _fill_stroke(ctx, col2, None, lw, th)
    _ellipse(ctx, 0, -r * 0.7, r * 1.45, r * 0.16)
    _fill_stroke(ctx, col, lc, lw, th)


def _h_cowboy(ctx, r, col, col2, lw, lc, th, t):
    _poly(ctx, [(-r * 0.7, -r * 0.75), (-r * 0.62, -r * 1.55), (0, -r * 1.35), (r * 0.62, -r * 1.55), (r * 0.7, -r * 0.75)])
    _fill_stroke(ctx, col, lc, lw, th)
    ctx.new_path()
    ctx.move_to(-r * 1.6, -r * 1.05)
    ctx.curve_to(-r * 1.2, -r * 0.55, r * 1.2, -r * 0.55, r * 1.6, -r * 1.05)
    ctx.curve_to(r * 1.2, -r * 0.7, -r * 1.2, -r * 0.7, -r * 1.6, -r * 1.05)
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw, th)


def _h_hard_hat(ctx, r, col, col2, lw, lc, th, t):
    _dome(ctx, r, 1.1, -r * 0.3)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.rrect(ctx, -r * 1.3, -r * 0.42, r * 2.6, r * 0.2, r * 0.08)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.line(ctx, 0, -r * 1.38, 0, -r * 0.45, lw * 1.4, col2, th)


def _h_chef(ctx, r, col, col2, lw, lc, th, t):
    for cx, cy, rr in ((-r * 0.55, -r * 1.55, r * 0.55), (r * 0.55, -r * 1.55, r * 0.55), (0, -r * 1.85, r * 0.65)):
        rc.circle(ctx, cx, cy, rr, th, fill=col, stroke=lc, sw=lw)
    rc.rrect(ctx, -r * 0.9, -r * 1.4, r * 1.8, r * 0.75, r * 0.1)
    _fill_stroke(ctx, col, lc, lw, th)


def _h_grad(ctx, r, col, col2, lw, lc, th, t):
    _dome(ctx, r, 0.95, -r * 0.45)
    _fill_stroke(ctx, col, lc, lw, th)
    _poly(ctx, [(-r * 1.5, -r * 1.25), (0, -r * 1.65), (r * 1.5, -r * 1.25), (0, -r * 0.9)])
    _fill_stroke(ctx, col, lc, lw, th)
    sw = math.sin(t * 2.5) * r * 0.08
    rc.line(ctx, 0, -r * 1.27, r * 1.1, -r * 1.15, lw, col2, th)
    rc.line(ctx, r * 1.1, -r * 1.15, r * 1.1 + sw, -r * 0.6, lw, col2, th)
    rc.circle(ctx, r * 1.1 + sw, -r * 0.55, r * 0.09, th, fill=col2)


def _h_crown(ctx, r, col, col2, lw, lc, th, t):
    _poly(ctx, [(-r * 0.85, -r * 0.75), (-r * 0.95, -r * 1.65), (-r * 0.45, -r * 1.2), (0, -r * 1.85),
                (r * 0.45, -r * 1.2), (r * 0.95, -r * 1.65), (r * 0.85, -r * 0.75)])
    _fill_stroke(ctx, col, lc, lw, th)
    for x in (-r * 0.45, 0, r * 0.45):
        rc.circle(ctx, x, -r * 0.98, r * 0.1, th, fill=col2)


def _h_party(ctx, r, col, col2, lw, lc, th, t):
    _poly(ctx, [(-r * 0.6, -r * 0.82), (r * 0.15, -r * 2.2), (r * 0.65, -r * 0.7)])
    _fill_stroke(ctx, col, lc, lw, th)
    for f in (0.35, 0.65):
        rc.line(ctx, -r * 0.6 + (r * 0.75) * f, -r * 0.82 - r * 1.38 * f, r * 0.65 - r * 0.5 * f, -r * 0.7 - r * 1.5 * f, lw, col2, th)
    rc.circle(ctx, r * 0.15, -r * 2.25, r * 0.16, th, fill=col2)


def _h_beret(ctx, r, col, col2, lw, lc, th, t):
    ctx.save(); ctx.rotate(-0.25)
    _ellipse(ctx, -r * 0.1, -r * 0.85, r * 1.2, r * 0.42)
    _fill_stroke(ctx, col, lc, lw, th)
    rc.line(ctx, -r * 0.1, -r * 1.27, -r * 0.05, -r * 1.45, lw * 1.3, col, th)
    ctx.restore()


def _h_straw(ctx, r, col, col2, lw, lc, th, t):
    _ellipse(ctx, 0, -r * 0.72, r * 1.8, r * 0.28)
    _fill_stroke(ctx, col, lc, lw, th)
    _dome(ctx, r, 0.85, -r * 0.75)
    _fill_stroke(ctx, col, lc, lw, th)
    ctx.rectangle(-r * 0.85, -r * 0.95, r * 1.7, r * 0.18)
    _fill_stroke(ctx, col2, None, lw, th)


def _h_wizard(ctx, r, col, col2, lw, lc, th, t):
    ctx.new_path()
    ctx.move_to(-r * 0.85, -r * 0.8)
    ctx.curve_to(-r * 0.4, -r * 1.6, -r * 0.1, -r * 2.2, r * 0.6, -r * 2.5)
    ctx.curve_to(r * 0.2, -r * 2.0, r * 0.5, -r * 1.4, r * 0.85, -r * 0.8)
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw, th)
    _ellipse(ctx, 0, -r * 0.8, r * 1.5, r * 0.2)
    _fill_stroke(ctx, col, lc, lw, th)
    _star(ctx, -r * 0.05, -r * 1.35, r * 0.2, r * 0.08)
    _fill_stroke(ctx, col2, None, lw, th)


def _h_space_helmet(ctx, r, col, col2, lw, lc, th, t):
    rc.circle(ctx, 0, 0, r * 1.5, th, fill=None, stroke=col, sw=lw * 1.6)
    ctx.new_path(); ctx.arc(0, 0, r * 1.5, 0, 2 * math.pi)
    rc.setc(ctx, "#bae6fd", th, 0.18); ctx.fill()
    ctx.new_path(); ctx.arc(0, 0, r * 1.22, math.pi * 1.1, math.pi * 1.4)
    rc.setc(ctx, "#ffffff", th, 0.75); ctx.set_line_width(lw * 1.2); ctx.stroke()
    rc.rrect(ctx, -r * 0.9, r * 1.25, r * 1.8, r * 0.45, r * 0.15)
    _fill_stroke(ctx, col, lc, lw, th)


def _h_headset(ctx, r, col, col2, lw, lc, th, t):
    ctx.new_path(); ctx.arc(0, 0, r * 1.15, math.pi * 1.05, math.pi * 1.95)
    rc.setc(ctx, col, th); ctx.set_line_width(lw * 1.6); ctx.stroke()
    for s in (-1, 1):
        rc.rrect(ctx, s * r * 1.12 - r * 0.18, -r * 0.3, r * 0.36, r * 0.6, r * 0.15)
        _fill_stroke(ctx, col, lc, lw, th)
    ctx.new_path(); ctx.move_to(-r * 1.1, r * 0.2); ctx.curve_to(-r * 1.0, r * 0.75, -r * 0.6, r * 0.6, -r * 0.3, r * 0.5)
    rc.setc(ctx, col, th); ctx.set_line_width(lw); ctx.stroke()
    rc.circle(ctx, -r * 0.28, r * 0.5, r * 0.09, th, fill=col2)


def _h_headphones(ctx, r, col, col2, lw, lc, th, t):
    ctx.new_path(); ctx.arc(0, 0, r * 1.2, math.pi * 1.05, math.pi * 1.95)
    rc.setc(ctx, col, th); ctx.set_line_width(lw * 2.2); ctx.stroke()
    for s in (-1, 1):
        _ellipse(ctx, s * r * 1.12, 0, r * 0.28, r * 0.42)
        _fill_stroke(ctx, col, lc, lw, th)
        _ellipse(ctx, s * r * 1.12, 0, r * 0.12, r * 0.22)
        _fill_stroke(ctx, col2, None, lw, th)


def _h_headband(ctx, r, col, col2, lw, lc, th, t):
    rc.line(ctx, -r * 0.98, -r * 0.48, r * 0.98, -r * 0.48, lw * 2.2, col, th)


def _h_nurse_cap(ctx, r, col, col2, lw, lc, th, t):
    _poly(ctx, [(-r * 0.7, -r * 0.85), (-r * 0.55, -r * 1.35), (r * 0.55, -r * 1.35), (r * 0.7, -r * 0.85)])
    _fill_stroke(ctx, col, lc, lw, th)
    rc.line(ctx, 0, -r * 1.25, 0, -r * 0.95, lw * 1.3, col2, th)
    rc.line(ctx, -r * 0.15, -r * 1.1, r * 0.15, -r * 1.1, lw * 1.3, col2, th)


def _h_santa(ctx, r, col, col2, lw, lc, th, t):
    ctx.new_path(); ctx.move_to(-r * 1.0, -r * 0.6)
    ctx.curve_to(-r * 0.6, -r * 1.9, r * 0.6, -r * 2.0, r * 1.4, -r * 1.2)
    ctx.line_to(r * 1.0, -r * 0.6); ctx.close_path()
    _fill_stroke(ctx, col, lc, lw, th)
    rc.rrect(ctx, -r * 1.12, -r * 0.78, r * 2.24, r * 0.32, r * 0.14)
    _fill_stroke(ctx, col2, lc, lw, th)
    rc.circle(ctx, r * 1.45, -r * 1.15, r * 0.2, th, fill=col2, stroke=lc, sw=lw)


def _h_mask(ctx, r, col, col2, lw, lc, th, t):
    rc.rrect(ctx, -r * 0.6, r * 0.18, r * 1.2, r * 0.6, r * 0.18)
    _fill_stroke(ctx, col, lc, lw * 0.8, th)
    for y in (0.35, 0.55):
        rc.line(ctx, -r * 0.45, r * y, r * 0.45, r * y, lw * 0.6, col2, th)
    for s in (-1, 1):
        rc.line(ctx, s * r * 0.6, r * 0.3, s * r * 0.98, -r * 0.05, lw * 0.6, col2, th)


def _h_eyepatch(ctx, r, col, col2, lw, lc, th, t):
    rc.line(ctx, -r * 0.98, -r * 0.45, r * 0.98, r * 0.05, lw * 0.8, col, th)
    _ellipse(ctx, r * 0.38, -r * 0.08, r * 0.27, r * 0.24)
    _fill_stroke(ctx, col, None, lw, th)


def _hair_cap(ctx, r, col, lw, lc, th, depth=0.35, k=1.06):
    ctx.new_path()
    ctx.arc(0, 0, r * k, math.pi * 1.0 + 0.05, math.pi * 2.0 - 0.05)
    ctx.curve_to(r * 0.7, -r * depth, -r * 0.7, -r * depth, -r * k, -r * 0.05)
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw * 0.55, th)


def _h_hair_spiky(ctx, r, col, col2, lw, lc, th, t):
    pts = []
    for i in range(9):
        a = math.pi + i * math.pi / 8
        rr = r * (1.45 if i % 2 else 1.02)
        pts.append((rr * math.cos(a), rr * math.sin(a) - r * 0.05))
    pts.append((r * 0.6, -r * 0.45)); pts.append((-r * 0.6, -r * 0.45))
    _poly(ctx, pts)
    _fill_stroke(ctx, col, lc, lw * 0.55, th)


def _h_hair_bun(ctx, r, col, col2, lw, lc, th, t):
    _hair_cap(ctx, r, col, lw, lc, th, 0.45)
    rc.circle(ctx, 0, -r * 1.3, r * 0.42, th, fill=col, stroke=lc, sw=lw * 0.55)
    _hair_cap(ctx, r, col, lw, lc, th, 0.45)
    rc.line(ctx, -r * 0.3, -r * 1.0, r * 0.3, -r * 1.0, lw, col2, th)


def _h_hair_top(ctx, r, col, col2, lw, lc, th, t):
    _hair_cap(ctx, r, col, lw, lc, th, 0.42)


def _h_hair_curly(ctx, r, col, col2, lw, lc, th, t):
    for i in range(9):
        a = math.pi * (0.95 + i * 1.1 / 8)
        rc.circle(ctx, r * 1.0 * math.cos(a), r * 1.0 * math.sin(a), r * 0.36, th, fill=col, stroke=lc, sw=lw * 0.5)
    _hair_cap(ctx, r, col, lw, lc, th, 0.4)


def _h_hair_bob(ctx, r, col, col2, lw, lc, th, t):
    ctx.new_path()
    ctx.arc(0, 0, r * 1.14, math.pi * 0.85, math.pi * 2.15)
    ctx.line_to(r * 0.95, r * 0.1)
    ctx.curve_to(r * 0.7, -r * 0.4, -r * 0.7, -r * 0.4, -r * 0.95, r * 0.1)
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw * 0.55, th)


def _h_mohawk(ctx, r, col, col2, lw, lc, th, t):
    _poly(ctx, [(-r * 0.3, -r * 0.95), (-r * 0.15, -r * 1.75), (r * 0.05, -r * 1.25), (r * 0.2, -r * 1.85),
                (r * 0.3, -r * 1.3), (r * 0.45, -r * 1.6), (r * 0.4, -r * 0.92)])
    _fill_stroke(ctx, col, lc, lw * 0.55, th)


def _h_side_part(ctx, r, col, col2, lw, lc, th, t):
    ctx.new_path()
    ctx.arc(0, 0, r * 1.07, math.pi * 1.0, math.pi * 2.0)
    ctx.curve_to(r * 0.6, -r * 0.6, -r * 0.3, -r * 0.2, -r * 1.07, -r * 0.2)
    ctx.close_path()
    _fill_stroke(ctx, col, lc, lw * 0.55, th)


def _h_bow(ctx, r, col, col2, lw, lc, th, t):
    cx, cy = r * 0.75, -r * 0.85
    for s in (-1, 1):
        _poly(ctx, [(cx, cy), (cx + s * r * 0.45, cy - r * 0.3), (cx + s * r * 0.45, cy + r * 0.3)])
        _fill_stroke(ctx, col, lc, lw * 0.6, th)
    rc.circle(ctx, cx, cy, r * 0.12, th, fill=col, stroke=lc, sw=lw * 0.6)


def _h_glasses(ctx, r, col, col2, lw, lc, th, t):
    for s in (-1, 1):
        rc.circle(ctx, s * r * 0.38, -r * 0.08, r * 0.3, th, stroke=col, sw=lw * 0.8)
    rc.line(ctx, -r * 0.1, -r * 0.1, r * 0.1, -r * 0.1, lw * 0.7, col, th)


def _h_glasses_square(ctx, r, col, col2, lw, lc, th, t):
    for s in (-1, 1):
        rc.rrect(ctx, s * r * 0.38 - r * 0.3, -r * 0.3, r * 0.6, r * 0.42, r * 0.06)
        _fill_stroke(ctx, None, col, lw * 0.9, th)
    rc.line(ctx, -r * 0.08, -r * 0.12, r * 0.08, -r * 0.12, lw * 0.7, col, th)


def _h_sunglasses(ctx, r, col, col2, lw, lc, th, t):
    for s in (-1, 1):
        ctx.new_path()
        ctx.move_to(s * r * 0.06, -r * 0.3)
        ctx.line_to(s * r * 0.7, -r * 0.3)
        ctx.curve_to(s * r * 0.7, r * 0.05, s * r * 0.15, r * 0.12, s * r * 0.06, -r * 0.3)
        ctx.close_path()
        _fill_stroke(ctx, col, lc, lw * 0.6, th)
    rc.line(ctx, -r * 0.1, -r * 0.27, r * 0.1, -r * 0.27, lw * 0.8, lc, th)
    rc.line(ctx, -r * 0.55, -r * 0.24, -r * 0.4, -r * 0.1, lw * 0.6, "#ffffff", th, 0.7)


def _h_monocle(ctx, r, col, col2, lw, lc, th, t):
    rc.circle(ctx, r * 0.38, -r * 0.08, r * 0.32, th, stroke=col, sw=lw)
    rc.line(ctx, r * 0.6, r * 0.15, r * 0.75, r * 0.9, lw * 0.5, col, th)


def _h_beard(ctx, r, col, col2, lw, lc, th, t):
    ctx.new_path()
    ctx.move_to(-r * 0.92, -r * 0.05)
    ctx.curve_to(-r * 0.9, r * 1.2, r * 0.9, r * 1.2, r * 0.92, -r * 0.05)
    ctx.curve_to(r * 0.6, r * 0.75, -r * 0.6, r * 0.75, -r * 0.92, -r * 0.05)
    ctx.close_path()
    _fill_stroke(ctx, col, None, lw, th)


def _h_mustache(ctx, r, col, col2, lw, lc, th, t):
    for s in (-1, 1):
        ctx.new_path()
        ctx.move_to(0, r * 0.28)
        ctx.curve_to(s * r * 0.2, r * 0.18, s * r * 0.45, r * 0.2, s * r * 0.55, r * 0.38)
        ctx.curve_to(s * r * 0.35, r * 0.36, s * r * 0.15, r * 0.4, 0, r * 0.34)
        ctx.close_path()
        _fill_stroke(ctx, col, None, lw, th)


def _h_goatee(ctx, r, col, col2, lw, lc, th, t):
    _poly(ctx, [(-r * 0.18, r * 0.62), (r * 0.18, r * 0.62), (0, r * 0.95)])
    _fill_stroke(ctx, col, None, lw, th)


def _h_halo(ctx, r, col, col2, lw, lc, th, t):
    _ellipse(ctx, 0, -r * 1.45 + math.sin(t * 2) * r * 0.05, r * 0.75, r * 0.18)
    _fill_stroke(ctx, None, col, lw * 1.4, th)


def _h_horns(ctx, r, col, col2, lw, lc, th, t):
    for s in (-1, 1):
        _poly(ctx, [(s * r * 0.35, -r * 0.92), (s * r * 0.75, -r * 1.55), (s * r * 0.7, -r * 0.7)])
        _fill_stroke(ctx, col, lc, lw * 0.6, th)


_HEAD: Dict[str, Callable] = {
    "cap": _h_cap, "beanie": _h_beanie, "top_hat": _h_top_hat, "fedora": _h_fedora, "cowboy_hat": _h_cowboy,
    "hard_hat": _h_hard_hat, "chef_hat": _h_chef, "grad_cap": _h_grad, "crown": _h_crown, "party_hat": _h_party,
    "beret": _h_beret, "straw_hat": _h_straw, "wizard_hat": _h_wizard, "space_helmet": _h_space_helmet,
    "headset": _h_headset, "headphones": _h_headphones, "headband": _h_headband, "nurse_cap": _h_nurse_cap,
    "santa_hat": _h_santa, "mask": _h_mask, "eyepatch": _h_eyepatch, "hair_spiky": _h_hair_spiky,
    "hair_bun": _h_hair_bun, "hair_long": _h_hair_top, "hair_ponytail": _h_hair_top, "hair_curly": _h_hair_curly,
    "hair_bob": _h_hair_bob, "hair_mohawk": _h_mohawk, "hair_side_part": _h_side_part, "bow": _h_bow,
    "glasses": _h_glasses, "glasses_square": _h_glasses_square, "sunglasses": _h_sunglasses, "monocle": _h_monocle,
    "beard": _h_beard, "mustache": _h_mustache, "goatee": _h_goatee, "halo": _h_halo, "horns": _h_horns,
}
# draw order inside the head layer: hair first, then facial hair, eyewear, then hats/helmets on top
_HEAD_ORDER = {k: 0 for k in _HEAD if k.startswith("hair") or k == "bow"}
_HEAD_ORDER.update({"beard": 1, "mustache": 1, "goatee": 1, "mask": 2, "glasses": 3, "glasses_square": 3,
                    "sunglasses": 3, "monocle": 3, "eyepatch": 3, "headset": 6, "headphones": 6, "space_helmet": 9})
HAT_KINDS = {"cap", "beanie", "top_hat", "fedora", "cowboy_hat", "hard_hat", "chef_hat", "grad_cap", "crown",
             "party_hat", "beret", "straw_hat", "wizard_hat", "nurse_cap", "santa_hat"}
ACCESSORY_KINDS = sorted(set(_HEAD) | set(_BODY))


# =========================================================================== faces
def blink_factor(t: float, period: float = 3.7, seed: float = 0.0) -> float:
    """1 = open, ~0.08 = closed. A quick blink every few seconds (never at t=0, so stills stay open-eyed)."""
    ph = (t + seed) % period
    if period - 0.16 < ph:
        return max(0.08, abs((ph - (period - 0.08)) / 0.08))
    return 1.0


def draw_eye(ctx, ex, ey, er, style: str, open_: float, pup: float, look: Tuple[float, float], side: int, theme, color,
             lw: float, wobble: float) -> None:
    if style in ("happy", "closed", "wink") or open_ <= 0.1:
        ctx.new_path()
        if style == "happy":
            ctx.arc(ex, ey + er * 0.35, er * 0.85, math.pi * 1.12, math.pi * 1.88)
        else:
            ctx.move_to(ex - er * 0.9, ey + er * 0.1)
            ctx.curve_to(ex - er * 0.3, ey + er * 0.55, ex + er * 0.3, ey + er * 0.55, ex + er * 0.9, ey + er * 0.1)
        rc.setc(ctx, color, theme); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        return
    if style == "x":
        for d in (-1, 1):
            rc.line(ctx, ex - er * 0.7, ey - d * er * 0.7, ex + er * 0.7, ey + d * er * 0.7, lw, color, theme)
        return
    if style == "heart":
        _heart(ctx, ex, ey, er * 0.95)
        _fill_stroke(ctx, "#f43f5e", None, lw, theme)
        return
    if style == "star":
        _star(ctx, ex, ey, er * 1.05, er * 0.45)
        _fill_stroke(ctx, "#facc15", None, lw, theme)
        return
    if style == "spiral":
        ctx.new_path()
        for i in range(40):
            a = i * 0.45
            rr = er * (0.1 + 0.9 * i / 40)
            (ctx.line_to if i else ctx.move_to)(ex + rr * math.cos(a + wobble * 3), ey + rr * math.sin(a + wobble * 3))
        rc.setc(ctx, color, theme); ctx.set_line_width(lw * 0.7); ctx.stroke()
        return
    if style == "dot":
        rc.circle(ctx, ex + look[0] * er * 0.3, ey + look[1] * er * 0.3, er * 0.32 * max(0.2, open_), theme, fill=color)
        return
    k = 1.25 if style == "wide" else 1.0
    ctx.save()
    ctx.translate(ex, ey)
    rc.safe_scale(ctx, 1.0, open_)
    rc.circle(ctx, 0, 0, er * k, theme, fill="#ffffff", stroke=color, sw=lw * 0.75)
    ctx.restore()
    px = ex + (look[0] * 0.35 + math.sin(wobble) * 0.15) * er
    py = ey + look[1] * 0.35 * er * open_
    rc.circle(ctx, px, py, er * 0.5 * pup * min(1.0, open_ + 0.25), theme, fill="#0f172a")
    if style == "sleepy":  # heavy lid
        ctx.new_path(); ctx.rectangle(ex - er * 1.1, ey - er * 1.1, er * 2.2, er * 0.95)
        rc.setc(ctx, theme.get("_skin", "#0f172a"), theme); ctx.fill()
        rc.line(ctx, ex - er, ey - er * 0.15, ex + er, ey - er * 0.15, lw * 0.75, color, theme)


def draw_face_ext(ctx, cx, cy, r, expr: Dict[str, Any], mouth: Any, t: float, theme, color, skin: str = "#0f172a") -> None:
    eyes = expr.get("eyes", {}) or {}
    brows = expr.get("brows", {}) or {}
    style = eyes.get("style", "round")
    open_ = rc.clamp(eyes.get("open", 0.8), 0.05, 1.0)
    if style in ("round", "wide", "dot", "sleepy") and expr.get("blink", True):
        open_ = min(open_, open_ * blink_factor(t))
    pup = eyes.get("pupil_scale", 1.0)
    look = tuple((eyes.get("look") or [0, 0])[:2]) if isinstance(eyes.get("look"), (list, tuple)) else (0, 0)
    lw = max(1.5, r * 0.08)
    th = {**theme, "_skin": skin}
    for side, sx in (("l", -1), ("r", 1)):
        ex, ey = cx + sx * r * 0.38, cy - r * 0.08
        er = r * 0.2
        st = style
        if style == "wink_l":
            st = "wink" if side == "l" else "round"
        elif style == "wink_r":
            st = "wink" if side == "r" else "round"
        draw_eye(ctx, ex, ey, er, st, open_, pup, look, sx, th, color, lw, t)
        if brows.get("hidden"):
            continue
        ang = math.radians(brows.get(f"{side}_angle", 0)) * -sx
        bx0, bx1 = ex - er * 1.1, ex + er * 1.1
        by = ey - er * 1.6 - brows.get("raise", 0.0) * r
        bw = lw * (1.6 if brows.get("thick") else 1.0)
        rc.line(ctx, bx0, by + math.sin(ang) * er * 1.1, bx1, by - math.sin(ang) * er * 1.1, bw, color, theme)
    for ex_ in expr.get("extras", []) or []:
        _face_extra(ctx, ex_, cx, cy, r, t, theme, color)
    draw_mouth_ext(ctx, cx, cy + r * 0.45, r, mouth, theme, color)


def _face_extra(ctx, kind: str, cx, cy, r, t, theme, color) -> None:
    if kind == "blush":
        for s in (-1, 1):
            _ellipse(ctx, cx + s * r * 0.55, cy + r * 0.28, r * 0.18, r * 0.09)
            rc.setc(ctx, "#fb7185", theme, 0.55); ctx.fill()
    elif kind in ("tear", "tears"):
        for s in ((1,) if kind == "tear" else (-1, 1)):
            y = cy + r * 0.15 + ((t * 0.9) % 1.0) * r * 0.5
            _drop(ctx, cx + s * r * 0.45, y, r * 0.1)
            rc.setc(ctx, "#7dd3fc", theme); ctx.fill()
    elif kind == "sweat":
        y = cy - r * 0.55 + ((t * 0.6) % 1.0) * r * 0.25
        _drop(ctx, cx + r * 0.85, y, r * 0.16)
        rc.setc(ctx, "#7dd3fc", theme); ctx.fill()
    elif kind == "anger":
        x0, y0, s = cx + r * 0.55, cy - r * 0.75, r * 0.14
        for a in range(4):
            ang = a * math.pi / 2 + math.pi / 4
            rc.line(ctx, x0 + math.cos(ang) * s * 0.4, y0 + math.sin(ang) * s * 0.4,
                    x0 + math.cos(ang) * s * 1.3, y0 + math.sin(ang) * s * 1.3, max(1.5, r * 0.07), "#ef4444", theme)
    elif kind == "sparkle":
        a = 0.6 + 0.4 * math.sin(t * 6)
        _star(ctx, cx - r * 0.8, cy - r * 0.75, r * 0.16 * a, r * 0.05, 4)
        rc.setc(ctx, "#fde047", theme); ctx.fill()
    elif kind == "shadow":  # gloom over the upper face
        ctx.new_path(); ctx.arc(cx, cy, r * 0.95, math.pi, 2 * math.pi)
        rc.setc(ctx, "#6366f1", theme, 0.3); ctx.fill()
        for i in range(4):
            x = cx - r * 0.45 + i * r * 0.3
            rc.line(ctx, x, cy - r * 0.85, x, cy - r * 0.5, max(1, r * 0.04), "#6366f1", theme, 0.8)
    elif kind == "freckles":
        for s in (-1, 1):
            for i in range(3):
                rc.circle(ctx, cx + s * (r * 0.42 + i * r * 0.1), cy + r * 0.22 + (i % 2) * r * 0.06, r * 0.025, theme, fill="#f59e0b")


MOUTH_SHAPES = ["flat", "smile", "big_smile", "grin", "frown", "sad_open", "o", "open_small", "tongue_out", "smirk_right",
                "smirk_left", "cat", "zigzag", "laugh", "scream", "grit", "wobble", "kiss", "line_small", "teeth_smile"]


def draw_mouth_ext(ctx, cx, cy, r, shape: Any, theme, color) -> None:
    if isinstance(shape, dict) or shape in ("smirk_right", "open_small", "wobble", "grit", "flat", None):
        rc.draw_mouth(ctx, cx, cy, r, shape if shape else "flat", theme, color)
        return
    lw = max(1.5, r * 0.09)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    rc.setc(ctx, color, theme)
    ctx.set_line_width(lw)
    ctx.new_path()
    if shape == "smile":
        ctx.arc(cx, cy - r * 0.2, r * 0.32, math.pi * 0.2, math.pi * 0.8); ctx.stroke()
    elif shape == "line_small":
        rc.line(ctx, cx - r * 0.14, cy, cx + r * 0.14, cy, lw, color, theme)
    elif shape in ("big_smile", "laugh", "teeth_smile"):
        y0 = cy - r * (0.08 if shape != "laugh" else 0.12)
        w = r * (0.38 if shape != "laugh" else 0.42)
        ctx.move_to(cx - w, y0)
        ctx.curve_to(cx - w, y0 + r * 0.55, cx + w, y0 + r * 0.55, cx + w, y0)
        ctx.close_path()
        rc.setc(ctx, "#ffffff" if shape == "teeth_smile" else "#7f1d1d", theme); ctx.fill_preserve()
        rc.setc(ctx, color, theme); ctx.stroke()
        if shape != "teeth_smile":
            _ellipse(ctx, cx, y0 + r * 0.3, w * 0.5, r * 0.08)
            rc.setc(ctx, "#fb7185", theme); ctx.fill()
            ctx.rectangle(cx - w * 0.75, y0 + lw * 0.5, w * 1.5, r * 0.09)
            rc.setc(ctx, "#ffffff", theme); ctx.fill()
    elif shape == "grin":
        rc.rrect(ctx, cx - r * 0.4, cy - r * 0.12, r * 0.8, r * 0.26, r * 0.12)
        rc.setc(ctx, "#ffffff", theme); ctx.fill_preserve(); rc.setc(ctx, color, theme); ctx.stroke()
        for i in (-1, 0, 1):
            rc.line(ctx, cx + i * r * 0.14, cy - r * 0.12, cx + i * r * 0.14, cy + r * 0.14, lw * 0.5, color, theme)
        rc.line(ctx, cx - r * 0.4, cy + r * 0.01, cx + r * 0.4, cy + r * 0.01, lw * 0.5, color, theme)
    elif shape == "frown":
        ctx.arc(cx, cy + r * 0.32, r * 0.3, math.pi * 1.2, math.pi * 1.8); ctx.stroke()
    elif shape == "sad_open":
        ctx.move_to(cx - r * 0.3, cy + r * 0.15)
        ctx.curve_to(cx - r * 0.3, cy - r * 0.22, cx + r * 0.3, cy - r * 0.22, cx + r * 0.3, cy + r * 0.15)
        ctx.close_path()
        rc.setc(ctx, "#7f1d1d", theme); ctx.fill_preserve(); rc.setc(ctx, color, theme); ctx.stroke()
    elif shape in ("o", "scream", "kiss"):
        rx, ry = {"o": (0.17, 0.2), "scream": (0.22, 0.38), "kiss": (0.09, 0.09)}[shape]
        _ellipse(ctx, cx + (r * 0.05 if shape == "kiss" else 0), cy + (r * 0.08 if shape == "scream" else 0), r * rx, r * ry)
        rc.setc(ctx, "#7f1d1d" if shape != "kiss" else color, theme); ctx.fill_preserve()
        rc.setc(ctx, color, theme); ctx.set_line_width(lw); ctx.stroke()
    elif shape == "tongue_out":
        ctx.arc(cx, cy - r * 0.2, r * 0.3, math.pi * 0.15, math.pi * 0.85); ctx.stroke()
        _ellipse(ctx, cx + r * 0.08, cy + r * 0.16, r * 0.11, r * 0.14)
        rc.setc(ctx, "#fb7185", theme); ctx.fill_preserve(); rc.setc(ctx, color, theme); ctx.set_line_width(lw * 0.6); ctx.stroke()
    elif shape == "smirk_left":
        ctx.move_to(cx + r * 0.3, cy)
        ctx.curve_to(cx, cy + r * 0.05, cx - r * 0.2, cy, cx - r * 0.4, cy - r * 0.18); ctx.stroke()
    elif shape == "cat":
        for s in (-1, 1):
            ctx.new_path(); ctx.arc(cx + s * r * 0.13, cy - r * 0.02, r * 0.13, math.pi * 0.05, math.pi * 0.95); ctx.stroke()
    elif shape == "zigzag":
        ctx.move_to(cx - r * 0.35, cy)
        for i in range(1, 6):
            ctx.line_to(cx - r * 0.35 + i * r * 0.14, cy + (r * 0.08 if i % 2 else -r * 0.08))
        ctx.stroke()
    else:
        rc.draw_mouth(ctx, cx, cy, r, "flat", theme, color)


# =========================================================================== widgets
def draw_widget_ext(ctx, wj: Dict[str, Any], x, y, w, h, theme, t: float) -> bool:
    kind = wj.get("type")
    fn = _WIDGETS.get(kind)
    if not fn:
        return False
    fn(ctx, wj.get("data", {}) or {}, wj.get("style", {}) or {}, x, y, w, h, theme, t)
    return True


def _num(v: float, decimals: int = 0) -> str:
    if decimals:
        return f"{v:,.{decimals}f}"
    return f"{int(round(v)):,}"


def _w_counter(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    p = rc.ease("expo_out", rc.clamp(t / float(d.get("duration_sec", 1.4))))
    v = float(d.get("from", 0)) + (float(d.get("to", 100)) - float(d.get("from", 0))) * p
    s = f"{d.get('prefix', '')}{_num(v, int(d.get('decimals', 0)))}{d.get('suffix', '')}"
    pop = 1.0 + 0.08 * math.sin(math.pi * rc.clamp((t - 1.3) / 0.25)) if t > 1.3 else 1.0
    ctx.save(); ctx.translate(x + w / 2, y + h * 0.58); rc.safe_scale(ctx, pop, pop)
    text_c(ctx, s, 0, 0, th, st.get("color", "theme.highlight"), w * 0.9, h * 0.42)
    ctx.restore()
    text_c(ctx, d.get("label", ""), x + w / 2, y + h * 0.86, th, "theme.text", w * 0.9, h * 0.13, "DejaVu Sans")
    if d.get("title"):
        text_c(ctx, d["title"], x + w / 2, y + h * 0.2, th, "theme.accent", w * 0.9, h * 0.13)


def _w_progress(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    items = d.get("items") or [{"label": d.get("label", ""), "value": d.get("value", 70)}]
    items = items[:4]
    n = len(items)
    text_c(ctx, d.get("title", ""), x + w / 2, y + h * 0.18, th, "theme.text", w * 0.9, h * 0.12)
    for i, it in enumerate(items):
        top = y + h * (0.3 + 0.62 * i / n)
        bh = h * 0.62 / n
        p = rc.ease("expo_out", rc.clamp((t - i * 0.15) / 0.9))
        val = float(it.get("value", 50))
        rc.set_font(ctx, "DejaVu Sans Bold", min(bh * 0.3, h * 0.1))
        rc.draw_text(ctx, str(it.get("label", ""))[:24], x + w * 0.06, top + bh * 0.32, th, "theme.text")
        s = f"{int(val * p)}%"
        rc.draw_text(ctx, s, x + w * 0.94 - rc.text_width(ctx, s), top + bh * 0.32, th, "theme.highlight")
        rc.rrect(ctx, x + w * 0.06, top + bh * 0.45, w * 0.88, bh * 0.32, bh * 0.16)
        rc.setc(ctx, "theme.bg", th, 0.8); ctx.fill()
        if val * p > 0.5:
            rc.rrect(ctx, x + w * 0.06, top + bh * 0.45, w * 0.88 * val / 100.0 * p, bh * 0.32, bh * 0.16)
            rc.setc(ctx, it.get("color", "theme.accent" if i % 2 == 0 else "theme.accent2"), th); ctx.fill()


def _w_donut(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    val = float(d.get("value", 75))
    p = rc.ease("expo_out", rc.clamp(t / 1.1))
    cx, cy, R = x + w * 0.3, y + h * 0.52, min(w * 0.22, h * 0.36)
    ctx.set_line_width(R * 0.32)
    ctx.new_path(); ctx.arc(cx, cy, R, 0, 2 * math.pi); rc.setc(ctx, "theme.bg", th, 0.8); ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if val * p > 0.5:
        ctx.new_path(); ctx.arc(cx, cy, R, -math.pi / 2, -math.pi / 2 + 2 * math.pi * val / 100 * p)
        rc.setc(ctx, st.get("color", "theme.accent"), th); ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    text_c(ctx, f"{int(val * p)}%", cx, cy + R * 0.18, th, "theme.text", R * 1.2, R * 0.5)
    rc.set_font(ctx, "DejaVu Sans Bold", h * 0.12)
    lines = wrap_lines(ctx, d.get("label", d.get("title", "")), w * 0.42, 3)
    for i, ln in enumerate(lines):
        rc.draw_text(ctx, ln, x + w * 0.55, y + h * (0.42 + 0.15 * i), th, "theme.text", alpha=rc.clamp(t / 0.4))


def _w_pie(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    vals = [max(0.0, float(v)) for v in (d.get("values") or [50, 30, 20])][:6]
    labels = (d.get("labels") or [])[:6]
    tot = sum(vals) or 1.0
    cols = ["theme.accent", "theme.accent2", "theme.highlight", "theme.danger", "#a78bfa", "#34d399"]
    cx, cy, R = x + w * 0.28, y + h * 0.52, min(w * 0.22, h * 0.38)
    p = rc.ease("expo_out", rc.clamp(t / 1.0))
    a0 = -math.pi / 2
    for i, v in enumerate(vals):
        a1 = a0 + 2 * math.pi * v / tot * p
        ctx.new_path(); ctx.move_to(cx, cy); ctx.arc(cx, cy, R, a0, a1); ctx.close_path()
        rc.setc(ctx, cols[i % 6], th); ctx.fill_preserve()
        rc.setc(ctx, "theme.surface", th); ctx.set_line_width(max(1.5, R * 0.03)); ctx.stroke()
        a0 = a1
    for i, v in enumerate(vals):
        yy = y + h * (0.25 + 0.6 * i / max(1, len(vals)))
        rc.rrect(ctx, x + w * 0.56, yy - h * 0.06, h * 0.07, h * 0.07, h * 0.015)
        rc.setc(ctx, cols[i % 6], th); ctx.fill()
        lab = f"{labels[i] if i < len(labels) else ''} {int(round(100 * v / tot))}%".strip()
        rc.set_font(ctx, "DejaVu Sans Bold", h * 0.08)
        fit_font(ctx, lab, w * 0.32, h * 0.08)
        rc.draw_text(ctx, lab, x + w * 0.56 + h * 0.1, yy, th, "theme.text", alpha=rc.clamp((t - 0.2 * i) / 0.3))


def _w_line(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    vals = [float(v) for v in (d.get("values") or [2, 3, 2.5, 5, 4, 8])][:12]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    gx, gy, gw, gh = x + w * 0.08, y + h * 0.25, w * 0.84, h * 0.6
    text_c(ctx, d.get("title", ""), x + w / 2, y + h * 0.17, th, "theme.text", w * 0.9, h * 0.1)
    for i in range(4):
        yy = gy + gh * i / 3
        rc.line(ctx, gx, yy, gx + gw, yy, 1, "theme.line", th, 0.15)
    p = rc.clamp(t / 1.2)
    n = len(vals)
    pts = [(gx + gw * i / max(1, n - 1), gy + gh * (1 - (v - lo) / span)) for i, v in enumerate(vals)]
    upto = p * (n - 1)
    ctx.new_path()
    for i, (px, py) in enumerate(pts):
        if i > upto + 1e-6:
            fx = upto - (i - 1)
            ax, ay = pts[i - 1]
            ctx.line_to(ax + (px - ax) * fx, ay + (py - ay) * fx)
            break
        (ctx.line_to if i else ctx.move_to)(px, py)
    up = vals[-1] >= vals[0]
    col = st.get("color", "#34d399" if up else "theme.danger")
    rc.setc(ctx, col, th); ctx.set_line_width(max(2, h * 0.025)); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    k = min(n - 1, int(upto))
    hx, hy = pts[k]
    if p >= 1.0:
        hx, hy = pts[-1]
        rc.circle(ctx, hx, hy, h * 0.03 * (1 + 0.25 * math.sin(t * 6)), th, fill=col)
        if d.get("end_label"):
            text_c(ctx, d["end_label"], min(hx, x + w * 0.8), hy - h * 0.06, th, col, w * 0.35, h * 0.09)


def _w_checklist(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    items = (d.get("items") or ["Step one", "Step two", "Step three"])[:5]
    checked = d.get("checked", [True] * len(items))
    n = len(items)
    title = d.get("title")
    top = y + h * (0.24 if title else 0.08)
    if title:
        text_c(ctx, title, x + w / 2, y + h * 0.17, th, "theme.highlight", w * 0.9, h * 0.11)
    rowh = (y + h * 0.96 - top) / n
    for i, it in enumerate(items):
        a = rc.clamp((t - 0.25 * i) / 0.25)
        cy = top + rowh * (i + 0.5)
        bx = x + w * 0.07
        bs = min(rowh * 0.55, h * 0.12)
        rc.rrect(ctx, bx, cy - bs / 2, bs, bs, bs * 0.2)
        rc.setc(ctx, "theme.line", th, 0.9 * a); ctx.set_line_width(max(1.5, bs * 0.1)); ctx.stroke()
        ok = checked[i] if i < len(checked) else True
        c = rc.clamp((t - 0.25 * i - 0.2) / 0.2)
        if c > 0:
            ctx.new_path()
            if ok:
                ctx.move_to(bx + bs * 0.2, cy)
                ctx.line_to(bx + bs * 0.2 + bs * 0.25 * c, cy + bs * 0.25 * c)
                if c > 0.5:
                    ctx.line_to(bx + bs * 0.45 + bs * 0.4 * (c - 0.5) * 2, cy + bs * 0.25 - bs * 0.55 * (c - 0.5) * 2)
                rc.setc(ctx, "#34d399", th)
            else:
                ctx.move_to(bx + bs * 0.25, cy - bs * 0.25); ctx.line_to(bx + bs * 0.75, cy + bs * 0.25)
                ctx.move_to(bx + bs * 0.75, cy - bs * 0.25); ctx.line_to(bx + bs * 0.25, cy + bs * 0.25)
                rc.setc(ctx, "theme.danger", th, c)
            ctx.set_line_width(max(2, bs * 0.16)); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        rc.set_font(ctx, "DejaVu Sans Bold", min(rowh * 0.4, h * 0.1))
        fit_font(ctx, str(it), w * 0.75, min(rowh * 0.4, h * 0.1))
        rc.draw_text(ctx, str(it), bx + bs * 1.5, cy + rowh * 0.13, th, "theme.text", alpha=a)


def _w_timeline(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    ev = (d.get("events") or [{"label": "Start", "year": "2020"}, {"label": "Now", "year": "2026"}])[:5]
    n = len(ev)
    ly = y + h * 0.5
    p = rc.ease("ease_in_out", rc.clamp(t / 1.2))
    x0, x1 = x + w * 0.08, x + w * 0.92
    rc.line(ctx, x0, ly, x0 + (x1 - x0) * p, ly, max(2, h * 0.02), "theme.line", th, 0.8)
    for i, e in enumerate(ev):
        fx = i / max(1, n - 1)
        px = x0 + (x1 - x0) * fx
        if p + 1e-6 < fx:
            continue
        pop = rc.clamp(rc.spring_step(t - fx * 1.2, 300, 16), 0, 1.3)
        rc.circle(ctx, px, ly, h * 0.05 * pop, th, fill="theme.accent" if i < n - 1 else "theme.highlight", stroke="theme.surface", sw=2)
        up = i % 2 == 0
        text_c(ctx, e.get("year", ""), px, ly + (-h * 0.12 if up else h * 0.2), th, "theme.highlight", w / n * 1.1, h * 0.12)
        text_c(ctx, e.get("label", ""), px, ly + (-h * 0.26 if up else h * 0.34), th, "theme.text", w / n * 1.15, h * 0.09,
               "DejaVu Sans")


def _w_steps(ctx, d, st, x, y, w, h, th, t):
    steps = (d.get("steps") or ["Plan", "Build", "Ship"])[:4]
    n = len(steps)
    gap = w * 0.06
    bw = (w - gap * (n - 1)) / n
    for i, s in enumerate(steps):
        a = rc.ease("expo_out", rc.clamp((t - 0.3 * i) / 0.4))
        bx = x + i * (bw + gap)
        ctx.save(); ctx.translate(bx + bw / 2, y + h / 2); rc.safe_scale(ctx, 0.7 + 0.3 * a, 0.7 + 0.3 * a)
        rc.draw_card(ctx, -bw / 2, -h * 0.4, bw, h * 0.8, th, 0.95 * a)
        rc.circle(ctx, 0, -h * 0.17, h * 0.12, th, fill="theme.accent" if i < n - 1 else "theme.highlight")
        text_c(ctx, str(i + 1), 0, -h * 0.11, th, "theme.bg", h * 0.2, h * 0.15, alpha=a)
        text_c(ctx, s, 0, h * 0.2, th, "theme.text", bw * 0.88, h * 0.13, alpha=a)
        ctx.restore()
        if i < n - 1 and a > 0.6:
            ax = bx + bw + gap * 0.15
            rc.line(ctx, ax, y + h / 2, ax + gap * 0.7, y + h / 2, max(2, h * 0.03), "theme.highlight", th)
            _poly(ctx, [(ax + gap * 0.75, y + h / 2), (ax + gap * 0.45, y + h / 2 - h * 0.05), (ax + gap * 0.45, y + h / 2 + h * 0.05)])
            rc.setc(ctx, "theme.highlight", th); ctx.fill()


def _w_versus(ctx, d, st, x, y, w, h, th, t):
    L, R = d.get("left", {"title": "A"}), d.get("right", {"title": "B"})
    for i, side in enumerate((L, R)):
        a = rc.ease("expo_out", rc.clamp((t - 0.1 * i) / 0.45))
        cw = w * 0.42
        cx = x + (0 if i == 0 else w - cw) + (1 - a) * (-1 if i == 0 else 1) * w * 0.3
        rc.draw_card(ctx, cx, y, cw, h, th, 0.95 * a)
        text_c(ctx, side.get("title", ""), cx + cw / 2, y + h * 0.3, th, "theme.highlight" if i == 0 else "theme.accent2",
               cw * 0.88, h * 0.16, alpha=a)
        if side.get("value") is not None:
            text_c(ctx, str(side.get("value")), cx + cw / 2, y + h * 0.62, th, "theme.text", cw * 0.88, h * 0.22, alpha=a)
        if side.get("caption"):
            text_c(ctx, side["caption"], cx + cw / 2, y + h * 0.85, th, "theme.text", cw * 0.88, h * 0.1, "DejaVu Sans", alpha=a)
    pop = rc.clamp(rc.spring_step(t - 0.35, 320, 14), 0, 1.4)
    if pop > 0.01:
        ctx.save(); ctx.translate(x + w / 2, y + h / 2); rc.safe_scale(ctx, pop, pop)
        rc.circle(ctx, 0, 0, h * 0.17, th, fill="theme.danger", stroke="theme.surface", sw=3)
        text_c(ctx, "VS", 0, h * 0.06, th, "#ffffff", h * 0.26, h * 0.15)
        ctx.restore()


def _w_ranking(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    items = (d.get("items") or ["First", "Second", "Third"])[:5]
    n = len(items)
    title = d.get("title")
    top = y + h * (0.24 if title else 0.08)
    if title:
        text_c(ctx, title, x + w / 2, y + h * 0.17, th, "theme.highlight", w * 0.9, h * 0.11)
    rowh = (y + h * 0.95 - top) / n
    medal = ["#facc15", "#cbd5e1", "#d97706", "theme.accent", "theme.accent"]
    for i, it in enumerate(items):
        k = n - 1 - i  # reveal from the bottom up, winner last
        a = rc.ease("expo_out", rc.clamp((t - 0.22 * k) / 0.35))
        cy = top + rowh * (i + 0.5)
        dx = (1 - a) * w * 0.25
        rc.circle(ctx, x + w * 0.12 + dx, cy, min(rowh * 0.32, h * 0.08), th, fill=medal[i])
        text_c(ctx, str(i + 1), x + w * 0.12 + dx, cy + rowh * 0.11, th, "#0f172a", rowh * 0.5, min(rowh * 0.34, h * 0.09), alpha=a)
        rc.set_font(ctx, "DejaVu Sans Bold", min(rowh * 0.38, h * 0.1))
        fit_font(ctx, str(it), w * 0.7, min(rowh * 0.38, h * 0.1))
        rc.draw_text(ctx, str(it), x + w * 0.22 + dx, cy + rowh * 0.13, th, "theme.text", alpha=a)


def _w_stat(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    a = rc.ease("expo_out", rc.clamp(t / 0.5))
    text_c(ctx, d.get("label", d.get("title", "")), x + w / 2, y + h * 0.25, th, "theme.text", w * 0.9, h * 0.12, "DejaVu Sans", alpha=a)
    pop = rc.clamp(rc.spring_step(t - 0.15, 260, 13), 0, 1.3)
    ctx.save(); ctx.translate(x + w / 2, y + h * 0.62); rc.safe_scale(ctx, pop, pop)
    text_c(ctx, d.get("value", "42"), 0, 0, th, st.get("color", "theme.highlight"), w * 0.85, h * 0.38)
    ctx.restore()
    delta = d.get("delta")
    if delta:
        up = not str(delta).startswith("-")
        col = "#34d399" if up else "theme.danger"
        cx, cy = x + w / 2, y + h * 0.84
        s = ("▲ " if up else "▼ ") + str(delta).lstrip("+-")
        text_c(ctx, s, cx, cy, th, col, w * 0.8, h * 0.1, alpha=rc.clamp((t - 0.6) / 0.3))


def _w_quote(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    a = rc.clamp(t / 0.5)
    rc.set_font(ctx, "DejaVu Serif Bold", h * 0.45)
    rc.draw_text(ctx, "“", x + w * 0.04, y + h * 0.45, th, "theme.accent", alpha=a)
    size = h * 0.13
    rc.set_font(ctx, "DejaVu Sans Bold", size)
    lines = wrap_lines(ctx, d.get("text", d.get("title", "")), w * 0.78, 3)
    for i, ln in enumerate(lines):
        rc.draw_text(ctx, ln, x + w * 0.14, y + h * (0.32 + 0.17 * i), th, "theme.text", alpha=rc.clamp((t - 0.15 * i) / 0.4))
    if d.get("author"):
        rc.set_font(ctx, "DejaVu Sans", h * 0.09)
        s = "— " + str(d["author"])
        rc.draw_text(ctx, s, x + w * 0.92 - rc.text_width(ctx, s), y + h * 0.9, th, "theme.highlight", alpha=rc.clamp((t - 0.5) / 0.4))


def _w_gauge(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    val = rc.clamp(float(d.get("value", 70)) / 100.0)
    cx, cy, R = x + w / 2, y + h * 0.78, min(w * 0.36, h * 0.6)
    segs = [("#34d399", 0.0, 0.5), ("#facc15", 0.5, 0.8), ("theme.danger", 0.8, 1.0)]
    ctx.set_line_width(R * 0.18)
    for col, a0, a1 in segs:
        ctx.new_path(); ctx.arc(cx, cy, R, math.pi * (1 + a0), math.pi * (1 + a1)); rc.setc(ctx, col, th); ctx.stroke()
    p = rc.spring_step(t, 120, 9) * val
    ang = math.pi * (1 + p)
    rc.line(ctx, cx, cy, cx + math.cos(ang) * R * 0.85, cy + math.sin(ang) * R * 0.85, max(3, R * 0.06), "theme.text", th)
    rc.circle(ctx, cx, cy, R * 0.08, th, fill="theme.text")
    text_c(ctx, d.get("label", ""), cx, y + h * 0.22, th, "theme.text", w * 0.9, h * 0.12)


def _w_countdown(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    start = int(d.get("from", 10))
    left = max(0, start - int(t * float(d.get("speed", 4))))
    s = f"00:{left:02d}"
    tick = (t * float(d.get("speed", 4))) % 1.0
    sc = 1.0 + 0.1 * (1 - tick)
    ctx.save(); ctx.translate(x + w / 2, y + h * 0.62); rc.safe_scale(ctx, sc, sc)
    text_c(ctx, s, 0, 0, th, "theme.danger" if left <= 3 else "theme.highlight", w * 0.8, h * 0.42, "DejaVu Sans Mono Bold")
    ctx.restore()
    text_c(ctx, d.get("label", ""), x + w / 2, y + h * 0.2, th, "theme.text", w * 0.9, h * 0.12)


def _w_calendar(ctx, d, st, x, y, w, h, th, t):
    cw, ch = min(w * 0.5, h * 0.95), h
    cx = x + (w - cw) / 2
    a = rc.ease("expo_out", rc.clamp(t / 0.5))
    ctx.save(); ctx.translate(cx + cw / 2, y + ch / 2); rc.safe_scale(ctx, 0.8 + 0.2 * a, 0.8 + 0.2 * a); ctx.translate(-cw / 2, -ch / 2)
    rc.rrect(ctx, 0, 0, cw, ch, cw * 0.08); rc.setc(ctx, "#ffffff", th); ctx.fill()
    rc.rrect(ctx, 0, 0, cw, ch * 0.28, cw * 0.08); rc.setc(ctx, "theme.danger", th); ctx.fill()
    ctx.rectangle(0, ch * 0.18, cw, ch * 0.1); ctx.fill()
    text_c(ctx, d.get("month", "JAN"), cw / 2, ch * 0.2, th, "#ffffff", cw * 0.85, ch * 0.14)
    text_c(ctx, str(d.get("day", 1)), cw / 2, ch * 0.78, th, "#0f172a", cw * 0.85, ch * 0.45)
    ctx.restore()
    if d.get("label"):
        text_c(ctx, d["label"], x + w / 2, y + h + h * 0.14, th, "theme.text", w, h * 0.12)


def _w_price(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    old, new = d.get("old", "$99"), d.get("new", "$49")
    text_c(ctx, d.get("label", ""), x + w / 2, y + h * 0.22, th, "theme.text", w * 0.9, h * 0.12)
    size = text_c(ctx, old, x + w * 0.3, y + h * 0.65, th, "theme.line", w * 0.35, h * 0.24)
    s = rc.clamp((t - 0.4) / 0.3)
    rc.set_font(ctx, "DejaVu Sans Bold", size)
    ow = rc.text_width(ctx, old)
    if s > 0:
        rc.line(ctx, x + w * 0.3 - ow / 2, y + h * 0.58, x + w * 0.3 - ow / 2 + ow * s, y + h * 0.58, max(2, h * 0.03), "theme.danger", th)
    pop = rc.clamp(rc.spring_step(t - 0.7, 280, 13), 0, 1.3)
    if pop > 0.01:
        ctx.save(); ctx.translate(x + w * 0.7, y + h * 0.65); rc.safe_scale(ctx, pop, pop)
        text_c(ctx, new, 0, 0, th, "#34d399", w * 0.4, h * 0.36)
        ctx.restore()


def _w_equation(ctx, d, st, x, y, w, h, th, t):
    parts = d.get("parts") or ["A", "+", "B", "=", "C"]
    n = len(parts)
    cw = w / n
    for i, p_ in enumerate(parts):
        a = rc.clamp(rc.spring_step(t - 0.22 * i, 300, 15), 0, 1.25)
        if a <= 0.01:
            continue
        cx = x + cw * (i + 0.5)
        op = p_ in ("+", "-", "=", "×", "÷", "→", ">", "<")
        ctx.save(); ctx.translate(cx, y + h / 2); rc.safe_scale(ctx, a, a)
        if not op:
            rc.draw_card(ctx, -cw * 0.46, -h * 0.4, cw * 0.92, h * 0.8, th)
        text_c(ctx, p_, 0, h * 0.1, th, "theme.highlight" if op else ("theme.accent" if i == n - 1 else "theme.text"),
               cw * 0.8, h * (0.42 if op else 0.24))
        ctx.restore()


def _w_map(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    pins = (d.get("pins") or [{"x": 0.3, "y": 0.5, "label": "A"}, {"x": 0.72, "y": 0.4, "label": "B"}])[:4]
    # stylised land masses
    for bx, by, rx, ry in ((0.3, 0.55, 0.2, 0.28), (0.7, 0.45, 0.22, 0.25), (0.52, 0.8, 0.1, 0.08)):
        _ellipse(ctx, x + w * bx, y + h * by, w * rx, h * ry)
        rc.setc(ctx, "theme.accent", th, 0.25); ctx.fill()
    pts = []
    for i, p in enumerate(pins):
        px, py = x + w * float(p.get("x", 0.5)), y + h * float(p.get("y", 0.5))
        pts.append((px, py))
        a = rc.clamp(rc.spring_step(t - 0.3 * i, 300, 14), 0, 1.3)
        ctx.save(); ctx.translate(px, py); rc.safe_scale(ctx, a, a)
        _drop(ctx, 0, -h * 0.07, h * 0.08)
        rc.setc(ctx, "theme.danger", th); ctx.fill()
        rc.circle(ctx, 0, -h * 0.085, h * 0.025, th, fill="#ffffff")
        ctx.restore()
        if p.get("label") and a > 0.3:
            text_c(ctx, p["label"], px, py + h * 0.1, th, "theme.text", w * 0.3, h * 0.08)
    if len(pts) >= 2 and d.get("route", True):
        p = rc.clamp((t - 0.6) / 0.8)
        ctx.set_dash([h * 0.03, h * 0.025])
        (ax, ay), (bx, by) = pts[0], pts[1]
        ctx.new_path(); ctx.move_to(ax, ay)
        mx, my = (ax + bx) / 2, min(ay, by) - h * 0.2
        steps = int(24 * p)
        for i in range(1, steps + 1):
            u = i / 24
            qx = (1 - u) ** 2 * ax + 2 * (1 - u) * u * mx + u * u * bx
            qy = (1 - u) ** 2 * ay + 2 * (1 - u) * u * my + u * u * by
            ctx.line_to(qx, qy)
        rc.setc(ctx, "theme.highlight", th); ctx.set_line_width(max(2, h * 0.015)); ctx.stroke()
        ctx.set_dash([])


def _w_battery(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    val = rc.clamp(float(d.get("value", 20)) / 100.0)
    bx, by, bw, bh = x + w * 0.15, y + h * 0.35, w * 0.62, h * 0.45
    rc.rrect(ctx, bx, by, bw, bh, bh * 0.15)
    rc.setc(ctx, "theme.text", th); ctx.set_line_width(max(2, h * 0.03)); ctx.stroke()
    ctx.rectangle(bx + bw, by + bh * 0.3, w * 0.04, bh * 0.4); ctx.fill()
    drain = d.get("drain", False)
    p = rc.ease("ease_in_out", rc.clamp(t / 1.4))
    lvl = (1 - p * (1 - val)) if drain else val * p
    col = "theme.danger" if lvl < 0.25 else ("#facc15" if lvl < 0.55 else "#34d399")
    if lvl > 0.01:
        rc.rrect(ctx, bx + bw * 0.04, by + bh * 0.12, (bw * 0.92) * lvl, bh * 0.76, bh * 0.08)
        rc.setc(ctx, col, th); ctx.fill()
    text_c(ctx, d.get("label", f"{int(lvl * 100)}%"), x + w / 2, y + h * 0.24, th, "theme.text", w * 0.9, h * 0.12)


def _w_scale(ctx, d, st, x, y, w, h, th, t):
    rc.draw_card(ctx, x, y, w, h, th)
    tilt = math.radians(float(d.get("tilt_deg", 12))) * rc.spring_step(t - 0.3, 90, 7)
    cx, cy = x + w / 2, y + h * 0.35
    rc.line(ctx, cx, cy, cx, y + h * 0.88, max(3, h * 0.035), "theme.line", th)
    rc.line(ctx, cx - w * 0.12, y + h * 0.88, cx + w * 0.12, y + h * 0.88, max(3, h * 0.035), "theme.line", th)
    L = w * 0.36
    ax, ay = cx - L * math.cos(tilt), cy - L * math.sin(tilt)
    bx, by = cx + L * math.cos(tilt), cy + L * math.sin(tilt)
    rc.line(ctx, ax, ay, bx, by, max(3, h * 0.03), "theme.line", th)
    for i, (px, py) in enumerate(((ax, ay), (bx, by))):
        lab = (d.get("left", "A"), d.get("right", "B"))[i]
        _poly(ctx, [(px - w * 0.11, py + h * 0.2), (px + w * 0.11, py + h * 0.2), (px + w * 0.07, py + h * 0.28), (px - w * 0.07, py + h * 0.28)])
        rc.setc(ctx, "theme.accent" if i == 0 else "theme.accent2", th); ctx.fill()
        rc.line(ctx, px, py, px - w * 0.1, py + h * 0.2, 1.5, "theme.line", th)
        rc.line(ctx, px, py, px + w * 0.1, py + h * 0.2, 1.5, "theme.line", th)
        text_c(ctx, lab, px, py + h * 0.17, th, "theme.text", w * 0.24, h * 0.09)
    rc.circle(ctx, cx, cy, h * 0.03, th, fill="theme.highlight")


_WIDGETS: Dict[str, Callable] = {
    "counter": _w_counter, "progress": _w_progress, "donut": _w_donut, "pie": _w_pie, "line_chart": _w_line,
    "checklist": _w_checklist, "timeline": _w_timeline, "steps": _w_steps, "versus": _w_versus, "ranking": _w_ranking,
    "stat_card": _w_stat, "quote": _w_quote, "gauge": _w_gauge, "countdown": _w_countdown, "calendar": _w_calendar,
    "price_tag": _w_price, "equation": _w_equation, "map_route": _w_map, "battery": _w_battery, "balance_scale": _w_scale,
}
WIDGET_TYPES = sorted(set(_WIDGETS) | {"bar_chart", "comparison_card", "funnel"})


def widget_with_story(wj: Dict[str, Any], fb: Any) -> Dict[str, Any]:
    """A library widget carrying this story's data (see widget_contract)."""
    import widget_contract
    return widget_contract.apply(wj, fb)


# =========================================================================== overlays
def draw_overlay_ext(ctx, oj: Dict[str, Any], W, H, theme, t: float, head: Pt, head_r: float, assets=None) -> bool:
    fn = _OVERLAYS.get(oj.get("kind"))
    if not fn:
        return False
    fn(ctx, oj, W, H, theme, t, head, head_r, assets)
    return True


def _rng(seed: int, i: int) -> float:
    return (math.sin(seed * 12.9898 + i * 78.233) * 43758.5453) % 1.0


def _o_burst(ctx, oj, W, H, th, t, head, hr, assets):
    n = int(oj.get("count", 14))
    col = oj.get("color", "theme.highlight")
    pulse = 0.5 + 0.5 * math.sin(t * float(oj.get("speed", 9)))
    for i in range(n):
        a = i * 2 * math.pi / n + t * 0.4
        r0 = hr * (1.5 + 0.2 * pulse)
        r1 = hr * (2.1 + 0.45 * pulse + 0.2 * (i % 2))
        rc.line(ctx, head[0] + math.cos(a) * r0, head[1] + math.sin(a) * r0, head[0] + math.cos(a) * r1,
                head[1] + math.sin(a) * r1, max(2, hr * 0.09), col, th, 0.9)


def _o_sparkle(ctx, oj, W, H, th, t, head, hr, assets):
    n = int(oj.get("count", 6))
    col = oj.get("color", "theme.highlight")
    for i in range(n):
        ph = (t * float(oj.get("speed", 1.6)) + i / n) % 1.0
        s = math.sin(math.pi * ph)
        a = i * 2.4
        rr = hr * (1.6 + 0.7 * _rng(3, i))
        px, py = head[0] + math.cos(a) * rr, head[1] + math.sin(a) * rr * 0.9
        _star(ctx, px, py, hr * 0.32 * s, hr * 0.08 * s, 4, 0)
        rc.setc(ctx, col, th, 0.95); ctx.fill()


def _o_confetti(ctx, oj, W, H, th, t, head, hr, assets):
    n = int(oj.get("count", 40))
    cols = oj.get("colors") or ["theme.accent", "theme.accent2", "theme.highlight", "#34d399", "#a78bfa"]
    for i in range(n):
        sp = 0.35 + 0.4 * _rng(1, i)
        y = ((t * sp + _rng(2, i)) % 1.15 - 0.1) * H
        x = _rng(4, i) * W + math.sin(t * 3 + i) * W * 0.02
        ctx.save(); ctx.translate(x, y); ctx.rotate(t * (2 + 3 * _rng(5, i)) + i)
        ctx.rectangle(-W * 0.008, -W * 0.004, W * 0.016, W * 0.008)
        rc.setc(ctx, cols[i % len(cols)], th); ctx.fill()
        ctx.restore()


def _o_weather(ctx, oj, W, H, th, t, head, hr, assets):
    kind = oj.get("weather", "rain")
    n = int(oj.get("count", 60))
    for i in range(n):
        if kind == "snow":
            sp = 0.08 + 0.1 * _rng(1, i)
            y = ((t * sp + _rng(2, i)) % 1.0) * H
            x = (_rng(3, i) * W + math.sin(t * 1.5 + i) * W * 0.03) % W
            rc.circle(ctx, x, y, W * (0.004 + 0.006 * _rng(4, i)), th, fill="#ffffff", alpha=0.85)
        elif kind == "leaves":
            sp = 0.1 + 0.08 * _rng(1, i)
            y = ((t * sp + _rng(2, i)) % 1.0) * H
            x = (_rng(3, i) * W + math.sin(t * 2 + i) * W * 0.05) % W
            ctx.save(); ctx.translate(x, y); ctx.rotate(t * 2 + i)
            _ellipse(ctx, 0, 0, W * 0.012, W * 0.006)
            rc.setc(ctx, ["#f59e0b", "#ea580c", "#84cc16"][i % 3], th, 0.9); ctx.fill(); ctx.restore()
        else:
            sp = 1.2 + 0.6 * _rng(1, i)
            y = ((t * sp + _rng(2, i)) % 1.0) * H
            x = _rng(3, i) * W
            rc.line(ctx, x, y, x - W * 0.01, y + H * 0.03, max(1, W * 0.003), "#93c5fd", th, 0.6)


def _o_rise(ctx, oj, W, H, th, t, head, hr, assets):
    """Symbols drifting up (hearts, notes, Zzz) or falling (money) from the character."""
    sym = oj.get("text", "♥")
    n = int(oj.get("count", 5))
    life = float(oj.get("lifetime_sec", 1.6))
    down = oj.get("direction") == "down"
    col = oj.get("color", "theme.danger")
    size = float(oj.get("size", 0.05)) * min(W, H)
    rc.set_font(ctx, "DejaVu Sans Bold", size)
    for i in range(n):
        u = ((t / life) + i / n) % 1.0
        if oj.get("spread") == "screen":
            px = _rng(7, i) * W
            py = (u * H * 1.1 - H * 0.05) if down else (H * (1 - u))
        else:
            side = 1 if i % 2 else -1
            px = head[0] + side * hr * (0.9 + 0.5 * _rng(8, i)) + math.sin(t * 3 + i) * hr * 0.25
            py = head[1] - hr * 0.8 - u * hr * 2.6 if not down else head[1] - hr * 2 + u * hr * 3
        s = sym if isinstance(sym, str) else sym[i % len(sym)]
        sc = 0.6 + 0.6 * math.sin(math.pi * min(1.0, u * 2))
        ctx.save(); ctx.translate(px, py); rc.safe_scale(ctx, sc, sc)
        rc.draw_text(ctx, s, -rc.text_width(ctx, s) / 2, size * 0.35, th, col, "#0f172a", size * 0.06, 1 - u * 0.85)
        ctx.restore()


def _o_orbit(ctx, oj, W, H, th, t, head, hr, assets):
    sym = oj.get("text", "★")
    n = int(oj.get("count", 3))
    col = oj.get("color", "theme.highlight")
    size = float(oj.get("size", 0.04)) * min(W, H)
    rc.set_font(ctx, "DejaVu Sans Bold", size)
    for i in range(n):
        a = t * float(oj.get("speed", 4)) + i * 2 * math.pi / n
        px, py = head[0] + math.cos(a) * hr * 1.5, head[1] - hr * 1.15 + math.sin(a) * hr * 0.35
        s = sym if isinstance(sym, str) else sym[i % len(sym)]
        rc.draw_text(ctx, s, px - rc.text_width(ctx, s) / 2, py + size * 0.35, th, col, "#0f172a", size * 0.06)


def _o_icon_pop(ctx, oj, W, H, th, t, head, hr, assets):
    """A library prop (or a drawn symbol) popping in next to the head, then bobbing."""
    pop = rc.clamp(rc.spring_step(t - 0.05, 320, 15), 0, 1.3)
    if pop < 0.01:
        return
    side = -1 if oj.get("side") == "left" else 1
    size = float(oj.get("size", 0.16)) * min(W, H)
    cx = head[0] + side * (hr * 1.2 + size * 0.45)
    cy = head[1] - hr * 1.0 - size * 0.25 + math.sin(t * 3) * size * 0.04
    cx = min(max(cx, size * 0.55), W - size * 0.55)
    cy = max(cy, size * 0.55)
    ctx.save(); ctx.translate(cx, cy); rc.safe_scale(ctx, pop, pop); ctx.rotate(math.sin(t * 2.5) * 0.08)
    prop = oj.get("prop_id")
    drew = False
    if prop and assets is not None:
        surf = assets.svg(prop, "06_props", int(size), int(size))
        if surf:
            rc.draw_surface(ctx, surf, -size / 2, -size / 2, size, size)
            drew = True
    if not drew:
        _symbol(ctx, oj.get("symbol", "exclaim"), size, th, oj.get("color", "theme.highlight"))
    ctx.restore()


def _symbol(ctx, sym: str, size: float, th, col) -> None:
    s = size * 0.42
    if sym == "heart":
        _heart(ctx, 0, 0, s * 0.8); _fill_stroke(ctx, "#f43f5e", "#0f172a", size * 0.03, th)
    elif sym == "star":
        _star(ctx, 0, 0, s, s * 0.45); _fill_stroke(ctx, "#facc15", "#0f172a", size * 0.03, th)
    elif sym == "bolt":
        _bolt(ctx, 0, 0, s); _fill_stroke(ctx, "#facc15", "#0f172a", size * 0.03, th)
    elif sym == "check":
        rc.circle(ctx, 0, 0, s, th, fill="#22c55e", stroke="#0f172a", sw=size * 0.03)
        ctx.new_path(); ctx.move_to(-s * 0.45, 0); ctx.line_to(-s * 0.1, s * 0.35); ctx.line_to(s * 0.5, -s * 0.35)
        rc.setc(ctx, "#ffffff", th); ctx.set_line_width(size * 0.07); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    elif sym == "cross":
        rc.circle(ctx, 0, 0, s, th, fill="#ef4444", stroke="#0f172a", sw=size * 0.03)
        for d in (-1, 1):
            rc.line(ctx, -s * 0.4, -d * s * 0.4, s * 0.4, d * s * 0.4, size * 0.07, "#ffffff", th)
    elif sym == "question":
        rc.circle(ctx, 0, 0, s, th, fill="#3b82f6", stroke="#0f172a", sw=size * 0.03)
        text_c(ctx, "?", 0, s * 0.42, th, "#ffffff", s * 1.4, s * 1.3)
    elif sym == "dollar":
        rc.circle(ctx, 0, 0, s, th, fill="#22c55e", stroke="#0f172a", sw=size * 0.03)
        text_c(ctx, "$", 0, s * 0.42, th, "#ffffff", s * 1.4, s * 1.3)
    elif sym == "idea":
        rc.circle(ctx, 0, -s * 0.15, s * 0.75, th, fill="#facc15", stroke="#0f172a", sw=size * 0.03)
        rc.rrect(ctx, -s * 0.3, s * 0.5, s * 0.6, s * 0.4, s * 0.1); _fill_stroke(ctx, "#94a3b8", "#0f172a", size * 0.03, th)
        for i in range(5):
            a = math.pi * (1.1 + i * 0.2)
            rc.line(ctx, math.cos(a) * s * 0.95, -s * 0.15 + math.sin(a) * s * 0.95, math.cos(a) * s * 1.25,
                    -s * 0.15 + math.sin(a) * s * 1.25, size * 0.035, "#facc15", th)
    elif sym == "warning":
        _poly(ctx, [(0, -s), (s * 1.0, s * 0.8), (-s * 1.0, s * 0.8)]); _fill_stroke(ctx, "#facc15", "#0f172a", size * 0.04, th)
        text_c(ctx, "!", 0, s * 0.62, th, "#0f172a", s, s * 1.1)
    elif sym == "fire":
        ctx.new_path(); ctx.move_to(0, -s); ctx.curve_to(s * 0.9, -s * 0.2, s * 0.8, s * 0.9, 0, s * 0.9)
        ctx.curve_to(-s * 0.8, s * 0.9, -s * 0.9, -s * 0.1, -s * 0.2, -s * 0.5); ctx.curve_to(-s * 0.1, -s * 0.1, 0, -s * 0.3, 0, -s)
        _fill_stroke(ctx, "#f97316", "#0f172a", size * 0.03, th)
    elif sym == "anger":
        for a in range(4):
            ang = a * math.pi / 2 + math.pi / 4
            rc.line(ctx, math.cos(ang) * s * 0.25, math.sin(ang) * s * 0.25, math.cos(ang) * s, math.sin(ang) * s, size * 0.09, "#ef4444", th)
    elif sym == "plus_one":
        text_c(ctx, "+1", 0, s * 0.4, th, "#22c55e", s * 2, s * 1.3, stroke="#0f172a", stroke_w=size * 0.03)
    elif sym == "zzz":
        text_c(ctx, "Zz", 0, s * 0.4, th, "#a5b4fc", s * 2, s * 1.2, stroke="#0f172a", stroke_w=size * 0.03)
    else:  # exclaim
        rc.circle(ctx, 0, 0, s, th, fill="#f97316", stroke="#0f172a", sw=size * 0.03)
        text_c(ctx, "!", 0, s * 0.42, th, "#ffffff", s * 1.4, s * 1.3)


def _o_thought(ctx, oj, W, H, th, t, head, hr, assets):
    pop = rc.clamp(rc.spring_step(t - 0.05, 260, 15), 0, 1.2)
    if pop < 0.01:
        return
    size = float(oj.get("size", 0.2)) * min(W, H)
    cx = min(max(head[0] + hr * 1.6 + size * 0.3, size * 0.6), W - size * 0.6)
    cy = max(head[1] - hr * 2.2 - size * 0.3, size * 0.5)
    for i, (k, rr) in enumerate(((0.25, 0.06), (0.55, 0.09))):
        px, py = head[0] + (cx - head[0]) * k, head[1] - hr * 1.0 + (cy - head[1] + hr) * k
        rc.circle(ctx, px, py, size * rr * pop, th, fill="#ffffff", stroke="#0f172a", sw=max(1.5, size * 0.02))
    ctx.save(); ctx.translate(cx, cy); rc.safe_scale(ctx, pop, pop)
    for dx, dy, rr in ((-0.3, 0.05, 0.28), (0.0, -0.12, 0.33), (0.3, 0.02, 0.28), (0.0, 0.15, 0.28)):
        rc.circle(ctx, dx * size, dy * size, rr * size, th, fill="#ffffff", stroke="#0f172a", sw=max(1.5, size * 0.02))
    for dx, dy, rr in ((-0.3, 0.05, 0.27), (0.0, -0.12, 0.32), (0.3, 0.02, 0.27), (0.0, 0.15, 0.27)):
        rc.circle(ctx, dx * size, dy * size, rr * size, th, fill="#ffffff")
    if oj.get("prop_id") and assets is not None:
        surf = assets.svg(oj["prop_id"], "06_props", int(size * 0.55), int(size * 0.55))
        if surf:
            rc.draw_surface(ctx, surf, -size * 0.275, -size * 0.3, size * 0.55, size * 0.55)
    else:
        text_c(ctx, oj.get("text", "?"), 0, size * 0.12, th, oj.get("color", "#0f172a"), size * 0.8, size * 0.32)
    ctx.restore()


def _o_vignette(ctx, oj, W, H, th, t, head, hr, assets):
    a = rc.clamp(t / 0.3) * float(oj.get("strength", 0.65))
    cx, cy = (head[0], head[1] + hr * 2.5) if oj.get("follow", True) else (W / 2, H / 2)
    g = cairo.RadialGradient(cx, cy, min(W, H) * 0.25, cx, cy, max(W, H) * 0.75)
    r, gg, b, _ = rc.hex_rgba(oj.get("color", "#000000"), th)
    g.add_color_stop_rgba(0, r, gg, b, 0)
    g.add_color_stop_rgba(1, r, gg, b, a)
    ctx.save(); ctx.set_source(g); ctx.paint(); ctx.restore()


def _o_spotlight(ctx, oj, W, H, th, t, head, hr, assets):
    a = rc.clamp(t / 0.35)
    ctx.save()
    ctx.new_path(); ctx.rectangle(0, 0, W, H)
    ctx.move_to(head[0] - hr * 0.6, 0); ctx.line_to(head[0] + hr * 0.6, 0)
    ctx.line_to(head[0] + hr * 3.2, H * 0.98); ctx.line_to(head[0] - hr * 3.2, H * 0.98); ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    rc.setc(ctx, "#000000", th, 0.55 * a); ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    _poly(ctx, [(head[0] - hr * 0.6, 0), (head[0] + hr * 0.6, 0), (head[0] + hr * 3.2, H * 0.98), (head[0] - hr * 3.2, H * 0.98)])
    rc.setc(ctx, oj.get("color", "#fef9c3"), th, 0.12 * a); ctx.fill()
    ctx.restore()


def _o_flash(ctx, oj, W, H, th, t, head, hr, assets):
    a = (1 - rc.clamp(t / float(oj.get("duration_sec", 0.35)))) * 0.85
    if a > 0.01:
        rc.setc(ctx, oj.get("color", "#ffffff"), th, a); ctx.paint()


def _o_focus_lines(ctx, oj, W, H, th, t, head, hr, assets):
    n = int(oj.get("count", 40))
    cx, cy = head[0], head[1] + hr * 2
    R = math.hypot(W, H)
    for i in range(n):
        a = i * 2 * math.pi / n + _rng(9, i) * 0.1
        jitter = (math.sin(t * 25 + i * 3) + 1) * 0.5
        r0 = R * (0.32 + 0.12 * _rng(10, i) + 0.04 * jitter)
        w0 = max(1.5, W * 0.006 * (0.5 + _rng(11, i)))
        ctx.new_path()
        ctx.move_to(cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        ctx.line_to(cx + math.cos(a + 0.02) * R, cy + math.sin(a + 0.02) * R)
        ctx.line_to(cx + math.cos(a - 0.02) * R, cy + math.sin(a - 0.02) * R)
        ctx.close_path()
        rc.setc(ctx, oj.get("color", "#ffffff"), th, 0.55); ctx.fill()
        _ = w0


def _o_motion_lines(ctx, oj, W, H, th, t, head, hr, assets):
    side = -1 if oj.get("side", "left") == "left" else 1
    for i in range(5):
        y = head[1] + hr * (1.0 + i * 0.9)
        x0 = head[0] + side * hr * (1.6 + 0.3 * (i % 2))
        ln = hr * (1.2 + 0.6 * ((math.sin(t * 14 + i) + 1) / 2))
        rc.line(ctx, x0, y, x0 + side * ln, y, max(2, hr * 0.1), oj.get("color", "theme.line"), th, 0.85)


def _o_glitch(ctx, oj, W, H, th, t, head, hr, assets):
    n = int(oj.get("count", 6))
    for i in range(n):
        if _rng(int(t * 12), i) > 0.55:
            continue
        y = _rng(int(t * 12) + 3, i) * H
        hgt = H * (0.01 + 0.03 * _rng(int(t * 12) + 7, i))
        rc.setc(ctx, ["#22d3ee", "#f472b6", "#ffffff"][i % 3], th, 0.35)
        ctx.rectangle(0, y, W, hgt); ctx.fill()


def _o_ring_pulse(ctx, oj, W, H, th, t, head, hr, assets):
    for i in range(3):
        u = ((t * float(oj.get("speed", 1.2))) + i / 3) % 1.0
        rc.circle(ctx, head[0], head[1] + hr * 2.2, hr * (1.2 + u * 4), th, stroke=oj.get("color", "theme.accent"),
                  sw=max(2, hr * 0.12 * (1 - u)), alpha=1 - u)


def _o_dust(ctx, oj, W, H, th, t, head, hr, assets):
    fy = head[1] + hr * 6.6
    for i in range(int(oj.get("count", 8))):
        u = ((t * 1.4) + i / 8) % 1.0
        side = 1 if i % 2 else -1
        rc.circle(ctx, head[0] + side * hr * (0.5 + u * 2.4), fy - u * hr * 0.6, hr * (0.25 + u * 0.35), th,
                  fill=oj.get("color", "#cbd5e1"), alpha=0.55 * (1 - u))


def _o_shine(ctx, oj, W, H, th, t, head, hr, assets):
    ph = (t * 0.9) % 1.4
    x = -W * 0.3 + ph * W * 1.2
    ctx.save()
    ctx.new_path(); ctx.move_to(x, 0); ctx.line_to(x + W * 0.12, 0); ctx.line_to(x - W * 0.18, H); ctx.line_to(x - W * 0.3, H)
    ctx.close_path(); rc.setc(ctx, "#ffffff", th, 0.12); ctx.fill()
    ctx.restore()


_OVERLAYS: Dict[str, Callable] = {
    "burst": _o_burst, "sparkle": _o_sparkle, "confetti": _o_confetti, "weather": _o_weather, "rise": _o_rise,
    "orbit": _o_orbit, "icon_pop": _o_icon_pop, "thought": _o_thought, "vignette": _o_vignette,
    "spotlight": _o_spotlight, "flash": _o_flash, "focus_lines": _o_focus_lines, "motion_lines": _o_motion_lines,
    "glitch": _o_glitch, "ring_pulse": _o_ring_pulse, "dust": _o_dust, "shine": _o_shine,
}
OVERLAY_KINDS = sorted(set(_OVERLAYS) | {"particles", "floating_text"})


# =========================================================================== transitions
def draw_transition_ext(ctx, tr: Dict[str, Any], kind: str, u: float, t: float, W: int, H: int, draw_fn) -> bool:
    fn = _TRANS.get(kind)
    if not fn:
        return False
    fn(ctx, tr, u, t, W, H, draw_fn)
    return True


def _t_slide(ctx, tr, u, t, W, H, draw_fn):
    d = tr.get("direction", "up")
    dx, dy = {"up": (0, 1), "down": (0, -1), "left": (1, 0), "right": (-1, 0)}.get(d, (0, 1))
    ctx.save(); ctx.translate(dx * (1 - u) * W, dy * (1 - u) * H); draw_fn(); ctx.restore()


def _shape_path(ctx, shape, cx, cy, R):
    if shape == "diamond":
        _poly(ctx, [(cx, cy - R), (cx + R, cy), (cx, cy + R), (cx - R, cy)])
    elif shape == "square":
        ctx.new_path(); ctx.rectangle(cx - R * 0.8, cy - R * 0.8, R * 1.6, R * 1.6)
    elif shape == "star":
        _star(ctx, cx, cy, R * 1.3, R * 0.6)
    elif shape == "heart":
        _heart(ctx, cx, cy, R * 0.9)
    else:
        ctx.new_path(); ctx.arc(cx, cy, R, 0, 2 * math.pi)


def _t_iris(ctx, tr, u, t, W, H, draw_fn):
    R = max(1.0, u * math.hypot(W, H) * 0.62 * (1.4 if tr.get("shape") in ("star", "heart", "diamond") else 1.0))
    cx, cy = W * tr.get("cx", 0.5), H * tr.get("cy", 0.5)
    ctx.save(); _shape_path(ctx, tr.get("shape", "circle"), cx, cy, R); ctx.clip(); draw_fn(); ctx.restore()
    if tr.get("ring", True) and u < 1:
        _shape_path(ctx, tr.get("shape", "circle"), cx, cy, R)
        rc.setc(ctx, tr.get("color", "#ffffff"), {}, 0.8); ctx.set_line_width(max(2, W * 0.008)); ctx.stroke()


def _t_dip(ctx, tr, u, t, W, H, draw_fn):
    col = tr.get("color", "#000000")
    if u < 0.5:
        rc.setc(ctx, col, {}, min(1.0, u * 2 * 0.5 + 0.1)); ctx.paint()
    else:
        ctx.push_group(); draw_fn(); ctx.pop_group_to_source(); ctx.paint()
        rc.setc(ctx, col, {}, (1 - u) * 2); ctx.paint()


def _t_spin(ctx, tr, u, t, W, H, draw_fn):
    ctx.save(); ctx.translate(W / 2, H / 2)
    ctx.rotate((1 - u) * math.radians(float(tr.get("degrees", 180))) * (-1 if tr.get("direction") == "ccw" else 1))
    s = max(0.02, u); rc.safe_scale(ctx, s, s); ctx.translate(-W / 2, -H / 2)
    draw_fn(); ctx.restore()


def _t_blinds(ctx, tr, u, t, W, H, draw_fn):
    n = int(tr.get("count", 7))
    vert = tr.get("orientation", "vertical") == "vertical"
    ctx.save(); ctx.new_path()
    for i in range(n):
        if vert:
            w = W / n
            ctx.rectangle(i * w, 0, w * u, H)
        else:
            h = H / n
            ctx.rectangle(0, i * h, W, h * u)
    ctx.clip(); draw_fn(); ctx.restore()


def _t_barn(ctx, tr, u, t, W, H, draw_fn):
    ctx.save(); ctx.new_path()
    if tr.get("orientation", "horizontal") == "horizontal":
        ctx.rectangle(W / 2 - W / 2 * u, 0, W * u, H)
    else:
        ctx.rectangle(0, H / 2 - H / 2 * u, W, H * u)
    ctx.clip(); draw_fn(); ctx.restore()


def _t_glitch(ctx, tr, u, t, W, H, draw_fn):
    ctx.push_group(); draw_fn(); pat = ctx.pop_group()
    n = 9
    for i in range(n):
        y0 = H * i / n
        off = (1 - u) * W * 0.25 * (_rng(int(t * 30), i) - 0.5) * 2
        ctx.save(); ctx.new_path(); ctx.rectangle(0, y0, W, H / n + 1); ctx.clip()
        ctx.translate(off, 0); ctx.set_source(pat); ctx.paint_with_alpha(min(1.0, 0.4 + u)); ctx.restore()
    if u < 0.6:
        rc.setc(ctx, "#22d3ee", {}, 0.15 * (1 - u)); ctx.paint()


def _t_flash(ctx, tr, u, t, W, H, draw_fn):
    s = 1.0 + (1 - u) * float(tr.get("scale", 0.08))
    ctx.save(); ctx.translate(W / 2, H / 2); rc.safe_scale(ctx, s, s); ctx.translate(-W / 2, -H / 2); draw_fn(); ctx.restore()
    rc.setc(ctx, tr.get("color", "#ffffff"), {}, (1 - u) * 0.95); ctx.paint()


def _t_pop(ctx, tr, u, t, W, H, draw_fn):
    s = max(0.02, rc.spring_step(t, 260, 14))
    ctx.save(); ctx.translate(W / 2, H / 2); rc.safe_scale(ctx, s, s); ctx.translate(-W / 2, -H / 2); draw_fn(); ctx.restore()


def _t_slice(ctx, tr, u, t, W, H, draw_fn):
    ctx.push_group(); draw_fn(); pat = ctx.pop_group()
    for i, s in enumerate((-1, 1)):
        ctx.save(); ctx.new_path()
        ctx.rectangle(0, 0 if i == 0 else H / 2, W, H / 2); ctx.clip()
        ctx.translate(s * (1 - u) * W, 0); ctx.set_source(pat); ctx.paint(); ctx.restore()


_TRANS: Dict[str, Callable] = {"slide": _t_slide, "iris": _t_iris, "dip": _t_dip, "spin": _t_spin, "blinds": _t_blinds,
                               "barn_door": _t_barn, "glitch": _t_glitch, "flash": _t_flash, "pop": _t_pop,
                               "slice": _t_slice}
TRANSITION_TYPES = sorted(set(_TRANS) | {"whip_pan", "zoom", "wipe", "fade"})
