#!/usr/bin/env python3
"""Topic-independent quality rules applied by audit.py (each returns human-readable repair notes).

* backgrounds: the same scene art for at most MAX_SAME_BG scenes in a row (longer runs get a new background).
* motions: never the same gesture/camera motion in two consecutive scenes.

Props are deliberately not auto-swapped: token matching picked worse props (e.g. start -> startup) than the
director's own semantic choice, so prop relevance stays a prompt rule.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

MAX_SAME_BG = 2
STATIC_MOTIONS = {"idle_breathing"}


# --------------------------------------------------------------------------- backgrounds
def _family(aid: str) -> str:
    return aid.split("_")[0]


def vary_backgrounds(scenes: List[Dict[str, Any]], index: Any) -> List[str]:
    """Break runs longer than MAX_SAME_BG. Prefer a sibling of the same place (kitchen_home -> kitchen_*) or a scene with
    3+ shared niche tags; with no close alternative the background is kept and the repeat is reported."""
    pool = list(index.by_category("05_scenes"))
    by_id = {a.id: a for a in pool}
    notes: List[str] = []
    run = 1
    for i, sc in enumerate(scenes):
        env = sc["environment"]
        run = run + 1 if i and env["scene_id"] == scenes[i - 1]["environment"]["scene_id"] else 1
        if run <= MAX_SAME_BG:
            continue
        cur = by_id.get(env["scene_id"])
        recent = {scenes[j]["environment"]["scene_id"] for j in range(max(0, i - 3), i)} | {env["scene_id"]}
        tags: Set[str] = {t for t in (cur.niche_tags if cur else []) if t != "general"}

        def score(a: Any) -> int:
            return (3 if _family(a.id) == _family(env["scene_id"]) else 0) + len(tags & set(a.niche_tags))

        ranked = sorted(((score(a), a.id) for a in pool if a.id not in recent), key=lambda x: (-x[0], x[1]))
        choice: Optional[str] = ranked[0][1] if ranked and ranked[0][0] >= 3 else None   # same place or 3 shared tags
        if choice is None:                                   # no close alternative: keep it, but say so
            notes.append(f"{sc['id']}: background {env['scene_id']} repeats {run} scenes in a row (no close alternative)")
            continue
        notes.append(f"{sc['id']}: background {env['scene_id']} -> {choice} (same one for {run} scenes in a row)")
        env["scene_id"] = choice
        run = 1
    return notes


# --------------------------------------------------------------------------- motions
def vary_motions(scenes: List[Dict[str, Any]], motion_pool: List[str]) -> List[str]:
    notes: List[str] = []
    for i in range(1, len(scenes)):
        cur = scenes[i]["character"].get("motion_id")
        if not cur or cur in STATIC_MOTIONS or cur != scenes[i - 1]["character"].get("motion_id"):
            continue
        nxt = scenes[i + 1]["character"].get("motion_id") if i + 1 < len(scenes) else None
        opts = [m for m in motion_pool if m != cur and m != nxt]
        if not opts:
            continue
        new = opts[i % len(opts)]
        notes.append(f"{scenes[i]['id']}: motion {cur} -> {new} (same as the previous scene)")
        scenes[i]["character"]["motion_id"] = new
    return notes
