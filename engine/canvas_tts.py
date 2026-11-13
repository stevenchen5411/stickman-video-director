#!/usr/bin/env python3
"""Canvas TTS provider (personal, non-commercial): local REST wrapper at 127.0.0.1:8767.

Enabled with STICKMAN_TTS_PROVIDER=canvas. Rules of the API: one request at a time, >= 2.5 s cooldown,
<= 2000 chars per request (we split by sentence at <= 1000), requests take tens of seconds.
Gender follows from the voice; style is one of the ~30 Indonesian emotion labels.
"""
from __future__ import annotations

import io
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import common

log = common.log
CANVAS_URL = os.environ.get("CANVAS_TTS_URL", "http://127.0.0.1:8767").rstrip("/")
MAX_CHARS = 1000
TIMEOUT = 300
COOLDOWN = 2.6
FEMALE = ["Zephyr", "Kore", "Aoede", "Leda", "Callirrhoe", "Autonoe", "Despina", "Erinome"]
MALE = ["Puck", "Charon", "Fenrir", "Orus", "Enceladus", "Iapetus", "Umbriel", "Algieba"]
DEFAULT_STYLE = "Bercerita"
# acting_direction keyword -> Canvas emotion label (first match wins)
STYLE_KEYWORDS: List[Tuple[Tuple[str, ...], str]] = [
    (("whisper", "bisik"), "Berbisik"), (("angry", "furious", "marah", "rage"), "Marah"),
    (("sad", "sedih", "grief"), "Sedih"), (("cry", "menangis", "sob"), "Menangis"),
    (("laugh", "tertawa"), "Tertawa"), (("joke", "playful", "bercanda"), "Bercanda"),
    (("excited", "energetic", "enthusias", "semangat"), "Bersemangat"), (("cheer", "happy", "ceria"), "Ceria"),
    (("calm", "tenang", "soothing"), "Tenang"), (("firm", "stern", "tegas"), "Tegas"),
    (("casual", "relaxed", "santai"), "Santai"), (("scared", "fear", "takut", "afraid"), "Takut"),
    (("surpris", "shock", "terkejut", "gasp"), "Terkejut"), (("worr", "anxious", "khawatir"), "Khawatir"),
    (("sarcas", "sarkas"), "Sarkas"), (("disappoint", "kecewa"), "Kecewa"), (("tired", "lelah", "exhaust"), "Lelah"),
    (("sleepy", "mengantuk"), "Mengantuk"), (("confus", "bingung"), "Bingung"), (("proud", "arrogant", "sombong"), "Sombong"),
    (("shy", "malu"), "Malu-malu"), (("authorit", "berwibawa", "news", "serious", "grave"), "Berwibawa"),
    (("promo", "sales", "hype"), "Promosi"), (("vlog",), "Vlogger"), (("narrat", "narator"), "Narator"),
    (("story", "cerita", "dramatic", "suspense", "mysterious"), "Bercerita"),
]
_last_call = 0.0
_lock = threading.Lock()          # one request at a time, never parallel
_state: Dict[str, Any] = {"fallback": False, "reason": ""}


def enabled() -> bool:
    return os.environ.get("STICKMAN_TTS_PROVIDER", "").strip().lower() == "canvas"


def _headers() -> Dict[str, str]:
    h = {"content-type": "application/json"}
    tok = os.environ.get("CANVAS_TTS_TOKEN", "")
    if tok:
        h["X-Canvas-Token"] = tok
    return h


def _get(path: str, timeout: float = 4.0) -> Dict[str, Any]:
    req = urllib.request.Request(CANVAS_URL + path, headers=_headers())
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - local 127.0.0.1
        return json.loads(r.read().decode("utf-8"))


def status() -> Dict[str, Any]:
    """Fields for the engine /health. Never raises."""
    out: Dict[str, Any] = {"enabled": enabled(), "url": CANVAS_URL, "up": False, "signed_in": False,
                           "calibrated": False, "needs_refresh": False, "fallback": _state["fallback"],
                           "fallback_reason": _state["reason"]}
    try:
        h = _get("/health")
        out.update(up=True, signed_in=bool(h.get("signed_in")), calibrated=bool(h.get("calibrated")),
                   iframe_attached=bool(h.get("iframe_attached")))
        out["needs_refresh"] = bool(_get("/auth/status").get("needs_refresh"))
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)[:100]
    return out


def load_map() -> Dict[str, Any]:
    """Character/narrator -> {voice, style}. File: <STICKMAN_HOME>/config/canvas_voices.json (optional)."""
    try:
        p = common.home() / "config" / "canvas_voices.json"
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("canvas_voices.json unreadable: %s", str(e)[:80])
    return {}


def pick_voice(voice: str, character: str = "", cmap: Optional[Dict[str, Any]] = None) -> str:
    cmap = load_map() if cmap is None else cmap
    ent = cmap.get(character) or cmap.get(voice) or {}
    v = ent.get("voice") or voice
    known = {x.lower(): x for x in FEMALE + MALE}
    if v.lower() in known:
        return known[v.lower()]
    return "Charon"


def pick_style(direction: str, character: str = "", cmap: Optional[Dict[str, Any]] = None) -> str:
    """Per-line emotion from the acting direction; else the character's default; else Bercerita."""
    cmap = load_map() if cmap is None else cmap
    d = (direction or "").lower()
    for keys, label in STYLE_KEYWORDS:
        if any(k in d for k in keys):
            return label
    return (cmap.get(character) or {}).get("style") or DEFAULT_STYLE


def split_text(text: str, limit: int = MAX_CHARS) -> List[str]:
    sents = [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text.strip()) if s.strip()]
    chunks: List[str] = []
    cur = ""
    for s in sents:
        while len(s) > limit:                       # one giant sentence: cut at a comma/space
            cut = max(s.rfind(", ", 0, limit), s.rfind(" ", 0, limit), limit - 1) + 1
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(s[:cut].strip())
            s = s[cut:].strip()
        if cur and len(cur) + 1 + len(s) > limit:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def plausible_max_sec(text: str) -> float:
    return 6.0 + 0.2 * len(text)


def _wav(data: bytes) -> Tuple[np.ndarray, int]:
    with wave.open(io.BytesIO(data)) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768.0
    return (x.reshape(-1, ch).mean(axis=1) if ch > 1 else x), sr


def _post_tts(text: str, voice: str, style: str) -> bytes:
    global _last_call
    body = json.dumps({"text": text, "voice": voice, "style": style, "sample_rate": 24000, "normalize": True}).encode()
    last: Optional[Exception] = None
    for attempt in range(2):                         # retry once on 502/504
        with _lock:
            wait = COOLDOWN - (time.time() - _last_call)
            if wait > 0:
                time.sleep(wait)
            try:
                req = urllib.request.Request(CANVAS_URL + "/tts", data=body, headers=_headers(), method="POST")
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310
                    return r.read()
            except urllib.error.HTTPError as e:
                last = e
                if e.code not in (502, 504):
                    raise
                log.warning("canvas tts HTTP %s, retrying once", e.code)
            finally:
                _last_call = time.time()
    raise last or RuntimeError("canvas failed")


def synthesize(text: str, voice: str = "Charon", style: str = "", character: str = "") -> Tuple[np.ndarray, int]:
    cmap = load_map()
    v = pick_voice(voice, character, cmap)
    st = pick_style(style, character, cmap)
    parts: List[np.ndarray] = []
    sr = 24000
    gap = np.zeros(int(0.18 * 24000), dtype=np.float32)
    for chunk in split_text(text):                   # sequential, never parallel
        x, sr = _wav(_post_tts(chunk, v, st))
        for _ in range(2):                           # Canvas sometimes returns runaway audio: retry up to twice
            if len(x) / sr <= plausible_max_sec(chunk):
                break
            log.warning("canvas audio too long (%.0fs for %d chars): regenerating", len(x) / sr, len(chunk))
            x, sr = _wav(_post_tts(chunk, v, st))
        else:
            if len(x) / sr > plausible_max_sec(chunk):
                raise RuntimeError(f"canvas returned implausible audio length {len(x) / sr:.0f}s")
        parts += [x, gap]
    if not parts:
        raise ValueError("empty text")
    return np.concatenate(parts[:-1]), sr


def synth_or_none(text: str, voice: str, style: str, character: str = "") -> Optional[Tuple[np.ndarray, int]]:
    """Canvas synthesis; None (flagged in log + /health) when Canvas is down / signed out / errors."""
    try:
        r = synthesize(text, voice, style, character)
        _state.update(fallback=False, reason="")
        return r
    except Exception as e:  # noqa: BLE001
        _state.update(fallback=True, reason=str(e)[:120])
        log.warning("CANVAS TTS UNAVAILABLE (%s): falling back to the default TTS provider", str(e)[:120])
        return None
