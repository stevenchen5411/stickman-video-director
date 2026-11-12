#!/usr/bin/env python3
"""Deterministic quality audit for analysis packages.

visual_activity_pct = share of scenes (beats) that move: a non-idle character motion, an overlay, or a widget.
If it is below 75%, motions/overlays from the library are injected onto the static beats and the repaired
scene ids are recorded in quality_audit.auto_repaired_scenes. All numbers are computed, never guessed.

CLI: python3 engine/audit.py PACKAGE.json [--write]
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from typing import Any, Dict, List, Optional

import common
import schemas

WORDS_PER_SEC = 2.6          # speaking rate at pace_multiplier 1.0
MIN_SPEECH_SEC = 0.8
STATIC_MOTIONS = {"idle_breathing"}
MAX_BEAT_SEC = 7.0           # longer beats are reported as warnings


def speech_sec(text: str, pace: float) -> float:
    words = len(text.split())
    return max(MIN_SPEECH_SEC, words / (WORDS_PER_SEC * max(0.5, pace)))


def scene_sec(scene: Dict[str, Any]) -> float:
    pr = scene["narration"]["prosody"]
    return speech_sec(scene["narration"]["text"], pr.get("pace_multiplier", 1.0)) + pr.get("post_breath_pause_ms", 240) / 1000


def is_active(scene: Dict[str, Any]) -> bool:
    motion = scene["character"].get("motion_id")
    va = scene["visual_aid"]
    return bool((motion and motion not in STATIC_MOTIONS) or va.get("overlay_id") or va.get("widget_id"))


def activity_pct(scenes: List[Dict[str, Any]]) -> float:
    if not scenes:
        return 0.0
    return round(100.0 * sum(1 for s in scenes if is_active(s)) / len(scenes), 1)


def _pools(index: schemas.LibraryIndex):
    motions = [a.id for a in index.by_category("04_motions")
               if a.id not in STATIC_MOTIONS and a.meta.get("kind", "") != "spring"] or \
              [a.id for a in index.by_category("04_motions") if a.id not in STATIC_MOTIONS]
    overlays = [a.id for a in index.by_category("08_overlays")]
    return motions, overlays


def auto_repair(scenes: List[Dict[str, Any]], index: schemas.LibraryIndex) -> List[str]:
    """Inject motions (preferred) or overlays onto static beats. Returns repaired scene ids."""
    motions, overlays = _pools(index)
    repaired: List[str] = []
    m_i = o_i = 0
    prev_motion: Optional[str] = None
    for sc in scenes:
        if is_active(sc):
            prev_motion = sc["character"].get("motion_id") or prev_motion
            continue
        if motions:
            choice = motions[m_i % len(motions)]
            if choice == prev_motion and len(motions) > 1:
                m_i += 1
                choice = motions[m_i % len(motions)]
            sc["character"]["motion_id"] = choice
            m_i += 1
            prev_motion = choice
        elif overlays:
            sc["visual_aid"]["overlay_id"] = overlays[o_i % len(overlays)]
            o_i += 1
        else:
            continue
        repaired.append(sc["id"])
    return repaired


def audit_dict(pkg: Dict[str, Any], index: schemas.LibraryIndex, shots: Optional[List[Dict[str, Any]]] = None
               ) -> Dict[str, Any]:
    """Return a copy of `pkg` with quality_audit + status recomputed, plus `_report` (warnings) stripped by callers."""
    out = copy.deepcopy(pkg)
    scenes = out["scenes"]
    warnings: List[str] = []
    pct = activity_pct(scenes)
    repaired: List[str] = []
    if pct < schemas.MIN_VISUAL_ACTIVITY_PCT:
        repaired = auto_repair(scenes, index)
        pct = activity_pct(scenes)

    grounded = True
    known = {s["shot_id"] for s in shots} if shots else None
    for sc in scenes:
        ref = sc.get("source_shot_ref") or {}
        if not (ref.get("shot_id") and ref.get("frame_path") and ref.get("original_duration_sec")):
            grounded = False
            warnings.append(f"{sc['id']}: missing source_shot_ref")
        elif known is not None and ref["shot_id"] not in known:
            grounded = False
            warnings.append(f"{sc['id']}: shot {ref['shot_id']} not in VIDEO.md")
        if not (sc["visual_aid"].get("fallback_visual_aid")):
            grounded = False
            warnings.append(f"{sc['id']}: missing fallback_visual_aid")
        if scene_sec(sc) > MAX_BEAT_SEC:
            warnings.append(f"{sc['id']}: beat {scene_sec(sc):.1f}s exceeds {MAX_BEAT_SEC}s")

    total = sum(scene_sec(s) for s in scenes)
    passed = pct >= schemas.MIN_VISUAL_ACTIVITY_PCT and grounded
    out["quality_audit"] = {
        "estimated_duration_sec": round(total, 2),
        "avg_beat_sec": round(total / len(scenes), 2) if scenes else 0.0,
        "visual_activity_pct": pct,
        "auto_repaired_scenes": repaired,
        "passed": passed,
    }
    if out.get("status") in (None, "draft", "ready_to_generate"):
        out["status"] = "ready_to_generate" if passed else "draft"
    out["_warnings"] = warnings
    return out


def audit_package(pkg: Dict[str, Any], index: schemas.LibraryIndex, shots=None) -> schemas.AnalysisPackage:
    d = audit_dict(pkg, index, shots)
    d.pop("_warnings", None)
    return schemas.AnalysisPackage.model_validate(d)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("package")
    ap.add_argument("--write", action="store_true", help="write repaired package back")
    a = ap.parse_args(argv)
    raw = schemas.load_json(a.package)
    index = schemas.load_library_index(common.library_dir())
    d = audit_dict(raw, index)
    warns = d.pop("_warnings")
    qa = d["quality_audit"]
    print(json.dumps(qa, indent=2))
    for w in warns:
        print("WARN", w)
    if a.write:
        schemas.save_json(a.package, schemas.AnalysisPackage.model_validate(d))
    return 0 if qa["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
