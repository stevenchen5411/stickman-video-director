"""Test bootstrap: isolated STICKMAN_HOME/TMPDIR, engine on sys.path, fake cairo/cairosvg when absent."""
import io
import os
import shutil
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "engine"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(Path(__file__).parent))

REAL_CAIRO = True
try:
    import cairo  # noqa: F401
except ImportError:
    REAL_CAIRO = False
    import fake_cairo
    sys.modules["cairo"] = fake_cairo

try:
    import cairosvg  # noqa: F401
except ImportError:
    from PIL import Image, ImageDraw

    stub = types.ModuleType("cairosvg")

    def svg2png(bytestring=None, output_width=64, output_height=64, **_kw):
        im = Image.new("RGBA", (output_width, output_height), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((2, 2, output_width - 3, output_height - 3), fill=(200, 120, 60, 255))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return buf.getvalue()

    stub.svg2png = svg2png
    sys.modules["cairosvg"] = stub


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    monkeypatch.setenv("STICKMAN_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("STICKMAN_LIBRARY", str(ROOT / "assets" / "library"))
    for k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    import common
    common.ensure_dirs()
    common.tmpdir()
    yield


@pytest.fixture
def lib_copy(tmp_path, monkeypatch):
    """Writable copy of the seed library (for forge tests)."""
    dst = tmp_path / "libcopy"
    shutil.copytree(ROOT / "assets" / "library", dst)
    monkeypatch.setenv("STICKMAN_LIBRARY", str(dst))
    return dst
