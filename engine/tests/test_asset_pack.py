"""Asset pack (engine/assetgen), renderer extensions (render_fx) and library previews."""
import json
import math
import shutil
from pathlib import Path

import pytest

import audit
import director
import previews
import render_cairo as rc
import render_fx as fx
import schemas
from assetgen import build as pack

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "assets" / "library"


def _lib_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "library"
    shutil.copytree(LIB, dst)
    return dst


def test_pack_plan_is_big_valid_and_unique(tmp_path):
    lib = _lib_copy(tmp_path)
    res = pack.build(lib, dry_run=True)
    assert res["pack_assets"] >= 1000 and not res["skipped_existing"]
    cats = res["by_category"]
    assert all(cats.get(c, 0) >= 20 for c in schemas.CATEGORIES), cats          # every category got a real set
    assert cats["06_props"] >= 300 and cats["05_scenes"] >= 100 and cats["02_poses"] >= 100 and cats["04_motions"] >= 100
    scopes = {e["scope"] for e in pack.plan()}
    assert scopes == {"global", "specific"}


def test_pack_install_merges_without_touching_user_assets(tmp_path):
    lib = _lib_copy(tmp_path)
    idx = schemas.load_library_index(lib)
    # a user-forged prop that happens to share an id with a pack prop must survive untouched
    (lib / "06_props" / "syringe.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>', encoding="utf-8")
    idx.assets.append(schemas.LibraryAsset(id="syringe", category="06_props", file_path="06_props/syringe.svg", niche_tags=["mine"]))
    schemas.save_json(lib / "library_index.json", idx)
    only = ["02_poses", "06_props", "07_widgets", "14_sfx"]
    res = pack.build(lib, only=only)
    assert "06_props:syringe" in res["skipped_existing"]
    idx2 = schemas.load_library_index(lib)
    mine = idx2.get("syringe", "06_props")
    assert mine.niche_tags == ["mine"] and not (mine.meta or {}).get("pack")
    for a in idx2.assets:
        assert (lib / a.file_path).is_file(), a.file_path
    again = pack.build(lib, only=only)                                             # idempotent
    assert again["pack_assets"] == res["pack_assets"] and len(schemas.load_library_index(lib).assets) == len(idx2.assets)
    sfx = idx2.get("ding_bell", "14_sfx")
    assert sfx and (lib / sfx.file_path).stat().st_size > 1000


def test_every_renderer_extension_draws(tmp_path):
    import cairo
    S = 160
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    ctx = cairo.Context(surf)
    th = dict(rc.DEFAULT_THEME)
    char = {"rig": rc.DEFAULT_RIG, "colors": {"line": "#f1f5f9", "fill": "#0f172a", "accent": "#22d3ee"},
            "accessories": [{"type": k, "color": "#ef4444", "color2": "#facc15"} for k in fx.ACCESSORY_KINDS]}
    rc.draw_character(ctx, char, {"joints": {}}, {"eyes": {"style": "heart"}, "extras": ["blush", "tears", "sweat", "anger", "sparkle", "shadow", "freckles"]},
                      "laugh", th, S * 0.9, (S / 2, S * 0.95), 1.0, 0.4)
    for style in ("round", "happy", "closed", "x", "heart", "star", "wink_l", "wink_r", "spiral", "dot", "wide", "sleepy"):
        rc.draw_face(ctx, S / 2, S / 2, 30, {"eyes": {"style": style}}, "smile", 0.0, th, "#fff")
    for m in fx.MOUTH_SHAPES:
        rc.draw_face(ctx, S / 2, S / 2, 30, {}, m, 0.0, th, "#fff")
    for kind in fx.WIDGET_TYPES:
        wj = {"type": kind, "data": {}}
        for t in (0.0, 0.5, 3.0):
            rc.draw_widget(ctx, wj, 5, 5, S - 10, S * 0.5, th, t)
    assets = rc.Assets(LIB, (S, S))
    for kind in fx.OVERLAY_KINDS:
        oj = {"kind": kind, "text": "?", "count": 3, "particle": {}, "motion": {}}
        assert fx.draw_overlay_ext(ctx, oj, S, S, th, 0.6, (S / 2, S / 3), 12, assets) or kind in ("particles", "floating_text")
    for kind in fx.TRANSITION_TYPES:
        for t in (0.0, 0.1, 0.25):
            rc.draw_with_transition(ctx, {"type": kind, "duration_sec": 0.3, "shape": "star"}, t, S, S, lambda: ctx.paint())


def test_signed_knees_and_ground_lock():
    rig = dict(rc.DEFAULT_RIG)
    squat = {**rc.DEFAULT_POSE, "l_hip": 70, "l_knee": 78, "r_hip": -70, "r_knee": 78}
    pts = rc.rig_points(rig, squat, 100.0, (50.0, 200.0))
    assert abs(max(pts["l_foot"][1], pts["r_foot"][1]) - 200.0) < 1e-6            # feet stay on the floor
    floating = rc.rig_points(rig, squat, 100.0, (50.0, 200.0), ground=False)
    assert max(floating["l_foot"][1], floating["r_foot"][1]) < 199.0              # airborne poses may leave the floor
    back = rc.rig_points(rig, {**rc.DEFAULT_POSE, "l_hip": -20, "l_knee": -40}, 100.0, (50.0, 200.0), ground=False)
    fwd = rc.rig_points(rig, {**rc.DEFAULT_POSE, "l_hip": -20, "l_knee": 40}, 100.0, (50.0, 200.0), ground=False)
    assert back["l_foot"][0] < fwd["l_foot"][0]                                    # knee sign picks the bend direction


def test_gesture_motion_offsets_reach_the_pose():
    from assetgen import rigs
    wave = next(m for m in rigs.motions() if m["id"] == "wave_right")["json"]
    ms = rc.eval_motion(wave, 0.3)
    assert ms["pose.r_shoulder"] < -60                                              # arm raised mid-wave
    assert {"character.rot", "character.scale", "camera.rot"} <= set(rc.eval_motion(None, 0))


def test_widget_takes_story_text_from_fallback():
    fb = schemas.FallbackVisualAid(type="callout_card", title="Tumor shrank", subtitle=None, values=[63.0])
    out = fx.widget_with_story({"type": "counter", "data": {"title": "Generic", "to": 10}}, fb)
    assert out["data"]["title"] == "Tumor shrank" and out["data"]["to"] == 63.0


def test_catalog_is_compact_grouped_and_complete():
    idx = schemas.load_library_index(LIB)
    cat = director.build_catalog(idx, "health", "a virus that fights cancer")
    ids = set()
    for c, v in cat.items():
        if isinstance(v, dict):
            for group in v.values():
                ids.update(group)
        else:
            ids.update(x["id"] for x in v)
    assert ids == {a.id for a in idx.assets}
    assert {"health", "general"} <= director.niche_tags("health", "virus")


def test_auto_repair_only_uses_safe_motions(tmp_path):
    lib = _lib_copy(tmp_path)
    pack.build(lib, only=["04_motions"])
    idx = schemas.load_library_index(lib)
    motions, _ = audit._pools(idx)
    assert motions and set(motions) <= set(audit.SAFE_REPAIR_MOTIONS)


def test_previews_thumbs_and_animated_webp(tmp_path):
    from PIL import Image
    lib = _lib_copy(tmp_path)
    pack.build(lib, only=["02_poses", "04_motions", "07_widgets", "08_overlays", "09_transitions", "13_bgm"])
    ids = ["wave_right", "hands_on_hips", "pie_budget", "thought_money", "iris_star", "lofi_study_chill", "brain_simple"]
    res = previews.build_all(lib, ids=ids)
    assert not res["failed"] and res["rendered"] == len(ids)
    idx = schemas.load_library_index(lib)
    for aid in ids:
        a = idx.get(aid)
        assert (lib / a.thumb_path).is_file()
        if a.category in previews.ANIMATED:
            im = Image.open(lib / a.preview_path)
            assert getattr(im, "n_frames", 1) > 4
        else:
            assert a.preview_path is None
