"""Procedural sound effects (14_sfx, WAV) and seamless music loops (13_bgm, OGG) for the asset pack."""
from __future__ import annotations

import hashlib
from typing import Any, Callable, Dict, List, Tuple

import numpy as np

SR = 44100


def _rng(seed: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha1(seed.encode()).hexdigest()[:8], 16))


def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def env(n: int, a: float = 0.005, d: float = 0.1, s: float = 0.0, r: float = 0.05, hold: float = 0.0) -> np.ndarray:
    """ADSR-ish envelope over n samples (times in seconds)."""
    t = np.arange(n) / SR
    e = np.ones(n)
    att = np.minimum(1.0, t / max(a, 1e-4))
    dec = s + (1 - s) * np.exp(-np.maximum(0, t - a - hold) / max(d, 1e-4))
    e = att * np.where(t < a + hold, 1.0, dec)
    rel_start = max(0.0, n / SR - r)
    e *= np.clip((n / SR - t) / max(r, 1e-4), 0, 1) if r > 0 else 1
    _ = rel_start
    return e


def osc(freq, t: np.ndarray, kind: str = "sine") -> np.ndarray:
    f = np.broadcast_to(np.asarray(freq, dtype=float), t.shape) if np.ndim(freq) else np.full(t.shape, float(freq))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "sine":
        return np.sin(ph)
    if kind == "tri":
        return sum(((-1) ** k) * np.sin((2 * k + 1) * ph) / (2 * k + 1) ** 2 for k in range(5)) * 0.81
    if kind == "square":
        return sum(np.sin((2 * k + 1) * ph) / (2 * k + 1) for k in range(7)) * 0.9
    if kind == "saw":
        return sum(((-1) ** (k + 1)) * np.sin(k * ph) / k for k in range(1, 10)) * 0.6
    return np.sin(ph)


def noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(n)


def lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # one-pole; inputs are short (sfx) or decimated (bgm pads)
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lp_fast(x: np.ndarray, k: int) -> np.ndarray:
    """Cheap FIR low-pass (moving average of k samples)."""
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def hp_fast(x: np.ndarray, k: int) -> np.ndarray:
    return x - lp_fast(x, k)


def norm(x: np.ndarray, peak: float = 0.85) -> np.ndarray:
    m = float(np.max(np.abs(x))) or 1.0
    y = x * (peak / m)
    fade = min(len(y) // 4, int(0.004 * SR))
    if fade > 0:
        y[:fade] *= np.linspace(0, 1, fade)
        y[-fade:] *= np.linspace(1, 0, fade)
    return y


def cat(*parts: np.ndarray) -> np.ndarray:
    return np.concatenate(parts)


def place(total: float, events: List[Tuple[float, np.ndarray]]) -> np.ndarray:
    out = np.zeros(int(total * SR))
    for at, x in events:
        s = int(at * SR)
        e = min(len(out), s + len(x))
        if s < len(out):
            out[s:e] += x[: e - s]
    return out


def midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


# =========================================================================== SFX
def _tone(f, dur, kind="sine", a=0.004, d=0.15, s=0.0) -> np.ndarray:
    t = _t(dur)
    return osc(f, t, kind) * env(len(t), a, d, s, 0.02)


def _sweep(f0, f1, dur, kind="sine", curve=2.0) -> np.ndarray:
    t = _t(dur)
    u = t / dur
    f = f0 + (f1 - f0) * (u ** curve if f1 > f0 else 1 - (1 - u) ** curve)
    return osc(f, t, kind)


def _noise_burst(dur, rng, smooth=1, decay=0.05) -> np.ndarray:
    n = int(dur * SR)
    return lp_fast(noise(n, rng), smooth) * np.exp(-np.arange(n) / SR / decay)


def _bell(f, dur=1.2, bright=1.0) -> np.ndarray:
    t = _t(dur)
    parts = [(1, 1.0, 1.0), (2.76, 0.45 * bright, 0.6), (5.4, 0.25 * bright, 0.35), (8.9, 0.12 * bright, 0.2)]
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (dur * dd)) for r, a, dd in parts) * env(len(t), 0.002, 9, 1, 0.05)


def sfx_bank() -> List[Tuple[str, str, Callable[[np.random.Generator], np.ndarray]]]:
    B: List[Tuple[str, str, Callable]] = []

    def s(sid, tags, fn):
        B.append((sid, tags, fn))

    # whooshes & swooshes
    for name, dur, f0, f1, k in (("whoosh_short", 0.25, 300, 1400, 6), ("whoosh_long", 0.7, 200, 1000, 10), ("whoosh_low", 0.5, 120, 500, 18),
                                 ("swoosh_up", 0.45, 200, 2400, 5), ("swoosh_down", 0.45, 2400, 200, 5), ("swish_fast", 0.18, 800, 3000, 3)):
        s(name, "transition movement general", lambda r, dur=dur, f0=f0, f1=f1, k=k: (lp_fast(noise(int(dur * SR), r), k) * np.sin(np.pi * _t(dur) / dur) ** 2
                                                                                      + 0.15 * _sweep(f0, f1, dur) * np.sin(np.pi * _t(dur) / dur)))
    # pops, clicks, blips
    s("pop_small", "ui general", lambda r: _sweep(900, 250, 0.08) * env(int(0.08 * SR), 0.001, 0.03))
    s("pop_big", "ui comedy", lambda r: _sweep(700, 120, 0.16) * env(int(0.16 * SR), 0.001, 0.06))
    s("bubble_pop", "ui comedy kids", lambda r: _sweep(400, 1600, 0.09, curve=0.5) * env(int(0.09 * SR), 0.001, 0.04))
    s("click_ui", "ui tech", lambda r: _noise_burst(0.03, r, 2, 0.004) + 0.4 * _tone(2400, 0.03, d=0.006))
    s("click_mouse", "tech office", lambda r: cat(_noise_burst(0.02, r, 1, 0.003), np.zeros(int(0.05 * SR)), 0.6 * _noise_burst(0.02, r, 1, 0.003)))
    s("toggle_switch", "ui tech", lambda r: cat(_tone(1200, 0.04, d=0.01), _tone(1800, 0.05, d=0.015)))
    s("blip_high", "ui game", lambda r: _tone(1760, 0.08, "square", d=0.04))
    s("blip_low", "ui game", lambda r: _tone(440, 0.1, "square", d=0.05))
    s("boop_soft", "ui kids", lambda r: _sweep(600, 400, 0.12) * env(int(0.12 * SR), 0.005, 0.05))
    s("tick_clock", "time", lambda r: _noise_burst(0.02, r, 1, 0.003) + 0.5 * _tone(3200, 0.02, d=0.004))
    s("clock_ticking", "time tension", lambda r: place(2.0, [(i * 0.5, (_noise_burst(0.02, r, 1, 0.003) + 0.5 * _tone(3200 if i % 2 else 2600, 0.02, d=0.004)))
                                                              for i in range(4)]))
    # bells, chimes, jingles
    s("ding_bell", "success ui", lambda r: _bell(1318, 1.0))
    s("ding_soft", "calm ui", lambda r: _bell(880, 1.0, 0.5) * 0.8)
    s("chime_up", "success magic", lambda r: place(1.2, [(i * 0.09, _bell(midi(n), 0.9, 0.7)) for i, n in enumerate((72, 76, 79, 84))]))
    s("chime_down", "failure sad", lambda r: place(1.2, [(i * 0.1, _bell(midi(n), 0.9, 0.7)) for i, n in enumerate((84, 79, 76, 72))]))
    s("success_jingle", "success winner", lambda r: place(1.0, [(i * 0.11, _tone(midi(n), 0.3, "tri", d=0.2)) for i, n in enumerate((67, 72, 76, 79))]))
    s("level_up", "game winner", lambda r: place(0.9, [(i * 0.07, _tone(midi(n), 0.12, "square", d=0.08)) for i, n in enumerate((60, 64, 67, 72, 76, 79, 84))]))
    s("game_over", "game failure", lambda r: place(1.4, [(i * 0.22, _tone(midi(n), 0.3, "square", d=0.2)) for i, n in enumerate((67, 63, 60, 55))]))
    s("coin_collect", "money game finance", lambda r: cat(_tone(midi(83), 0.06, "square", d=0.05), _tone(midi(88), 0.3, "square", d=0.15)))
    s("cash_register_ching", "money finance shopping", lambda r: place(1.2, [(0, _noise_burst(0.12, r, 2, 0.04)), (0.1, _bell(2093, 1.0, 1.2))]))
    s("notification_ping", "tech social_media", lambda r: cat(_tone(1046, 0.09, d=0.06), _tone(1568, 0.3, d=0.15)))
    s("message_received", "tech social_media communication", lambda r: cat(_tone(880, 0.07, "tri", d=0.05), np.zeros(int(0.03 * SR)), _tone(1175, 0.2, "tri", d=0.1)))
    s("error_buzz", "failure tech", lambda r: _tone(110, 0.4, "saw", d=0.6, s=0.8) * 0.8)
    s("wrong_answer", "failure game education", lambda r: cat(_tone(196, 0.18, "square", d=0.5, s=0.7), _tone(147, 0.35, "square", d=0.5, s=0.7)))
    s("correct_answer", "success education game", lambda r: cat(_tone(784, 0.1, "tri", d=0.1), _tone(1175, 0.25, "tri", d=0.15)))
    s("alarm_beeps", "danger time", lambda r: place(1.2, [(i * 0.3, _tone(1400, 0.15, "square", d=1, s=1)) for i in range(4)]))
    s("siren_wail", "danger emergency", lambda r: osc(700 + 300 * np.sin(2 * np.pi * 1.2 * _t(1.6)), _t(1.6), "tri") * env(int(1.6 * SR), 0.05, 9, 1, 0.2))
    s("countdown_beeps", "time tension", lambda r: place(3.2, [(i, _tone(880 if i < 3 else 1760, 0.18 if i < 3 else 0.5, "sine", d=1, s=1)) for i in range(4)]))
    # impacts
    s("thud_heavy", "impact general", lambda r: _sweep(140, 40, 0.35) * env(int(0.35 * SR), 0.002, 0.12) + 0.3 * _noise_burst(0.35, r, 30, 0.04))
    s("impact_boom", "impact danger", lambda r: _sweep(90, 30, 1.2) * env(int(1.2 * SR), 0.003, 0.4) + 0.5 * _noise_burst(1.2, r, 60, 0.25))
    s("punch_hit", "impact fitness comedy", lambda r: _noise_burst(0.18, r, 4, 0.03) + 0.8 * _sweep(200, 60, 0.18) * env(int(0.18 * SR), 0.001, 0.05))
    s("slap_comedy", "comedy impact", lambda r: _noise_burst(0.12, r, 1, 0.015) * 1.2)
    s("door_knock", "home storytelling", lambda r: place(0.6, [(0, _sweep(220, 120, 0.08) * env(int(0.08 * SR), 0.001, 0.03) + 0.3 * _noise_burst(0.08, r, 8, 0.01)),
                                                              (0.22, _sweep(220, 120, 0.08) * env(int(0.08 * SR), 0.001, 0.03) + 0.3 * _noise_burst(0.08, r, 8, 0.01))]))
    s("footsteps", "movement storytelling", lambda r: place(1.6, [(i * 0.4, _noise_burst(0.1, r, 12, 0.03) + 0.4 * _sweep(120, 70, 0.1)) for i in range(4)]))
    s("heartbeat", "health tension love", lambda r: place(1.0, [(0, _sweep(70, 45, 0.15) * env(int(0.15 * SR), 0.003, 0.06)),
                                                               (0.22, 0.7 * _sweep(65, 45, 0.15) * env(int(0.15 * SR), 0.003, 0.06))]))
    s("drum_roll", "celebration tension", lambda r: place(1.6, [(i * 0.04, 0.4 * _noise_burst(0.05, r, 3, 0.012) * (0.5 + i / 80)) for i in range(40)]))
    s("cymbal_crash", "celebration impact", lambda r: hp_fast(noise(int(1.8 * SR), r), 3) * np.exp(-_t(1.8) / 0.6))
    s("rimshot_joke", "comedy", lambda r: place(1.4, [(0, _tone(200, 0.12, d=0.05)), (0.18, _tone(150, 0.12, d=0.05)), (0.36, hp_fast(noise(int(0.9 * SR), r), 2) * np.exp(-_t(0.9) / 0.3))]))
    # cartoon & motion
    s("boing_spring", "comedy kids", lambda r: osc(220 * (1 + 0.5 * np.sin(2 * np.pi * 14 * _t(0.7)) * np.exp(-_t(0.7) / 0.3)), _t(0.7)) * env(int(0.7 * SR), 0.003, 0.3))
    s("slide_whistle_up", "comedy", lambda r: _sweep(400, 1800, 0.7, curve=1.0) * env(int(0.7 * SR), 0.02, 2, 1, 0.05))
    s("slide_whistle_down", "comedy failure", lambda r: _sweep(1800, 300, 0.8, curve=1.0) * env(int(0.8 * SR), 0.02, 2, 1, 0.05))
    s("cartoon_run", "comedy movement", lambda r: place(0.9, [(i * 0.05, 0.6 * _tone(500 + (i % 2) * 200, 0.04, "square", d=0.02)) for i in range(18)]))
    s("squeak_toy", "comedy kids", lambda r: osc(1400 + 400 * np.sin(2 * np.pi * 9 * _t(0.25)), _t(0.25), "tri") * env(int(0.25 * SR), 0.01, 0.1))
    s("laser_zap", "game tech", lambda r: _sweep(2400, 200, 0.3, "square", 0.6) * env(int(0.3 * SR), 0.001, 0.12))
    s("magic_sparkle", "magic celebration", lambda r: place(1.2, [(r.uniform(0, 0.8), 0.5 * _bell(r.uniform(1800, 4200), 0.4, 0.3)) for _ in range(9)]))
    s("riser_tension", "tension transition", lambda r: (lp_fast(noise(int(2.0 * SR), r), 4) * 0.4 + _sweep(200, 1200, 2.0, "saw", 1.5) * 0.5) * (_t(2.0) / 2.0) ** 2)
    s("downlifter", "transition", lambda r: (lp_fast(noise(int(1.5 * SR), r), 6) * 0.4 + _sweep(1200, 80, 1.5, "saw", 1.5) * 0.5) * (1 - _t(1.5) / 1.5) ** 2)
    s("record_scratch", "comedy surprise", lambda r: lp_fast(noise(int(0.45 * SR), r), 3) * np.abs(np.sin(2 * np.pi * 7 * _t(0.45))) * np.exp(-_t(0.45) / 0.25))
    s("glitch_burst", "tech security", lambda r: np.sign(np.sin(2 * np.pi * np.repeat(r.choice([220, 440, 880, 1760], 12), int(0.03 * SR)) * _t(0.36)[: 12 * int(0.03 * SR)])) * 0.5)
    s("power_up", "game energy", lambda r: _sweep(200, 1600, 0.6, "square", 1.2) * env(int(0.6 * SR), 0.01, 2, 1, 0.08) * 0.6)
    s("power_down", "game failure", lambda r: _sweep(1200, 80, 0.8, "square", 1.2) * env(int(0.8 * SR), 0.01, 2, 1, 0.08) * 0.6)
    # tech & office
    s("typing_keys", "tech office productivity", lambda r: place(1.4, [(i * 0.09 + r.uniform(0, 0.03), 0.6 * _noise_burst(0.03, r, 1, 0.006)) for i in range(14)]))
    s("camera_shutter", "photography media", lambda r: cat(_noise_burst(0.05, r, 1, 0.01), np.zeros(int(0.06 * SR)), 0.8 * _noise_burst(0.07, r, 2, 0.015)))
    s("phone_vibrate", "tech social_media", lambda r: place(1.0, [(i * 0.45, osc(150, _t(0.3), "saw") * 0.5 * env(int(0.3 * SR), 0.01, 2, 1, 0.02)) for i in range(2)]))
    s("unlock_chime", "security success", lambda r: place(0.8, [(0, _noise_burst(0.03, r, 1, 0.005)), (0.08, _bell(1568, 0.6, 0.6))]))
    s("lock_click", "security", lambda r: cat(_noise_burst(0.02, r, 1, 0.004), np.zeros(int(0.04 * SR)), _noise_burst(0.03, r, 1, 0.006)))
    s("page_turn", "education storytelling", lambda r: lp_fast(noise(int(0.4 * SR), r), 3) * np.sin(np.pi * _t(0.4) / 0.4) ** 3 * 0.8)
    s("pencil_scribble", "education art", lambda r: hp_fast(noise(int(0.8 * SR), r), 6) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 6 * _t(0.8)))) * 0.5)
    s("swipe_ui", "tech ui", lambda r: lp_fast(noise(int(0.2 * SR), r), 2) * np.sin(np.pi * _t(0.2) / 0.2) ** 2 + 0.2 * _sweep(1200, 2400, 0.2))
    # nature & ambience
    s("water_drip", "nature health", lambda r: _sweep(1600, 600, 0.12, curve=0.5) * env(int(0.12 * SR), 0.001, 0.05))
    s("bubbles_rising", "ocean nature", lambda r: place(1.2, [(r.uniform(0, 0.9), 0.5 * _sweep(r.uniform(300, 600), r.uniform(900, 1600), 0.08, curve=0.5)
                                                              * env(int(0.08 * SR), 0.001, 0.04)) for _ in range(10)]))
    s("wind_gust", "weather nature", lambda r: lp_fast(noise(int(2.0 * SR), r), 40) * np.sin(np.pi * _t(2.0) / 2.0) ** 2 * 3)
    s("rain_light", "weather nature calm", lambda r: hp_fast(noise(int(2.0 * SR), r), 4) * 0.25 + place(2.0, [(r.uniform(0, 1.9), 0.3 * _noise_burst(0.01, r, 1, 0.002)) for _ in range(60)]))
    s("thunder_rumble", "weather danger", lambda r: lp_fast(noise(int(2.2 * SR), r), 120) * np.exp(-_t(2.2) / 0.8) * 6 + _noise_burst(2.2, r, 20, 0.1) * 0.5)
    s("fire_crackle", "nature adventure", lambda r: lp_fast(noise(int(1.6 * SR), r), 20) * 0.6 + place(1.6, [(r.uniform(0, 1.5), _noise_burst(0.02, r, 1, 0.004)) for _ in range(30)]))
    s("bird_chirp", "nature animals", lambda r: place(0.8, [(i * 0.18, osc(2500 + 900 * np.sin(2 * np.pi * 18 * _t(0.1)), _t(0.1)) * env(int(0.1 * SR), 0.005, 0.04))
                                                          for i in range(3)]))
    s("crowd_applause", "celebration entertainment", lambda r: (hp_fast(noise(int(2.4 * SR), r), 3) * 0.3
                                                                + place(2.4, [(r.uniform(0, 2.3), 0.5 * _noise_burst(0.02, r, 1, 0.006)) for _ in range(160)]))
      * np.minimum(1, _t(2.4) / 0.3) * np.minimum(1, (2.4 - _t(2.4)) / 0.8))
    s("crowd_gasp", "surprise entertainment", lambda r: lp_fast(noise(int(0.9 * SR), r), 8) * np.sin(np.pi * _t(0.9) / 0.9) * 0.8)
    s("crowd_laugh", "comedy entertainment", lambda r: place(1.6, [(i * 0.16 + r.uniform(0, 0.04), 0.5 * osc(r.uniform(180, 320), _t(0.12), "saw") * env(int(0.12 * SR), 0.01, 0.06))
                                                                  for i in range(9)]))
    s("ocean_wave", "ocean nature calm", lambda r: lp_fast(noise(int(3.0 * SR), r), 25) * np.sin(np.pi * _t(3.0) / 3.0) ** 2 * 3)
    s("engine_start", "transport", lambda r: osc(40 + 30 * np.minimum(1, _t(1.6) / 1.0), _t(1.6), "saw") * env(int(1.6 * SR), 0.1, 3, 1, 0.2) * 0.7)
    s("car_horn", "transport comedy", lambda r: (_tone(440, 0.5, "square", d=2, s=1) + _tone(554, 0.5, "square", d=2, s=1)) * 0.5)
    s("train_whistle", "transport travel", lambda r: (osc(523, _t(1.0), "tri") + osc(659, _t(1.0), "tri")) * env(int(1.0 * SR), 0.05, 2, 1, 0.2) * 0.5)
    s("airplane_flyby", "transport travel", lambda r: lp_fast(noise(int(2.5 * SR), r), 10) * np.sin(np.pi * _t(2.5) / 2.5) ** 2 * 2)
    s("rocket_launch_roar", "space adventure", lambda r: lp_fast(noise(int(2.5 * SR), r), 60) * np.minimum(1, _t(2.5) / 0.6) * 4)
    s("spaceship_hum", "space tech", lambda r: (osc(55, _t(2.0), "saw") * 0.4 + osc(110.5, _t(2.0)) * 0.3) * np.sin(np.pi * _t(2.0) / 2.0))
    s("ghost_woo", "spooky holiday", lambda r: osc(400 + 120 * np.sin(2 * np.pi * 0.8 * _t(1.6)), _t(1.6)) * np.sin(np.pi * _t(1.6) / 1.6) * 0.8)
    s("evil_laugh_low", "spooky comedy", lambda r: place(1.4, [(i * 0.18, osc(110, _t(0.14), "saw") * env(int(0.14 * SR), 0.01, 0.08)) for i in range(6)]))
    s("snore_sleep", "sleep comedy", lambda r: lp_fast(noise(int(1.6 * SR), r), 30) * np.sin(np.pi * _t(1.6) / 1.6) ** 2 * 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * _t(1.6))))
    s("gulp_drink", "food comedy", lambda r: _sweep(500, 180, 0.15) * env(int(0.15 * SR), 0.005, 0.06))
    s("crunch_bite", "food", lambda r: place(0.5, [(i * 0.07, _noise_burst(0.05, r, 1, 0.01)) for i in range(4)]))
    s("sizzle_cooking", "food cooking", lambda r: hp_fast(noise(int(2.0 * SR), r), 3) * 0.3 * (0.8 + 0.2 * np.sin(2 * np.pi * 3 * _t(2.0))))
    s("kiss_smooch", "love comedy", lambda r: _noise_burst(0.06, r, 1, 0.01) * 0.6 + 0.5 * _sweep(900, 1500, 0.06) * env(int(0.06 * SR), 0.001, 0.02))
    s("meditation_bowl", "mental_health calm", lambda r: _bell(220, 3.0, 0.6) * (1 + 0.15 * np.sin(2 * np.pi * 4 * _t(3.0))))
    s("gong_hit", "celebration history", lambda r: _bell(110, 3.0, 1.4) + 0.2 * lp_fast(noise(int(3.0 * SR), r), 30) * np.exp(-_t(3.0) / 1.0))
    s("dramatic_sting", "tension surprise storytelling", lambda r: (osc(midi(48), _t(1.5), "saw") + osc(midi(51), _t(1.5), "saw") + osc(midi(54), _t(1.5), "saw"))
      * env(int(1.5 * SR), 0.005, 0.7, 0.2, 0.3) * 0.4)
    return B


# =========================================================================== BGM
def _reverb(x: np.ndarray, amt: float = 0.25) -> np.ndarray:
    out = x.copy()
    for d, g in ((1499, 0.5), (2207, 0.42), (3109, 0.35), (4241, 0.28)):
        out[d:] += np.roll(x, 0)[:-d] * g * amt
    return out


def _wrap(x: np.ndarray, n: int) -> np.ndarray:
    """Fold anything past n back onto the start so the loop is seamless."""
    y = x[:n].copy()
    tail = x[n:]
    y[: len(tail)] += tail[: n]
    return y


SCALES = {"major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10], "dorian": [0, 2, 3, 5, 7, 9, 10], "penta": [0, 2, 4, 7, 9],
          "minor_penta": [0, 3, 5, 7, 10], "phrygian": [0, 1, 3, 5, 7, 8, 10]}


def _chord(root: int, scale: List[int], degree: int, size: int = 3) -> List[int]:
    out = []
    for k in range(size):
        idx = degree + 2 * k
        out.append(root + scale[idx % len(scale)] + 12 * (idx // len(scale)))
    return out


def make_bgm(spec: Dict[str, Any], seed: str) -> np.ndarray:
    """Stereo (2, n) loop from a small spec: bpm, key root (midi), scale, progression degrees, layers."""
    rng = _rng(seed)
    bpm, root, scale = spec["bpm"], spec["root"], SCALES[spec["scale"]]
    prog = spec["prog"]
    beat = 60.0 / bpm
    bars = len(prog) * spec.get("bars_per_chord", 1)
    n = int(round(bars * 4 * beat * SR))
    pad_wave, lead_wave = spec.get("pad", "tri"), spec.get("lead", "sine")
    L = np.zeros(n + SR * 2)
    R = np.zeros(n + SR * 2)

    def add(at: float, x: np.ndarray, pan: float = 0.0, gain: float = 1.0) -> None:
        s = int(at * SR)
        e = min(len(L), s + len(x))
        L[s:e] += x[: e - s] * gain * (1 - max(0, pan))
        R[s:e] += x[: e - s] * gain * (1 + min(0, pan))

    bar = 4 * beat
    for ci, deg in enumerate(prog):
        t0 = ci * bar * spec.get("bars_per_chord", 1)
        dur = bar * spec.get("bars_per_chord", 1)
        notes = _chord(root, scale, deg, 4 if spec.get("sevenths") else 3)
        if "pad" in spec.get("layers", ["pad"]):
            tt = _t(dur + 0.4)
            for k, m in enumerate(notes):
                x = osc(midi(m) * (1 + 0.002 * (k - 1)), tt, pad_wave) * env(len(tt), 0.3, 9, 1, 0.4)
                add(t0, x, -0.3 + 0.3 * k, 0.11)
        if "bass" in spec.get("layers", []):
            for b in range(int(dur / beat)):
                if spec.get("bass_pattern", "quarter") == "half" and b % 2:
                    continue
                m = notes[0] - 12
                tt = _t(beat * 0.9)
                add(t0 + b * beat, osc(midi(m), tt, spec.get("bass_wave", "tri")) * env(len(tt), 0.005, 0.25, 0.4, 0.05), 0, 0.32)
        if "arp" in spec.get("layers", []):
            step = beat / spec.get("arp_rate", 2)
            seq = notes + [notes[1] + 12]
            for i in range(int(dur / step)):
                m = seq[i % len(seq)] + 12
                tt = _t(step * 1.6)
                add(t0 + i * step, osc(midi(m), tt, lead_wave) * env(len(tt), 0.004, step * 1.2, 0, 0.05), 0.4 if i % 2 else -0.4, 0.09)
        if "bells" in spec.get("layers", []):
            for i in range(2):
                m = rng.choice(notes) + 24
                add(t0 + i * bar / 2 + rng.uniform(0, beat), _bell(midi(m), 1.6, 0.4) * 0.5, rng.uniform(-0.6, 0.6), 0.07)
        if "melody" in spec.get("layers", []):
            for i in range(int(dur / beat)):
                if rng.random() < 0.35:
                    continue
                m = root + 12 + rng.choice(scale) + (12 if rng.random() < 0.2 else 0)
                tt = _t(beat * rng.choice([0.5, 1.0]))
                add(t0 + i * beat, osc(midi(m), tt, lead_wave) * env(len(tt), 0.01, 0.3, 0.2, 0.06), 0.2, 0.07)
    # drums
    drums = spec.get("drums", "")
    if drums:
        kick = _sweep(150, 45, 0.25) * env(int(0.25 * SR), 0.001, 0.12)
        snare = _noise_burst(0.18, rng, 2, 0.05) * 0.7 + 0.3 * _tone(190, 0.18, d=0.05)
        hat = hp_fast(noise(int(0.05 * SR), rng), 2) * np.exp(-_t(0.05) / 0.012) * 0.4
        clap = place(0.06, [(0, _noise_burst(0.04, rng, 1, 0.01)), (0.012, _noise_burst(0.04, rng, 1, 0.01))]) * 0.6
        total_beats = int(n / SR / beat)
        for b in range(total_beats):
            at = b * beat
            if drums in ("four", "house"):
                add(at, kick, 0, 0.55)
                add(at + beat / 2, hat, 0.3, 0.6)
                if b % 2 == 1:
                    add(at, clap if drums == "house" else snare, 0, 0.45)
            elif drums == "lofi":
                if b % 4 in (0, 2) or (b % 4 == 3 and rng.random() < 0.5):
                    add(at + (0.02 if b % 4 == 2 else 0), kick, 0, 0.45)
                if b % 4 in (1, 3):
                    add(at + 0.02, snare, 0, 0.35)
                for k in range(2):
                    add(at + k * beat / 2 + 0.015 * k, hat, -0.3, 0.35)
            elif drums == "trap":
                if b % 4 == 0 or (b % 8 == 6):
                    add(at, kick, 0, 0.55)
                if b % 4 == 2:
                    add(at, clap, 0, 0.5)
                for k in range(4 if b % 4 != 3 else 6):
                    add(at + k * beat / (4 if b % 4 != 3 else 6), hat, 0.4, 0.3)
            elif drums == "pulse":
                add(at, kick * 0.7, 0, 0.5)
            elif drums == "march":
                add(at, kick, 0, 0.45)
                if b % 2:
                    add(at, snare, 0, 0.3)
                    add(at + beat * 0.75, snare * 0.5, 0, 0.25)
    mix = np.vstack([_wrap(_reverb(L, spec.get("verb", 0.3)), n), _wrap(_reverb(R, spec.get("verb", 0.3)), n)])
    mix *= 0.7 / (np.max(np.abs(mix)) or 1.0)
    return mix


BGM_SPECS: List[Tuple[str, str, Dict[str, Any]]] = [
    ("lofi_study_chill", "education productivity calm", {"bpm": 78, "root": 57, "scale": "dorian", "prog": [0, 3, 4, 2], "layers": ["pad", "bass", "bells"], "drums": "lofi",
                                                        "sevenths": True, "pad": "tri"}),
    ("upbeat_corporate", "business marketing", {"bpm": 112, "root": 60, "scale": "major", "prog": [0, 4, 5, 3], "layers": ["pad", "bass", "arp"], "drums": "four", "arp_rate": 2}),
    ("happy_ukulele_like", "kids family comedy", {"bpm": 120, "root": 65, "scale": "major", "prog": [0, 3, 4, 0], "layers": ["bass", "arp"], "drums": "pulse", "arp_rate": 4,
                                                  "lead": "tri"}),
    ("tense_suspense", "mystery tension spooky", {"bpm": 90, "root": 45, "scale": "phrygian", "prog": [0, 1, 0, 6], "layers": ["pad", "bass"], "drums": "pulse", "pad": "saw",
                                                  "bass_pattern": "half", "verb": 0.5}),
    ("epic_heroic", "motivation sports winner", {"bpm": 96, "root": 50, "scale": "minor", "prog": [0, 5, 2, 6], "layers": ["pad", "bass", "arp"], "drums": "march", "pad": "saw",
                                                 "arp_rate": 2}),
    ("sad_reflective", "sad storytelling mental_health", {"bpm": 64, "root": 57, "scale": "minor", "prog": [0, 5, 3, 4], "layers": ["pad", "melody"], "drums": "", "pad": "sine",
                                                          "lead": "tri", "bars_per_chord": 1, "verb": 0.5}),
    ("dreamy_ambient", "sleep calm magic", {"bpm": 60, "root": 62, "scale": "major", "prog": [0, 3, 5, 4], "layers": ["pad", "bells"], "drums": "", "pad": "sine", "verb": 0.6,
                                            "sevenths": True}),
    ("tech_future_pulse", "tech ai startup", {"bpm": 118, "root": 57, "scale": "minor", "prog": [0, 5, 3, 6], "layers": ["pad", "bass", "arp"], "drums": "house", "arp_rate": 4,
                                              "lead": "square", "pad": "saw"}),
    ("crypto_trap_beat", "crypto trading finance", {"bpm": 140, "root": 53, "scale": "minor_penta", "prog": [0, 3, 2, 4], "layers": ["pad", "bass"], "drums": "trap",
                                                    "bass_wave": "sine", "bass_pattern": "half"}),
    ("funky_groove", "entertainment comedy", {"bpm": 104, "root": 55, "scale": "dorian", "prog": [0, 3, 0, 4], "layers": ["bass", "arp", "pad"], "drums": "four",
                                              "bass_wave": "saw", "arp_rate": 4, "lead": "tri"}),
    ("cinematic_rise", "storytelling motivation", {"bpm": 80, "root": 48, "scale": "minor", "prog": [5, 6, 0, 4], "layers": ["pad", "arp", "bass"], "drums": "pulse", "pad": "saw",
                                                   "arp_rate": 2, "verb": 0.45, "bars_per_chord": 1}),
    ("meditation_drone", "mental_health calm stoicism", {"bpm": 50, "root": 50, "scale": "penta", "prog": [0, 0, 3, 0], "layers": ["pad", "bells"], "drums": "", "pad": "sine",
                                                         "verb": 0.7}),
    ("playful_pizzicato", "kids education comedy", {"bpm": 126, "root": 67, "scale": "major", "prog": [0, 4, 3, 4], "layers": ["arp", "bass"], "drums": "", "arp_rate": 2,
                                                    "lead": "tri"}),
    ("news_bulletin", "media business", {"bpm": 120, "root": 52, "scale": "minor", "prog": [0, 6, 5, 4], "layers": ["pad", "bass", "arp"], "drums": "four", "arp_rate": 4,
                                         "lead": "square"}),
    ("tropical_chill", "travel ocean relaxation", {"bpm": 100, "root": 64, "scale": "major", "prog": [0, 5, 3, 4], "layers": ["pad", "bass", "bells"], "drums": "house",
                                                   "pad": "sine"}),
    ("retro_chiptune", "gaming kids", {"bpm": 132, "root": 60, "scale": "major", "prog": [0, 5, 3, 4], "layers": ["bass", "arp", "melody"], "drums": "four", "lead": "square",
                                       "bass_wave": "square", "arp_rate": 4}),
    ("dark_documentary", "history science storytelling", {"bpm": 72, "root": 45, "scale": "minor", "prog": [0, 3, 5, 4], "layers": ["pad", "bass"], "drums": "pulse",
                                                          "pad": "tri", "verb": 0.5}),
    ("hopeful_piano_like", "motivation self_improvement health", {"bpm": 84, "root": 60, "scale": "major", "prog": [0, 4, 5, 3], "layers": ["pad", "melody", "arp"], "drums": "",
                                                                  "lead": "tri", "pad": "sine", "arp_rate": 2}),
    ("mystery_detective", "mystery law storytelling", {"bpm": 86, "root": 50, "scale": "dorian", "prog": [0, 3, 0, 4], "layers": ["bass", "melody"], "drums": "lofi",
                                                       "bass_wave": "sine", "lead": "tri"}),
    ("workout_energy", "fitness sports motivation", {"bpm": 128, "root": 57, "scale": "minor", "prog": [0, 5, 6, 4], "layers": ["bass", "arp", "pad"], "drums": "house",
                                                     "arp_rate": 4, "lead": "saw", "pad": "saw"}),
    ("spooky_halloween", "spooky holiday", {"bpm": 76, "root": 50, "scale": "phrygian", "prog": [0, 1, 4, 1], "layers": ["pad", "bells", "bass"], "drums": "pulse",
                                            "pad": "saw", "verb": 0.6}),
    ("festive_holiday", "holiday celebration family", {"bpm": 116, "root": 62, "scale": "major", "prog": [0, 3, 4, 0], "layers": ["bells", "bass", "arp"], "drums": "march",
                                                       "arp_rate": 2, "lead": "tri"}),
    ("space_ambient", "space science calm", {"bpm": 56, "root": 52, "scale": "major", "prog": [0, 5, 3, 1], "layers": ["pad", "bells"], "drums": "", "pad": "sine",
                                             "verb": 0.7, "sevenths": True}),
    ("cooking_show", "food cooking", {"bpm": 110, "root": 65, "scale": "major", "prog": [0, 3, 1, 4], "layers": ["bass", "arp", "bells"], "drums": "lofi", "arp_rate": 2,
                                      "lead": "tri"}),
]
