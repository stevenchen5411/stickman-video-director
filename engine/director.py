#!/usr/bin/env python3
"""AI Director: shot-grounded viral remix -> analysis_package.json.

* The AI plans scenes using ONLY library ids (it may propose a few new ids; forge.py creates them).
* Code, not the AI, fills `source_shot_ref` from VIDEO.md/shots.json, so every scene points at a real shot.
* Voice casting: one distinct Gemini voice persona per character (code-enforced).
* Prosody: pause presets 80/240/450 ms, pace clamped, emphasis words must occur in the text, SFX must exist.
* Without any usable AI provider the package is a `draft` (transcript beats, needs an AI rewrite).

CLI: python3 engine/director.py VIDEO_ID [--niche N] [--multiplier X] [--channel C] [--offline]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import audit
import common
import forensics
import llm
import schemas

log = common.log
MAX_NEW_IDS = 6
MAX_SHARED_RUN = 7          # words copied verbatim from the source transcript before we object
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
STAGE_RE = re.compile(r"\[[^\]]*\]|\*[^*]+\*")

SYSTEM_PROMPT = (
    "You are the director of faceless stickman explainer videos. You remix a proven viral video's STRUCTURE "
    "into a fresh script in your own words. Reply with one JSON object only."
)


# --------------------------------------------------------------------------- helpers
def clean_id(v: Any) -> Optional[str]:
    if not isinstance(v, str):
        return None
    s = re.sub(r"[^a-z0-9_]+", "_", v.strip().lower()).strip("_")
    return s if ID_RE.match(s) else None


def clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", STAGE_RE.sub("", t or "")).strip()


MAX_SPEECH_SCENES = 6


def clean_say(sp: Any) -> Optional[Dict[str, Any]]:
    """Normalize an LLM-proposed stickman line; None when there is nothing usable."""
    if not isinstance(sp, dict):
        return None
    text = " ".join(clean_text(sp.get("text", "")).split()[:schemas.MAX_SPEECH_WORDS])
    if not re.search(r"[A-Za-z0-9]", text):
        return None
    return {"text": text, "voice_profile_id": None, "expression_id": None,
            "acting_direction": clean_text(sp.get("acting_direction", ""))[:200],
            "placement": "before" if sp.get("placement") == "before" else "after"}


def words_norm(t: str) -> List[str]:
    return re.findall(r"[a-z0-9']+", t.lower())


def longest_shared_run(a: str, b: str) -> int:
    """Longest run of consecutive words shared by a and b (plagiarism guard)."""
    wa, wb = words_norm(a), words_norm(b)
    if not wa or not wb:
        return 0
    best = 0
    prev = [0] * (len(wb) + 1)
    for i in range(1, len(wa) + 1):
        cur = [0] * (len(wb) + 1)
        for j in range(1, len(wb) + 1):
            if wa[i - 1] == wb[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def build_catalog(index: schemas.LibraryIndex) -> Dict[str, List[Dict[str, Any]]]:
    return {c: [{"id": a.id, "tags": a.niche_tags[:4]} for a in index.by_category(c)] for c in schemas.CATEGORIES}


# --------------------------------------------------------------------------- planning
def plan_with_llm(fx: Dict[str, Any], index: schemas.LibraryIndex, niche: str, extra_warning: str = ""
                  ) -> Tuple[Dict[str, Any], str]:
    shots = [{"shot_id": s["shot_id"], "dur": s["duration_sec"], "said": s.get("transcript", "")[:240]}
             for s in fx["shots"]][:60]
    prompt = json.dumps({
        "task": "Remix this viral video's structure into an original 25-45 second vertical stickman video script.",
        "niche": niche,
        "source_title": fx.get("title", ""),
        "source_shots": shots,
        "library_catalog": build_catalog(index),
        "rules": [
            "Use ONLY ids from library_catalog for character_id, theme/caption/bgm and voices. For other asset types you "
            f"may propose at most {MAX_NEW_IDS} NEW snake_case ids in total when nothing fits.",
            "Write 8-14 scenes. Each scene `text` is verbatim spoken narration (<=18 words), in your own words; "
            "never copy 8+ consecutive words from source_shots. No stage directions, brackets or emojis in `text`.",
            "Put acting/delivery instructions ONLY in `acting_direction`.",
            "Give the stickman a personality: on 3-5 scenes (not all) add `speech` = a short line the stickman himself "
            f"says in a speech bubble (<={schemas.MAX_SPEECH_WORDS} words, verbatim, no brackets): a gut reaction, a "
            "question the viewer is thinking, a joke, or a doubt. It must add something the narrator did NOT say. "
            "The narrator keeps telling the story; the stickman reacts to it. placement='before' for a hook question "
            "that sets up the narration, 'after' for a reaction to it. Leave `speech` out of the other scenes.",
            "Every scene needs `shot_id` copied from source_shots (the shot whose pacing/beat it echoes).",
            "Make most scenes move: set motion_id and/or overlay_id/widget_id.",
            "Exactly one scene has climax=true; set dramatic_beat=true on punchline scenes.",
            "emphasis_words[].word must appear in text; trigger_sfx must be an id from 14_sfx.",
            extra_warning,
        ],
        "output_schema": {
            "title_variants": ["3 distinct viral titles"], "cover_scene_index": 0, "cover_text_hook": "<=5 words, caps",
            "render_config": {"theme_id": "", "caption_style_id": "", "bgm_id": ""},
            "scenes": [{
                "shot_id": "", "character_id": "", "pose_id": "", "expression_id": "", "motion_id": "",
                "scene_id": "", "transition_in_id": "", "prop_id": "", "widget_id": "", "overlay_id": "",
                "fallback": {"type": "callout_card|chart_bar", "title": "", "subtitle": ""},
                "text": "", "acting_direction": "", "pace_multiplier": 1.0,
                "speech": {"text": "", "expression_id": "", "placement": "before|after", "acting_direction": ""},
                "emphasis_words": [{"word": "", "stress": "", "trigger_sfx": ""}],
                "dramatic_beat": False, "climax": False}],
        },
    })
    plan, provider = llm.call_json(SYSTEM_PROMPT, prompt)
    if not isinstance(plan.get("scenes"), list) or not plan["scenes"]:
        raise ValueError("plan has no scenes")
    return plan, provider


def heuristic_plan(fx: Dict[str, Any], index: schemas.LibraryIndex, niche: str) -> Dict[str, Any]:
    """Offline fallback: transcript beats + round-robin library assets. Produces a DRAFT only."""
    text = " ".join(t["text"] for t in fx.get("transcript", []))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text)) if s.strip()]
    # auto-captions rarely carry punctuation, so long runs are cut into <=16-word units before packing beats
    units: List[List[str]] = []
    for s in sentences or [text]:
        w = s.split()
        units += [w[i:i + 16] for i in range(0, len(w), 16)]
    beats: List[str] = []
    cur: List[str] = []
    for w in units:
        if cur and len(cur) + len(w) > 18:
            beats.append(" ".join(cur))
            cur = []
        cur += w
    if cur:
        beats.append(" ".join(cur))
    beats = [b for b in beats if b.strip()][:14]
    if not beats:
        raise ValueError("no transcript available: an AI provider is required to write this video")

    def pool(cat: str, tags_first: bool = True) -> List[str]:
        items = index.by_category(cat)
        hit = [a.id for a in items if niche.lower() in " ".join(a.niche_tags).lower()]
        return hit + [a.id for a in items if a.id not in hit] if tags_first else [a.id for a in items]

    motions = [m for m in pool("04_motions") if m not in audit.STATIC_MOTIONS]
    poses, exprs = pool("02_poses"), pool("03_expressions")
    exprs = [e for e in exprs if e != "viseme_default"]
    scenes_pool, overlays = pool("05_scenes"), pool("08_overlays")
    trans = pool("09_transitions")
    char = pool("01_characters")[0]
    plan_scenes = []
    for i, b in enumerate(beats):
        plan_scenes.append({
            "shot_id": None, "character_id": char, "pose_id": poses[i % len(poses)],
            "expression_id": exprs[i % len(exprs)], "motion_id": motions[i % len(motions)] if motions else None,
            "scene_id": scenes_pool[(i // 3) % len(scenes_pool)], "transition_in_id": trans[i % len(trans)] if i else None,
            "overlay_id": overlays[i % len(overlays)] if i % 3 == 2 and overlays else None,
            "text": b, "acting_direction": "Natural, clear and engaged; lift pitch on the key noun.",
            "pace_multiplier": 1.0, "emphasis_words": [], "dramatic_beat": i == len(beats) - 2,
            "climax": i == len(beats) - 2})
    return {"title_variants": [], "render_config": {}, "scenes": plan_scenes}


# --------------------------------------------------------------------------- assembly
def cast_voices(char_ids: List[str], index: schemas.LibraryIndex) -> Dict[str, str]:
    """One distinct voice persona per character (prefers the character's own default)."""
    personas = [a.id for a in index.by_category("12_voices")]
    used: set = set()
    out: Dict[str, str] = {}
    for cid in dict.fromkeys(char_ids):
        want = None
        try:
            asset = index.get(cid, "01_characters")
            if asset:
                data = schemas.load_json(common.library_dir() / asset.file_path)
                want = data.get("default_voice_profile_id")
        except Exception:  # noqa: BLE001
            pass
        if want not in personas or want in used:
            want = next((p for p in personas if p not in used), personas[0] if personas else "")
        used.add(want)
        out[cid] = want
    return out


def finalize_prosody(sc: Dict[str, Any], idx: int, n: int, sfx_ids: set) -> Dict[str, Any]:
    text = sc["text"]
    if idx == 0:
        pause = schemas.PAUSE_FAST_HOOK_MS
    elif sc.get("dramatic_beat") or text.rstrip().endswith("...") or idx == n - 1:
        pause = schemas.PAUSE_DRAMATIC_MS
    else:
        pause = schemas.PAUSE_SENTENCE_MS
    emph = []
    low = text.lower()
    for e in (sc.get("emphasis_words") or [])[:3]:
        w = (e.get("word") or "").strip()
        if not w or w.lower() not in low:
            continue
        sfx = clean_id(e.get("trigger_sfx"))
        emph.append({"word": w, "stress": (e.get("stress") or "emphasis")[:40],
                     "trigger_sfx": sfx if sfx in sfx_ids else None})
    try:
        pace = float(sc.get("pace_multiplier", 1.0))
    except (TypeError, ValueError):
        pace = 1.0
    return {"acting_direction": (sc.get("acting_direction") or "Clear, engaged delivery.")[:400],
            "pace_multiplier": round(min(1.25, max(0.8, pace)), 2), "emphasis_words": emph,
            "post_breath_pause_ms": pause, "bgm_drop_on_climax": bool(sc.get("climax"))}


def assemble_package(plan: Dict[str, Any], fx: Dict[str, Any], index: schemas.LibraryIndex,
                     source: Dict[str, Any]) -> Dict[str, Any]:
    shots = fx["shots"]
    by_id = {s["shot_id"]: s for s in shots}
    ids = {c: {a.id for a in index.by_category(c)} for c in schemas.CATEGORIES}
    pools = {c: sorted(ids[c]) for c in schemas.CATEGORIES}
    new_budget = [MAX_NEW_IDS]

    def pick(cat: str, v: Any, i: int, required: bool = False, allow_new: bool = True) -> Optional[str]:
        cid = clean_id(v)
        if cid and cid in ids[cat]:
            return cid
        if cid and allow_new and not required and new_budget[0] > 0:
            new_budget[0] -= 1
            return cid
        return pools[cat][i % len(pools[cat])] if (required and pools[cat]) else None

    raw_scenes = plan["scenes"][:14]
    n = len(raw_scenes)
    chars = [pick("01_characters", s.get("character_id"), i, required=True, allow_new=False) for i, s in enumerate(raw_scenes)]
    voices = cast_voices([c for c in chars if c], index)
    sfx_ids = ids["14_sfx"]
    scenes: List[Dict[str, Any]] = []
    for i, ps in enumerate(raw_scenes):
        shot = by_id.get(ps.get("shot_id")) or shots[min(len(shots) - 1, int(i * len(shots) / max(1, n)))]
        text = clean_text(ps.get("text", "")) or "..."
        words = text.split()
        fb = ps.get("fallback") or {}
        fb_title = (fb.get("title") or " ".join(words[:4]) or "KEY POINT")[:60]
        fallback = {"type": fb.get("type") if fb.get("type") in ("callout_card", "chart_bar") else "callout_card",
                    "title": fb_title, "subtitle": (fb.get("subtitle") or None)}
        prop = pick("06_props", ps.get("prop_id"), i)
        widget = pick("07_widgets", ps.get("widget_id"), i)
        overlay = pick("08_overlays", ps.get("overlay_id"), i)
        va_type = "library_prop" if prop else "widget" if widget else "overlay_only" if overlay else "callout_card"
        cid = chars[i]
        scenes.append({
            "id": f"scene_{i + 1:02d}",
            "source_shot_ref": {"shot_id": shot["shot_id"], "frame_path": shot["frame_path"],
                                "original_duration_sec": max(0.1, shot["duration_sec"])},
            "character": {"character_id": cid, "pose_id": pick("02_poses", ps.get("pose_id"), i, True),
                          "expression_id": pick("03_expressions", ps.get("expression_id"), i, True),
                          "motion_id": pick("04_motions", ps.get("motion_id"), i)},
            "environment": {"scene_id": pick("05_scenes", ps.get("scene_id"), i, True),
                            "transition_in_id": pick("09_transitions", ps.get("transition_in_id"), i) if i else None},
            "visual_aid": {"type": va_type, "prop_id": prop, "widget_id": widget, "overlay_id": overlay,
                           "fallback_visual_aid": fallback},
            "narration": {"character_id": cid, "voice_profile_id": voices[cid], "text": text,
                          "prosody": finalize_prosody({**ps, "text": text}, i, n, sfx_ids)}})
        say = clean_say(ps.get("speech"))
        if say and sum(1 for x in scenes if x.get("speech")) < MAX_SPEECH_SCENES:
            say["expression_id"] = pick("03_expressions", (ps.get("speech") or {}).get("expression_id"), i, allow_new=False)
            scenes[-1]["speech"] = say
    # exactly one climax scene
    if not any(s["narration"]["prosody"]["bgm_drop_on_climax"] for s in scenes) and n >= 1:
        scenes[max(0, n - 2)]["narration"]["prosody"]["bgm_drop_on_climax"] = True

    rc_in = plan.get("render_config") or {}
    bgm_pool = index.by_category("13_bgm")
    niche_l = source["niche"].lower().replace("_", " ")
    bgm_default = next((a.id for a in bgm_pool if any(t in niche_l for t in a.niche_tags)), bgm_pool[0].id)
    render_config = {
        "aspect_ratio": "9:16",
        "theme_id": rc_in.get("theme_id") if rc_in.get("theme_id") in ids["11_themes"] else pools["11_themes"][0],
        "caption_style_id": rc_in.get("caption_style_id") if rc_in.get("caption_style_id") in ids["10_caption_styles"]
        else ("hormozi_pop_yellow" if "hormozi_pop_yellow" in ids["10_caption_styles"] else pools["10_caption_styles"][0]),
        "bgm_id": rc_in.get("bgm_id") if rc_in.get("bgm_id") in ids["13_bgm"] else bgm_default}

    topic = niche_l.split()[0] if niche_l else "this"
    titles = [t for t in (plan.get("title_variants") or []) if isinstance(t, str) and t.strip()][:3]
    fallbacks = [f"The Truth About {topic.title()} Nobody Tells You", f"Why {topic.title()} Matters More Than You Think",
                 f"Stop Ignoring {topic.title()} — Do This Instead"]
    titles += fallbacks[len(titles):3]

    ci = plan.get("cover_scene_index")
    if not isinstance(ci, int) or not 0 <= ci < n:
        ci = max(range(n), key=lambda k: len(scenes[k]["narration"]["prosody"]["emphasis_words"])) if n else 0
    hook = clean_text(plan.get("cover_text_hook") or "") or " ".join(scenes[ci]["narration"]["text"].split()[:4])
    hook = " ".join(hook.upper().split()[:6])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    pid = f"pkg_{stamp}_{re.sub(r'[^A-Za-z0-9_-]', '', fx['video_id'])[:12]}"
    return {
        "package_id": pid, "status": "draft",
        "source_viral_video": {"video_id": fx["video_id"], "channel": source.get("channel") or fx.get("channel") or "unknown",
                               "outlier_multiplier": float(source.get("outlier_multiplier", 0) or 0),
                               "niche": source["niche"], "video_md_path": fx["video_md_path"]},
        "render_config": render_config,
        "viral_packaging": {"title_variants": titles, "cover_scene_id": scenes[ci]["id"], "cover_text_hook": hook},
        "quality_audit": {"estimated_duration_sec": 0, "avg_beat_sec": 0, "visual_activity_pct": 0,
                          "auto_repaired_scenes": [], "passed": False},
        "scenes": scenes}


# --------------------------------------------------------------------------- orchestration
def direct(video_id: str, source: Optional[Dict[str, Any]] = None, offline: bool = False,
           forge_missing: bool = True, save: bool = True) -> schemas.AnalysisPackage:
    source = dict(source or {})
    source.setdefault("niche", "general")
    fx = forensics.analyze(video_id, source.get("channel", ""), source.get("title", ""))
    index = schemas.load_library_index(common.library_dir())
    transcript_text = " ".join(t["text"] for t in fx.get("transcript", []))

    plan, provider, is_offline = None, "", offline
    if not offline:
        warning = ""
        for attempt in range(2):
            try:
                plan, provider = plan_with_llm(fx, index, source["niche"], warning)
            except Exception as e:  # noqa: BLE001 - no key / rate limit / bad JSON
                # A template script is not a usable video: fail loudly instead of queueing a junk package.
                # (Offline mode, chosen explicitly by the user, still builds the template draft below.)
                log.warning("AI planning unavailable (%s)", str(e)[:160])
                raise RuntimeError(f"AI unavailable: {str(e)[:100]}. Reopen the app to re-sync Claude, or use Offline mode.") from e
            worst = max((longest_shared_run(s.get("text", ""), transcript_text) for s in plan["scenes"]), default=0)
            if worst <= MAX_SHARED_RUN:
                break
            warning = f"PREVIOUS ATTEMPT COPIED {worst} CONSECUTIVE WORDS FROM THE SOURCE. Rewrite completely."
            log.warning("plan copied %d source words; retrying", worst)
    if plan is None:
        plan, is_offline = heuristic_plan(fx, index, source["niche"]), True

    raw = assemble_package(plan, fx, index, source)
    pkg = schemas.AnalysisPackage.model_validate(raw)
    if forge_missing:
        missing = pkg.missing_library_refs(index)
        if missing:
            import forge
            forge.forge_missing(missing, niche=source["niche"])
            index = schemas.load_library_index(common.library_dir())
    result = audit.audit_package(pkg.model_dump(mode="json"), index, fx["shots"])
    if is_offline:
        d = result.model_dump(mode="json")
        d["status"] = "draft"
        result = schemas.AnalysisPackage.model_validate(d)
    if save:
        schemas.save_json(common.queue_dir() / f"{result.package_id}.json", result)
        log.info("queued %s (%s, provider=%s)", result.package_id, result.status, provider or "offline")
    return result


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video_id")
    ap.add_argument("--niche", default="general")
    ap.add_argument("--multiplier", type=float, default=0)
    ap.add_argument("--channel", default="")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args(argv)
    common.ensure_dirs()
    pkg = direct(a.video_id, {"niche": a.niche, "outlier_multiplier": a.multiplier, "channel": a.channel}, offline=a.offline)
    print(f"{pkg.package_id} status={pkg.status} activity={pkg.quality_audit.visual_activity_pct}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
