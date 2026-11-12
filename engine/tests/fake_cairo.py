"""Minimal PIL-backed stand-in for the pycairo subset used by render_cairo.

ONLY for running the render pipeline in sandboxes without pycairo (tests/conftest.py installs it when
`import cairo` fails). It exercises layout, timing, piping and file outputs; it is not pixel-faithful to cairo.
"""
from __future__ import annotations

import io
import math
from typing import Any, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

FORMAT_ARGB32 = 0
FONT_SLANT_NORMAL = 0
FONT_WEIGHT_NORMAL = 0
FONT_WEIGHT_BOLD = 1
LINE_CAP_ROUND = 1
LINE_JOIN_ROUND = 1

try:
    _FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ImageFont.truetype(_FONT_PATH, 10)
except OSError:
    _FONT_PATH = None


class ImageSurface:
    def __init__(self, fmt: int, w: int, h: int, image: Optional[Image.Image] = None):
        self.im = image or Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.w, self.h = self.im.size

    @classmethod
    def create_from_png(cls, fobj) -> "ImageSurface":
        im = Image.open(fobj).convert("RGBA")
        return cls(0, im.width, im.height, im)

    def get_width(self) -> int:
        return self.w

    def get_height(self) -> int:
        return self.h

    def get_stride(self) -> int:
        return self.w * 4

    def flush(self) -> None:
        pass

    def get_data(self) -> bytes:
        r, g, b, a = self.im.split()
        return Image.merge("RGBA", (b, g, r, a)).tobytes()

    def write_to_png(self, path: str) -> None:
        self.im.save(path, "PNG")


class _Pattern:
    def __init__(self, im: Image.Image):
        self.im = im


class _Extents:
    def __init__(self, adv: float, h: float):
        self.x_advance, self.width, self.height = adv, adv, h


class Context:
    def __init__(self, surface: ImageSurface):
        self.s = surface
        self.m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)           # a b c d e f
        self.src: Any = (0, 0, 0, 1)
        self.lw, self.fs = 1.0, 12.0
        self.bold = False
        self.path: List[List[Tuple[float, float]]] = []
        self.text_pending: Optional[Tuple[str, Tuple[float, float]]] = None
        self.stack: List[Tuple] = []
        self.groups: List[Image.Image] = []
        self.cur: Tuple[float, float] = (0.0, 0.0)

    # ---- state
    def save(self) -> None:
        self.stack.append((self.m, self.src, self.lw, self.fs, self.bold))

    def restore(self) -> None:
        self.m, self.src, self.lw, self.fs, self.bold = self.stack.pop()

    def _mul(self, n) -> None:
        a, b, c, d, e, f = self.m
        na, nb, nc, nd, ne, nf = n
        self.m = (a * na + c * nb, b * na + d * nb, a * nc + c * nd, b * nc + d * nd, a * ne + c * nf + e, b * ne + d * nf + f)

    def translate(self, x, y) -> None:
        self._mul((1, 0, 0, 1, x, y))

    def scale(self, x, y) -> None:
        self._mul((x, 0, 0, y, 0, 0))

    def rotate(self, a) -> None:
        self._mul((math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0))

    def _pt(self, x, y) -> Tuple[float, float]:
        a, b, c, d, e, f = self.m
        return (a * x + c * y + e, b * x + d * y + f)

    def _lwd(self) -> float:
        a, b, c, d, _, _ = self.m
        return max(1.0, self.lw * math.sqrt(abs(a * d - b * c)))

    # ---- source
    def set_source_rgba(self, r, g, b, a=1.0) -> None:
        self.src = (r, g, b, a)

    def set_source_surface(self, surf: ImageSurface, x=0, y=0) -> None:
        self.src = ("surf", surf, x, y, self.m)

    def set_source(self, pattern: _Pattern) -> None:
        self.src = ("pat", pattern, self.m)

    def set_line_width(self, w) -> None:
        self.lw = w

    def set_line_cap(self, _c) -> None:
        pass

    def set_line_join(self, _j) -> None:
        pass

    def select_font_face(self, family, slant, weight) -> None:
        self.bold = weight == FONT_WEIGHT_BOLD

    def set_font_size(self, s) -> None:
        self.fs = s

    def _font(self, size: float):
        if _FONT_PATH is None:
            return ImageFont.load_default()
        return ImageFont.truetype(_FONT_PATH.replace("Sans.ttf", "Sans-Bold.ttf") if self.bold else _FONT_PATH, max(6, int(size)))

    def text_extents(self, s: str) -> _Extents:
        return _Extents(self._font(self.fs).getlength(s), self.fs)

    # ---- path
    def new_path(self) -> None:
        self.path, self.text_pending = [], None

    def move_to(self, x, y) -> None:
        self.cur = (x, y)
        self.path.append([self._pt(x, y)])

    def line_to(self, x, y) -> None:
        if not self.path:
            self.move_to(x, y)
            return
        self.cur = (x, y)
        self.path[-1].append(self._pt(x, y))

    def curve_to(self, x1, y1, x2, y2, x3, y3) -> None:
        x0, y0 = self.cur
        for i in range(1, 13):
            t = i / 12
            u = 1 - t
            self.line_to(u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3,
                         u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3)

    def arc(self, xc, yc, r, a0, a1) -> None:
        n = max(8, int(abs(a1 - a0) / (2 * math.pi) * 40))
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            x, y = xc + r * math.cos(a), yc + r * math.sin(a)
            self.line_to(x, y) if (self.path and i > 0) or (self.path and self.path[-1]) else self.move_to(x, y)

    def rectangle(self, x, y, w, h) -> None:
        self.move_to(x, y)
        self.line_to(x + w, y)
        self.line_to(x + w, y + h)
        self.line_to(x, y + h)
        self.close_path()

    def close_path(self) -> None:
        if self.path and self.path[-1]:
            self.path[-1].append(self.path[-1][0])

    def text_path(self, s: str) -> None:
        self.text_pending = (s, self._pt(*self.cur))

    def show_text(self, s: str) -> None:
        self.text_pending = (s, self._pt(*self.cur))
        self.fill()

    # ---- painting
    def _color(self):
        if isinstance(self.src, tuple) and len(self.src) == 4 and not isinstance(self.src[0], str):
            r, g, b, a = self.src
            return (int(r * 255), int(g * 255), int(b * 255), int(a * 255))
        return (255, 0, 255, 255)

    def _blit(self, layer: Image.Image) -> None:
        self.s.im.alpha_composite(layer)

    def _layer(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        lay = Image.new("RGBA", self.s.im.size, (0, 0, 0, 0))
        return lay, ImageDraw.Draw(lay)

    def fill_preserve(self) -> None:
        col = self._color()
        lay, dr = self._layer()
        if self.text_pending:
            s, (x, y) = self.text_pending
            dr.text((x, y), s, font=self._font(self.fs), fill=col, anchor="ls")
        for sub in self.path:
            if len(sub) >= 3:
                dr.polygon(sub, fill=col)
        self._blit(lay)

    def fill(self) -> None:
        self.fill_preserve()
        self.new_path()

    def stroke_preserve(self) -> None:
        col = self._color()
        lay, dr = self._layer()
        w = int(round(self._lwd()))
        if self.text_pending:
            s, (x, y) = self.text_pending
            dr.text((x, y), s, font=self._font(self.fs), fill=col, anchor="ls", stroke_width=max(1, w // 2), stroke_fill=col)
        for sub in self.path:
            if len(sub) >= 2:
                dr.line(sub, fill=col, width=w, joint="curve")
        self._blit(lay)

    def stroke(self) -> None:
        self.stroke_preserve()
        self.new_path()

    def clip(self) -> None:
        self.new_path()   # clipping not emulated

    def _paint(self, alpha: float) -> None:
        src = self.src
        if isinstance(src, tuple) and src and src[0] == "surf":
            _, surf, x, y, m = src
            self._draw_image(surf.im, m, x, y, alpha)
        elif isinstance(src, tuple) and src and src[0] == "pat":
            lay = src[1].im.copy()
            if alpha < 1:
                lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
            self._blit(lay)
        else:
            r, g, b, a = self._color()
            self._blit(Image.new("RGBA", self.s.im.size, (r, g, b, int(a * alpha))))

    def _draw_image(self, im: Image.Image, m, x: float, y: float, alpha: float) -> None:
        a, b, c, d, e, f = m
        e2, f2 = a * x + c * y + e, b * x + d * y + f
        det = a * d - b * c
        if abs(det) < 1e-9:
            return
        ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
        coeffs = (ia, ic, -(ia * e2 + ic * f2), ib, id_, -(ib * e2 + id_ * f2))
        out = im.transform(self.s.im.size, Image.AFFINE, coeffs, resample=Image.BILINEAR)
        if alpha < 1:
            out.putalpha(out.getchannel("A").point(lambda v: int(v * alpha)))
        self._blit(out)

    def paint(self) -> None:
        self._paint(1.0)

    def paint_with_alpha(self, alpha: float) -> None:
        self._paint(alpha)

    # ---- groups
    def push_group(self) -> None:
        self.groups.append(self.s.im)
        self.s.im = Image.new("RGBA", self.s.im.size, (0, 0, 0, 0))

    def pop_group(self) -> _Pattern:
        grp = self.s.im
        self.s.im = self.groups.pop()
        return _Pattern(grp)

    def pop_group_to_source(self) -> None:
        self.src = ("pat", self.pop_group(), self.m)


class LinearGradient:  # not used by render_cairo; present for API completeness
    def __init__(self, *a):
        pass

    def add_color_stop_rgba(self, *a):
        pass
