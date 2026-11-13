"""Widget data contract: story data or no widget; never library sample text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit  # noqa: E402
import widget_contract as wc  # noqa: E402

VERSUS = {"type": "versus", "data": {"left": {"title": "BEFORE", "value": "Tired", "caption": "4h sleep"},
                                      "right": {"title": "AFTER", "value": "Sharp", "caption": "8h sleep"}}}
STEPS = {"type": "steps", "data": {"steps": ["Cue", "Routine", "Reward"]}}
BARS = {"type": "bar_chart", "data": {"labels": ["a", "b"], "values": [1, 2]}}
MYTH = {"left": {"title": "MYTH", "value": "Fat is bad", "caption": "Old advice"},
        "right": {"title": "FACT", "value": "Fat fuels you", "caption": "Healthy fats"}}


def test_sample_widget_is_stock():
    assert wc.is_stock(VERSUS, {"title": "x", "subtitle": None})
    assert wc.is_stock(STEPS, None)


def test_story_data_makes_it_real():
    fb = {"title": "t", "data": MYTH}
    assert not wc.is_stock(VERSUS, fb)
    assert wc.apply(VERSUS, fb)["data"]["left"]["value"] == "Fat is bad"


def test_missing_keys_rejected_no_stock_fill_in():
    bad = {"left": {"title": "MYTH", "value": "Fat is bad"}, "right": MYTH["right"]}     # caption missing
    assert wc.coerce(VERSUS, bad) is None
    assert wc.is_stock(VERSUS, {"title": "t", "data": bad})


def test_wrong_types_rejected():
    assert wc.coerce(STEPS, {"steps": "Plan then act"}) is None
    assert wc.coerce(STEPS, {"steps": []}) is None
    assert wc.coerce(STEPS, {"steps": list("abcdefghij")}) is None


def test_chart_labels_and_values_must_match():
    assert wc.coerce(BARS, {"labels": ["a", "b", "c"], "values": [1, 2]}) is None
    assert wc.coerce(BARS, {"labels": ["Carbs", "Fat"], "values": [60, 40]}) == {"labels": ["Carbs", "Fat"], "values": [60, 40]}


def test_long_text_trimmed():
    out = wc.coerce(STEPS, {"steps": ["x" * 200, "b"]})
    assert out and len(out["steps"][0]) <= wc.MAX_STR


def test_partial_fill_is_still_stock():
    counter = {"type": "counter", "data": {"title": "Generic", "label": "L", "to": 10}}
    assert wc.is_stock(counter, {"title": "Calories", "values": [2000]})              # label is still sample text
    assert not wc.is_stock(counter, {"title": "Calories", "data": {"title": "Cal", "label": "per day", "to": 2000}})
    checklist = {"type": "checklist", "data": {"title": "Cons", "items": ["Risky", "Slow"], "checked": [False, False]}}
    assert wc.is_stock(checklist, {"title": "Fats"})                                  # new title over sample items


def test_audit_drops_stock_widget_and_keeps_real_one(monkeypatch):
    lib = {"w_stock": VERSUS, "w_real": VERSUS}
    monkeypatch.setattr(wc, "load", lambda index, lib_dir, wid: lib.get(wid))
    sc = lambda i, wid, data: {"id": f"scene_{i}", "visual_aid": {"type": "widget", "widget_id": wid, "prop_id": None,
                               "overlay_id": None, "fallback_visual_aid": {"type": "callout_card", "title": "T", "data": data}}}
    scenes = [sc(1, "w_stock", None), sc(2, "w_real", MYTH)]
    warns = []
    dropped = audit.strip_stock_widgets(scenes, None, warns)
    assert dropped == ["scene_1"]
    assert scenes[0]["visual_aid"]["widget_id"] is None and scenes[0]["visual_aid"]["type"] == "callout_card"
    assert scenes[1]["visual_aid"]["widget_id"] == "w_real"


def _story(v):
    if isinstance(v, str):
        return "Story " + v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v + 1
    if isinstance(v, list):
        return [_story(x) for x in v]
    if isinstance(v, dict):
        return {k: _story(x) for k, x in v.items()}
    return v


def test_director_keeps_widget_with_story_data_and_drops_sample(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import common
    import director
    import schemas
    import test_engine as te
    idx = te.index()
    lib = common.library_dir()
    wid, wj = next((a.id, wc.load(idx, lib, a.id)) for a in idx.by_category("07_widgets")
                   if (wc.load(idx, lib, a.id) or {}).get("type") in wc.CONTENT)
    story = _story(wc.content(wj["type"], wj["data"]))
    base = {"character_id": "kael_hoodie", "pose_id": "shrug", "expression_id": "neutral", "widget_id": wid}
    plan = {"title_variants": ["A", "B", "C"], "scenes": [
        {**base, "shot_id": "shot_01", "text": "Here is the real point.", "fallback": {"title": "Real", "widget_data": story}},
        {**base, "shot_id": "shot_02", "text": "Here is a lazy one.", "fallback": {"title": "Lazy"}}]}
    pkg = schemas.AnalysisPackage.model_validate(director.assemble_package(plan, te.fake_fx(), idx, {"niche": "habits"}))
    assert pkg.scenes[0].visual_aid.widget_id == wid and pkg.scenes[0].visual_aid.fallback_visual_aid.data == story
    assert pkg.scenes[1].visual_aid.widget_id is None
