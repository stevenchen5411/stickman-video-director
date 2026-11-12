#!/usr/bin/env python3
"""Audio-first assembly + FFmpeg psychoacoustic mastering.

Pipeline (48 kHz):
  1. Assemble voice: per-scene clips (silence-trimmed) + post_breath_pause_ms, 15 ms cosine fades at every clip
     boundary (inside the pause, so timing never drifts), over a continuous -48 dBFS room-tone bed.
  2. Voice chain in FFmpeg: highpass=f=80, +2 dB high shelf at 3.2 kHz, acompressor 3:1.
  3. emphasis_words[].trigger_sfx placed at estimated word timestamps, level = scene voice RMS - 12 dB.
  4. BGM (13_bgm loop): ducked exactly -20 dB while speech is active (envelope computed from the voice track,
     100 Hz VAD, 30 ms attack / 300 ms release); bgm_drop_on_climax mutes it 150 ms before the punchline word.
  5. amix -> loudnorm I=-14 TP=-1.0 LRA=7 (two-pass, linear) -> master.wav.
Also writes timeline.json (scene start/speech/pause/end + scene-relative word timings) used by the renderer.

CLI: python3 engine/audio_master.py --package PATH --audio-dir DIR --out DIR
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import common
import schemas
import tts_expressive as tts

log = common.log
SR = 48000
FADE_SEC = 0.015
ROOM_TONE_DBFS = -48.0
SFX_UNDER_VOICE_DB = -12.0
DUCK_DB = -20.0
BGM_BASE_RMS_DB = -16.0
PRE_CLIMAX_MUTE_SEC = 0.150
TAIL_SEC = 0.25


# --------------------------------------------------------------------------- I/O
def decode(path: Path, sr: int = SR, channels: int = 1) -> np.ndarray:
    cp = common.run([common.ffmpeg_bin(), "-v", "error", "-i", str(path), "-ar", str(sr), "-ac", str(channels),
                     "-f", "f32le", "-"])
    x = np.frombuffer(cp.stdout, dtype="<f4")
    return x.reshape(-1, channels).T.copy() if channels > 1 else x.copy()


def write_pcm16(path: Path, x: np.ndarray, sr: int = SR) -> None:
    arr = np.atleast_2d(x)
    pcm = (np.clip(arr, -1, 1) * 32767).astype("<i2").T.copy()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(arr.shape[0])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def rms_db(x: np.ndarray) -> float:
    r = float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0
    return 20 * math.log10(max(r, 1e-9))


def cosine_fade(x: np.ndarray, sr: int = SR, fade: float = FADE_SEC) -> np.ndarray:
    n = min(int(fade * sr), len(x) // 2)
    if n > 0:
        ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)
        x[:n] *= ramp
        x[-n:] *= ramp[::-1]
    return x


# --------------------------------------------------------------------------- timeline
def frame_spans(timeline: Dict[str, Any], fps: int) -> List[Tuple[int, int]]:
    """Cumulative-ceil frame spans per scene: end_frame_i = ceil(end_sec_i * fps) (no drift vs. audio)."""
    spans, prev = [], 0
    for s in timeline["scenes"]:
        end = max(prev + 1, math.ceil(s["end_sec"] * fps - 1e-9))
        spans.append((prev, end))
        prev = end
    return spans


def norm_phrase(w: str) -> List[str]:
    return [tts.norm_word(t) for t in w.split() if tts.norm_word(t)]


def find_phrase(words: List[Dict[str, Any]], phrase: str) -> Optional[Tuple[int, int]]:
    target = norm_phrase(phrase)
    toks = [tts.norm_word(w["word"]) for w in words]
    for i in range(len(toks) - len(target) + 1):
        if target and toks[i:i + len(target)] == target:
            return i, i + len(target) - 1
    return None


SAY_GAP_SEC = 0.16   # breath between the narrator and the stickman's own line inside one scene


def _load_clip(audio_dir: Path, stem: str) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Trimmed, faded 48 kHz clip + its word timings relative to the trimmed start."""
    wav = audio_dir / f"{stem}.wav"
    meta_p = audio_dir / f"{stem}.json"
    if not wav.is_file():
        raise FileNotFoundError(f"missing TTS audio for {stem}: {wav}")
    x24, sr24 = tts.read_wav(wav)
    t0, t1 = tts.trim_bounds(x24, sr24)
    a, b = max(0.0, t0 - 0.03), min(len(x24) / sr24, t1 + 0.03)
    x = cosine_fade(decode(wav)[int(a * SR): int(b * SR)].astype(np.float64))
    words_raw = json.loads(meta_p.read_text(encoding="utf-8"))["words"] if meta_p.is_file() else []
    words = [{"word": w["word"], "start": round(max(0.0, w["start"] - a), 3), "end": round(max(0.0, w["end"] - a), 3)}
             for w in words_raw]
    return x, words


def _shift(words: List[Dict[str, Any]], off: float) -> List[Dict[str, Any]]:
    return [{"word": w["word"], "start": round(w["start"] + off, 3), "end": round(w["end"] + off, 3)} for w in words]


def build_timeline(pkg: schemas.AnalysisPackage, audio_dir: Path
                   ) -> Tuple[Dict[str, Any], np.ndarray, List[np.ndarray]]:
    """Returns (timeline, voice_track_mono, per-scene narration clips) at 48 kHz.

    A scene with `speech` holds two clips: the narrator and the stickman's own line, in the order set by
    speech.placement. `words` stays the narration's (scene-relative) so sfx and climax cues keep working;
    the stickman's line is in the scene's `say` entry.
    """
    scenes_tl: List[Dict[str, Any]] = []
    clips: List[np.ndarray] = []
    placed: List[Tuple[float, np.ndarray]] = []
    t = 0.0
    for sc in pkg.scenes:
        x, words = _load_clip(audio_dir, sc.id)
        n_len = len(x) / SR
        say_entry = None
        narr_off, speech = 0.0, n_len
        if sc.speech and (audio_dir / f"{sc.id}{tts.SAY_SUFFIX}.wav").is_file():
            y, ywords = _load_clip(audio_dir, f"{sc.id}{tts.SAY_SUFFIX}")
            y_len = len(y) / SR
            if sc.speech.placement == "before":
                say_off, narr_off = 0.0, y_len + SAY_GAP_SEC
            else:
                narr_off, say_off = 0.0, n_len + SAY_GAP_SEC
            speech = n_len + SAY_GAP_SEC + y_len
            say_entry = {"text": sc.speech.text, "start": round(say_off, 4), "end": round(say_off + y_len, 4),
                         "words": _shift(ywords, say_off)}
            placed.append((t + say_off, y))
        words = _shift(words, narr_off)
        pause = sc.narration.prosody.post_breath_pause_ms / 1000.0
        entry = {"scene_id": sc.id, "start_sec": round(t, 4), "speech_sec": round(speech, 4),
                 "pause_sec": round(pause, 4), "end_sec": round(t + speech + pause, 4), "words": words}
        if say_entry:
            entry["say"] = say_entry
        scenes_tl.append(entry)
        clips.append(x)
        placed.append((t + narr_off, x))
        t += speech + pause
    total = t + TAIL_SEC
    scenes_tl[-1]["end_sec"] = round(total, 4)  # tail belongs to the last scene
    voice = np.zeros(int(math.ceil(total * SR)))
    for at, x in placed:
        s = int(round(at * SR))
        voice[s:s + len(x)] += x[: len(voice) - s]
    return {"sample_rate": SR, "total_sec": round(total, 4), "scenes": scenes_tl,
            "bgm_id": pkg.render_config.bgm_id}, voice, clips


def room_tone(n: int, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    x = np.cumsum(x)                                   # brown-ish noise: low-frequency room rumble
    x -= np.convolve(x, np.ones(4800) / 4800, mode="same")  # remove DC drift
    x *= 10 ** (ROOM_TONE_DBFS / 20) / (np.sqrt(np.mean(x ** 2)) or 1.0)
    return x


def place_sfx(pkg: schemas.AnalysisPackage, timeline: Dict[str, Any], clips: List[np.ndarray], lib: Path,
              index: schemas.LibraryIndex, n: int) -> np.ndarray:
    track = np.zeros(n)
    cache: Dict[str, np.ndarray] = {}
    for sc, tl, clip in zip(pkg.scenes, timeline["scenes"], clips):
        voice_db = rms_db(clip)
        for e in sc.narration.prosody.emphasis_words:
            if not e.trigger_sfx:
                continue
            asset = index.get(e.trigger_sfx, "14_sfx")
            hit = find_phrase(tl["words"], e.word)
            if not asset or hit is None:
                continue
            if e.trigger_sfx not in cache:
                cache[e.trigger_sfx] = decode(lib / asset.file_path).astype(np.float64)
            s = cache[e.trigger_sfx]
            gain = 10 ** ((voice_db + SFX_UNDER_VOICE_DB - rms_db(s)) / 20)
            clipped = np.clip(s * gain, -0.9, 0.9)
            start = int(round((tl["start_sec"] + tl["words"][hit[0]]["start"]) * SR))
            end = min(n, start + len(clipped))
            if start < n:
                track[start:end] += clipped[: end - start]
    return track


def duck_envelope(voice: np.ndarray, sr: int = SR, depth_db: float = DUCK_DB) -> np.ndarray:
    """Per-sample linear gain: depth_db while speech is active, 0 dB otherwise (30 ms attack, 300 ms release)."""
    hop = sr // 100
    n = len(voice) // hop + 1
    pad = np.pad(voice, (0, n * hop - len(voice)))
    rms = np.sqrt(np.mean(pad.reshape(n, hop) ** 2, axis=1))
    active = (rms > max(rms.max() * 0.03, 1e-5)).astype(float)
    k = 10  # dilate 100 ms so ducking spans word gaps
    active = (np.convolve(active, np.ones(2 * k + 1), mode="same") > 0).astype(float)
    a_att, a_rel = 1 - math.exp(-1 / (0.03 * 100)), 1 - math.exp(-1 / (0.3 * 100))
    env, cur = np.zeros(n), 0.0
    for i, tgt in enumerate(active):
        cur += (tgt - cur) * (a_att if tgt > cur else a_rel)
        env[i] = cur
    gain_frames = 10 ** (depth_db * env / 20)
    return np.interp(np.arange(len(voice)) / sr, (np.arange(n) + 0.5) * hop / sr, gain_frames)


def climax_mute(pkg: schemas.AnalysisPackage, timeline: Dict[str, Any], n: int) -> np.ndarray:
    g = np.ones(n)
    ramp = int(0.02 * SR)
    for sc, tl in zip(pkg.scenes, timeline["scenes"]):
        if not sc.narration.prosody.bgm_drop_on_climax or not tl["words"]:
            continue
        idx = len(tl["words"]) - 1
        for e in reversed(sc.narration.prosody.emphasis_words):
            hit = find_phrase(tl["words"], e.word)
            if hit:
                idx = hit[0]
                break
        punch = tl["start_sec"] + tl["words"][idx]["start"]
        a = max(0, int((punch - PRE_CLIMAX_MUTE_SEC) * SR))
        b = min(n, int((tl["end_sec"] + 0.1) * SR))
        g[a:b] = 0.0
        fi = min(n, a + ramp)
        g[a:fi] = np.linspace(1, 0, fi - a)
        ri = min(n, b + int(0.4 * SR))
        g[b:ri] = np.linspace(0, 1, ri - b)
    return g


def bgm_track(path: Path, n: int, voice: np.ndarray, mute: np.ndarray) -> np.ndarray:
    loop = decode(path, SR, 2).astype(np.float64)
    reps = int(math.ceil(n / loop.shape[1]))
    bed = np.tile(loop, (1, reps))[:, :n]
    bed *= 10 ** ((BGM_BASE_RMS_DB - rms_db(bed)) / 20)
    bed *= (duck_envelope(voice) * mute)[None, :]
    fade = min(n, int(1.0 * SR))
    bed[:, -fade:] *= np.linspace(1, 0, fade)[None, :]
    return bed


# --------------------------------------------------------------------------- ffmpeg mastering
VOICE_CHAIN = ("highpass=f=80,highshelf=f=3200:g=2,"
               "acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=1")


def _graph(loud_args: str) -> str:
    return (f"[0:a]{VOICE_CHAIN},pan=stereo|c0=c0|c1=c0[v];"
            "[1:a]pan=stereo|c0=c0|c1=c0[s];[2:a]pan=stereo|c0=c0|c1=c0[r];[3:a]anull[b];"
            "[v][s][r][b]amix=inputs=4:duration=longest:normalize=0[m];"
            f"[m]loudnorm={loud_args}[out]")


def master_mix(stems: List[Path], out_wav: Path) -> Dict[str, Any]:
    ff = common.ffmpeg_bin()
    ins: List[str] = []
    for s in stems:
        ins += ["-i", str(s)]
    base = "I=-14:TP=-1.0:LRA=7"
    p1 = common.run([ff, "-hide_banner", "-y", *ins, "-filter_complex", _graph(base + ":print_format=json"),
                     "-map", "[out]", "-f", "null", "-"])
    txt = p1.stderr.decode("utf-8", "replace")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", txt, re.S)
    if not m:
        raise RuntimeError("loudnorm pass 1 produced no measurements")
    meas = json.loads(m.group(0))
    second = (f"{base}:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:measured_LRA={meas['input_lra']}"
              f":measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true")
    common.run([ff, "-hide_banner", "-y", *ins, "-filter_complex", _graph(second), "-map", "[out]",
                "-ar", str(SR), "-c:a", "pcm_s16le", str(out_wav)])
    return meas


def master_package(pkg: schemas.AnalysisPackage, audio_dir: Path, out_dir: Path,
                   library: Optional[Path] = None) -> Dict[str, Any]:
    lib = library or common.library_dir()
    index = schemas.load_library_index(lib)
    out_dir.mkdir(parents=True, exist_ok=True)
    timeline, voice, clips = build_timeline(pkg, audio_dir)
    n = len(voice)
    sfx = place_sfx(pkg, timeline, clips, lib, index, n)
    tone = room_tone(n)
    bgm_asset = index.get(pkg.render_config.bgm_id, "13_bgm")
    if bgm_asset:
        bed = bgm_track(lib / bgm_asset.file_path, n, voice, climax_mute(pkg, timeline, n))
    else:
        log.warning("bgm %s not in library; mastering without BGM", pkg.render_config.bgm_id)
        bed = np.zeros((2, n))
    tmp = common.tmpdir()
    stems = [tmp / f"stem_{pkg.package_id}_{k}.wav" for k in ("voice", "sfx", "room", "bgm")]
    try:
        write_pcm16(stems[0], voice * 0.9)
        write_pcm16(stems[1], sfx)
        write_pcm16(stems[2], tone)
        write_pcm16(stems[3], bed)
        master = out_dir / "master.wav"
        meas = master_mix(stems, master)
    finally:
        for s in stems:
            s.unlink(missing_ok=True)
    (out_dir / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return {"master": str(master), "timeline": timeline, "loudnorm_pass1": meas}


def load_timeline(out_dir: Path) -> Dict[str, Any]:
    return json.loads((Path(out_dir) / "timeline.json").read_text(encoding="utf-8"))


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", required=True)
    ap.add_argument("--audio-dir", required=True, help="dir containing audio/<scene>.wav from tts_expressive")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    pkg = schemas.load_package(a.package)
    r = master_package(pkg, Path(a.audio_dir), Path(a.out))
    print(f"master: {r['master']}  total {r['timeline']['total_sec']:.2f}s  (pass-1 input {r['loudnorm_pass1']['input_i']} LUFS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
