#!/usr/bin/env python3
"""Seed the 14-category starter asset library (idempotent; regenerates deterministically).

Writes JSON/SVG assets, synthesizes starter WAV/OGG audio with numpy + ffmpeg
(no network, no pycairo needed), and (re)builds assets/library/library_index.json.

Usage: python3 bootstrap/seed_assets.py [--library DIR]

Notes
  * `perceptual_hash` is a content-SHA1 prefix until `engine/forge.py --rebuild-thumbs`
    replaces it with a real pHash computed from the rendered 256x256 thumbnail.
  * Thumbnails (.thumbs/<id>.png) are produced by forge.py in Milestone 2.
  * Voice previews are synthetic formant placeholders; real Gemini TTS previews overwrite them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SR = 44100
VSR = 24000
RNG = np.random.default_rng(1234)

INDEX: list[dict] = []
LIB: Path = Path(".")

THUMB_CATS = {"01_characters", "02_poses", "03_expressions", "04_motions", "05_scenes", "06_props",
              "07_widgets", "08_overlays", "09_transitions", "10_caption_styles", "11_themes"}


# ----------------------------------------------------------------- file helpers
def _write_text(rel: str, text: str) -> None:
    p = LIB / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _register(cat: str, aid: str, rel: str, scope: str, tags: list[str], **extra) -> None:
    digest = hashlib.sha1((LIB / rel).read_bytes()).hexdigest()[:12]
    entry = {
        "id": aid,
        "category": cat,
        "scope": scope,
        "niche_tags": tags,
        "file_path": rel,
        "usage_count": 0,
        "perceptual_hash": digest,
    }
    if cat in THUMB_CATS:
        entry["thumb_path"] = f".thumbs/{aid}.png"
    entry.update({k: v for k, v in extra.items() if v is not None})
    INDEX.append(entry)


def jasset(cat: str, aid: str, obj: dict, scope="global", tags=None, **extra) -> None:
    rel = f"{cat}/{aid}.json"
    _write_text(rel, json.dumps({"id": aid, **obj}, indent=2) + "\n")
    _register(cat, aid, rel, scope, tags or ["general"], **extra)


def sasset(cat: str, aid: str, svg: str, scope="global", tags=None) -> None:
    rel = f"{cat}/{aid}.svg"
    _write_text(rel, svg.strip() + "\n")
    _register(cat, aid, rel, scope, tags or ["general"])


# ----------------------------------------------------------------- audio helpers
def _t(n: int, sr: int = SR) -> np.ndarray:
    return np.arange(n) / sr


def _norm(x: np.ndarray, peak: float = 0.8) -> np.ndarray:
    m = float(np.max(np.abs(x))) or 1.0
    return x * (peak / m)


def _write_wav(path: Path, data: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.atleast_2d(data)
    pcm = (np.clip(arr, -1, 1) * 32767).astype("<i2").T.copy()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(arr.shape[0])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def _lowpass(x: np.ndarray, width: int) -> np.ndarray:
    return np.convolve(x, np.ones(width) / width, mode="same")


def sfx_clock_tick():
    n = int(0.12 * SR); t = _t(n)
    return _norm((np.sin(2 * np.pi * 2400 * t) * 0.7 + RNG.standard_normal(n) * 0.3) * np.exp(-t / 0.012))


def sfx_thud_soft():
    n = int(0.45 * SR); t = _t(n)
    f = 55 + 70 * np.exp(-t / 0.05)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    click = _lowpass(RNG.standard_normal(n), 40) * np.exp(-t / 0.02) * 2
    return _norm(body + click * 0.4)


def sfx_whoosh_fast():
    n = int(0.6 * SR); t = _t(n)
    env = np.sin(np.pi * t / t[-1]) ** 2
    sweep = np.sin(2 * np.pi * np.cumsum(300 + 2600 * (t / t[-1]) ** 2) / SR)
    return _norm((_lowpass(RNG.standard_normal(n), 6) * 0.8 + sweep * 0.25) * env)


def sfx_pop_bubble():
    n = int(0.16 * SR); t = _t(n)
    f = 200 + 700 * np.exp(-t / 0.02)
    return _norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05))


def sfx_ding_success():
    n = int(1.1 * SR); t = _t(n)
    s = np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t) + 0.2 * np.sin(2 * np.pi * 2640 * t)
    return _norm(s * np.exp(-t / 0.28) * np.minimum(1, t / 0.004))


def sfx_glitch_blip():
    n = int(0.22 * SR); t = _t(n)
    steps = np.repeat(RNG.choice([440, 660, 990, 1320, 1760], size=11), n // 11 + 1)[:n]
    return _norm(np.sign(np.sin(2 * np.pi * np.cumsum(steps) / SR)) * 0.5 * np.exp(-t / 0.12))


def _place(buf: np.ndarray, sig: np.ndarray, start: int, pan: float = 0.5, gain: float = 1.0) -> None:
    """Add `sig` into stereo buf at `start`, wrapping around the loop end (seamless loops)."""
    n = buf.shape[1]
    idx = (start + np.arange(len(sig))) % n
    np.add.at(buf[0], idx, sig * gain * (1 - pan) * 1.4142)
    np.add.at(buf[1], idx, sig * gain * pan * 1.4142)


def _snap(f: float, dur: float) -> float:
    """Snap frequency so an integer number of cycles fits in `dur` seconds (click-free loop)."""
    return round(f * dur) / dur


def bgm_tense_clockwork_pulse():
    dur, bpm = 16.0, 120
    n = int(dur * SR); t = _t(n)
    buf = np.zeros((2, n))
    beat = 60 / bpm
    drone = (np.sin(2 * np.pi * _snap(55, dur) * t) + 0.5 * np.sin(2 * np.pi * _snap(82.5, dur) * t)) \
        * (0.7 + 0.3 * np.sin(2 * np.pi * t / dur * 2))
    buf += drone * 0.35
    tick = sfx_clock_tick()
    for i in range(int(dur / (beat / 2))):
        _place(buf, tick, int(i * beat / 2 * SR), pan=0.3 if i % 2 else 0.7, gain=0.55 if i % 8 == 0 else 0.28)
    kick = sfx_thud_soft()
    for i in range(int(dur / beat)):
        _place(buf, kick, int(i * beat * SR), gain=0.45 if i % 4 == 0 else 0.25)
    return _norm(buf, 0.7)


def bgm_calm_ambient_pad():
    dur = 16.0
    n = int(dur * SR); t = _t(n)
    buf = np.zeros((2, n))
    chords = [(220, 261.63, 329.63), (174.61, 220, 261.63), (261.63, 329.63, 392), (196, 246.94, 293.66)]
    win = np.hanning(int(8 * SR))
    for i, ch in enumerate(chords):
        pad = sum(np.sin(2 * np.pi * _snap(f, dur) * t) + 0.3 * np.sin(2 * np.pi * _snap(f * 2, dur) * t) for f in ch)
        w = np.zeros(n); w[: len(win)] = win
        w = np.roll(w, int((i * 4 - 2) * SR))
        buf[0] += pad * w * 0.12
        buf[1] += np.roll(pad, 137) * w * 0.12
    return _norm(buf, 0.6)


def bgm_upbeat_lofi_groove():
    dur, bpm = 16.0, 90
    n = int(round(dur * SR)); buf = np.zeros((2, n))
    beat = 60 / bpm
    kick, snare, hat = sfx_thud_soft(), sfx_pop_bubble(), sfx_clock_tick()
    for b in range(int(dur / beat)):
        s = int(b * beat * SR)
        if b % 4 in (0, 2):
            _place(buf, kick, s, gain=0.7)
        if b % 4 in (1, 3):
            _place(buf, snare, s, gain=0.45)
        _place(buf, hat, s, pan=0.65, gain=0.2)
        _place(buf, hat, s + int(beat / 2 * SR), pan=0.35, gain=0.14)
    bass_notes = [110, 87.31, 130.81, 98]
    bar = beat * 4
    for i, f in enumerate(bass_notes + bass_notes[:2]):
        m = int(bar * SR); tt = _t(m)
        note = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.9) * np.minimum(1, tt / 0.01)
        _place(buf, note, int(i * bar * SR), gain=0.4)
    chords = [(220, 261.63, 329.63), (174.61, 220, 261.63), (261.63, 329.63, 392), (196, 246.94, 293.66)]
    for i, ch in enumerate(chords + chords[:2]):
        m = int(beat * 2 * SR); tt = _t(m)
        stab = sum(np.sin(2 * np.pi * f * tt) for f in ch) * np.exp(-tt / 0.35)
        _place(buf, stab, int((i * bar + beat) * SR), gain=0.12)
    return _norm(buf, 0.7)


def voice_preview(f0: float, vowels: list[tuple[float, float]], seed: int) -> np.ndarray:
    syl = 0.26
    n = int(syl * len(vowels) * VSR); out = np.zeros(n)
    for i, (f1, f2) in enumerate(vowels):
        m = int(syl * VSR); tt = np.arange(m) / VSR
        pitch = f0 * (1 + 0.04 * np.sin(2 * np.pi * 5 * tt + seed)) * (1.08 - 0.12 * i / max(1, len(vowels)))
        phase = 2 * np.pi * np.cumsum(pitch) / VSR
        sig = np.zeros(m)
        for h in range(1, int(4000 / f0)):
            fh = h * f0
            amp = (np.exp(-((fh - f1) / 150) ** 2) + 0.6 * np.exp(-((fh - f2) / 250) ** 2) + 0.05) / h
            sig += amp * np.sin(h * phase)
        env = np.sin(np.pi * tt / tt[-1]) ** 0.7
        out[int(i * syl * VSR): int(i * syl * VSR) + m] += sig * env
    return _norm(out, 0.6)


def _to_ogg(wav_path: Path, ogg_path: Path) -> None:
    ogg_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
                    "-c:a", "libvorbis", "-q:a", "4", str(ogg_path)], check=True)


# ----------------------------------------------------------------- SVG snippets
def svg(w: int, h: int, body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{body}</svg>'


# ----------------------------------------------------------------- build
def build_characters():
    base = {"format": "stickman_rig/v1", "units": "fraction_of_height",
            "rig": {"head_radius": 0.085, "neck": 0.03, "torso": 0.26, "upper_arm": 0.14, "forearm": 0.13,
                    "thigh": 0.18, "shin": 0.18, "line_width": 0.012, "hand_radius": 0.016}}
    chars = [
        ("kael_hoodie", "Kael", "Charon", "kael_calm_charon", ["calm", "authority", "narrator"], "#22d3ee",
         ["explainer", "psychology", "tech"], {"type": "hoodie", "color": "#334155", "hood_up": False}),
        ("nova_scientist", "Nova", "Kore", "nova_bright_kore", ["curious", "precise", "upbeat"], "#a78bfa",
         ["science", "explainer", "health"], {"type": "labcoat", "color": "#e2e8f0", "glasses": True}),
        ("rex_coach", "Rex", "Fenrir", "rex_bold_fenrir", ["bold", "intense", "motivational"], "#f97316",
         ["fitness", "business", "stoicism"], {"type": "tank", "color": "#b91c1c", "headband": True}),
        ("pip_sidekick", "Pip", "Puck", "pip_quirky_puck", ["playful", "quirky", "comic"], "#facc15",
         ["comedy", "gaming", "explainer"], {"type": "cap", "color": "#16a34a", "cap_backwards": True}),
        ("luna_sage", "Luna", "Aoede", "luna_warm_aoede", ["warm", "wise", "gentle"], "#f472b6",
         ["stoicism", "psychology", "storytelling"], {"type": "scarf", "color": "#f472b6", "hair": "bun"}),
    ]
    for cid, name, voice, vp, pers, accent, tags, acc in chars:
        jasset("01_characters", cid, {**base, "name": name, "personality_tags": pers,
                                      "default_voice_id": voice, "default_voice_profile_id": vp,
                                      "colors": {"line": "#f1f5f9", "fill": "#0f172a", "accent": accent},
                                      "accessory": acc},
               tags=tags, default_voice_id=voice)


def build_poses():
    def pose(aid, joints, anchors, tags):
        jasset("02_poses", aid, {"format": "pose/v1", "angles_unit": "degrees_from_vertical",
                                 "joints": joints, "hand_anchors": anchors}, tags=tags)
    J = lambda **k: {"torso_lean": 0, "neck": 0, "l_shoulder": 8, "l_elbow": 5, "r_shoulder": -8, "r_elbow": -5,
                     "l_hip": 4, "l_knee": 0, "r_hip": -4, "r_knee": 0, **k}
    pose("standing_neutral", J(), {"l": "free", "r": "free"}, ["idle"])
    pose("holding_head", J(l_shoulder=150, l_elbow=120, r_shoulder=-150, r_elbow=-120, neck=-6),
         {"l": "head_side", "r": "head_side"}, ["stress", "shock"])
    pose("pointing_right", J(r_shoulder=-80, r_elbow=0, l_shoulder=10, torso_lean=3),
         {"l": "free", "r": "point"}, ["explain"])
    pose("arms_crossed", J(l_shoulder=35, l_elbow=115, r_shoulder=-35, r_elbow=-115),
         {"l": "chest", "r": "chest"}, ["confident"])
    pose("shrug", J(l_shoulder=40, l_elbow=70, r_shoulder=-40, r_elbow=-70, neck=4),
         {"l": "free", "r": "free"}, ["unsure", "comic"])
    pose("running", J(l_shoulder=50, l_elbow=90, r_shoulder=-50, r_elbow=-90, l_hip=40, l_knee=60,
                      r_hip=-35, r_knee=10, torso_lean=12), {"l": "free", "r": "free"}, ["action"])
    pose("holding_prop_right", J(r_shoulder=-60, r_elbow=-70), {"l": "free", "r": "prop_grip"}, ["props"])


def build_expressions():
    def expr(aid, brow_l, brow_r, eye_open, pupil, mouth, tags):
        jasset("03_expressions", aid, {"format": "expression/v1",
                                       "brows": {"l_angle": brow_l, "r_angle": brow_r, "raise": 0.0},
                                       "eyes": {"open": eye_open, "pupil_scale": pupil, "look": [0, 0]},
                                       "mouth_rest": mouth}, tags=tags)
    expr("neutral", 0, 0, 0.8, 1.0, "flat", ["idle"])
    expr("wide_eyed_shock", -15, 15, 1.0, 0.45, "open_small", ["shock", "surprise"])
    expr("smirk_confident", 10, -5, 0.65, 1.0, "smirk_right", ["confident"])
    expr("worried_brow", -22, 22, 0.9, 0.8, "wobble", ["worry", "stress"])
    expr("angry_squint", 25, -25, 0.45, 1.0, "grit", ["anger"])
    jasset("03_expressions", "viseme_default", {
        "format": "viseme_set/v1",
        "visemes": {"rest": {"open": 0.0, "width": 0.5}, "A": {"open": 0.9, "width": 0.7},
                    "E": {"open": 0.5, "width": 1.0}, "O": {"open": 0.7, "width": 0.35},
                    "M": {"open": 0.0, "width": 0.6}},
        "amplitude_thresholds": {"rest": 0.02, "E": 0.18, "O": 0.35, "A": 0.55},
        "notes": "Pick by word-level phoneme class when alignment exists, else by RMS amplitude bands."},
        tags=["mouth_sync"])


def build_motions():
    def mot(aid, kind, dur, loop, tracks, tags, **extra):
        jasset("04_motions", aid, {"format": "motion/v1", "kind": kind, "duration_sec": dur, "loop": loop,
                                   "tracks": tracks, **extra}, tags=tags)
    mot("camera_punch_in", "camera", 0.35, False,
        [{"target": "camera.scale", "keys": [[0, 1.0, "linear"], [0.35, 1.22, "expo_out"]]}], ["emphasis", "hook"])
    mot("camera_pan_right", "camera", 1.2, False,
        [{"target": "camera.x", "keys": [[0, 0.0, "linear"], [1.2, 0.08, "ease_in_out"]]}], ["travel"])
    mot("idle_breathing", "character", 2.4, True,
        [{"target": "torso.scale_y", "keys": [[0, 1.0, "sine"], [1.2, 1.018, "sine"], [2.4, 1.0, "sine"]]}], ["idle"])
    mot("shake_nervous", "character", 0.5, True,
        [{"target": "character.x", "keys": [[0, 0, "linear"], [0.06, 0.006, "linear"], [0.12, -0.006, "linear"],
                                            [0.5, 0, "linear"]]}], ["stress"])
    mot("spring_pop_in", "spring", 0.6, False,
        [{"target": "object.scale", "keys": [[0, 0.0, "spring"], [0.6, 1.0, "spring"]]}], ["pop"],
        spring={"stiffness": 260, "damping": 14})
    mot("bounce_loop", "character", 0.8, True,
        [{"target": "character.y", "keys": [[0, 0, "ease_out"], [0.4, -0.03, "ease_in"], [0.8, 0, "ease_out"]]}],
        ["energy"])


def build_scenes():
    jasset("05_scenes", "bedroom_morning", {
        "format": "layered_scene/v1", "canvas": [1080, 1920], "coords": "normalized",
        "layers": {
            "back": [{"type": "rect", "x": 0, "y": 0, "w": 1, "h": 0.74, "fill": "#334155"},
                     {"type": "rect", "x": 0.62, "y": 0.12, "w": 0.28, "h": 0.22, "fill": "#fde68a"},
                     {"type": "rect", "x": 0.64, "y": 0.14, "w": 0.24, "h": 0.18, "fill": "#7dd3fc"}],
            "mid": [{"type": "rect", "x": 0.04, "y": 0.52, "w": 0.5, "h": 0.2, "fill": "#64748b"},
                    {"type": "rect", "x": 0.04, "y": 0.47, "w": 0.18, "h": 0.07, "fill": "#e2e8f0"}],
            "ground": [{"type": "rect", "x": 0, "y": 0.74, "w": 1, "h": 0.26, "fill": "#1e293b"},
                       {"type": "line", "x1": 0, "y1": 0.74, "x2": 1, "y2": 0.74, "stroke": "#0f172a", "width": 4}]},
        "character_anchor": [0.62, 0.74]}, scope="specific", tags=["sleep", "habits", "psychology"])
    sasset("05_scenes", "mountain_cliff_storm", svg(1080, 1920, """
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1020"/><stop offset="1" stop-color="#3b4a6b"/></linearGradient></defs>
<g id="back"><rect width="1080" height="1920" fill="url(#sky)"/><circle cx="820" cy="360" r="110" fill="#cbd5e1" opacity="0.35"/>
<polygon points="0,1100 220,760 420,980 640,640 860,960 1080,820 1080,1300 0,1300" fill="#1e293b"/></g>
<g id="mid"><polygon points="0,1300 300,1180 620,1260 1080,1120 1080,1500 0,1500" fill="#111827"/>
<path d="M620 300 L560 520 L610 520 L540 760" stroke="#fde68a" stroke-width="10" fill="none" opacity="0.8"/></g>
<g id="ground"><polygon points="0,1500 380,1440 700,1470 1080,1400 1080,1920 0,1920" fill="#0f172a"/></g>"""),
           scope="specific", tags=["stoicism", "resilience", "struggle"])
    sasset("05_scenes", "studio_gradient", svg(1080, 1920, """
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0f172a"/><stop offset="1" stop-color="#1e3a5f"/></linearGradient></defs>
<g id="back"><rect width="1080" height="1920" fill="url(#g)"/></g>
<g id="mid"><circle cx="540" cy="760" r="420" fill="#22d3ee" opacity="0.07"/></g>
<g id="ground"><rect y="1480" width="1080" height="440" fill="#0b1220"/><rect y="1478" width="1080" height="4" fill="#22d3ee" opacity="0.6"/></g>"""),
           tags=["explainer", "tech", "general"])
    sasset("05_scenes", "city_night_skyline", svg(1080, 1920, """
<g id="back"><rect width="1080" height="1920" fill="#0b1020"/><circle cx="200" cy="300" r="70" fill="#e2e8f0" opacity="0.5"/></g>
<g id="mid"><rect x="60" y="900" width="160" height="600" fill="#1e293b"/><rect x="260" y="760" width="200" height="740" fill="#111827"/>
<rect x="500" y="960" width="150" height="540" fill="#1e293b"/><rect x="690" y="700" width="210" height="800" fill="#111827"/><rect x="930" y="880" width="120" height="620" fill="#1e293b"/>
<g fill="#fde68a" opacity="0.8"><rect x="290" y="800" width="24" height="30"/><rect x="340" y="860" width="24" height="30"/><rect x="730" y="760" width="24" height="30"/><rect x="800" y="840" width="24" height="30"/></g></g>
<g id="ground"><rect y="1500" width="1080" height="420" fill="#0f172a"/></g>"""),
           tags=["business", "general", "storytelling"])


def build_props():
    sasset("06_props", "snooze_alarm_clock", svg(256, 256, """
<circle cx="128" cy="140" r="82" fill="#e2e8f0" stroke="#0f172a" stroke-width="8"/><circle cx="60" cy="70" r="26" fill="#f87171" stroke="#0f172a" stroke-width="6"/>
<circle cx="196" cy="70" r="26" fill="#f87171" stroke="#0f172a" stroke-width="6"/><line x1="128" y1="140" x2="128" y2="92" stroke="#0f172a" stroke-width="8" stroke-linecap="round"/>
<line x1="128" y1="140" x2="164" y2="158" stroke="#0f172a" stroke-width="8" stroke-linecap="round"/><rect x="104" y="30" width="48" height="16" rx="6" fill="#0f172a"/>
<line x1="70" y1="224" x2="52" y2="244" stroke="#0f172a" stroke-width="8" stroke-linecap="round"/><line x1="186" y1="224" x2="204" y2="244" stroke="#0f172a" stroke-width="8" stroke-linecap="round"/>"""),
           scope="specific", tags=["sleep", "habits", "morning"])
    sasset("06_props", "lightbulb_idea", svg(256, 256, """
<circle cx="128" cy="108" r="64" fill="#facc15" stroke="#0f172a" stroke-width="8"/><rect x="100" y="166" width="56" height="40" rx="8" fill="#94a3b8" stroke="#0f172a" stroke-width="8"/>
<rect x="108" y="206" width="40" height="22" rx="8" fill="#475569" stroke="#0f172a" stroke-width="8"/>
<g stroke="#facc15" stroke-width="8" stroke-linecap="round"><line x1="128" y1="14" x2="128" y2="-2"/><line x1="40" y1="46" x2="28" y2="34"/><line x1="216" y1="46" x2="228" y2="34"/></g>"""),
           tags=["explainer", "idea", "general"])
    sasset("06_props", "brain_simple", svg(256, 256, """
<path d="M128 52 C80 36 44 72 56 112 C28 128 40 176 82 180 C94 214 150 214 170 180 C214 180 228 128 200 112 C212 72 176 36 128 52 Z" fill="#f9a8d4" stroke="#0f172a" stroke-width="8" stroke-linejoin="round"/>
<path d="M128 56 L128 188" stroke="#0f172a" stroke-width="6" fill="none"/><path d="M84 110 C100 100 112 118 128 108 M172 110 C156 100 144 118 128 108 M88 150 C104 140 116 156 128 148 M168 150 C152 140 140 156 128 148" stroke="#0f172a" stroke-width="5" fill="none"/>"""),
           tags=["psychology", "science", "explainer"])
    sasset("06_props", "coin_stack", svg(256, 256, """
<g stroke="#0f172a" stroke-width="7"><ellipse cx="128" cy="188" rx="72" ry="24" fill="#ca8a04"/><rect x="56" y="150" width="144" height="38" fill="#eab308"/><ellipse cx="128" cy="150" rx="72" ry="24" fill="#facc15"/>
<rect x="56" y="112" width="144" height="38" fill="#eab308"/><ellipse cx="128" cy="112" rx="72" ry="24" fill="#facc15"/><rect x="56" y="74" width="144" height="38" fill="#eab308"/><ellipse cx="128" cy="74" rx="72" ry="24" fill="#fde047"/></g>"""),
           tags=["business", "finance", "general"])


def build_widgets():
    jasset("07_widgets", "bar_chart_spike", {
        "format": "widget/v1", "type": "bar_chart", "data": {"labels": ["Mon", "Tue", "Wed", "Thu", "Fri"], "values": [3, 4, 3, 9, 4]},
        "highlight_index": 3, "animate": "grow_stagger", "stagger_ms": 90,
        "style": {"bar_color": "theme.accent", "highlight_color": "theme.danger", "show_values": True}},
        tags=["data", "explainer", "general"])
    jasset("07_widgets", "comparison_card_two_up", {
        "format": "widget/v1", "type": "comparison_card",
        "data": {"left": {"title": "Before", "bullets": ["Tired", "Foggy"]}, "right": {"title": "After", "bullets": ["Alert", "Focused"]}},
        "animate": "slide_in_split", "style": {"divider": "vs"}}, tags=["comparison", "general"])
    jasset("07_widgets", "funnel_three_stage", {
        "format": "widget/v1", "type": "funnel",
        "data": {"stages": [{"label": "Visitors", "value": 1000}, {"label": "Leads", "value": 240}, {"label": "Buyers", "value": 38}]},
        "animate": "drop_down", "style": {"gradient": ["theme.accent", "theme.accent2"]}}, tags=["business", "marketing"])


def build_overlays():
    jasset("08_overlays", "sweat_drops_nervous", {
        "format": "overlay/v1", "kind": "particles", "anchor": "character.head", "count": 3,
        "particle": {"shape": "teardrop", "color": "#7dd3fc", "size": 0.018},
        "motion": {"direction": [0.5, -1.0], "gravity": 0.9, "lifetime_sec": 0.9, "respawn": True}},
        tags=["stress", "comic"])
    jasset("08_overlays", "question_marks_confused", {
        "format": "overlay/v1", "kind": "floating_text", "anchor": "character.head", "text": "?",
        "count": 3, "color": "theme.highlight", "size": 0.05, "motion": {"bob": 0.01, "lifetime_sec": 1.2}},
        tags=["confusion", "comic"])
    sasset("08_overlays", "speed_lines_radial", svg(1080, 1920, """
<g stroke="#ffffff" stroke-width="6" opacity="0.75" stroke-linecap="round">""" + "".join(
        f'<line x1="{540 + 330 * np.cos(a):.0f}" y1="{960 + 330 * np.sin(a):.0f}" x2="{540 + 1400 * np.cos(a):.0f}" y2="{960 + 1400 * np.sin(a):.0f}"/>'
        for a in np.linspace(0, 2 * np.pi, 40, endpoint=False)) + "</g>"), tags=["action", "emphasis"])
    sasset("08_overlays", "exclamation_burst", svg(512, 512, """
<polygon points="256,20 300,150 430,90 360,210 492,256 360,302 430,422 300,362 256,492 212,362 82,422 152,302 20,256 152,210 82,90 212,150" fill="#facc15" stroke="#0f172a" stroke-width="10" stroke-linejoin="round"/>
<rect x="236" y="130" width="40" height="150" rx="14" fill="#0f172a"/><circle cx="256" cy="340" r="24" fill="#0f172a"/>"""), tags=["shock", "emphasis"])


def build_transitions():
    def tr(aid, obj, tags):
        jasset("09_transitions", aid, {"format": "transition/v1", **obj}, tags=tags)
    tr("whip_pan_left", {"type": "whip_pan", "direction": "left", "duration_sec": 0.25, "motion_blur": True, "easing": "expo_out"}, ["fast", "energy"])
    tr("zoom_punch", {"type": "zoom", "from_scale": 1.0, "to_scale": 1.6, "duration_sec": 0.2, "flash": True, "easing": "expo_in"}, ["emphasis"])
    tr("wipe_diagonal", {"type": "wipe", "angle_deg": 35, "duration_sec": 0.3, "edge_color": "theme.accent", "easing": "ease_in_out"}, ["clean"])
    tr("cross_fade_soft", {"type": "fade", "duration_sec": 0.35, "easing": "linear"}, ["calm"])


def build_captions_themes():
    jasset("10_caption_styles", "hormozi_pop_yellow", {
        "format": "caption_style/v1", "font": "DejaVu Sans Bold", "size_ratio": 0.07, "case": "upper",
        "max_words_per_line": 3, "position_y": 0.68, "inactive_color": "#ffffff",
        "active_word": {"color": "#facc15", "scale_pop": 1.18, "pop_ms": 90},
        "stroke": {"color": "#000000", "width_ratio": 0.012}}, tags=["shorts", "viral"])
    jasset("10_caption_styles", "clean_white_bar", {
        "format": "caption_style/v1", "font": "DejaVu Sans", "size_ratio": 0.045, "case": "sentence",
        "max_words_per_line": 6, "position_y": 0.82, "inactive_color": "#e2e8f0",
        "active_word": {"color": "#ffffff", "scale_pop": 1.0, "pop_ms": 0},
        "background": {"color": "#000000", "opacity": 0.55, "radius_ratio": 0.01}}, tags=["calm", "documentary"])
    jasset("11_themes", "dark_slate_neon", {
        "format": "theme/v1", "palette": {"bg": "#0f172a", "surface": "#1e293b", "line": "#e2e8f0", "text": "#f8fafc",
                                         "accent": "#22d3ee", "accent2": "#f472b6", "highlight": "#facc15", "danger": "#f87171"}},
           tags=["tech", "psychology", "general"])
    jasset("11_themes", "paper_light", {
        "format": "theme/v1", "palette": {"bg": "#f8fafc", "surface": "#e2e8f0", "line": "#0f172a", "text": "#0f172a",
                                         "accent": "#2563eb", "accent2": "#db2777", "highlight": "#f59e0b", "danger": "#dc2626"}},
           tags=["education", "business"])


def build_audio():
    tmp = Path(os.environ.get("TMPDIR") or os.path.join(os.environ.get("PREFIX", ""), "tmp") or tempfile.gettempdir())
    tmp.mkdir(parents=True, exist_ok=True)
    # SFX (<1.5 s)
    sfx = {
        "clock_tick_single": (sfx_clock_tick, ["clock", "time", "tension"]),
        "thud_soft": (sfx_thud_soft, ["impact", "weight"]),
        "whoosh_fast": (sfx_whoosh_fast, ["transition", "motion"]),
        "pop_bubble": (sfx_pop_bubble, ["pop", "comic"]),
        "ding_success": (sfx_ding_success, ["success", "reward"]),
        "glitch_blip": (sfx_glitch_blip, ["tech", "glitch"]),
    }
    for aid, (fn, tags) in sfx.items():
        rel = f"14_sfx/{aid}.wav"
        data = fn()
        _write_wav(LIB / rel, data, SR)
        _register("14_sfx", aid, rel, "global", tags, meta={"duration_sec": round(len(data) / SR, 3), "sample_rate": SR})
    # BGM loops
    bgm = {
        "tense_clockwork_pulse": (bgm_tense_clockwork_pulse, 120, "tense", ["thriller", "psychology", "stress"]),
        "calm_ambient_pad": (bgm_calm_ambient_pad, 60, "calm", ["stoicism", "documentary", "storytelling"]),
        "upbeat_lofi_groove": (bgm_upbeat_lofi_groove, 90, "upbeat", ["explainer", "business", "tech"]),
    }
    for aid, (fn, bpm, mood, tags) in bgm.items():
        wav = tmp / f"seed_{aid}.wav"
        _write_wav(wav, fn(), SR)
        rel = f"13_bgm/{aid}.ogg"
        _to_ogg(wav, LIB / rel)
        wav.unlink(missing_ok=True)
        _register("13_bgm", aid, rel, "global", tags, meta={"bpm": bpm, "mood": mood, "loop_sec": 16.0, "loop": True})
    # Voice personas + placeholder previews
    A, I, O = (800, 1200), (300, 2300), (500, 900)
    voices = [
        ("kael_calm_charon", "Charon", 110, [A, O, I, A], ["narrator", "authority"], "Calm, authoritative, measured; low steady delivery."),
        ("nova_bright_kore", "Kore", 200, [I, A, I, O], ["upbeat", "science"], "Bright, precise, curious; crisp consonants."),
        ("rex_bold_fenrir", "Fenrir", 95, [A, A, O, I], ["bold", "motivational"], "Bold, intense, punchy; push on key words."),
        ("pip_quirky_puck", "Puck", 190, [I, O, A, I], ["playful", "comic"], "Playful, quick, quirky; bouncy pitch."),
        ("luna_warm_aoede", "Aoede", 220, [O, A, O, I], ["warm", "storytelling"], "Warm, gentle, wise; unhurried with soft endings."),
    ]
    for i, (vid, gname, f0, vow, tags, style) in enumerate(voices):
        prev_rel = f"12_voices/{vid}_preview.wav"
        _write_wav(LIB / prev_rel, voice_preview(f0, vow, i), VSR)
        rel = f"12_voices/{vid}.json"
        _write_text(rel, json.dumps({
            "id": vid, "format": "voice_persona/v1", "type": "prebuilt", "gemini_voice_name": gname,
            "tts_model": "gemini-3.8-flash-tts", "default_style": style, "pace_multiplier": 1.0,
            "preview_audio_path": prev_rel, "preview_is_placeholder": True}, indent=2) + "\n")
        _register("12_voices", vid, rel, "global", tags, gemini_voice_name=gname, preview_audio_path=prev_rel)


def main() -> int:
    global LIB
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", default=str(Path(__file__).resolve().parent.parent / "assets" / "library"))
    args = ap.parse_args()
    LIB = Path(args.library)
    LIB.mkdir(parents=True, exist_ok=True)
    (LIB / ".thumbs").mkdir(exist_ok=True)
    (LIB / ".thumbs" / ".gitkeep").touch()

    build_characters(); build_poses(); build_expressions(); build_motions(); build_scenes()
    build_props(); build_widgets(); build_overlays(); build_transitions(); build_captions_themes(); build_audio()

    order = sorted(INDEX, key=lambda a: (a["category"], a["id"]))
    index = {"schema_version": "1.0",
             "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "assets": order}
    (LIB / "library_index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    cats = sorted({a["category"] for a in order})
    print(f"seeded {len(order)} assets across {len(cats)} categories -> {LIB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
