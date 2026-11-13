#!/usr/bin/env python3
"""Expressive TTS (Gemini 3.8 Flash TTS) with role casting, multi-speaker turns and word alignment.

* Acting/delivery goes ONLY into `speech_metadata={"style": ...}`; `text` stays verbatim.
* Voice per character comes from the cast voice_profile_id (library 12_voices persona, a raw voice name such as
  "Charon", or a custom `voice_...` id created by `design_voice`, which uses `client.voices(type="prompted", store=True)`).
* Consecutive turns by two different characters are synthesized in ONE multi-speaker call and split back per scene.
* Gemini returns no word timestamps, so word timings are estimated (silence-trimmed, syllable/punctuation weighted).
* No key / no google-genai -> a formant-synth PLACEHOLDER voice is used so drafts, keyframes and tests still work.

CLI: python3 engine/tts_expressive.py --package PATH --out DIR [--placeholder]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import canvas_tts

import common
import llm
import schemas

log = common.log
SR = 24000
TTS_MODEL = "gemini-3.8-flash-tts"
VOICE_F0 = {"Charon": 110, "Puck": 190, "Fenrir": 95, "Aoede": 220, "Kore": 200}
MAX_GROUP_TURNS = 4


# --------------------------------------------------------------------------- text / alignment helpers
def syllables(word: str) -> int:
    return max(1, len(re.findall(r"[aeiouy]+", word.lower())))


def norm_word(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def _pause_weight(token: str) -> float:
    if token.endswith("..."):
        return 1.4
    if token[-1:] in ".!?":
        return 1.0
    if token[-1:] in ",;:—-":
        return 0.6
    return 0.0


def trim_bounds(x: np.ndarray, sr: int, rel: float = 0.04) -> Tuple[float, float]:
    """(start_sec, end_sec) of the voiced region using 10 ms RMS frames."""
    hop = max(1, sr // 100)
    n = len(x) // hop
    if n == 0:
        return 0.0, len(x) / sr
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    voiced = np.where(rms > rms.max() * rel)[0]
    if len(voiced) == 0:
        return 0.0, len(x) / sr
    return voiced[0] * hop / sr, (voiced[-1] + 1) * hop / sr


def align_words(text: str, x: np.ndarray, sr: int = SR) -> List[Dict[str, Any]]:
    """Estimate per-word timings across the voiced span of `x`."""
    tokens = text.split()
    if not tokens:
        return []
    t0, t1 = trim_bounds(x, sr)
    span = max(0.05, t1 - t0)
    w_word = [syllables(t) + 0.35 for t in tokens]
    w_pause = [_pause_weight(t) for t in tokens]
    w_pause[-1] = 0.0
    total = sum(w_word) + sum(w_pause)
    out, cur = [], t0
    for tok, ww, pw in zip(tokens, w_word, w_pause):
        dur = span * ww / total
        out.append({"word": tok, "start": round(cur, 3), "end": round(cur + dur, 3)})
        cur += dur + span * pw / total
    return out


def apply_pace(x: np.ndarray, sr: int, pace: float) -> np.ndarray:
    """Time-stretch (pitch preserved) with ffmpeg atempo when pace differs noticeably from 1.0."""
    if abs(pace - 1.0) < 0.03:
        return x
    tmp = common.tmpdir()
    src, dst = tmp / f"pace_in_{id(x)}.wav", tmp / f"pace_out_{id(x)}.wav"
    write_wav(src, x, sr)
    try:
        common.run([common.ffmpeg_bin(), "-y", "-loglevel", "error", "-i", str(src), "-filter:a",
                    f"atempo={min(2.0, max(0.5, pace)):.3f}", str(dst)])
        return read_wav(dst)[0]
    finally:
        src.unlink(missing_ok=True)
        dst.unlink(missing_ok=True)


# --------------------------------------------------------------------------- WAV I/O
def write_wav(path: Path, x: np.ndarray, sr: int = SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def read_wav(path: Path) -> Tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        sr, ch = w.getframerate(), w.getnchannels()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        raw = raw.reshape(-1, ch).mean(axis=1)
    return raw, sr


# --------------------------------------------------------------------------- Chatterbox (Modal) backend
CHATTERBOX_URL = os.environ.get("STICKMAN_CHATTERBOX_URL",
                                "https://n541921024--near-chatterbox-chatterbox-tts.us-east.modal.run")
CHATTERBOX_ID_URL = os.environ.get("STICKMAN_CHATTERBOX_ID_URL",
                                   "https://n541921024--near-chatterbox-id-chatterboxid-tts.us-east.modal.run")
F5_ID_URL = os.environ.get("STICKMAN_F5_ID_URL", "https://n541921024--near-f5-id-f5indo-tts-api.us-east.modal.run")
_ID_WORDS = {"yang", "dan", "di", "ini", "itu", "untuk", "dengan", "tidak", "kamu", "aku", "kita", "adalah",
             "dari", "ke", "pada", "akan", "bisa", "jadi", "kalau", "saya", "anda", "juga", "atau", "sudah"}


def use_chatterbox() -> bool:
    return bool(CHATTERBOX_URL) and os.environ.get("STICKMAN_TTS", "chatterbox") == "chatterbox"


def detect_lang(text: str) -> str:
    """'ms' means Indonesian (Chatterbox V3 has no Indonesian id). The video language is configured
    (STICKMAN_LANGUAGE, default Indonesian), so short lines are never misread as English."""
    cfg = os.environ.get("STICKMAN_LANGUAGE", "Indonesian").strip().lower()
    if cfg.startswith(("indo", "bahasa", "id")):
        return "ms"
    words = re.findall(r"[a-z]+", text.lower())
    if sum(w in _ID_WORDS for w in words) >= max(2, len(words) // 12):
        return "ms"
    return os.environ.get("STICKMAN_TTS_LANG", "en")


def parse_wav_bytes(data: bytes) -> Tuple[np.ndarray, int]:
    """RIFF/WAVE (PCM16 or float32 as torchaudio writes) -> mono float32 + sample rate."""
    import struct
    fmt = ch = sr = bits = None
    pos = 12
    while pos + 8 <= len(data):
        cid, size = data[pos:pos + 4], struct.unpack("<I", data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            fmt, ch, sr, _, _, bits = struct.unpack("<HHIIHH", body[:16])
            if fmt == 0xFFFE and len(body) >= 26:
                fmt = struct.unpack("<H", body[24:26])[0]
        elif cid == b"data":
            if fmt == 3:
                x = np.frombuffer(body[: len(body) // 4 * 4], dtype="<f4").astype(np.float32)
            elif bits == 16:
                x = np.frombuffer(body[: len(body) // 2 * 2], dtype="<i2").astype(np.float32) / 32768.0
            else:
                raise RuntimeError(f"unsupported wav format {fmt}/{bits}")
            if ch and ch > 1:
                x = x[: len(x) // ch * ch].reshape(-1, ch).mean(axis=1)
            return x, int(sr)
        pos += 8 + size + (size & 1)
    raise RuntimeError("wav has no data chunk")


def chatterbox_synthesize(text: str, style: str = "", voice: str = "") -> Tuple[np.ndarray, int]:
    """Text -> speech through the near-chatterbox Modal endpoint (default voice; style/voice names are Gemini-only)."""
    import time as _t
    import urllib.parse
    import urllib.request
    lang = detect_lang(text)
    cands: List[Tuple[str, str]] = []              # (endpoint, query)
    if lang == "ms" and F5_ID_URL:                 # Indonesian: F5-TTS Indonesian only (no Chatterbox mixing)
        cands.append((F5_ID_URL, urllib.parse.urlencode({"text": text, "ref": "reporter", "arch": "F5TTS_v1_Base"})))
    else:
        cands.append((CHATTERBOX_URL, urllib.parse.urlencode({"text": text, "lang": lang})))
    last: Optional[Exception] = None
    for base, q in cands:
        for attempt in range(2):                  # first call after idle cold-starts the GPU (can take minutes)
            try:
                with urllib.request.urlopen(f"{base}?{q}", timeout=290) as r:
                    data = r.read()
                if data[:4] != b"RIFF":
                    raise RuntimeError("TTS endpoint returned no audio")
                return parse_wav_bytes(data)
            except Exception as e:  # noqa: BLE001
                last = e
                log.warning("tts %s attempt %d failed: %s", base.split("//")[1][:40], attempt + 1, str(e)[:100])
                _t.sleep(3)
    raise last if last else RuntimeError("chatterbox failed")


def synth_line(client, text: str, style: str, voice: str) -> Tuple[np.ndarray, int]:
    if canvas_tts.enabled():
        r = canvas_tts.synth_or_none(text, voice, style)
        if r is not None:
            return r
    if use_chatterbox():
        return chatterbox_synthesize(text, style, voice)
    return gemini_synthesize(client, text, style, voice)


# --------------------------------------------------------------------------- placeholder voice
def placeholder_speech(text: str, voice: str = "Charon", min_sec: float = 0.0) -> Tuple[np.ndarray, int]:
    """Formant-synth babble whose timing follows the text (syllables + punctuation). Offline/dev only."""
    f0 = VOICE_F0.get(voice, 140)
    vowels = [(800, 1200), (300, 2300), (500, 900), (400, 1900)]
    segs: List[np.ndarray] = []
    vi = 0
    tokens = text.split() or ["..."]
    for tok in tokens:
        for _ in range(syllables(tok)):
            f1, f2 = vowels[vi % len(vowels)]
            vi += 1
            m = int(0.17 * SR)
            tt = np.arange(m) / SR
            pitch = f0 * (1 + 0.05 * np.sin(2 * np.pi * 5 * tt + vi))
            phase = 2 * np.pi * np.cumsum(pitch) / SR
            sig = np.zeros(m)
            for h in range(1, max(2, int(3800 / f0))):
                fh = h * f0
                sig += (np.exp(-((fh - f1) / 150) ** 2) + 0.6 * np.exp(-((fh - f2) / 250) ** 2) + 0.04) / h * np.sin(h * phase)
            segs.append(sig * np.sin(np.pi * tt / tt[-1]) ** 0.7)
        segs.append(np.zeros(int((0.05 + 0.22 * _pause_weight(tok)) * SR)))
    x = np.concatenate(segs)
    x = x * (0.5 / (np.max(np.abs(x)) or 1.0))
    need = int(min_sec * SR) - len(x)
    if need > 0:
        x = np.concatenate([x, np.zeros(need)])
    return x.astype(np.float32), SR


# --------------------------------------------------------------------------- Gemini adapters
def _client():
    from google import genai
    key = llm.api_key("gemini")
    kw: Dict[str, Any] = {"http_options": {"api_version": "v1beta"}}
    if key:
        kw["api_key"] = key
    return genai.Client(**kw)


def _walk(obj: Any, depth: int = 0):
    """Yield (mime, data) pairs for audio payloads anywhere in an SDK response (object or dict)."""
    if depth > 8 or obj is None:
        return
    if isinstance(obj, dict):
        items = obj
        get = items.get
        children = list(items.values())
    else:
        get = lambda k, d=None: getattr(obj, k, d)  # noqa: E731
        children = [getattr(obj, k, None) for k in ("inline_data", "audio", "candidates", "content", "parts",
                                                    "outputs", "output", "steps", "data_parts")]
    data, mime = get("data"), get("mime_type")
    if isinstance(data, (bytes, str)) and data and (not mime or str(mime).startswith("audio")):
        yield (mime or "audio/L16;rate=24000", data)
    for c in children:
        if isinstance(c, (list, tuple)):
            for it in c:
                yield from _walk(it, depth + 1)
        elif c is not None and not isinstance(c, (str, bytes, int, float, bool)):
            yield from _walk(c, depth + 1)


def decode_audio_payload(mime: str, data: Any) -> Tuple[np.ndarray, int]:
    raw = base64.b64decode(data) if isinstance(data, str) else data
    if raw[:4] == b"RIFF":
        tmp = common.tmpdir() / f"gem_{hashlib.sha1(raw[:256]).hexdigest()[:8]}.wav"
        tmp.write_bytes(raw)
        try:
            return read_wav(tmp)
        finally:
            tmp.unlink(missing_ok=True)
    m = re.search(r"rate=(\d+)", mime or "")
    sr = int(m.group(1)) if m else SR
    return np.frombuffer(raw[: len(raw) // 2 * 2], dtype="<i2").astype(np.float32) / 32768.0, sr


def _voice_cfg_dict(voice: str) -> Dict[str, Any]:
    return {"voice_config": {"prebuilt_voice_config": {"voice_name": voice}}}


# Free-tier quota is per model (e.g. 10 requests/day on gemini-3.8-flash-tts), so we fail over across the TTS line.
TTS_MODELS = [m for m in dict.fromkeys([os.environ.get("STICKMAN_TTS_MODEL", TTS_MODEL), TTS_MODEL,
                                        "gemini-3.8-flash-lite-tts", "gemini-3.1-flash-tts-preview",
                                        "gemini-2.5-flash-preview-tts"]) if m]
_EXHAUSTED: Dict[str, float] = {}          # model -> unix time until which its quota is spent


def style_tag(style: str, max_words: int = 6) -> str:
    """Acting direction -> a short inline audio tag. The TTS API has no style field (a 'developer instruction' is
    rejected) and a 'Say ...:' prefix gets read aloud, but a short [tag] is treated as direction."""
    first = re.split(r"[.!?\n]", (style or "").strip(), maxsplit=1)[0]
    words = re.sub(r"[^A-Za-z, -]", " ", first).lower().split()[:max_words]
    return " ".join(words).strip(" ,-")


def tagged(text: str, style: str) -> str:
    t = style_tag(style)
    return f"[{t}] {text}" if t else text


def _retry_after(msg: str) -> float:
    m = re.search(r"retry in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", msg)
    if m and any(m.groups()):
        h, mi, sec = (float(g) if g else 0.0 for g in m.groups())
        return h * 3600 + mi * 60 + sec
    m = re.search(r"retryDelay'?: ?'?([\d.]+)s", msg)
    return float(m.group(1)) if m else 60.0


def _with_models(call, model: Optional[str]):
    """Run call(model_id) over the usable TTS models: hop on a spent quota (429), retry once on transient 5xx."""
    import time as _t
    models = [model] if model else [m for m in TTS_MODELS if _EXHAUSTED.get(m, 0) <= _t.time()]
    if not models:
        raise RuntimeError("Gemini TTS: every model's free quota is spent (resets daily); enable billing or wait")
    last: Optional[Exception] = None
    for m in models:
        for attempt in range(2):
            try:
                out = call(m)
                log.info("tts via %s", m)
                return out
            except Exception as e:  # noqa: BLE001
                last = e
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or msg.startswith("429"):
                    wait = _retry_after(msg)
                    if wait <= 45 and attempt == 0:          # per-minute limit: wait it out once
                        _t.sleep(wait + 1)
                        continue
                    _EXHAUSTED[m] = _t.time() + wait
                    log.warning("tts model %s quota spent (retry in %.0fs); trying the next model", m, wait)
                    break
                if attempt == 0 and (" 500 " in f" {msg[:40]} " or "INTERNAL" in msg or " 503 " in f" {msg[:40]} "):
                    _t.sleep(2)
                    continue
                raise
    raise last if last else RuntimeError("no TTS model available")


def gemini_synthesize(client, text: str, style: str, voice: str, model: Optional[str] = None) -> Tuple[np.ndarray, int]:
    """Single-speaker synthesis. Style goes in as an inline [tag] inside the text (no style/system field exists)."""
    line = tagged(text, style)

    def one(m: str) -> Tuple[np.ndarray, int]:
        try:
            resp = client.interactions.create(model=m, input=line, response_modalities=["AUDIO"],
                                              speech_config=_voice_cfg_dict(voice))
            for mime, data in _walk(resp):
                return decode_audio_payload(mime, data)
            raise RuntimeError("interactions response had no audio")
        except (AttributeError, TypeError) as e:
            log.info("interactions API unavailable (%s); using generate_content", str(e)[:80])
        from google.genai import types
        cfg = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))))
        resp = client.models.generate_content(model=m, contents=line, config=cfg)
        for mime, data in _walk(resp):
            return decode_audio_payload(mime, data)
        raise RuntimeError("generate_content response had no audio")

    return _with_models(one, model)


def gemini_multispeaker(client, turns: List[Dict[str, str]], model: Optional[str] = None) -> Tuple[np.ndarray, int]:
    """turns: [{speaker, voice, text, style}] with exactly two distinct speakers."""
    from google.genai import types
    speakers = list(dict.fromkeys(t["speaker"] for t in turns))
    voice_of = {t["speaker"]: t["voice"] for t in turns}
    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[types.SpeakerVoiceConfig(speaker=s, voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_of[s]))) for s in speakers])))
    script = "\n".join(f'{t["speaker"]}: {tagged(t["text"], t.get("style", ""))}' for t in turns)

    def one(m: str) -> Tuple[np.ndarray, int]:
        resp = client.models.generate_content(model=m, contents=script, config=cfg)
        for mime, data in _walk(resp):
            return decode_audio_payload(mime, data)
        raise RuntimeError("multi-speaker response had no audio")

    return _with_models(one, model)


def design_voice(client, name: str, description: str) -> str:
    """Create a stored Voice Design profile (type='prompted', store=True); returns the custom voice id."""
    v = client.voices.create(type="prompted", store=True, name=name, prompt=description)
    vid = getattr(v, "id", None) or getattr(v, "name", None) or (v.get("id") if isinstance(v, dict) else None)
    if not vid:
        raise RuntimeError("voice design returned no id")
    return str(vid)


def split_on_gaps(x: np.ndarray, sr: int, parts: int, min_gap: float = 0.12) -> Optional[List[np.ndarray]]:
    """Split a multi-speaker take into `parts` clips at its (parts-1) longest silent gaps."""
    if parts <= 1:
        return [x]
    hop = sr // 100
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    silent = rms < rms.max() * 0.04
    gaps, i = [], 0
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            if i > 0 and j < n and (j - i) * hop / sr >= min_gap:
                gaps.append((j - i, (i + j) // 2))
            i = j
        else:
            i += 1
    if len(gaps) < parts - 1:
        return None
    cuts = sorted(c for _, c in sorted(gaps, reverse=True)[: parts - 1])
    bounds = [0] + [c * hop for c in cuts] + [len(x)]
    return [x[a:b] for a, b in zip(bounds, bounds[1:])]


# --------------------------------------------------------------------------- package synthesis
def resolve_voice(profile_id: str, index: schemas.LibraryIndex, lib: Path) -> Tuple[str, str]:
    """-> (gemini voice name or custom voice id, default style text)."""
    asset = index.get(profile_id, "12_voices")
    if asset:
        data = schemas.load_json(lib / asset.file_path)
        return data.get("gemini_voice_name") or asset.gemini_voice_name or "Charon", data.get("default_style", "")
    if profile_id in schemas.GEMINI_VOICES or profile_id.startswith("voice_"):
        return profile_id, ""
    return "Charon", ""


def group_dialogue(scenes: List[Any]) -> List[List[Any]]:
    """Group consecutive scenes spoken by exactly two alternating characters (<= MAX_GROUP_TURNS)."""
    groups: List[List[Any]] = []
    cur: List[Any] = []
    for sc in scenes:
        speakers = {s.narration.character_id for s in cur} | {sc.narration.character_id}
        alternates = bool(cur) and cur[-1].narration.character_id != sc.narration.character_id
        if cur and alternates and len(speakers) <= 2 and len(cur) < MAX_GROUP_TURNS:
            cur.append(sc)
        else:
            if cur:
                groups.append(cur)
            cur = [sc]
    if cur:
        groups.append(cur)
    return groups


SAY_SUFFIX = "_say"
SAY_VOICES = ["Puck", "Aoede", "Fenrir", "Kore", "Charon"]   # the stickman's default voices, in order of preference


def say_voice_for(narrator_voice: str) -> str:
    """A voice for the stickman's own lines that differs from the narrator's."""
    return next((v for v in SAY_VOICES if v != narrator_voice), SAY_VOICES[0])


def _style(sc, base_style: str) -> str:
    d = sc.narration.prosody.acting_direction
    return f"{base_style} {d}".strip() if base_style else d


def synthesize_package(pkg: schemas.AnalysisPackage, out_dir: Path, placeholder: Optional[bool] = None,
                       library: Optional[Path] = None, force: bool = False) -> Dict[str, Dict[str, Any]]:
    """Write <out>/audio/<scene_id>.wav (+ .json word timings). Returns per-scene info dict."""
    lib = library or common.library_dir()
    index = schemas.load_library_index(lib)
    adir = Path(out_dir) / "audio"
    adir.mkdir(parents=True, exist_ok=True)

    client = None
    if placeholder is None and use_chatterbox():
        placeholder = False
    elif placeholder is None:
        try:
            if not llm.api_key("gemini"):
                raise RuntimeError("no Gemini API key")
            client = _client()
            placeholder = False
        except Exception as e:  # noqa: BLE001
            log.warning("Gemini TTS unavailable (%s): using PLACEHOLDER voice", str(e)[:100])
            placeholder = True
    elif not placeholder and not use_chatterbox():
        client = _client()

    info: Dict[str, Dict[str, Any]] = {}

    def finish(sc, x: np.ndarray, sr: int, is_ph: bool, key: str, stem: Optional[str] = None,
               pace: Optional[float] = None, text: Optional[str] = None) -> None:
        stem = stem or sc.id
        if sr != SR:
            x = np.interp(np.arange(int(len(x) * SR / sr)) / SR, np.arange(len(x)) / sr, x).astype(np.float32)
        x = apply_pace(x, SR, sc.narration.prosody.pace_multiplier if pace is None else pace)
        write_wav(adir / f"{stem}.wav", x, SR)
        words = align_words(text or sc.narration.text, x, SR)
        meta = {"scene_id": stem, "key": key, "placeholder": is_ph, "duration_sec": round(len(x) / SR, 3),
                "words": words}
        (adir / f"{stem}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        info[stem] = {"wav": str(adir / f"{stem}.wav"), **meta}

    def cache_key(sc, voice: str, style: str) -> str:
        return hashlib.sha1(f"{sc.narration.text}|{voice}|{style}|{sc.narration.prosody.pace_multiplier}|{placeholder}|{use_chatterbox()}|{canvas_tts.enabled()}".encode()).hexdigest()[:16]

    def cached(sc, key: str, stem: Optional[str] = None) -> bool:
        stem = stem or sc.id
        mp = adir / f"{stem}.json"
        if force or not mp.is_file() or not (adir / f"{stem}.wav").is_file():
            return False
        meta = json.loads(mp.read_text(encoding="utf-8"))
        if meta.get("key") != key:
            return False
        if meta.get("placeholder") and not placeholder:
            return False  # a robotic fallback from an earlier quota failure: retry the real voice
        info[stem] = {"wav": str(adir / f"{stem}.wav"), **meta}
        return True

    for group in group_dialogue(pkg.scenes):
        voices = {sc.id: resolve_voice(sc.narration.voice_profile_id, index, lib) for sc in group}
        keys = {sc.id: cache_key(sc, voices[sc.id][0], _style(sc, voices[sc.id][1])) for sc in group}
        todo = [sc for sc in group if not cached(sc, keys[sc.id])]
        if not todo:
            continue
        if placeholder:
            for sc in todo:
                x, sr = placeholder_speech(sc.narration.text, voices[sc.id][0])
                finish(sc, x, sr, True, keys[sc.id])
            continue
        done_multi = False
        if not use_chatterbox() and len(group) >= 2 and len(todo) == len(group) and len({s.narration.character_id for s in group}) == 2:
            try:
                names = {cid: f"Speaker{i + 1}" for i, cid in enumerate(dict.fromkeys(s.narration.character_id for s in group))}
                turns = [{"speaker": names[s.narration.character_id], "voice": voices[s.id][0],
                          "text": s.narration.text, "style": _style(s, voices[s.id][1])} for s in group]
                x, sr = gemini_multispeaker(client, turns)
                parts = split_on_gaps(x, sr, len(group))
                if parts:
                    for sc, part in zip(group, parts):
                        finish(sc, part, sr, False, keys[sc.id])
                    done_multi = True
                else:
                    log.info("multi-speaker split failed; synthesizing turns separately")
            except Exception as e:  # noqa: BLE001
                log.warning("multi-speaker failed (%s); synthesizing turns separately", str(e)[:120])
        if not done_multi:
            for sc in todo:
                voice, base = voices[sc.id]
                try:
                    x, sr = synth_line(client, sc.narration.text, _style(sc, base), voice)
                    finish(sc, x, sr, False, keys[sc.id])
                except Exception as e:  # noqa: BLE001 - keep the pipeline alive; mark placeholder
                    log.warning("TTS failed for %s (%s): placeholder used", sc.id, str(e)[:120])
                    x, sr = placeholder_speech(sc.narration.text, voice)
                    finish(sc, x, sr, True, keys[sc.id])

    # the stickman's own lines: one short clip per scene that has `speech`, in a voice that contrasts the narrator
    for sc in pkg.scenes:
        sp = sc.speech
        if sp is None:
            continue
        stem = f"{sc.id}{SAY_SUFFIX}"
        narr_voice = resolve_voice(sc.narration.voice_profile_id, index, lib)[0]
        if sp.voice_profile_id:
            voice, base = resolve_voice(sp.voice_profile_id, index, lib)
        else:
            voice, base = say_voice_for(narr_voice), ""
        style = f"{base} {sp.acting_direction}".strip()
        key = hashlib.sha1(f"{sp.text}|{voice}|{style}|say|{placeholder}|{use_chatterbox()}|{canvas_tts.enabled()}".encode()).hexdigest()[:16]
        if cached(sc, key, stem):
            continue
        if not placeholder:
            try:
                x, sr = synth_line(client, sp.text, style, voice)
                finish(sc, x, sr, False, key, stem, 1.0, sp.text)
                continue
            except Exception as e:  # noqa: BLE001 - keep the pipeline alive; mark placeholder
                log.warning("TTS failed for %s (%s): placeholder used", stem, str(e)[:120])
        x, sr = placeholder_speech(sp.text, voice)
        finish(sc, x, sr, True, key, stem, 1.0, sp.text)
    return info


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    pkg = schemas.load_package(a.package)
    info = synthesize_package(pkg, Path(a.out), True if a.placeholder else None, force=a.force)
    for sid, m in info.items():
        print(f"{sid}: {m['duration_sec']:.2f}s {'(placeholder)' if m['placeholder'] else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
