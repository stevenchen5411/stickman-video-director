import io
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canvas_tts as c  # noqa: E402


def make_wav(sec=0.2, sr=24000):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.zeros(int(sec * sr), dtype="<i2")).tobytes())
    return b.getvalue()


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(c, "COOLDOWN", 0)
    monkeypatch.setattr(c, "load_map", lambda: {"hero": {"voice": "kore", "style": "Ceria"}})


def test_voice_style_mapping():
    assert c.pick_voice("Puck") == "Puck"
    assert c.pick_voice("whatever", "hero") == "Kore"
    assert c.pick_voice("unknown-voice") == "Charon"
    assert c.pick_style("whispering softly") == "Berbisik"
    assert c.pick_style("", "hero") == "Ceria"
    assert c.pick_style("") == "Bercerita"


def test_split_text_limits():
    t = " ".join(["Kalimat nomor satu yang cukup panjang."] * 80)
    parts = c.split_text(t)
    assert len(parts) > 1 and all(len(p) <= c.MAX_CHARS for p in parts)
    assert " ".join(parts) == t
    assert all(len(p) <= 100 for p in c.split_text("a" * 250 + " b", 100))


def test_sequential_calls_and_retry(monkeypatch):
    calls, active = [], []

    def fake(text, voice, style):
        assert not active
        active.append(1)
        calls.append((text, voice, style))
        active.pop()
        return make_wav()

    monkeypatch.setattr(c, "_post_tts", fake)
    x, sr = c.synthesize("Satu. Dua. " + "Tiga " * 300, "Puck", "angry")
    assert sr == 24000 and len(x) > 0 and len(calls) >= 2
    assert {(v, s) for _, v, s in calls} == {("Puck", "Marah")}


def test_fallback_flag(monkeypatch):
    def boom(*a):
        raise RuntimeError("503 not signed in")
    monkeypatch.setattr(c, "_post_tts", boom)
    assert c.synth_or_none("Halo.", "Puck", "") is None
    assert c._state["fallback"] and "503" in c._state["reason"]


def test_http_retry_once(monkeypatch):
    import urllib.error
    n = {"i": 0}

    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return make_wav()

    def fake_open(req, timeout=0):
        n["i"] += 1
        if n["i"] == 1:
            raise urllib.error.HTTPError("u", 504, "gw", {}, None)
        return R()

    monkeypatch.setattr(c.urllib.request, "urlopen", fake_open)
    assert c._post_tts("Halo", "Puck", "Tenang")[:4] == b"RIFF" and n["i"] == 2


def test_status_down(monkeypatch):
    monkeypatch.setattr(c, "CANVAS_URL", "http://127.0.0.1:9")
    s = c.status()
    assert s["up"] is False and "enabled" in s


def test_runaway_audio_is_regenerated(monkeypatch):
    calls = []

    def fake(text, voice, style):
        calls.append(1)
        return make_wav(300.0) if len(calls) == 1 else make_wav(2.0)

    monkeypatch.setattr(c, "_post_tts", fake)
    x, sr = c.synthesize("Halo semuanya.", "Kore", "sedih")
    assert len(calls) == 2 and len(x) / sr < 5
