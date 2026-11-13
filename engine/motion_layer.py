#!/usr/bin/env python3
"""Default motion that every scene gets on top of its authored motion, so nothing freezes:
emphasis pulse (on the words the director stressed), slow camera drift (when the motion has no camera track) and
varied prop entrances. Pure functions; render_cairo applies them."""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Sequence, Tuple

PULSE_SEC = 0.45
DRIFT_SCALE = 0.035
DRIFT_SHIFT = 0.008


def _n(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(w).lower())


def emphasis_times(words: Sequence[Dict[str, Any]], phrases: Sequence[str]) -> List[float]:
    """Start time (scene-local) of each stressed phrase found in the scene's spoken words."""
    toks = [_n(w.get("word", "")) for w in words]
    out: List[float] = []
    for ph in phrases:
        want = [_n(x) for x in str(ph).split() if _n(x)]
        if not want:
            continue
        for i in range(len(toks) - len(want) + 1):
            if toks[i:i + len(want)] == want:
                out.append(float(words[i]["start"]))
                break
    return sorted(out)


def pulse(t: float, times: Sequence[float]) -> float:
    """0..1 bump that peaks at each emphasis time and fades over PULSE_SEC."""
    best = 0.0
    for te in times:
        dt = t - te
        if 0.0 <= dt <= PULSE_SEC:
            best = max(best, (1.0 - dt / PULSE_SEC) ** 2)
    return best


def has_camera_track(motion: Any) -> bool:
    return bool(motion) and any(str(tr.get("target", "")).startswith("camera.") for tr in motion.get("tracks", []))


def drift(t: float, dur: float, index: int, motion: Any) -> Tuple[float, float]:
    """(extra camera scale factor, extra camera.x) - a slow push that alternates direction per scene."""
    if has_camera_track(motion):
        return 1.0, 0.0
    p = min(1.0, max(0.0, t / max(1.5, dur)))
    return 1.0 + DRIFT_SCALE * p, (DRIFT_SHIFT if index % 2 == 0 else -DRIFT_SHIFT) * p


def entrance_variant(prop_id: str) -> int:
    return sum(ord(c) for c in prop_id or "") % 3


def entrance_offset(variant: int, p: float, W: float, H: float, outward: int) -> Tuple[float, float]:
    """Extra (dx, dy) for the prop while it enters: 0 pop in place, 1 slide in from the outer edge, 2 drop from above."""
    q = 1.0 - min(1.0, max(0.0, p))
    if variant == 1:
        return outward * q * 0.35 * W, 0.0
    if variant == 2:
        return 0.0, -q * 0.12 * H
    return 0.0, 0.0
