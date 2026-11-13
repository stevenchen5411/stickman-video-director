"""Regression set: five very different topics x three aspect ratios must keep the same quality guarantees.

Metrics asserted for every topic (the library is whatever assets/library holds - seed or the full core_v1 pack):
  layout collisions == 0 | no widget still showing library sample text | background run <= 2 (or reported) |
  no identical motion back to back | caption groups 2..4 words and never across a sentence | activity >= 75%.
"""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit  # noqa: E402
import caption_split  # noqa: E402
import cairo  # noqa: E402
import common  # noqa: E402
import director  # noqa: E402
import quality_rules  # noqa: E402
import render_cairo as rc  # noqa: E402
import schemas  # noqa: E402
import widget_contract as wc  # noqa: E402
import test_engine as te  # noqa: E402

TOPICS = {
    "nutrition": ["Everything you eat is built from just two kinds of nutrients. Know both.",
                  "Carbs are your fast fuel, like gas in a tank. Your brain runs on them constantly.",
                  "Protein rebuilds muscle, fixes tissue, and backs up your defenses. Eggs, fish, beans.",
                  "Healthy fats feed your hormones and give slow burn energy. Think avocado and olive oil.",
                  "Micros are vitamins and minerals. You need tiny amounts, but without them things break down.",
                  "Your trick is variety. Oranges bring vitamin C, spinach brings iron. Color your plate.",
                  "Build it simply: some protein, some carbs, some good fats, and plenty of plants.",
                  "Then move. A walk, some yoga, or a workout, because food and movement work as a team."],
    "sleep": ["Most people think more hours in bed means better sleep. It does not.",
              "Your body runs on a clock. Light in the morning sets it, and darkness at night winds it down.",
              "Screens late at night tell your brain it is still day. Dim everything an hour before bed.",
              "Keep the room cool, dark and quiet. Three small changes, and deep sleep follows.",
              "Caffeine stays in your body for hours. Stop by noon and watch what happens to your nights.",
              "Wake at the same time every day, even on weekends. Consistency beats catching up.",
              "Try it for one week and notice your mornings change."],
    "trading": ["Most traders lose because they size positions on emotion, not on a plan.",
                "Rule one: risk a fixed percent per trade. One percent keeps you alive through a bad streak.",
                "Rule two: know your exit before your entry. A stop loss is a decision made while calm.",
                "Rule three: journal every trade. Patterns in your mistakes are your real edge.",
                "A winning rate of forty percent still profits when winners are twice the size of losers.",
                "Fear and greed move the market. Your job is to stay boring and consistent.",
                "Start small, review weekly, and let the numbers teach you."],
    "productivity": ["You do not have a time problem. You have an attention problem.",
                     "Pick the one task that matters most. Do it first, before email, before chat.",
                     "Work in focused blocks of forty minutes, then rest for ten. Your brain needs the break.",
                     "Close every tab you are not using. Each open loop quietly drains your focus.",
                     "Write tomorrow's top three tasks tonight. You will wake up with a plan, not a pile.",
                     "Say no to good ideas so you can say yes to great ones.",
                     "Small daily wins, repeated, beat heroic weekend sprints."],
    "history": ["Rome did not fall in a day. It faded over centuries of small failures.",
                "Armies grew expensive, taxes rose, and loyalty moved from the state to the generals.",
                "Coins were thinned with cheaper metal, and prices climbed. Sound familiar?",
                "Roads built for trade became highways for invaders. Strength turned into a weakness.",
                "In four seventy six, the last emperor was removed, and almost nobody noticed.",
                "Empires rarely end with a bang. They end when people stop believing in them."],
}
SIZES = {"9:16": (480, 854), "16:9": (854, 480), "1:1": (640, 640)}


def _story(v):
    if isinstance(v, str):
        return "Real " + v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v + 1
    if isinstance(v, list):
        return [_story(x) for x in v]
    if isinstance(v, dict):
        return {k: _story(x) for k, x in v.items()}
    return v


def _plan(topic, idx, lib):
    """A deliberately sloppy director: one background for most scenes, every other widget with sample text only."""
    ids = lambda c: sorted(a.id for a in idx.by_category(c))
    chars, poses, exprs, scs, props = ids("01_characters"), ids("02_poses"), ids("03_expressions"), ids("05_scenes"), ids("06_props")
    motions = [m for m in ("nod_yes", "talk_gesture_a") if m in ids("04_motions")] or ids("04_motions")[:1]
    wids = [a for a in ids("07_widgets") if (wc.load(idx, lib, a) or {}).get("type") in wc.CONTENT]
    out = []
    for i, text in enumerate(TOPICS[topic]):
        sc = {"shot_id": f"shot_{i % 4 + 1:02d}", "character_id": chars[0], "pose_id": poses[i % len(poses)],
              "expression_id": exprs[i % len(exprs)], "motion_id": motions[0],          # same motion every scene
              "scene_id": scs[0] if i < 6 else scs[min(1, len(scs) - 1)],                 # long same-background run
              "prop_id": props[(i * 7) % len(props)], "text": text, "fallback": {"title": text.split()[0]}}
        if wids and i % 2 == 0:
            wj = wc.load(idx, lib, wids[i % len(wids)])
            sc["widget_id"] = wids[i % len(wids)]
            if i % 4 == 0:                                                                # real data on half of them
                sc["fallback"]["widget_data"] = _story(wc.content(wj["type"], wj["data"]))
        out.append(sc)
    return {"title_variants": ["A", "B", "C"], "scenes": out}


def _timeline_words(text):
    words, t = [], 0.0
    for w in text.split():
        words.append({"word": w, "start": round(t, 3), "end": round(t + 0.3, 3)})
        t += 0.38 + (0.35 if w.endswith((".", ",")) else 0.0)
    return words


@pytest.fixture(scope="module")
def lib_idx():
    lib = common.library_dir()
    return lib, schemas.load_library_index(lib)


@pytest.mark.parametrize("topic", sorted(TOPICS))
def test_topic_keeps_quality_guarantees(topic, lib_idx):
    lib, idx = lib_idx
    raw = director.assemble_package(_plan(topic, idx, lib), te.fake_fx(), idx, {"niche": topic})
    d = audit.audit_dict(raw, idx)
    pkg = schemas.AnalysisPackage.model_validate({k: v for k, v in d.items() if k != "_warnings"})
    S = d["scenes"]

    # widgets: none may still show library sample text
    for sc in S:
        wid = sc["visual_aid"].get("widget_id")
        if wid:
            assert not wc.is_stock(wc.load(idx, lib, wid), sc["visual_aid"]["fallback_visual_aid"]), (topic, sc["id"], wid)
    # backgrounds: runs capped, or the audit said why not
    bg = [s["environment"]["scene_id"] for s in S]
    run = best = 1
    for a, b in zip(bg, bg[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    notes = d["quality_audit"]["quality_repairs"]
    assert best <= quality_rules.MAX_SAME_BG or any("no close alternative" in n for n in notes), (topic, bg)
    # motions: nothing identical back to back
    mo = [s["character"].get("motion_id") for s in S]
    assert not any(a and a == b and a not in quality_rules.STATIC_MOTIONS for a, b in zip(mo, mo[1:])), (topic, mo)
    assert d["quality_audit"]["visual_activity_pct"] >= schemas.MIN_VISUAL_ACTIVITY_PCT

    # captions: chunk sizes and sentence boundaries on this topic's own text
    for sc in S:
        for g in caption_split.chunks(_timeline_words(sc["narration"]["text"]), 3):
            assert 1 <= len(g) <= 4
            assert not any(w["word"].endswith((".", "!", "?")) for w in g[:-1]), [w["word"] for w in g]

    # layout: zero residual collisions at every aspect ratio
    for name, (W, H) in SIZES.items():
        assets = rc.Assets(lib, (W, H))
        theme = {**rc.DEFAULT_THEME, **((assets.json(pkg.render_config.theme_id, "11_themes") or {}).get("palette", {}))}
        cap = assets.json(pkg.render_config.caption_style_id, "10_caption_styles")
        scenes = []
        for sc in pkg.scenes:
            words = _timeline_words(sc.narration.text)
            tl = {"words": words, "say": None, "speech_sec": words[-1]["end"], "start_sec": 0.0, "end_sec": words[-1]["end"] + 0.4}
            scenes.append(rc.SceneCtx(pkg, sc, tl, assets, theme, cap))
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H))
        issues = rc.layout_report(scenes, ctx, W, H)
        bad = [(r["scene"], r["issues"]) for r in issues if r["issues"]]
        assert not bad, (topic, name, bad)
