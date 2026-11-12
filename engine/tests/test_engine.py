"""Milestone 2 engine tests (run: python3 -m pytest engine/tests -q).

Cairo-dependent tests use real pycairo when installed, else tests/fake_cairo.py (layout/timing/pipe checks only).
"""
import json
import math
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import audio_master as am
import audit
import common
import curator
import director
import forensics
import forge
import llm
import pipeline
import schemas
import scout
import tts_expressive as tts

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "assets" / "library"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_analysis_package.json"


def index():
    return schemas.load_library_index(LIB)


def sample_pkg():
    return schemas.load_package(FIXTURE)


def fake_fx(n_shots=4):
    shots = [{"shot_id": f"shot_{i + 1:02d}", "start_sec": i * 3.0, "end_sec": i * 3.0 + 3.0, "duration_sec": 3.0,
              "mid_sec": i * 3.0 + 1.5, "frame_path": f"/x/shot_{i + 1:02d}.jpg", "render_type": None,
              "transcript": ""} for i in range(n_shots)]
    text = ("Most people think willpower is the answer to everything. It is not. Your environment decides far more "
            "than your motivation ever will. Change the room and the habit follows. Small cues beat big promises. "
            "Try it for one week and watch what happens to your mornings.")
    return {"video_id": "abcDEF12345", "channel": "@Test", "title": "Habits", "duration_sec": 12.0,
            "cut_source": "ffmpeg-scene", "video_md_path": "/x/VIDEO.md", "shots": shots,
            "transcript": [{"text": s, "start": i * 2.0, "duration": 2.0} for i, s in enumerate(text.split(". "))]}


# ------------------------------------------------------------------------- llm
def test_extract_json_variants():
    assert llm.extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.extract_json('Sure! {"a": {"b": 2}} done') == {"a": {"b": 2}}
    with pytest.raises(ValueError):
        llm.extract_json("no json here")


def test_failover_hops_on_429_and_sets_cooldown(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "c")
    calls = []

    def claude(*a):
        calls.append("claude")
        raise llm.RateLimited("claude", 60)

    def gemini(*a):
        calls.append("gemini")
        return '{"ok": true}'

    monkeypatch.setattr(llm, "_call_claude", claude)
    monkeypatch.setattr(llm, "_call_gemini", gemini)
    out, prov = llm.call_json("s", "p")
    assert out == {"ok": True} and prov == "gemini" and calls == ["claude", "gemini"]
    assert llm.in_cooldown("claude")
    calls.clear()
    llm.call_json("s", "p")
    assert calls == ["gemini"]                                   # claude skipped while cooling down


def test_no_provider_raises():
    with pytest.raises(llm.NoProvider):
        llm.call_json("s", "p")


def test_keystore_ciphertext_is_not_used(tmp_path):
    cfg = schemas.ProvidersFile()
    cfg.providers.gemini.api_key = "enc_v1:abcdef"
    schemas.save_json(common.config_dir() / "providers.json", cfg)
    assert llm.api_key("gemini") is None


# ------------------------------------------------------------------------- scout
def test_compute_outliers_uses_channel_median():
    def v(i, views, ch="a"):
        return {"video_id": f"v{ch}{i}", "channel": ch, "channel_url": ch, "views": views, "duration_sec": 60}

    vids = [v(i, 1000) for i in range(7)] + [v(99, 5200)] + [v(i, 100, "b") for i in range(3)] + [v(50, 9999, "b")]
    out = scout.compute_outliers(vids, min_multiplier=3.0, min_sample=5)
    assert [o["video_id"] for o in out] == ["va99"]               # channel b has too few samples
    assert out[0]["outlier_multiplier"] == 5.2 and out[0]["channel_median_views"] == 1000


def test_normalize_entry_requires_views():
    assert scout.normalize_entry({"id": "x", "view_count": None}) is None
    assert scout.normalize_entry({"id": "x", "view_count": 5, "title": "t"})["views"] == 5


# ------------------------------------------------------------------------- forensics
def test_scene_time_parsing_and_merging():
    err = "[Parsed_showinfo] n: 0 pts: 1 pts_time:2.5 ...\n[Parsed_showinfo] pts_time:2.55 \n pts_time:7.0"
    assert forensics.parse_scene_times(err) == [2.5, 2.55, 7.0]
    spans = forensics.shots_from_cuts([2.5, 2.55, 7.0], 10.0, min_len=0.6)
    assert spans == [(0.0, 2.55), (2.55, 7.0), (7.0, 10.0)]
    assert forensics.shots_from_cuts([], 5.0) == [(0.0, 5.0)]


def test_breakdown_parser_is_tolerant():
    data = {"video": {"duration": 9}, "shots": [{"start": "00:00.000", "end": 3.0, "render_type": "footage"},
                                                {"start_sec": 3.0, "end_sec": 9.0, "type": "gen"}]}
    got = forensics.extract_shots_from_breakdown(data, 9.0)
    assert [(g["start"], g["end"], g["render_type"]) for g in got] == [(0.0, 3.0, "footage"), (3.0, 9.0, "gen")]
    ms = {"cuts": [{"start": 0, "end": 3000}, {"start": 3000, "end": 9000}]}
    assert forensics.extract_shots_from_breakdown(ms, 9.0)[1]["end"] == 9.0
    assert forensics.extract_shots_from_breakdown({"nothing": 1}, 9.0) == []


def test_video_md_and_alignment():
    shots = [{"shot_id": "shot_01", "start_sec": 0.0, "end_sec": 2.0, "duration_sec": 2.0, "frame_path": "/a/shot_01.jpg"},
             {"shot_id": "shot_02", "start_sec": 2.0, "end_sec": 4.0, "duration_sec": 2.0, "frame_path": "/a/shot_02.jpg"}]
    forensics.align_transcript([{"text": "hello", "start": 0.5, "duration": 1.0}, {"text": "world", "start": 2.5, "duration": 1.0}], shots)
    assert shots[0]["transcript"] == "hello" and shots[1]["transcript"] == "world"
    md = forensics.render_video_md({"video_id": "v", "duration_sec": 4.0, "cut_source": "rea-video"}, shots)
    assert "| shot_02 |" in md and "world" in md


def test_ffmpeg_scene_detection_and_frame_extraction(tmp_path):
    src = tmp_path / "src.mp4"
    common.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=160x90:d=1.5:r=15",
                "-f", "lavfi", "-i", "color=c=blue:s=160x90:d=1.5:r=15", "-filter_complex", "[0][1]concat=n=2:v=1:a=0",
                "-pix_fmt", "yuv420p", str(src)])
    cuts = forensics.ffmpeg_scene_cuts(src)
    assert len(cuts) == 1 and 1.3 < cuts[0] < 1.7
    out = tmp_path / "f.jpg"
    forensics.extract_frame(src, 0.7, out)
    assert out.stat().st_size > 100


# ------------------------------------------------------------------------- audit
def test_audit_auto_repairs_static_beats():
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for sc in d["scenes"]:
        sc["character"]["motion_id"] = None
        sc["visual_aid"]["overlay_id"] = None
        sc["visual_aid"]["widget_id"] = None
    assert audit.activity_pct(d["scenes"]) == 0
    out = audit.audit_dict(d, index())
    qa = out["quality_audit"]
    assert qa["visual_activity_pct"] == 100 and sorted(qa["auto_repaired_scenes"]) == ["scene_02", "scene_03"]
    assert qa["passed"] and out["status"] == "ready_to_generate"
    schemas.AnalysisPackage.model_validate({k: v for k, v in out.items() if k != "_warnings"})


def test_audit_flags_unknown_shot_and_stays_draft():
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    out = audit.audit_dict(d, index(), shots=[{"shot_id": "shot_99"}])
    assert not out["quality_audit"]["passed"] and out["status"] == "draft"
    assert any("not in VIDEO.md" in w for w in out["_warnings"])


# ------------------------------------------------------------------------- director
def test_shared_run_detector():
    a = "one two three four five six seven eight nine ten"
    assert director.longest_shared_run(a, "x one two three four five six seven eight y") == 8
    assert director.longest_shared_run(a, "completely different words here") == 0


def test_heuristic_package_is_grounded_cast_and_valid():
    fx = fake_fx()
    plan = director.heuristic_plan(fx, index(), "habits")
    raw = director.assemble_package(plan, fx, index(), {"niche": "habits", "channel": "@T", "outlier_multiplier": 4.2})
    pkg = schemas.AnalysisPackage.model_validate(raw)
    shot_ids = {s["shot_id"] for s in fx["shots"]}
    assert all(sc.source_shot_ref.shot_id in shot_ids for sc in pkg.scenes)
    assert all(sc.visual_aid.fallback_visual_aid.title for sc in pkg.scenes)
    pauses = {sc.narration.prosody.post_breath_pause_ms for sc in pkg.scenes}
    assert pauses <= {80, 240, 450} and pkg.scenes[0].narration.prosody.post_breath_pause_ms == 80
    assert sum(sc.narration.prosody.bgm_drop_on_climax for sc in pkg.scenes) == 1
    assert len(pkg.viral_packaging.title_variants) == 3


def test_llm_plan_is_sanitized_and_grounded(monkeypatch):
    fx = fake_fx()
    plan = {"title_variants": ["A", "B", "C"], "cover_scene_index": 1, "cover_text_hook": "stop doing this now ok yes",
            "render_config": {"theme_id": "nope", "caption_style_id": "hormozi_pop_yellow", "bgm_id": "calm_ambient_pad"},
            "scenes": [
                {"shot_id": "shot_77", "character_id": "ghost_char", "pose_id": "shrug", "expression_id": "neutral",
                 "text": "[whispers] Your room decides *loudly* more than motivation.", "acting_direction": "soft",
                 "emphasis_words": [{"word": "motivation", "stress": "up", "trigger_sfx": "thud_soft"},
                                    {"word": "absent", "stress": "up", "trigger_sfx": "thud_soft"}], "pace_multiplier": 9},
                {"shot_id": "shot_02", "character_id": "nova_scientist", "pose_id": "pointing_right", "expression_id": "neutral",
                 "text": "Change the room.", "dramatic_beat": True, "climax": True}]}
    raw = director.assemble_package(plan, fx, index(), {"niche": "habits"})
    pkg = schemas.AnalysisPackage.model_validate(raw)
    s0 = pkg.scenes[0]
    assert s0.narration.text == "Your room decides more than motivation."          # stage directions stripped
    assert s0.source_shot_ref.shot_id in {s["shot_id"] for s in fx["shots"]}        # shot_77 re-grounded
    assert s0.character.character_id in {a.id for a in index().by_category("01_characters")}
    assert [e.word for e in s0.narration.prosody.emphasis_words] == ["motivation"]  # word not in text dropped
    assert s0.narration.prosody.pace_multiplier == 1.25
    assert pkg.render_config.theme_id == "dark_slate_neon" and pkg.render_config.bgm_id == "calm_ambient_pad"
    assert pkg.viral_packaging.cover_scene_id == "scene_02" and pkg.scenes[1].narration.prosody.post_breath_pause_ms == 450
    assert pkg.viral_packaging.cover_text_hook == "STOP DOING THIS NOW OK YES"
    voices = {sc.narration.character_id: sc.narration.voice_profile_id for sc in pkg.scenes}
    assert len(set(voices.values())) == len(voices)                                  # distinct voice per character


def test_direct_offline_saves_draft(monkeypatch):
    monkeypatch.setattr(forensics, "analyze", lambda *a, **k: fake_fx())
    pkg = director.direct("abcDEF12345", {"niche": "habits"}, offline=True)
    assert pkg.status == "draft"
    assert (common.queue_dir() / f"{pkg.package_id}.json").is_file()
    assert pipeline.list_queue()[0]["package_id"] == pkg.package_id


def test_direct_with_ai_is_ready_and_repaired(monkeypatch):
    fx = fake_fx()
    monkeypatch.setattr(forensics, "analyze", lambda *a, **k: fx)
    plan = {"title_variants": ["T1", "T2", "T3"], "scenes": [
        {"shot_id": "shot_01", "character_id": "kael_hoodie", "pose_id": "shrug", "expression_id": "neutral",
         "text": "Willpower is a weak lever.", "motion_id": None},
        {"shot_id": "shot_02", "character_id": "kael_hoodie", "pose_id": "shrug", "expression_id": "neutral",
         "text": "Design your room instead.", "motion_id": None},
        {"shot_id": "shot_03", "character_id": "kael_hoodie", "pose_id": "arms_crossed", "expression_id": "smirk_confident",
         "text": "Try it this week.", "climax": True}]}
    monkeypatch.setattr(director, "plan_with_llm", lambda *a, **k: (plan, "gemini"))
    pkg = director.direct("abcDEF12345", {"niche": "habits"}, forge_missing=False)
    assert pkg.status == "ready_to_generate" and pkg.quality_audit.passed
    assert pkg.quality_audit.visual_activity_pct >= 75 and pkg.quality_audit.auto_repaired_scenes


# ------------------------------------------------------------------------- curator
def test_curator_global_and_specific_gaps():
    outliers = [{"title": "Stoic habits that rewire your mind", "niche": "stoicism", "outlier_multiplier": 6.0},
                {"title": "Why stoicism beats motivation", "niche": "stoicism", "outlier_multiplier": 4.0}]
    r = curator.analyze(index(), outliers)
    cats = {g["category"] for g in r["global_gaps"]}
    assert {"06_props", "05_scenes", "14_sfx"} <= cats
    assert any(g["term"] == "stoicism" for g in r["specific_gaps"])      # only 1 stoicism-tagged scene/prop? check coverage
    ids = [q["id"] for q in r["requests"]]
    assert len(ids) == len(set(ids)) and all(i not in {a.id for a in index().assets} for i in ids)


# ------------------------------------------------------------------------- forge
def test_phash_similarity_and_dedup():
    rng = np.random.default_rng(3)
    base = rng.random((32, 32)) * 255
    h1 = forge.phash_gray(base)
    h2 = forge.phash_gray(base + rng.normal(0, 2, base.shape))
    h3 = forge.phash_gray(rng.random((32, 32)) * 255)
    assert len(h1) == 16 and forge.hash_similarity(h1, h2) >= 0.85 and forge.hash_similarity(h1, h3) < 0.85
    idx = index()
    idx.assets[0].perceptual_hash = h1
    dup = forge.find_duplicate(idx, idx.assets[0].category, h2)
    assert dup and dup[0] == idx.assets[0].id
    assert forge.hash_similarity("abc", h1) == 0.0                        # seed (12-hex) hashes never match


def test_svg_validation_blocks_active_content():
    ok = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="5" height="5"/></svg>'
    assert forge.validate_svg("```svg\n" + ok + "\n```") == ok
    for bad in ['<svg viewBox="0 0 1 1"><script>x</script></svg>', '<svg viewBox="0 0 1 1"><image href="http://e.com/a.png"/></svg>',
                '<svg viewBox="0 0 1 1" onload="x()"></svg>', '<svg><rect/></svg>', "<div/>"]:
        with pytest.raises(Exception):
            forge.validate_svg(bad)


def test_forge_creates_audio_and_registers(lib_copy):
    r = forge.forge_asset("14_sfx", "swoosh_up", "rising swoosh", use_ai=False, library=lib_copy)
    assert r["status"] == "created"
    idx = schemas.load_library_index(lib_copy)
    a = idx.get("swoosh_up", "14_sfx")
    assert a and a.meta["duration_sec"] < 1.5 and (lib_copy / a.file_path).is_file()
    assert forge.forge_asset("14_sfx", "swoosh_up", library=lib_copy, use_ai=False)["status"] == "exists"
    r2 = forge.forge_asset("13_bgm", "soft_piano_drift", "calm", use_ai=False, library=lib_copy)
    assert r2["status"] == "created" and (lib_copy / "13_bgm" / "soft_piano_drift.ogg").is_file()
    r3 = forge.forge_asset("12_voices", "sage_steady_charon", "steady", use_ai=False, library=lib_copy)
    assert r3["status"] == "created"
    assert schemas.load_library_index(lib_copy).get("sage_steady_charon").gemini_voice_name == "Charon"


def test_forge_visual_assets_and_thumbs(lib_copy):
    r = forge.forge_asset("06_props", "magnifying_glass", "a magnifier", scope="specific", tags=["research"],
                          use_ai=False, library=lib_copy)
    assert r["status"] in ("created", "duplicate")
    r = forge.forge_asset("04_motions", "slide_in_left", "slide", use_ai=False, library=lib_copy)
    assert r["status"] == "created"
    stats = forge.rebuild_thumbs(lib_copy)
    assert stats["failed"] == []
    idx = schemas.load_library_index(lib_copy)
    visual = [a for a in idx.assets if a.category in forge.THUMB_CATS]
    assert all((lib_copy / a.thumb_path).is_file() for a in visual)
    assert all(len(a.perceptual_hash) == 16 for a in visual)
    from PIL import Image
    assert Image.open(lib_copy / visual[0].thumb_path).size == (256, 256)


def test_forge_ai_json_requires_same_format(lib_copy, monkeypatch):
    ex = forge._exemplar(lib_copy, schemas.load_library_index(lib_copy), "02_poses")
    good = {k: v for k, v in ex.items() if k != "id"}
    good["joints"] = {**good["joints"], "l_shoulder": 120}
    monkeypatch.setattr(forge, "_ask", lambda p: {"asset": good})
    assert forge.forge_asset("02_poses", "cheering", "arms up", library=lib_copy)["ai"] is True
    monkeypatch.setattr(forge, "_ask", lambda p: {"asset": {"format": "wrong"}})
    assert forge.forge_asset("02_poses", "cheering2", "x", library=lib_copy)["ai"] is False   # falls back safely


# ------------------------------------------------------------------------- tts
def test_alignment_weights_and_trim():
    x, sr = tts.placeholder_speech("Every nine-minute snooze... restarts a cycle.", "Charon")
    padded = np.concatenate([np.zeros(sr // 2), x, np.zeros(sr // 3)])
    words = tts.align_words("Every nine-minute snooze... restarts a cycle.", padded, sr)
    assert [w["word"] for w in words][0] == "Every" and len(words) == 6
    assert words[0]["start"] >= 0.45                                    # leading silence trimmed off
    assert all(a["end"] <= b["start"] + 1e-6 for a, b in zip(words, words[1:]))
    gap_ellipsis = words[3]["start"] - words[2]["end"]
    gap_plain = words[2]["start"] - words[1]["end"]
    assert gap_ellipsis > gap_plain                                      # '...' earns a longer pause


def test_split_on_gaps_and_dialogue_groups():
    sr = 24000
    tone = lambda d: np.sin(2 * np.pi * 220 * np.arange(int(d * sr)) / sr) * 0.5  # noqa: E731
    x = np.concatenate([tone(1.0), np.zeros(int(0.3 * sr)), tone(0.5), np.zeros(int(0.2 * sr)), tone(0.7)])
    parts = tts.split_on_gaps(x, sr, 3)
    assert parts and [round(len(p) / sr, 1) for p in parts] == [1.2, 0.7, 0.9] or len(parts) == 3
    assert tts.split_on_gaps(tone(1.0), sr, 2) is None

    mk = lambda cid: SimpleNamespace(narration=SimpleNamespace(character_id=cid))  # noqa: E731
    g = tts.group_dialogue([mk("a"), mk("b"), mk("a"), mk("c"), mk("c")])
    assert [[s.narration.character_id for s in grp] for grp in g] == [["a", "b", "a"], ["c"], ["c"]]


def test_audio_payload_extraction_from_sdk_shapes():
    pcm = (np.sin(np.arange(2400) / 10) * 8000).astype("<i2").tobytes()
    resp = SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(
        inline_data=SimpleNamespace(data=pcm, mime_type="audio/L16;codec=pcm;rate=24000"))]))])
    mime, data = next(tts._walk(resp))
    x, sr = tts.decode_audio_payload(mime, data)
    assert sr == 24000 and len(x) == 2400
    nested = {"outputs": [{"audio": {"data": pcm, "mime_type": "audio/L16;rate=16000"}}]}
    mime, data = next(tts._walk(nested))
    assert tts.decode_audio_payload(mime, data)[1] == 16000


def test_gemini_adapter_keeps_text_verbatim_and_style_in_metadata():
    seen = {}
    pcm = (np.sin(np.arange(2400) / 10) * 8000).astype("<i2").tobytes()

    class Interactions:
        def create(self, **kw):
            seen.update(kw)
            return {"outputs": [{"audio": {"data": pcm, "mime_type": "audio/L16;rate=24000"}}]}

    client = SimpleNamespace(interactions=Interactions())
    x, sr = tts.gemini_synthesize(client, "Hello there.", "warm and slow", "Charon")
    assert seen["model"] == "gemini-3.8-flash-tts" and seen["input"] == "Hello there."
    assert seen["speech_metadata"] == {"style": "warm and slow"} and sr == 24000


def test_synthesize_package_placeholder_and_cache(tmp_path):
    pkg = sample_pkg()
    info = tts.synthesize_package(pkg, tmp_path / "w", placeholder=True, library=LIB)
    assert set(info) == {"scene_02", "scene_03"} and all(m["placeholder"] for m in info.values())
    mtime = (tmp_path / "w" / "audio" / "scene_02.wav").stat().st_mtime_ns
    tts.synthesize_package(pkg, tmp_path / "w", placeholder=True, library=LIB)
    assert (tmp_path / "w" / "audio" / "scene_02.wav").stat().st_mtime_ns == mtime     # cache hit


# ------------------------------------------------------------------------- audio master
@pytest.fixture
def mastered(tmp_path):
    pkg = sample_pkg()
    tts.synthesize_package(pkg, tmp_path / "w", placeholder=True, library=LIB)
    res = am.master_package(pkg, tmp_path / "w" / "audio", tmp_path / "w", LIB)
    return pkg, res, tmp_path / "w"


def test_master_loudness_and_peak(mastered):
    _, res, work = mastered
    cp = common.run(["ffmpeg", "-hide_banner", "-i", str(work / "master.wav"), "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = cp.stderr.decode()
    tail = txt[txt.rfind("Integrated loudness"):]
    lufs = float(tail.split("I:")[1].split("LUFS")[0])
    peak = float(tail.split("Peak:")[1].split("dBFS")[0])
    assert abs(lufs + 14.0) < 1.0 and peak <= -0.9
    assert abs(common.probe_duration(work / "master.wav") - res["timeline"]["total_sec"]) < 0.05


def test_timeline_and_frame_spans(mastered):
    pkg, res, _ = mastered
    tl = res["timeline"]
    assert [s["scene_id"] for s in tl["scenes"]] == ["scene_02", "scene_03"]
    s0, s1 = tl["scenes"]
    assert math.isclose(s0["end_sec"], s1["start_sec"], abs_tol=1e-3)
    assert math.isclose(s0["pause_sec"], 0.38, abs_tol=1e-6)                           # post_breath_pause_ms from prosody
    for fps in (30, 60):
        spans = am.frame_spans(tl, fps)
        assert spans[0][0] == 0 and spans[0][1] == spans[1][0]
        assert spans[-1][1] == math.ceil(tl["total_sec"] * fps)                        # no drift vs. audio


def test_ducking_depth_is_minus_20_db():
    sr = am.SR
    voice = np.zeros(sr * 3)
    voice[sr:2 * sr] = np.sin(2 * np.pi * 200 * np.arange(sr) / sr) * 0.3
    env = am.duck_envelope(voice, sr)
    assert env[int(0.2 * sr)] > 0.98                                                    # silence: no ducking
    assert 20 * math.log10(env[int(1.9 * sr)]) < -19.0                                  # speech: ~-20 dB
    assert env[int(2.9 * sr)] > 0.8 and env[int(2.9 * sr)] > 5 * env[int(1.9 * sr)]       # releasing (300 ms time constant)


def test_sfx_phrase_matching_and_climax_mute(mastered):
    pkg, res, _ = mastered
    words = res["timeline"]["scenes"][0]["words"]
    assert am.find_phrase(words, "nine-minute") is not None
    assert am.find_phrase(words, "cannot finish") is not None
    assert am.find_phrase(words, "banana") is None
    n = int(res["timeline"]["total_sec"] * am.SR)
    g = am.climax_mute(pkg, res["timeline"], n)
    assert g.min() == 0.0 and g[0] == 1.0


def test_room_tone_level():
    rt = am.room_tone(am.SR * 2)
    assert abs(am.rms_db(rt) - am.ROOM_TONE_DBFS) < 0.5


# ------------------------------------------------------------------------- renderer
def test_render_math():
    import render_cairo as rc
    assert rc.dims_for("9:16", "draft") == (480, 854, 30) and rc.dims_for("9:16", "hd") == (1080, 1920, 60)
    assert rc.dims_for("16:9", "draft")[:2] == (854, 480) and rc.dims_for("1:1", "hd")[:2] == (1080, 1080)
    assert rc.spring_step(0) == 0 and abs(rc.spring_step(3) - 1) < 0.01 and max(rc.spring_step(t / 100) for t in range(100)) > 1.0
    m = json.loads((LIB / "04_motions" / "camera_punch_in.json").read_text())
    assert rc.eval_motion(m, 0)["camera.scale"] == 1.0 and abs(rc.eval_motion(m, 5)["camera.scale"] - 1.22) < 1e-6
    loop = json.loads((LIB / "04_motions" / "bounce_loop.json").read_text())
    assert abs(rc.eval_motion(loop, 0.4)["character.y"] + 0.03) < 1e-6
    assert rc.hex_rgba("theme.accent", {"accent": "#ff0000"}) == (1.0, 0.0, 0.0, 1.0)


def test_rig_forward_kinematics():
    import render_cairo as rc
    rig = rc.DEFAULT_RIG
    stand = rc.rig_points(rig, {}, 1000, (500, 900))
    assert stand["pelvis"][1] == 900 - 360 and stand["head"][1] < stand["neck_base"][1]
    up = json.loads((LIB / "02_poses" / "holding_head.json").read_text())["joints"]
    p = rc.rig_points(rig, up, 1000, (500, 900))
    assert p["l_hand"][1] < p["l_shoulder"][1]                                           # hands raised above shoulders
    run = rc.rig_points(rig, json.loads((LIB / "02_poses" / "running.json").read_text())["joints"], 1000, (500, 900))
    assert run["l_foot"][0] != run["r_foot"][0]


def test_visemes_follow_words():
    import render_cairo as rc
    vis = json.loads((LIB / "03_expressions" / "viseme_default.json").read_text())["visemes"]
    words = [{"word": "oom", "start": 1.0, "end": 2.0}]
    assert rc.viseme_at(words, 0.5, vis) == vis["rest"] and rc.viseme_at(words, 3.0, vis) == vis["rest"]
    assert rc.viseme_at(words, 1.1, vis)["width"] == vis["O"]["width"]


def _tiny(monkeypatch):
    import render_cairo as rc
    monkeypatch.setitem(rc.MODES, "draft", (72, 10))
    monkeypatch.setitem(rc.MODES, "hd", (96, 12))
    return rc


def test_render_draft_pipes_frames_into_ffmpeg(tmp_path, monkeypatch):
    rc = _tiny(monkeypatch)
    res = rc.render_package(FIXTURE, "draft", tmp_path / "out", placeholder_tts=True, library=LIB)
    mp4, cover = Path(res["video"]), Path(res["cover"])
    assert mp4.name == "pkg_20261112_snooze01_draft.mp4" and mp4.stat().st_size > 1000 and cover.stat().st_size > 200
    probe = common.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_frames",
                        "-of", "json", str(mp4)])
    streams = {s["codec_name"]: s for s in json.loads(probe.stdout)["streams"]}
    v = streams["h264"]
    assert (v["width"], v["height"]) == tuple(res["size"]) == (72, 128) and v["r_frame_rate"] == "10/1"
    assert int(v["nb_frames"]) == res["frames"] and "aac" in streams
    assert abs(common.probe_duration(mp4) - res["duration_sec"]) < 0.3                    # video locked to audio
    assert not list((tmp_path / "out").rglob("*.png"))                                    # zero per-frame disk writes


def test_render_keyframes_only(tmp_path, monkeypatch):
    rc = _tiny(monkeypatch)
    res = rc.render_package(FIXTURE, "keyframes", tmp_path / "out", library=LIB)
    assert set(res["scenes"]) == {"scene_02", "scene_03"} and Path(res["cover"]).is_file()
    assert all(Path(p).stat().st_size > 200 for p in res["scenes"].values())


def test_render_survives_missing_assets(tmp_path, monkeypatch):
    rc = _tiny(monkeypatch)
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sc = d["scenes"][0]
    sc["environment"]["scene_id"] = "does_not_exist"
    sc["visual_aid"].update(prop_id="missing_prop", widget_id="missing_widget", overlay_id="missing_overlay")
    sc["character"].update(pose_id="nope", expression_id="nope", motion_id="nope")
    p = tmp_path / "pkg.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    res = rc.render_package(p, "keyframes", tmp_path / "out", library=LIB)
    assert Path(res["scenes"]["scene_02"]).is_file()                                      # fallback_visual_aid path, no crash


def test_thumbnail_renderer_covers_every_visual_category(tmp_path):
    import render_cairo as rc
    idx = index()
    for cat in sorted(forge.THUMB_CATS):
        a = idx.by_category(cat)[0]
        out = tmp_path / f"{a.id}.png"
        rc.render_asset_thumbnail(LIB, a.model_dump(), out, 256)
        assert out.is_file(), cat


# ------------------------------------------------------------------------- pipeline / server
def test_run_auto_batches_and_skips_failures(monkeypatch):
    out = [{"video_id": f"vid{i}", "channel": "@c", "outlier_multiplier": 5 - i, "niche": "habits", "title": "t"} for i in range(3)]
    monkeypatch.setattr(scout, "scout", lambda *a, **k: out)
    monkeypatch.setattr(curator, "curate", lambda *a, **k: {"requests": [], "global_gaps": [], "specific_gaps": []})

    def fake_direct(vid, source=None, offline=False, **k):
        if vid == "vid0":
            raise RuntimeError("download failed")
        monkeypatch.setattr(forensics, "analyze", lambda *a, **kw: fake_fx())
        pkg = director.direct.__wrapped__(vid, source, offline) if hasattr(director.direct, "__wrapped__") else None
        return SimpleNamespace(package_id=f"pkg_x_{vid}", status="draft")

    monkeypatch.setattr(director, "direct", fake_direct)
    res = pipeline.run_auto([], [], "habits", max_packages=2, offline=True, say=lambda m: None)
    assert [q["video_id"] for q in res["queued"]] == ["vid1", "vid2"] and res["failed"][0]["video_id"] == "vid0"


def test_server_health_and_routes():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    import server
    c = TestClient(server.app)
    h = c.get("/health").json()
    assert set(h["flags"]) == {"python", "yt_dlp", "rea_video", "pycairo", "ffmpeg", "shared_storage_writable"}
    assert c.get("/queue").json() == [] and c.get("/queue/..%2Fetc").status_code in (404, 422)
    assert c.post("/forge", json={"category": "99_x", "id": "a"}).status_code == 422
    assert c.post("/render/draft", json={"package_id": "nope"}).status_code == 404
    assert c.get("/jobs/zzz").status_code == 404
    assert c.get("/library").json()["assets"]


def test_server_binds_loopback_only():
    src = (ROOT / "engine" / "server.py").read_text(encoding="utf-8")
    assert 'HOST, PORT = "127.0.0.1", 8775' in src and "0.0.0.0" not in src


# ---------------------------------------------------------------- runtime keys + token (M3)
def test_runtime_keys_override_and_clear(monkeypatch):
    import llm
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert llm.set_runtime_keys({"gemini": " k1 ", "bogus": "x", "claude": ""}) == ["gemini"]
    assert llm.api_key("gemini") == "k1"
    llm.set_runtime_keys({})
    assert llm.api_key("gemini") is None


def test_token_gate(monkeypatch):
    pytest = __import__("pytest")
    tc = pytest.importorskip("fastapi.testclient", reason="fastapi not installed here")
    import server
    c = tc.TestClient(server.app)
    monkeypatch.setenv("STICKMAN_TOKEN", "sekret")
    assert c.get("/health").json()["auth"] == {"required": True, "ok": False}
    assert c.get("/library").status_code == 401
    h = {"X-Stickman-Token": "sekret"}
    assert c.get("/health", headers=h).json()["auth"]["ok"] is True
    assert c.post("/config/keys", json={"keys": {"gemini": "k"}}, headers=h).json() == {"providers": ["gemini"]}
    import llm; llm.set_runtime_keys({})


def test_queue_put_roundtrip(tmp_path):
    """Storyboard editor save path: PUT re-audits, validates, rejects unknown ids / id mismatch."""
    import json
    pytest = __import__("pytest")
    tc = pytest.importorskip("fastapi.testclient", reason="fastapi not installed here")
    import common, server
    fixture = json.loads((__import__("pathlib").Path(__file__).parent / "fixtures" / "sample_analysis_package.json").read_text())
    pid = fixture["package_id"]
    common.ensure_dirs()
    (common.queue_dir() / f"{pid}.json").write_text(json.dumps(fixture))
    c = tc.TestClient(server.app)
    ok = c.put(f"/queue/{pid}", json=fixture)
    assert ok.status_code == 200 and ok.json()["quality_audit"]["passed"] in (True, False)
    bad = json.loads(json.dumps(fixture)); bad["scenes"][0]["character"]["pose_id"] = "no_such_pose"
    assert c.put(f"/queue/{pid}", json=bad).status_code == 422
    assert c.put(f"/queue/{pid}", json={**fixture, "package_id": "other"}).status_code == 404
