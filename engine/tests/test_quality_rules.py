"""Quality rules: background runs and repeated motions are broken; nothing is invented when no good alternative."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import quality_rules as qr  # noqa: E402


class Idx:
    def __init__(self, scenes):
        self.s = scenes

    def by_category(self, cat):
        return self.s if cat == "05_scenes" else []


def scene(i, bg, motion=None):
    return {"id": f"scene_{i}", "environment": {"scene_id": bg}, "character": {"motion_id": motion},
            "narration": {"text": "x"}, "visual_aid": {"fallback_visual_aid": {}}}


IDX = Idx([NS(id="kitchen_home", niche_tags=["food", "home"]), NS(id="kitchen_modern", niche_tags=["food"]),
           NS(id="gym_floor", niche_tags=["fitness"]), NS(id="park_day", niche_tags=["outdoor"])])


def run(scs):
    return [s["environment"]["scene_id"] for s in scs]


def test_three_in_a_row_gets_a_sibling_background():
    scs = [scene(i, "kitchen_home") for i in range(4)]
    notes = qr.vary_backgrounds(scs, IDX)
    assert run(scs)[:2] == ["kitchen_home"] * 2 and run(scs)[2] == "kitchen_modern"
    assert notes and "kitchen_modern" in notes[0]


def test_max_run_never_exceeds_limit_when_alternatives_exist():
    scs = [scene(i, "kitchen_home") for i in range(7)]
    qr.vary_backgrounds(scs, Idx([NS(id=f"kitchen_{k}", niche_tags=["food"]) for k in "abcdef"] + [NS(id="kitchen_home", niche_tags=["food"])]))
    best = cur = 1
    for a, b in zip(run(scs), run(scs)[1:]):
        cur = cur + 1 if a == b else 1
        best = max(best, cur)
    assert best <= qr.MAX_SAME_BG


def test_no_close_alternative_keeps_background_and_reports():
    scs = [scene(i, "gym_floor") for i in range(3)]
    notes = qr.vary_backgrounds(scs, IDX)
    assert run(scs) == ["gym_floor"] * 3 and "no close alternative" in notes[0]


def test_short_runs_untouched():
    scs = [scene(0, "kitchen_home"), scene(1, "kitchen_home"), scene(2, "park_day")]
    assert qr.vary_backgrounds(scs, IDX) == [] and run(scs)[0] == "kitchen_home"


def test_repeated_motion_replaced_not_equal_to_neighbours():
    scs = [scene(0, "a", "nod_yes"), scene(1, "a", "nod_yes"), scene(2, "b", "wave_right")]
    notes = qr.vary_motions(scs, ["nod_yes", "wave_right", "explain_hands", "sway_gentle"])
    new = scs[1]["character"]["motion_id"]
    assert notes and new not in ("nod_yes", "wave_right")


def test_static_and_empty_motions_ignored():
    scs = [scene(0, "a", "idle_breathing"), scene(1, "a", "idle_breathing"), scene(2, "a", None), scene(3, "a", None)]
    assert qr.vary_motions(scs, ["nod_yes"]) == []
