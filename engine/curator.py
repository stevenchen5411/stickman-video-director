#!/usr/bin/env python3
"""Library Curator Agent: Global vs. Specific gap analysis against scouted videos.

* Global gaps: categories whose global-scope asset count is below TARGET_MIN.
* Specific gaps: niche terms that scouted outliers keep using (weighted by outlier multiplier) but that the
  library covers with fewer than MIN_COVERAGE assets tagged for them.
Output (cache/curator_report.json) includes ready-to-run `requests` for forge.py.

CLI: python3 engine/curator.py [--scout latest|FILE]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

import common
import scout as scout_mod
import schemas

TARGET_MIN = {"01_characters": 5, "02_poses": 8, "03_expressions": 6, "04_motions": 6, "05_scenes": 6,
              "06_props": 8, "07_widgets": 4, "08_overlays": 5, "09_transitions": 4, "10_caption_styles": 3,
              "11_themes": 3, "12_voices": 5, "13_bgm": 4, "14_sfx": 8}
IDEAS = {
    "01_characters": ["quinn_detective", "milo_student", "ada_engineer", "bruno_chef", "zed_astronaut"],
    "02_poses": ["thinking_chin", "celebrating_arms_up", "facepalm", "waving", "sitting_desk", "pushing_wall"],
    "03_expressions": ["laughing_open", "sad_droop", "determined_focus", "confused_tilt", "sleepy_half_lid"],
    "04_motions": ["slide_in_left", "pulse_scale", "zoom_out_reveal", "wobble_dizzy", "shake_impact", "drift_up"],
    "05_scenes": ["office_desk", "park_bench", "classroom_board", "kitchen_counter", "gym_floor", "night_street"],
    "06_props": ["magnifying_glass", "stopwatch", "trophy", "warning_sign", "smartphone", "calendar_page", "key_gold", "heart_red"],
    "07_widgets": ["pie_split_chart", "timeline_three_steps", "checklist_card", "line_chart_decline"],
    "08_overlays": ["stars_dizzy", "hearts_float", "anger_vein", "zzz_sleep", "lightning_flash"],
    "09_transitions": ["swipe_up", "iris_close", "glitch_cut", "spin_zoom"],
    "10_caption_styles": ["karaoke_blue_glow", "minimal_lowercase"],
    "11_themes": ["sunset_warm", "mono_ink", "forest_calm"],
    "12_voices": ["sage_steady_charon", "spark_fast_puck", "velvet_soft_aoede"],
    "13_bgm": ["epic_build_rise", "soft_piano_drift", "dark_suspense_low"],
    "14_sfx": ["swoosh_up", "error_buzz", "coin_ping", "camera_shutter", "heartbeat_single", "page_flip", "click_ui", "sparkle_short"],
}
STOP = set("the a an and or of to in on for with is are was be it this that you your how why what when i we they my "
           "from at as by not no do does did can will just more most about into out up so if but than then them "
           "their there these those have has had get got make made one two three video shorts".split())
MIN_COVERAGE = 2
VISUAL_SPECIFIC = ("05_scenes", "06_props")


def niche_terms(outliers: List[Dict[str, Any]], top_k: int = 8) -> List[str]:
    score: Counter = Counter()
    for o in outliers:
        w = float(o.get("outlier_multiplier", 1.0))
        for tok in re.findall(r"[a-z]{4,}", (o.get("niche", "") + " " + o.get("title", "")).lower().replace("_", " ")):
            if tok not in STOP:
                score[tok] += w
    return [t for t, _ in score.most_common(top_k)]


def analyze(index: schemas.LibraryIndex, outliers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    outliers = outliers or []
    counts = {c: len(index.by_category(c)) for c in schemas.CATEGORIES}
    existing = {a.id for a in index.assets}
    requests: List[Dict[str, Any]] = []
    global_gaps = []
    for cat in schemas.CATEGORIES:
        have = sum(1 for a in index.by_category(cat) if a.scope == "global")
        need = TARGET_MIN[cat] - have
        if need > 0:
            global_gaps.append({"category": cat, "have": have, "target": TARGET_MIN[cat], "missing": need})
            for idea in [i for i in IDEAS[cat] if i not in existing][:need]:
                requests.append({"category": cat, "id": idea, "scope": "global", "niche_tags": ["general"],
                                 "brief": f"general-purpose {cat[3:].replace('_', ' ')} asset: {idea.replace('_', ' ')}"})
    specific_gaps = []
    for term in niche_terms(outliers):
        cover = sum(1 for a in index.assets if a.category in VISUAL_SPECIFIC
                    and any(term in t.lower() for t in a.niche_tags))
        if cover < MIN_COVERAGE:
            specific_gaps.append({"term": term, "coverage": cover, "needed": MIN_COVERAGE - cover})
            for cat, suffix in (("05_scenes", "backdrop"), ("06_props", "icon")):
                rid = f"{term}_{suffix}"
                if rid not in existing and not any(r["id"] == rid for r in requests):
                    requests.append({"category": cat, "id": rid, "scope": "specific", "niche_tags": [term],
                                     "brief": f"{suffix} illustrating '{term}' for short explainer videos"})
    return {"updated_at_utc": common.utc_now_iso(), "library_counts": counts, "global_gaps": global_gaps,
            "specific_gaps": specific_gaps, "requests": requests,
            "outliers_considered": len(outliers)}


def enrich_briefs(report: Dict[str, Any]) -> Dict[str, Any]:
    """Optional: ask the AI for richer one-line forge briefs. Silently skipped when no provider works."""
    if not report["requests"]:
        return report
    try:
        import llm
        data, _ = llm.call_json(
            "You write concise art briefs for a stickman-video asset library. Reply with one JSON object.",
            json.dumps({"requests": [{"id": r["id"], "category": r["category"], "brief": r["brief"]} for r in report["requests"]],
                        "output": {"briefs": {"<id>": "<=20 word visual brief"}}}))
        briefs = data.get("briefs", {})
        for r in report["requests"]:
            if isinstance(briefs.get(r["id"]), str):
                r["brief"] = briefs[r["id"]][:200]
    except Exception:  # noqa: BLE001
        pass
    return report


def curate(outliers: Optional[List[Dict[str, Any]]] = None, use_ai: bool = True, save: bool = True) -> Dict[str, Any]:
    index = schemas.load_library_index(common.library_dir())
    if outliers is None:
        outliers = scout_mod.load_scout()
    report = analyze(index, outliers)
    if use_ai:
        report = enrich_briefs(report)
    if save:
        p = common.cache_dir() / "curator_report.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-ai", action="store_true")
    a = ap.parse_args(argv)
    common.ensure_dirs()
    r = curate(use_ai=not a.no_ai)
    print(json.dumps({k: r[k] for k in ("global_gaps", "specific_gaps")}, indent=2))
    print(f"{len(r['requests'])} forge requests queued in report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
