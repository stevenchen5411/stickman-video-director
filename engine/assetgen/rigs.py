"""Characters, poses, expressions and motions for the asset pack (all JSON, drawn by render_cairo/render_fx)."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from .kit import *  # noqa: F401,F403

# =========================================================================== characters
# (id, name, tags, voice persona id, colors(line, fill, accent), accessories[(type, color, color2)], rig overrides, personality)
_CH = [
    ("dr_amara", "Dr. Amara", "health medical science", "warm_sulafat", ("#f1f5f9", "#0f172a", "#34d399"),
     [("labcoat", "#e2e8f0"), ("stethoscope", "#475569", "#cbd5e1"), ("hair_bun", "#57534e"), ("glasses", "#34d399")], {}, ["calm", "caring", "precise"]),
    ("nurse_noah", "Noah", "health medical", "friendly_achird", ("#f1f5f9", "#0f172a", "#38bdf8"),
     [("scrubs", "#14b8a6"), ("nurse_cap", "#f8fafc", "#ef4444"), ("lanyard", "#3b82f6", "#f8fafc")], {}, ["kind", "steady"]),
    ("surgeon_sam", "Sam", "health medical", "clear_iapetus", ("#f1f5f9", "#0f172a", "#22d3ee"),
     [("scrubs", "#3b82f6"), ("mask", "#7dd3fc", "#1d4ed8"), ("beanie", "#3b82f6", "#60a5fa")], {}, ["focused", "serious"]),
    ("chef_marco", "Marco", "food cooking", "lively_sadachbia", ("#f1f5f9", "#0f172a", "#f97316"),
     [("apron", "#f8fafc", "#f97316"), ("chef_hat", "#f8fafc"), ("mustache", "#57534e"), ("scarf", "#ef4444")], {}, ["passionate", "loud"]),
    ("builder_bo", "Bo", "construction industry", "gravel_algenib", ("#f1f5f9", "#0f172a", "#f59e0b"),
     [("vest_safety", "#f97316", "#fde047"), ("hard_hat", "#facc15", "#f59e0b"), ("toolbelt", "#92400e", "#fbbf24"), ("beard", "#78350f")], {"line_width": 0.014}, ["tough", "practical"]),
    ("astro_nia", "Nia", "space science adventure", "bright_zephyr", ("#f1f5f9", "#0f172a", "#f43f5e"),
     [("jacket", "#e2e8f0"), ("space_helmet", "#cbd5e1"), ("medal", "#fbbf24", "#3b82f6")], {}, ["brave", "curious"]),
    ("trader_tom", "Tom", "finance trading crypto business", "smooth_algieba", ("#f1f5f9", "#0f172a", "#22c55e"),
     [("suit", "#1e3a8a", "#f8fafc"), ("tie", "#22c55e"), ("hair_side_part", "#57534e"), ("glasses_square", "#e2e8f0")], {}, ["sharp", "fast"]),
    ("crypto_kai", "Kai", "crypto web3 tech finance", "casual_zubenelgenubi", ("#f1f5f9", "#0f172a", "#a78bfa"),
     [("hoodie", "#6366f1"), ("sunglasses", "#1e293b"), ("hair_spiky", "#a855f7"), ("necklace", "#fbbf24", "#f59e0b")], {}, ["bold", "hype"]),
    ("ceo_vera", "Vera", "business leader career", "firm_kore", ("#f1f5f9", "#0f172a", "#f472b6"),
     [("suit", "#334155", "#f8fafc"), ("hair_bob", "#57534e"), ("necklace", "#fbbf24", "#f8fafc")], {}, ["confident", "decisive"]),
    ("intern_ivy", "Ivy", "business career education", "youthful_leda", ("#f1f5f9", "#0f172a", "#38bdf8"),
     [("tshirt", "#38bdf8"), ("hair_ponytail", "#b45309"), ("lanyard", "#ef4444", "#f8fafc")], {"head_radius": 0.09}, ["eager", "nervous"]),
    ("coder_dev", "Dev", "tech coding ai", "knowledge_sadaltager", ("#f1f5f9", "#0f172a", "#22d3ee"),
     [("hoodie", "#334155"), ("headphones", "#1e293b", "#22d3ee"), ("glasses", "#22d3ee")], {}, ["nerdy", "dry humor"]),
    ("gamer_zed", "Zed", "gaming entertainment tech", "upbeat_puck", ("#f1f5f9", "#0f172a", "#f43f5e"),
     [("jersey", "#ef4444", "#f8fafc"), ("headset", "#1e293b", "#22c55e"), ("cap", "#1e293b", "#ef4444")], {}, ["competitive", "loud"]),
    ("teacher_tara", "Ms. Tara", "education", "gentle_vindemiatrix", ("#f1f5f9", "#0f172a", "#facc15"),
     [("dress", "#8b5cf6", "#f8fafc"), ("hair_bun", "#78350f"), ("glasses", "#facc15")], {}, ["patient", "clear"]),
    ("professor_oak", "Prof. Oak", "education science history", "mature_gacrux", ("#f1f5f9", "#0f172a", "#d6a76c"),
     [("jacket", "#92400e"), ("bowtie", "#ef4444"), ("beard", "#e2e8f0"), ("glasses_square", "#d6a76c")], {}, ["wise", "slow"]),
    ("student_sky", "Sky", "education kids", "lively_laomedeia", ("#f1f5f9", "#0f172a", "#22c55e"),
     [("tshirt", "#22c55e"), ("backpack", "#ef4444", "#facc15"), ("cap", "#3b82f6", "#facc15")], {"head_radius": 0.1, "torso": 0.22, "thigh": 0.15, "shin": 0.15}, ["playful", "curious"]),
    ("kid_mila", "Mila", "kids family education", "bright_autonoe", ("#f1f5f9", "#0f172a", "#f472b6"),
     [("dress", "#f472b6", "#f8fafc"), ("hair_ponytail", "#57534e"), ("bow", "#ef4444")], {"head_radius": 0.11, "torso": 0.2, "thigh": 0.14, "shin": 0.14, "upper_arm": 0.12, "forearm": 0.11},
     ["sweet", "energetic"]),
    ("grandpa_joe", "Grandpa Joe", "family storytelling history", "mature_gacrux", ("#e2e8f0", "#0f172a", "#94a3b8"),
     [("jacket", "#475569"), ("mustache", "#e2e8f0"), ("fedora", "#64748b", "#1e293b"), ("glasses", "#cbd5e1")], {}, ["warm", "slow"]),
    ("grandma_rose", "Grandma Rose", "family storytelling food", "warm_sulafat", ("#e2e8f0", "#0f172a", "#f472b6"),
     [("dress", "#db2777", "#f8fafc"), ("hair_bun", "#cbd5e1"), ("glasses", "#f472b6"), ("scarf", "#a855f7")], {}, ["loving", "funny"]),
    ("farmer_fern", "Fern", "agriculture nature food", "easy_callirrhoe", ("#f1f5f9", "#0f172a", "#84cc16"),
     [("overalls", "#2563eb", "#facc15"), ("straw_hat", "#fde68a", "#ef4444"), ("hair_long", "#b45309")], {}, ["cheerful", "hardworking"]),
    ("pilot_pax", "Pax", "travel transport", "forward_pulcherrima", ("#f1f5f9", "#0f172a", "#facc15"),
     [("suit", "#1e3a8a", "#f8fafc"), ("tie", "#0f172a"), ("cap", "#1e3a8a", "#facc15"), ("sunglasses", "#334155")], {}, ["cool", "calm"]),
    ("detective_dash", "Dash", "mystery law storytelling", "breathy_enceladus", ("#f1f5f9", "#0f172a", "#d6a76c"),
     [("trench_coat", "#a16207"), ("fedora", "#78350f", "#1e293b"), ("hair_side_part", "#57534e")], {}, ["sly", "observant"]),
    ("lawyer_lex", "Lex", "law business", "even_schedar", ("#f1f5f9", "#0f172a", "#94a3b8"),
     [("suit", "#0f172a", "#f8fafc"), ("tie", "#7f1d1d"), ("hair_side_part", "#78350f")], {}, ["formal", "precise"]),
    ("athlete_ace", "Ace", "fitness sports", "excited_fenrir", ("#f1f5f9", "#0f172a", "#f97316"),
     [("tank", "#f97316"), ("headband", "#f8fafc"), ("medal", "#fbbf24", "#ef4444")], {"line_width": 0.014}, ["driven", "energetic"]),
    ("yogi_luna", "Luna", "mental_health fitness self_improvement", "soft_achernar", ("#f1f5f9", "#0f172a", "#a78bfa"),
     [("tank", "#a78bfa"), ("hair_long", "#57534e"), ("necklace", "#fbbf24", "#34d399")], {}, ["calm", "mindful"]),
    ("musician_rio", "Rio", "music entertainment", "upbeat_laomedeia", ("#f1f5f9", "#0f172a", "#ec4899"),
     [("jacket", "#1e293b"), ("hair_mohawk", "#ec4899"), ("headphones", "#ec4899", "#f8fafc")], {}, ["creative", "wild"]),
    ("artist_ari", "Ari", "art creativity", "breezy_aoede", ("#f1f5f9", "#0f172a", "#f59e0b"),
     [("apron", "#fde68a", "#ef4444"), ("beret", "#ef4444"), ("hair_curly", "#78350f")], {}, ["dreamy", "expressive"]),
    ("hero_max", "Max", "storytelling motivation comedy", "excited_fenrir", ("#f1f5f9", "#0f172a", "#facc15"),
     [("cape", "#ef4444"), ("tshirt", "#2563eb"), ("belt", "#facc15", "#ef4444"), ("hair_spiky", "#57534e")], {"line_width": 0.014}, ["heroic", "goofy"]),
    ("wizard_wren", "Wren", "magic storytelling mystery", "gravel_algenib", ("#e2e8f0", "#0f172a", "#a855f7"),
     [("robe", "#4c1d95"), ("wizard_hat", "#4c1d95", "#facc15"), ("beard", "#f8fafc")], {}, ["mysterious", "wise"]),
    ("king_leo", "King Leo", "history leader storytelling", "mature_gacrux", ("#f1f5f9", "#0f172a", "#fbbf24"),
     [("cape", "#7f1d1d"), ("robe", "#b91c1c"), ("crown", "#fbbf24", "#ef4444"), ("beard", "#78350f")], {}, ["proud", "dramatic"]),
    ("explorer_indy", "Indy", "adventure history travel", "forward_orus", ("#f1f5f9", "#0f172a", "#d6a76c"),
     [("jacket", "#a16207"), ("cowboy_hat", "#78350f", "#1e293b"), ("backpack", "#65a30d", "#d6a76c")], {}, ["daring", "witty"]),
    ("robot_r2", "Bolt", "ai tech comedy", "clear_erinome", ("#cbd5e1", "#1e293b", "#22d3ee"),
     [("headset", "#94a3b8", "#22d3ee"), ("belt", "#475569", "#22d3ee")], {"line_width": 0.016, "head_radius": 0.095}, ["logical", "deadpan"]),
    ("reporter_rae", "Rae", "media communication storytelling", "informative_rasalgethi", ("#f1f5f9", "#0f172a", "#ef4444"),
     [("jacket", "#ef4444"), ("hair_bob", "#78350f"), ("lanyard", "#1e293b", "#f8fafc")], {}, ["curious", "fast"]),
    ("santa_nick", "Nick", "holiday celebration", "warm_sulafat", ("#f1f5f9", "#0f172a", "#ef4444"),
     [("jacket", "#dc2626"), ("belt", "#1e293b", "#facc15"), ("santa_hat", "#dc2626", "#f8fafc"), ("beard", "#f8fafc")], {"line_width": 0.014}, ["jolly"]),
    ("ghost_gus", "Gus", "spooky comedy", "breathy_enceladus", ("#e2e8f0", "#1e293b", "#a78bfa"),
     [("halo", "#facc15"), ("scarf", "#a78bfa")], {}, ["shy", "spooky"]),
    ("devil_dex", "Dex", "comedy psychology storytelling", "casual_zubenelgenubi", ("#f1f5f9", "#0f172a", "#ef4444"),
     [("horns", "#ef4444", "#7f1d1d"), ("cape", "#7f1d1d"), ("goatee", "#57534e")], {}, ["mischievous", "tempting"]),
    ("angel_ana", "Ana", "comedy psychology storytelling", "soft_achernar", ("#f1f5f9", "#0f172a", "#facc15"),
     [("halo", "#facc15"), ("robe", "#f8fafc"), ("hair_long", "#fde68a")], {}, ["kind", "honest"]),
    ("pirate_pete", "Pete", "adventure history comedy", "gravel_algenib", ("#f1f5f9", "#0f172a", "#facc15"),
     [("jacket", "#7f1d1d"), ("eyepatch", "#0f172a"), ("bandana", "#ef4444"), ("beard", "#57534e"), ("sash", "#facc15")], {}, ["loud", "greedy"]),
    ("grad_gia", "Gia", "education career celebration", "bright_autonoe", ("#f1f5f9", "#0f172a", "#facc15"),
     [("robe", "#0f172a"), ("grad_cap", "#0f172a", "#facc15"), ("hair_long", "#78350f")], {}, ["proud", "hopeful"]),
    ("party_pip", "Pip", "celebration comedy kids", "upbeat_puck", ("#f1f5f9", "#0f172a", "#ec4899"),
     [("tshirt", "#ec4899"), ("party_hat", "#22d3ee", "#facc15"), ("bowtie", "#facc15")], {"head_radius": 0.095}, ["silly", "happy"]),
    ("office_otto", "Otto", "business productivity office", "even_schedar", ("#f1f5f9", "#0f172a", "#38bdf8"),
     [("tshirt", "#f8fafc"), ("tie", "#2563eb"), ("lanyard", "#2563eb", "#f8fafc"), ("glasses_square", "#38bdf8")], {}, ["tired", "relatable"]),
    ("monk_tenzin", "Tenzin", "stoicism mental_health self_improvement", "gentle_vindemiatrix", ("#f1f5f9", "#0f172a", "#f59e0b"),
     [("robe", "#ea580c"), ("sash", "#f59e0b")], {}, ["serene", "wise"]),
]


def characters() -> List[Dict[str, Any]]:
    out = []
    for cid, name, tags, voice, (lc, fc, ac), accs, rig, pers in _CH:
        rig_full = {"head_radius": 0.085, "neck": 0.03, "torso": 0.26, "upper_arm": 0.14, "forearm": 0.13, "thigh": 0.18,
                    "shin": 0.18, "line_width": 0.012, "hand_radius": 0.016, **rig}
        accessories = []
        for a in accs:
            if a[0] == "bandana":
                accessories.append({"type": "headband", "color": a[1]})
                continue
            d = {"type": a[0], "color": a[1]}
            if len(a) > 2:
                d["color2"] = a[2]
            accessories.append(d)
        out.append({"id": cid, "tags": tags.split(), "scope": "specific" if tags.split()[0] not in ("comedy", "storytelling") else "global",
                    "json": {"id": cid, "format": "stickman_rig/v1", "units": "fraction_of_height", "rig": rig_full, "name": name,
                             "personality_tags": pers, "default_voice_profile_id": voice,
                             "colors": {"line": lc, "fill": fc, "accent": ac}, "accessories": accessories}})
    return out


# =========================================================================== poses
J = Dict[str, float]


def _pose(torso=0, neck=0, l=(8, 5), r=(-8, -5), lh=(4, 0), rh=(-4, 0)) -> J:
    return {"torso_lean": torso, "neck": neck, "l_shoulder": l[0], "l_elbow": l[1], "r_shoulder": r[0], "r_elbow": r[1],
            "l_hip": lh[0], "l_knee": lh[1], "r_hip": rh[0], "r_knee": rh[1]}


def mirror(j: J) -> J:
    return {"torso_lean": -j["torso_lean"], "neck": -j["neck"], "l_shoulder": -j["r_shoulder"], "l_elbow": -j["r_elbow"],
            "r_shoulder": -j["l_shoulder"], "r_elbow": -j["l_elbow"], "l_hip": -j["r_hip"], "l_knee": j["r_knee"],
            "r_hip": -j["l_hip"], "r_knee": j["l_knee"]}


UPPER, FORE = 0.14, 0.13  # default rig arm lengths (fractions of U)


def _ang(dx: float, dy: float) -> float:
    """Rig angle convention: 0 = straight down, +90 = screen-left, -90 = screen-right."""
    return math.degrees(math.atan2(-dx, dy))


def ik(side: str, tx: float, ty: float) -> Tuple[float, float]:
    """(shoulder, elbow) so the hand reaches (tx, ty) relative to the shoulder (x right, y down, units of U)."""
    d = max(abs(UPPER - FORE) + 1e-3, min(UPPER + FORE - 1e-3, math.hypot(tx, ty)))
    base = math.atan2(ty, tx)
    off = math.acos((UPPER ** 2 + d ** 2 - FORE ** 2) / (2 * UPPER * d))
    best = None
    for sgn in (1, -1):
        a = base + sgn * off
        ex, ey = UPPER * math.cos(a), UPPER * math.sin(a)
        score = ex if side == "r" else -ex          # keep the elbow out to the character's side
        if best is None or score > best[0]:
            best = (score, ex, ey)
    _, ex, ey = best
    sh = _ang(ex, ey)
    fa = _ang(tx - ex, ty - ey)
    el = (fa - sh + 180) % 360 - 180
    return round(sh, 1), round(el, 1)


def _P(torso=0, neck=0, l=(8, 5), r=(-8, -5), lh=(4, 0), rh=(-4, 0)) -> J:
    """Like _pose, but an arm given as ("ik", x, y) is solved so the hand lands on that point."""
    if l and l[0] == "ik":
        l = ik("l", l[1], l[2])
    if r and r[0] == "ik":
        r = ik("r", r[1], r[2])
    return _pose(torso, neck, l, r, lh, rh)


# landmarks relative to the shoulder point (x right, y down, units of U)
FACE, CHIN, MOUTH, BROW_R, TOP_R, EAR_R, HIP_R, HIP_L, CHEST = ((0.02, -0.14), (0.0, -0.05), (0.01, -0.09), (0.06, -0.19),
                                                                 (0.05, -0.23), (0.095, -0.13), (0.07, 0.22), (-0.07, 0.22), (0.0, 0.07))

# (id, tags, joints, airborne, mirror_id or "")
# Leg rule: knee bend is signed. For a profile facing screen-right, use l_knee < 0 and r_knee > 0 (both bend backwards).
_POSES: List[Tuple[str, str, J, bool, str]] = [
    ("stand_relaxed", "general", _P(0, 0, (10, 6), (-10, -6), (5, 0), (-5, 0)), False, ""),
    ("stand_attention", "general", _P(0, 0, (3, 0), (-3, 0), (2, 0), (-2, 0)), False, ""),
    ("hands_on_hips", "general confident", _P(0, 0, ("ik", *HIP_L), ("ik", *HIP_R), (8, 0), (-8, 0)), False, ""),
    ("hands_behind_back", "general calm", _P(0, 0, (-14, 30), (14, -30), (4, 0), (-4, 0)), False, ""),
    ("arms_open_welcome", "general presenting", _P(0, 0, (70, 20), (-70, -20), (8, 0), (-8, 0)), False, ""),
    ("arms_wide_wow", "general excited", _P(0, 0, (110, 10), (-110, -10), (10, 0), (-10, 0)), False, ""),
    ("arms_up_victory", "general winner celebration", _P(0, 0, (150, 10), (-150, -10), (8, 0), (-8, 0)), False, ""),
    ("arms_straight_up", "general celebration", _P(0, 0, (172, 0), (-172, 0), (4, 0), (-4, 0)), False, ""),
    ("surrender_hands_up", "general scared", _P(0, 0, (110, 70), (-110, -70), (6, 0), (-6, 0)), False, ""),
    ("cheer_bent_arms", "general excited celebration", _P(0, 0, (120, 60), (-120, -60), (8, 0), (-8, 0)), False, ""),
    ("flex_both", "fitness confident", _P(0, 0, (95, 100), (-95, -100), (10, 0), (-10, 0)), False, ""),
    ("t_pose", "general comedy", _P(0, 0, (90, 0), (-90, 0), (4, 0), (-4, 0)), False, ""),
    ("shrug_big", "general confused", _P(0, 0, (60, 85), (-60, -85), (5, 0), (-5, 0)), False, ""),
    ("facepalm", "general frustrated", _P(0, 8, (14, 5), ("ik", *FACE), (5, 0), (-5, 0)), False, "facepalm_left"),
    ("hand_on_chin", "thinking", _P(0, 4, ("ik", 0.02, 0.1), ("ik", *CHIN), (5, 0), (-5, 0)), False, "hand_on_chin_left"),
    ("scratch_head", "thinking confused", _P(0, -6, (12, 4), ("ik", *TOP_R), (5, 0), (-5, 0)), False, "scratch_head_left"),
    ("finger_on_temple", "thinking smart", _P(0, 3, (10, 4), ("ik", 0.08, -0.16), (5, 0), (-5, 0)), False, "finger_on_temple_left"),
    ("both_hands_head", "general shocked stress", _P(0, 0, ("ik", -0.09, -0.15), ("ik", 0.09, -0.15), (6, 0), (-6, 0)), False, ""),
    ("point_up_right", "presenting", _P(-3, 6, (12, 5), (-140, -5), (5, 0), (-5, 0)), False, "point_up_left"),
    ("point_right_far", "presenting", _P(-6, 4, (14, 6), (-92, -4), (8, 0), (-6, 0)), False, "point_left_far"),
    ("point_down_right", "presenting", _P(0, 8, (12, 5), (-40, 0), (5, 0), (-5, 0)), False, "point_down_left"),
    ("present_palm_right", "presenting business", _P(-3, 5, (14, 6), (-70, 30), (5, 0), (-5, 0)), False, "present_palm_left"),
    ("wave_hello_right", "general greeting", _P(0, 4, (10, 5), (-130, -40), (5, 0), (-5, 0)), False, "wave_hello_left"),
    ("raise_hand_question", "education", _P(0, -3, (10, 5), (-170, -6), (5, 0), (-5, 0)), False, "raise_hand_left"),
    ("fist_pump_right", "winner excited", _P(0, 0, (14, 5), (-120, -100), (6, 0), (-6, 0)), False, "fist_pump_left"),
    ("thumbs_up_right", "general approval", _P(0, 3, (12, 5), (-45, -105), (5, 0), (-5, 0)), False, "thumbs_up_left"),
    ("stop_hand_right", "general warning", _P(0, 0, (12, 5), (-85, 80), (6, 0), (-6, 0)), False, "stop_hand_left"),
    ("salute_right", "general respect", _P(0, 0, (8, 4), ("ik", *BROW_R), (4, 0), (-4, 0)), False, "salute_left"),
    ("flex_one_arm", "fitness confident", _P(0, 0, (12, 5), (-95, -100), (8, 0), (-8, 0)), False, "flex_one_arm_left"),
    ("phone_look", "tech social_media", _P(0, 14, (12, 5), ("ik", 0.03, -0.01), (5, 0), (-5, 0)), False, "phone_look_left"),
    ("drink_sip", "food", _P(0, -8, (12, 5), ("ik", *MOUTH), (5, 0), (-5, 0)), False, "drink_sip_left"),
    ("hold_sign_up", "presenting marketing", _P(0, 0, ("ik", -0.07, -0.25), ("ik", 0.07, -0.25), (6, 0), (-6, 0)), False, ""),
    ("carry_box", "logistics work", _P(0, 0, ("ik", -0.04, 0.12), ("ik", 0.04, 0.12), (8, 0), (-8, 0)), False, ""),
    ("typing_keyboard", "tech office work", _P(0, 12, ("ik", -0.05, 0.16), ("ik", 0.05, 0.16), (6, 0), (-6, 0)), False, ""),
    ("reading_book", "education", _P(0, 14, ("ik", -0.03, 0.04), ("ik", 0.03, 0.04), (5, 0), (-5, 0)), False, ""),
    ("hug_self", "mental_health sad", _P(0, 8, ("ik", 0.05, 0.03), ("ik", -0.05, 0.03), (5, 0), (-5, 0)), False, ""),
    ("shy_hands_low", "shy", _P(0, 10, ("ik", -0.01, 0.2), ("ik", 0.01, 0.2), (3, 0), (-3, 0)), False, ""),
    ("praying_hands", "gratitude calm", _P(0, 10, ("ik", -0.012, 0.07), ("ik", 0.012, 0.07), (4, 0), (-4, 0)), False, ""),
    ("binoculars_look", "adventure mystery", _P(0, -6, ("ik", -0.035, -0.14), ("ik", 0.035, -0.14), (6, 0), (-6, 0)), False, ""),
    ("hand_to_ear_listen", "communication", _P(-4, -8, (12, 5), ("ik", *EAR_R), (5, 0), (-5, 0)), False, "hand_to_ear_left"),
    ("counting_fingers", "education explaining", _P(0, 4, ("ik", -0.03, 0.06), ("ik", 0.05, -0.02), (6, 0), (-6, 0)), False, ""),
    ("explain_open_hands", "presenting explaining", _P(0, 4, (45, -60), (-45, 60), (6, 0), (-6, 0)), False, ""),
    ("slump_sad", "sad tired", _P(4, 14, (4, 0), (-4, 0), (3, 0), (-3, 0)), False, "slump_sad_left"),
    ("tired_lean", "tired", _P(10, 16, (2, 0), (-6, 0), (8, 6), (-2, 0)), False, "tired_lean_left"),
    ("angry_fists", "angry", _P(0, -4, (25, 60), (-25, -60), (10, 0), (-10, 0)), False, ""),
    ("scared_cower", "scared", _P(-8, 10, ("ik", -0.06, -0.12), ("ik", 0.07, -0.08), (20, 30), (-14, 20)), False, "scared_cower_left"),
    ("lean_casual_right", "general cool", _P(8, -6, (12, 6), ("ik", *HIP_R), (2, 0), (-14, 0)), False, "lean_casual_left"),
    ("confident_stance", "confident leader", _P(0, -6, ("ik", *HIP_L), ("ik", *HIP_R), (16, 0), (-16, 0)), False, ""),
    ("superhero_stance", "comedy confident", _P(0, -8, ("ik", -0.08, 0.2), ("ik", 0.08, 0.2), (22, 0), (-22, 0)), False, ""),
    ("bow_greeting", "general respect", _P(16, 20, (6, 0), (-30, 0), (4, 0), (-4, 0)), False, ""),
    ("walk_a", "general movement", _P(3, 0, (25, -15), (-25, -25), (18, 0), (-20, 5)), False, ""),
    ("walk_b", "general movement", _P(3, 0, (-25, 15), (25, 25), (-20, -5), (18, 30)), False, ""),
    ("walk_left", "general movement", mirror(_P(3, 0, (25, -15), (-25, -25), (18, 0), (-20, 5))), False, ""),
    ("run_a", "fitness movement", _P(10, 0, (45, 70), (-50, -90), (-45, -30), (40, 70)), False, "run_left"),
    ("run_b", "fitness movement", _P(10, 0, (-50, 90), (45, -70), (40, -70), (-45, 30)), False, ""),
    ("sprint_lean", "fitness movement", _P(18, 0, (70, 60), (-70, -100), (-55, -35), (55, 95)), False, "sprint_lean_left"),
    ("jump_star", "celebration excited", _P(0, 0, (140, 5), (-140, -5), (35, 0), (-35, 0)), True, ""),
    ("jump_tuck", "celebration excited", _P(0, 0, (130, 50), (-130, -50), (60, 110), (-60, 110)), True, ""),
    ("jumping_jack_open", "fitness", _P(0, 0, (150, 0), (-150, 0), (28, 0), (-28, 0)), False, ""),
    ("squat_low", "fitness", _P(0, 0, (80, 0), (-80, 0), (70, 78), (-70, 78)), False, ""),
    ("lunge_right", "fitness", _P(0, 0, (12, 5), (-12, -5), (32, 0), (-62, 62)), False, "lunge_left"),
    ("kick_right", "fitness sports", _P(12, 0, (60, 20), (-30, -20), (6, 0), (-95, 10)), False, "kick_left"),
    ("punch_right", "fitness sports", _P(-6, 0, ("ik", -0.02, 0.0), (-90, 0), (14, 0), (-14, 0)), False, "punch_left"),
    ("boxing_guard", "fitness sports", _P(0, 6, ("ik", -0.04, -0.06), ("ik", 0.05, -0.08), (14, 0), (-14, 0)), False, ""),
    ("yoga_tree", "fitness mental_health", _P(0, 0, (170, 15), (-170, -15), (4, 0), (-60, 140)), False, "yoga_tree_left"),
    ("meditate_sit", "mental_health", _P(0, 0, (30, -30), (-30, 30), (85, 160), (-85, 160)), False, ""),
    ("sit_chair", "office general", _P(0, 0, (20, -40), (-20, 40), (85, 85), (-85, 85)), False, ""),
    ("sit_think", "thinking office", _P(0, 8, (20, -40), ("ik", *CHIN), (85, 85), (-85, 85)), False, "sit_think_left"),
    ("dance_disco_up", "music celebration", _P(-6, 0, ("ik", -0.04, 0.2), (-150, 0), (10, 0), (-30, 40)), False, "dance_disco_down"),
    ("dance_arms_wave", "music celebration", _P(6, 0, (110, -60), (-70, -60), (14, 20), (-8, 0)), False, "dance_arms_wave_left"),
    ("guitar_strum", "music", _P(0, 10, ("ik", -0.09, 0.05), ("ik", 0.03, 0.16), (10, 0), (-10, 0)), False, ""),
    ("conductor", "music", _P(0, -6, (120, 40), (-130, -30), (6, 0), (-6, 0)), False, ""),
    ("throw_ball", "sports", _P(-10, 0, (60, 0), (-150, 60), (14, 0), (-20, 20)), False, "throw_ball_left"),
    ("catch_ready", "sports", _P(0, 6, (60, 50), (-60, -50), (20, 30), (-20, 30)), False, ""),
    ("push_heavy", "work effort", _P(18, -4, (-70, 0), (-85, 10), (35, 0), (-15, 30)), False, "push_heavy_left"),
    ("pull_rope", "work effort", _P(-16, 4, (-60, -20), (-75, -10), (25, -40), (-25, 0)), False, "pull_rope_left"),
    ("climb_reach", "goal effort", _P(0, -10, (20, 30), (-165, 0), (6, 0), (-60, 90)), False, "climb_reach_left"),
    ("sweep_floor", "home work", _P(10, 10, (30, -60), (-20, -40), (8, 0), (-8, 0)), False, ""),
    ("stir_pot", "food cooking", _P(0, 14, (20, 4), ("ik", 0.09, 0.12), (6, 0), (-6, 0)), False, "stir_pot_left"),
    ("hammer_up", "construction work", _P(0, 4, (14, 5), (-160, -70), (10, 0), (-10, 0)), False, "hammer_up_left"),
    ("writing_board", "education presenting", _P(-4, 4, (14, 5), (-120, 20), (6, 0), (-6, 0)), False, "writing_board_left"),
    ("magnify_look", "mystery thinking", _P(-8, 12, (14, 5), (-70, -40), (6, 0), (-6, 0)), False, "magnify_look_left"),
    ("hero_fly", "comedy", _P(0, 0, (172, 0), (-20, 10), (10, 0), (-30, 60)), True, ""),
    ("fall_dramatic", "comedy", _P(-30, -10, (150, 30), (-110, -30), (40, 20), (-60, 30)), False, "fall_dramatic_left"),
    ("tiptoe_sneak", "mystery comedy", _P(6, 8, ("ik", -0.03, -0.06), (-30, -90), (20, -40), (-30, 30)), False, "tiptoe_sneak_left"),
    ("dab_move", "comedy celebration", _P(-10, 20, (120, 0), ("ik", -0.02, -0.12), (8, 0), (-8, 0)), False, "dab_move_left"),
    ("victory_v_sign", "winner celebration", _P(0, -4, (12, 5), (-150, -30), (8, 0), (-8, 0)), False, "victory_v_left"),
    ("kneel_one", "general respect", _P(0, 4, (12, 5), (-20, -30), (40, -110), (-80, 85)), False, "kneel_one_left"),
    ("sit_floor_hug_knees", "sad mental_health", _P(0, 14, ("ik", -0.05, 0.2), ("ik", 0.05, 0.2), (150, 165), (-150, 165)), False, ""),
    ("arms_crossed_tight", "confident doubt", _P(0, -3, ("ik", 0.06, 0.08), ("ik", -0.06, 0.06), (8, 0), (-8, 0)), False, ""),
    ("pointing_viewer", "presenting motivation", _P(0, 0, (12, 5), ("ik", 0.0, -0.02), (8, 0), (-8, 0)), False, ""),
]


def poses() -> List[Dict[str, Any]]:
    out = []
    for pid, tags, j, air, mid in _POSES:
        out.append({"id": pid, "tags": tags.split(), "json": {"id": pid, "format": "pose/v1", "angles_unit": "degrees_from_vertical",
                                                             "joints": j, **({"airborne": True} if air else {})}})
        if mid:
            out.append({"id": mid, "tags": tags.split(), "json": {"id": mid, "format": "pose/v1", "angles_unit": "degrees_from_vertical",
                                                                 "joints": mirror(j), **({"airborne": True} if air else {})}})
    return out


# =========================================================================== expressions
def _ex(eyes=None, brows=None, mouth="flat", extras=None, blink=True):
    e = {"open": 0.85, "pupil_scale": 1.0, "look": [0, 0], **(eyes or {})}
    b = {"l_angle": 0, "r_angle": 0, "raise": 0.0, **(brows or {})}
    d = {"format": "expression/v1", "brows": b, "eyes": e, "mouth_rest": mouth}
    if extras:
        d["extras"] = extras
    if not blink:
        d["blink"] = False
    return d


_EXPR = [
    ("happy", "general positive", _ex({"style": "happy"}, {"raise": 0.05}, "smile")),
    ("joyful", "general positive celebration", _ex({"style": "happy"}, {"raise": 0.1}, "big_smile", ["blush"])),
    ("laughing", "comedy positive", _ex({"style": "closed"}, {"raise": 0.12}, "laugh", ["tears"])),
    ("grinning", "positive comedy", _ex({"open": 0.9}, {"raise": 0.05}, "grin")),
    ("smile_soft", "general calm", _ex({"open": 0.7}, {}, "smile")),
    ("excited", "positive celebration", _ex({"style": "wide", "pupil_scale": 1.1}, {"raise": 0.12}, "big_smile", ["sparkle"])),
    ("in_love", "love relationships", _ex({"style": "heart"}, {"raise": 0.08}, "smile", ["blush"])),
    ("star_struck", "celebration winner", _ex({"style": "star"}, {"raise": 0.12}, "big_smile")),
    ("proud", "confident winner", _ex({"style": "happy"}, {"l_angle": -5, "r_angle": 5}, "smirk_right")),
    ("cool_halflid", "confident cool", _ex({"style": "sleepy", "open": 0.6}, {"l_angle": -6, "r_angle": 6}, "smirk_left")),
    ("wink_smile", "comedy confident", _ex({"style": "wink_r"}, {"raise": 0.05}, "smile")),
    ("playful_tongue", "comedy kids", _ex({"style": "wink_l"}, {"raise": 0.05}, "tongue_out")),
    ("shy_blush", "shy relationships", _ex({"open": 0.75, "look": [0.4, 0.6]}, {"l_angle": 10, "r_angle": -10}, "line_small", ["blush"])),
    ("embarrassed", "shy comedy", _ex({"open": 0.8, "look": [-0.5, 0.3]}, {"l_angle": 12, "r_angle": -12}, "wobble", ["blush", "sweat"])),
    ("nervous", "stress anxiety", _ex({"open": 0.95, "pupil_scale": 0.7}, {"l_angle": 14, "r_angle": -14, "raise": 0.08}, "wobble", ["sweat"])),
    ("anxious", "mental_health stress", _ex({"open": 0.9, "pupil_scale": 0.55, "look": [0.5, 0]}, {"l_angle": 18, "r_angle": -18, "raise": 0.1}, "zigzag")),
    ("scared", "scared spooky", _ex({"style": "wide", "pupil_scale": 0.45}, {"l_angle": 20, "r_angle": -20, "raise": 0.15}, "sad_open", ["sweat"])),
    ("terrified", "scared spooky", _ex({"style": "wide", "pupil_scale": 0.35}, {"l_angle": 22, "r_angle": -22, "raise": 0.2}, "scream", ["sweat", "shadow"])),
    ("surprised", "general surprise", _ex({"style": "wide", "pupil_scale": 0.8}, {"raise": 0.18}, "o")),
    ("amazed", "positive surprise", _ex({"style": "wide", "pupil_scale": 1.2}, {"raise": 0.2}, "o", ["sparkle"])),
    ("mind_blown", "surprise comedy", _ex({"style": "spiral"}, {"raise": 0.22}, "scream", ["sparkle"])),
    ("confused", "thinking confused", _ex({"open": 0.85, "look": [0.4, -0.3]}, {"l_angle": -12, "r_angle": -8, "raise": 0.06}, "zigzag")),
    ("skeptical", "thinking doubt", _ex({"open": 0.6, "look": [0.5, 0]}, {"l_angle": -14, "r_angle": 2, "raise": 0.0}, "smirk_left")),
    ("suspicious", "mystery doubt", _ex({"style": "sleepy", "open": 0.55, "look": [0.8, 0]}, {"l_angle": -10, "r_angle": 10}, "flat")),
    ("thinking_up", "thinking", _ex({"open": 0.85, "look": [0.5, -0.8]}, {"l_angle": -6, "r_angle": 0, "raise": 0.05}, "line_small")),
    ("curious", "thinking curious", _ex({"open": 0.95, "pupil_scale": 1.1}, {"l_angle": -10, "raise": 0.12}, "o")),
    ("bored", "tired", _ex({"style": "sleepy", "open": 0.5, "look": [0.4, 0.2]}, {}, "flat")),
    ("sleepy", "sleep tired", _ex({"style": "closed"}, {"raise": -0.02}, "o", ["shadow"], blink=False)),
    ("exhausted", "tired mental_health", _ex({"style": "sleepy", "open": 0.4}, {"l_angle": 12, "r_angle": -12}, "frown", ["sweat"])),
    ("sad", "sad mental_health", _ex({"open": 0.8, "look": [0, 0.5]}, {"l_angle": 18, "r_angle": -18, "raise": 0.05}, "frown")),
    ("crying", "sad", _ex({"style": "closed"}, {"l_angle": 20, "r_angle": -20, "raise": 0.08}, "sad_open", ["tears"], blink=False)),
    ("disappointed", "sad", _ex({"open": 0.6, "look": [0, 0.7]}, {"l_angle": 10, "r_angle": -10}, "frown")),
    ("lonely_gloom", "sad mental_health", _ex({"open": 0.6, "look": [-0.3, 0.6]}, {"l_angle": 16, "r_angle": -16}, "frown", ["shadow"])),
    ("furious", "angry", _ex({"open": 0.75, "pupil_scale": 0.6}, {"l_angle": -24, "r_angle": 24, "thick": True}, "grit", ["anger"])),
    ("annoyed", "angry frustrated", _ex({"style": "sleepy", "open": 0.55, "look": [0.6, 0]}, {"l_angle": -12, "r_angle": 12}, "flat", ["anger"])),
    ("disgusted", "negative", _ex({"open": 0.5, "look": [0.6, 0.2]}, {"l_angle": -16, "r_angle": 8}, "zigzag")),
    ("dizzy", "comedy confused", _ex({"style": "spiral"}, {"l_angle": 10, "r_angle": -10}, "wobble", blink=False)),
    ("knocked_out", "comedy", _ex({"style": "x"}, {}, "tongue_out", blink=False)),
    ("determined", "motivation confident", _ex({"open": 0.85, "pupil_scale": 0.9}, {"l_angle": -16, "r_angle": 16, "thick": True}, "grit")),
    ("focused", "productivity thinking", _ex({"open": 0.7, "pupil_scale": 0.7}, {"l_angle": -10, "r_angle": 10}, "line_small")),
    ("evil_grin", "comedy mystery", _ex({"open": 0.65, "pupil_scale": 0.6, "look": [0.3, 0]}, {"l_angle": -22, "r_angle": 22}, "grin", ["shadow"])),
    ("smug", "confident comedy", _ex({"style": "sleepy", "open": 0.55}, {"l_angle": -4, "r_angle": 12}, "smirk_left")),
    ("relieved", "calm positive", _ex({"style": "closed"}, {"l_angle": 10, "r_angle": -10}, "smile", ["sweat"], blink=False)),
    ("grateful", "positive calm", _ex({"style": "happy"}, {"l_angle": 8, "r_angle": -8}, "smile", ["blush"])),
    ("hopeful", "motivation positive", _ex({"open": 0.95, "look": [0.2, -0.6]}, {"l_angle": 8, "r_angle": -8, "raise": 0.08}, "smile")),
    ("whistling", "comedy calm", _ex({"open": 0.8, "look": [0.7, -0.4]}, {"raise": 0.1}, "kiss")),
    ("singing", "music positive", _ex({"style": "closed"}, {"raise": 0.12}, "o", blink=False)),
    ("sneaky", "mystery comedy", _ex({"open": 0.6, "look": [0.9, 0.1]}, {"l_angle": -10, "r_angle": 10}, "smirk_right")),
    ("cringe", "comedy negative", _ex({"style": "wink_l"}, {"l_angle": 14, "r_angle": -14}, "grit", ["sweat"])),
    ("hungry", "food comedy", _ex({"open": 0.95, "pupil_scale": 1.2, "look": [0.4, -0.5]}, {"raise": 0.1}, "tongue_out")),
    ("crazy_grin", "comedy", _ex({"style": "spiral"}, {"l_angle": -15, "r_angle": 5}, "grin")),
    ("sick_nauseous", "health negative", _ex({"style": "sleepy", "open": 0.45}, {"l_angle": 14, "r_angle": -14}, "zigzag", ["sweat", "shadow"])),
    ("calm_neutral", "general calm", _ex({"open": 0.75}, {}, "line_small")),
    ("serious", "general business", _ex({"open": 0.75, "pupil_scale": 0.85}, {"l_angle": -6, "r_angle": 6}, "flat")),
    ("talking_open", "general", _ex({"open": 0.85}, {"raise": 0.05}, "open_small")),
    ("teeth_smile", "positive", _ex({"open": 0.85}, {"raise": 0.05}, "teeth_smile")),
    ("kissy", "love comedy", _ex({"style": "closed"}, {"raise": 0.08}, "kiss", ["blush"], blink=False)),
    ("freckled_cheer", "kids positive", _ex({"style": "happy"}, {"raise": 0.1}, "big_smile", ["freckles"])),
    ("worried_side", "stress", _ex({"open": 0.85, "pupil_scale": 0.7, "look": [-0.7, 0]}, {"l_angle": 16, "r_angle": -16, "raise": 0.06}, "wobble")),
    ("dead_inside", "comedy tired", _ex({"style": "dot", "open": 0.8}, {}, "flat", ["shadow"])),
]


def expressions() -> List[Dict[str, Any]]:
    return [{"id": eid, "tags": tags.split(), "json": {"id": eid, **d}} for eid, tags, d in _EXPR]


# =========================================================================== motions
def _m(kind: str, dur: float, loop: bool, tracks: Dict[str, List[List[Any]]], spring=None) -> Dict[str, Any]:
    d = {"format": "motion/v1", "kind": kind, "duration_sec": dur, "loop": loop,
         "tracks": [{"target": k, "keys": v} for k, v in tracks.items()]}
    if spring:
        d["spring"] = spring
    return d


def _osc(n: int, dur: float, amp: float, base: float = 0.0, ease_name: str = "sine", phase: int = 0) -> List[List[Any]]:
    """Keyframes alternating +amp/-amp n times over dur, starting/ending at base (seamless loop)."""
    keys: List[List[Any]] = [[0.0, base, "linear"]]
    steps = n * 2
    for i in range(1, steps):
        sgn = 1 if (i + phase) % 2 else -1
        keys.append([round(dur * i / steps, 3), base + sgn * amp, ease_name])
    keys.append([dur, base, ease_name])
    return keys


def _seq(points: List[Tuple[float, float]], ease_name: str = "ease_in_out") -> List[List[Any]]:
    return [[t, v, "linear" if i == 0 else ease_name] for i, (t, v) in enumerate(points)]


def motions() -> List[Dict[str, Any]]:
    M: List[Tuple[str, str, Dict[str, Any]]] = []
    add = lambda mid, tags, d: M.append((mid, tags, d))  # noqa: E731
    # ---- camera
    for name, s, dur, e in (("cam_punch_small", 1.12, 0.3, "expo_out"), ("cam_punch_big", 1.35, 0.35, "expo_out"), ("cam_punch_slow", 1.18, 0.9, "ease_out")):
        add(name, "camera emphasis", _m("camera", dur, False, {"camera.scale": [[0, 1.0, "linear"], [dur, s, e]]}))
    add("cam_zoom_out_reveal", "camera reveal", _m("camera", 1.2, False, {"camera.scale": [[0, 1.3, "linear"], [1.2, 1.0, "ease_out"]]}))
    add("cam_slow_push", "camera calm", _m("camera", 5.0, False, {"camera.scale": [[0, 1.0, "linear"], [5.0, 1.1, "ease_in_out"]]}))
    add("cam_slow_pull", "camera calm", _m("camera", 5.0, False, {"camera.scale": [[0, 1.12, "linear"], [5.0, 1.0, "ease_in_out"]]}))
    add("cam_pan_left", "camera", _m("camera", 4.0, False, {"camera.x": [[0, 0.05, "linear"], [4.0, -0.05, "ease_in_out"]]}))
    add("cam_pan_up", "camera reveal", _m("camera", 3.0, False, {"camera.y": [[0, -0.06, "linear"], [3.0, 0.03, "ease_in_out"]]}))
    add("cam_pan_down", "camera", _m("camera", 3.0, False, {"camera.y": [[0, 0.05, "linear"], [3.0, -0.04, "ease_in_out"]]}))
    add("cam_shake_small", "camera impact", _m("camera", 0.6, True, {"camera.x": _osc(6, 0.6, 0.006, ease_name="linear"), "camera.y": _osc(5, 0.6, 0.004, ease_name="linear", phase=1)}))
    add("cam_shake_strong", "camera impact", _m("camera", 0.5, False, {"camera.x": [[0, 0, "linear"], [0.05, 0.03, "linear"], [0.1, -0.025, "linear"], [0.17, 0.02, "linear"],
                                                                                    [0.25, -0.012, "linear"], [0.35, 0.006, "linear"], [0.5, 0, "ease_out"]],
                                                                       "camera.rot": [[0, 0, "linear"], [0.08, 2.5, "linear"], [0.18, -2, "linear"], [0.3, 1, "linear"], [0.5, 0, "ease_out"]]}))
    add("cam_dutch_tilt", "camera tension", _m("camera", 0.8, False, {"camera.rot": [[0, 0, "linear"], [0.8, -5, "ease_out"]], "camera.scale": [[0, 1.0, "linear"], [0.8, 1.08, "ease_out"]]}))
    add("cam_handheld", "camera documentary", _m("camera", 4.0, True, {"camera.x": _osc(2, 4.0, 0.006), "camera.y": _osc(3, 4.0, 0.004, phase=1), "camera.rot": _osc(2, 4.0, 0.6, phase=1)}))
    add("cam_heartbeat", "camera tension health", _m("camera", 1.0, True, {"camera.scale": [[0, 1.0, "linear"], [0.1, 1.05, "ease_out"], [0.22, 1.0, "ease_in"], [0.34, 1.04, "ease_out"],
                                                                                           [0.5, 1.0, "ease_in"], [1.0, 1.0, "linear"]]}))
    add("cam_zoom_bounce", "camera emphasis", _m("camera", 0.8, False, {"camera.scale": [[0, 1.0, "linear"], [0.8, 1.2, "spring"]]}, {"stiffness": 220, "damping": 9}))
    add("cam_whip_right", "camera transition", _m("camera", 0.35, False, {"camera.x": [[0, -0.3, "linear"], [0.35, 0.0, "expo_out"]]}))
    add("cam_whip_left", "camera transition", _m("camera", 0.35, False, {"camera.x": [[0, 0.3, "linear"], [0.35, 0.0, "expo_out"]]}))
    add("cam_spin_in", "camera transition comedy", _m("camera", 0.6, False, {"camera.rot": [[0, -90, "linear"], [0.6, 0, "expo_out"]], "camera.scale": [[0, 0.6, "linear"], [0.6, 1.0, "expo_out"]]}))
    add("cam_dolly_vertigo", "camera tension", _m("camera", 2.0, False, {"camera.scale": [[0, 1.0, "linear"], [2.0, 1.25, "ease_in_out"]], "camera.y": [[0, 0.0, "linear"], [2.0, 0.04, "ease_in_out"]]}))
    add("cam_drift_right", "camera calm", _m("camera", 6.0, False, {"camera.x": [[0, -0.03, "linear"], [6.0, 0.03, "ease_in_out"]], "camera.scale": [[0, 1.04, "linear"], [6.0, 1.04, "linear"]]}))
    add("cam_rock_boat", "camera comedy ocean", _m("camera", 3.0, True, {"camera.rot": _osc(1, 3.0, 3.0), "camera.y": _osc(2, 3.0, 0.01)}))
    add("cam_focus_snap", "camera emphasis", _m("camera", 0.5, False, {"camera.scale": [[0, 1.0, "linear"], [0.12, 1.25, "expo_out"], [0.5, 1.15, "ease_in_out"]]}))
    add("cam_impact_zoom", "camera impact", _m("camera", 0.45, False, {"camera.scale": [[0, 1.4, "linear"], [0.45, 1.0, "expo_out"]], "camera.rot": [[0, 4, "linear"], [0.45, 0, "expo_out"]]}))
    add("cam_float_dream", "camera calm", _m("camera", 6.0, True, {"camera.y": _osc(1, 6.0, 0.012), "camera.scale": _osc(1, 6.0, 0.02, 1.04, phase=1)}))
    # ---- whole body
    add("hop_once", "character happy", _m("character", 0.6, False, {"character.y": _seq([(0, 0), (0.25, -0.05), (0.6, 0)], "ease_out")}))
    add("jump_big", "character celebration", _m("character", 0.9, False, {"character.y": [[0, 0, "linear"], [0.12, 0.012, "ease_out"], [0.45, -0.12, "ease_out"], [0.8, 0, "ease_in"], [0.9, 0.006, "ease_out"]],
                                                                          "torso.scale_y": [[0, 1, "linear"], [0.12, 0.88, "ease_out"], [0.3, 1.06, "ease_out"], [0.8, 1.0, "linear"], [0.86, 0.9, "ease_out"],
                                                                                            [0.9, 1.0, "ease_out"]]}))
    add("jump_loop_excited", "character celebration excited", _m("character", 0.7, True, {"character.y": [[0, 0, "linear"], [0.3, -0.06, "ease_out"], [0.6, 0, "ease_in"], [0.7, 0, "linear"]],
                                                                                         "torso.scale_y": [[0, 0.94, "linear"], [0.15, 1.04, "ease_out"], [0.6, 1.0, "linear"], [0.7, 0.94, "ease_out"]]}))
    add("bob_talk", "character talking", _m("character", 1.2, True, {"character.y": _osc(2, 1.2, 0.004)}))
    add("sway_gentle", "character calm", _m("character", 3.0, True, {"character.rot": _osc(1, 3.0, 2.5)}))
    add("sway_music", "character music", _m("character", 1.0, True, {"character.rot": _osc(1, 1.0, 6.0), "character.y": _osc(2, 1.0, 0.006)}))
    add("lean_in_curious", "character curious", _m("character", 0.6, False, {"character.rot": [[0, 0, "linear"], [0.6, -7, "ease_out"]]}))
    add("lean_back_shock", "character surprise", _m("character", 0.4, False, {"character.rot": [[0, 0, "linear"], [0.4, 9, "spring"]], "character.x": [[0, 0, "linear"], [0.4, 0.02, "ease_out"]]},
                                                    {"stiffness": 300, "damping": 12}))
    add("spin_twirl", "character celebration comedy", _m("character", 0.8, False, {"character.rot": [[0, 0, "linear"], [0.8, 360, "ease_in_out"]]}))
    add("jelly_wobble", "character comedy", _m("character", 0.8, False, {"torso.scale_y": [[0, 0.8, "linear"], [0.8, 1.0, "spring"]], "character.scale": [[0, 1.08, "linear"], [0.8, 1.0, "spring"]]},
                                                {"stiffness": 260, "damping": 7}))
    add("squash_land", "character impact", _m("character", 0.5, False, {"torso.scale_y": [[0, 0.75, "linear"], [0.5, 1.0, "spring"]]}, {"stiffness": 300, "damping": 9}))
    add("shiver_cold", "character scared weather", _m("character", 0.24, True, {"character.x": _osc(3, 0.24, 0.003, ease_name="linear")}))
    add("tremble_fear", "character scared", _m("character", 0.3, True, {"character.x": _osc(3, 0.3, 0.005, ease_name="linear"), "character.rot": _osc(2, 0.3, 1.5, ease_name="linear")}))
    add("slide_in_left", "character entrance", _m("character", 0.6, False, {"character.x": [[0, -0.7, "linear"], [0.6, 0, "expo_out"]]}))
    add("slide_in_right", "character entrance", _m("character", 0.6, False, {"character.x": [[0, 0.7, "linear"], [0.6, 0, "expo_out"]]}))
    add("exit_right", "character exit", _m("character", 0.8, False, {"character.x": [[0, 0, "linear"], [0.3, -0.02, "ease_out"], [0.8, 0.8, "ease_in"]]}))
    add("rise_from_bottom", "character entrance", _m("character", 0.7, False, {"character.y": [[0, 0.5, "linear"], [0.7, 0, "expo_out"]]}))
    add("drop_in_top", "character entrance comedy", _m("character", 0.9, False, {"character.y": [[0, -0.8, "linear"], [0.9, 0, "spring"]]}, {"stiffness": 200, "damping": 11}))
    add("pop_in_scale", "character entrance", _m("character", 0.6, False, {"character.scale": [[0, 0.01, "linear"], [0.6, 1, "spring"]]}, {"stiffness": 260, "damping": 13}))
    add("shrink_small", "character comedy sad", _m("character", 1.0, False, {"character.scale": [[0, 1.0, "linear"], [1.0, 0.7, "ease_in_out"]]}))
    add("grow_big", "character confident", _m("character", 1.0, False, {"character.scale": [[0, 1.0, "linear"], [1.0, 1.2, "ease_in_out"]]}))
    add("float_hover", "character magic dream", _m("character", 2.4, True, {"character.y": [[0, -0.02, "linear"], [1.2, -0.05, "sine"], [2.4, -0.02, "sine"]]}))
    add("pace_back_forth", "character thinking stress", _m("character", 3.2, True, {"character.x": [[0, -0.06, "linear"], [1.6, 0.06, "ease_in_out"], [3.2, -0.06, "ease_in_out"]],
                                                                                    "character.y": _osc(4, 3.2, 0.006, ease_name="linear")}))
    add("faint_fall", "character comedy", _m("character", 1.0, False, {"character.rot": [[0, 0, "linear"], [0.25, -6, "ease_out"], [1.0, 82, "ease_in"]]}))
    add("bounce_happy", "character happy", _m("character", 0.5, True, {"character.y": [[0, 0, "linear"], [0.25, -0.025, "ease_out"], [0.5, 0, "ease_in"]]}))
    add("heavy_breath", "character tired fitness", _m("character", 1.4, True, {"torso.scale_y": _osc(1, 1.4, 0.04, 1.0), "character.y": _osc(1, 1.4, 0.004)}))
    # ---- gestures (pose offsets in degrees, added to whatever pose the scene uses)
    add("wave_right", "gesture greeting", _m("gesture", 0.8, True, {"pose.r_shoulder": _seq([(0, 0), (0.15, -110), (0.65, -110), (0.8, 0)]),
                                                                    "pose.r_elbow": [[0, 0, "linear"], [0.15, -40, "ease_out"], [0.3, -10, "sine"], [0.45, -45, "sine"], [0.6, -10, "sine"], [0.8, 0, "sine"]]}))
    add("wave_left", "gesture greeting", _m("gesture", 0.8, True, {"pose.l_shoulder": _seq([(0, 0), (0.15, 110), (0.65, 110), (0.8, 0)]),
                                                                   "pose.l_elbow": [[0, 0, "linear"], [0.15, 40, "ease_out"], [0.3, 10, "sine"], [0.45, 45, "sine"], [0.6, 10, "sine"], [0.8, 0, "sine"]]}))
    add("wave_both_cheer", "gesture celebration", _m("gesture", 0.7, True, {"pose.l_shoulder": _osc(1, 0.7, 25, 120), "pose.r_shoulder": _osc(1, 0.7, 25, -120, phase=1)}))
    add("nod_yes", "gesture agree", _m("gesture", 0.8, True, {"torso.scale_y": _osc(2, 0.8, 0.025, 1.0)}))
    add("head_shake_no", "gesture disagree", _m("gesture", 0.6, True, {"pose.neck": _osc(2, 0.6, 9)}))
    add("head_tilt_curious", "gesture curious", _m("gesture", 0.6, False, {"pose.neck": [[0, 0, "linear"], [0.6, 16, "spring"]]}, {"stiffness": 220, "damping": 12}))
    add("shrug_bounce", "gesture confused", _m("gesture", 0.7, False, {"pose.l_shoulder": _seq([(0, 0), (0.25, 55), (0.55, 55), (0.7, 0)]), "pose.l_elbow": _seq([(0, 0), (0.25, 85), (0.55, 85), (0.7, 0)]),
                                                                       "pose.r_shoulder": _seq([(0, 0), (0.25, -55), (0.55, -55), (0.7, 0)]), "pose.r_elbow": _seq([(0, 0), (0.25, -85), (0.55, -85), (0.7, 0)]),
                                                                       "character.y": _seq([(0, 0), (0.25, -0.012), (0.7, 0)])}))
    add("clap_hands", "gesture celebration", _m("gesture", 0.4, True, {"pose.l_shoulder": _seq([(0, 40), (0.2, 25), (0.4, 40)]), "pose.l_elbow": _seq([(0, -90), (0.2, -120), (0.4, -90)]),
                                                                       "pose.r_shoulder": _seq([(0, -40), (0.2, -25), (0.4, -40)]), "pose.r_elbow": _seq([(0, 90), (0.2, 120), (0.4, 90)])}))
    add("point_jab", "gesture presenting emphasis", _m("gesture", 0.5, True, {"pose.r_shoulder": _seq([(0, -80), (0.15, -90), (0.5, -80)]), "pose.r_elbow": _seq([(0, -20), (0.15, 0), (0.5, -20)])}))
    add("fist_pump", "gesture winner", _m("gesture", 0.5, True, {"pose.r_shoulder": _seq([(0, -100), (0.2, -150), (0.5, -100)]), "pose.r_elbow": _seq([(0, -100), (0.2, -20), (0.5, -100)])}))
    add("thumbs_up_pop", "gesture approval", _m("gesture", 0.5, False, {"pose.r_shoulder": [[0, 0, "linear"], [0.5, -40, "spring"]], "pose.r_elbow": [[0, 0, "linear"], [0.5, -105, "spring"]]},
                                                {"stiffness": 260, "damping": 12}))
    add("typing_fast", "gesture tech work", _m("gesture", 0.24, True, {"pose.l_elbow": _osc(2, 0.24, 6, ease_name="linear"), "pose.r_elbow": _osc(2, 0.24, 6, ease_name="linear", phase=1)}))
    add("chin_tap_think", "gesture thinking", _m("gesture", 1.0, True, {"pose.r_shoulder": [[0, -40, "linear"], [1.0, -40, "linear"]], "pose.r_elbow": _osc(2, 1.0, 6, -125), "pose.neck": _osc(1, 1.0, 3, 4)}))
    add("scratch_head_loop", "gesture confused", _m("gesture", 0.5, True, {"pose.r_shoulder": [[0, -150, "linear"], [0.5, -150, "linear"]], "pose.r_elbow": _osc(2, 0.5, 10, -40, ease_name="linear")}))
    add("explain_hands", "gesture explaining talking", _m("gesture", 1.6, True, {"pose.l_shoulder": _osc(1, 1.6, 12, 40), "pose.l_elbow": _osc(1, 1.6, 20, -60, phase=1),
                                                                                  "pose.r_shoulder": _osc(1, 1.6, 12, -40, phase=1), "pose.r_elbow": _osc(1, 1.6, 20, 60)}))
    add("talk_gesture_a", "gesture talking", _m("gesture", 2.0, True, {"pose.r_shoulder": [[0, 0, "linear"], [0.4, -50, "ease_out"], [1.0, -35, "sine"], [1.5, -55, "sine"], [2.0, 0, "ease_in_out"]],
                                                                        "pose.r_elbow": [[0, 0, "linear"], [0.4, 50, "ease_out"], [1.0, 70, "sine"], [1.5, 40, "sine"], [2.0, 0, "ease_in_out"]],
                                                                        "pose.neck": _osc(2, 2.0, 4)}))
    add("talk_gesture_b", "gesture talking", _m("gesture", 2.2, True, {"pose.l_shoulder": [[0, 0, "linear"], [0.5, 60, "ease_out"], [1.2, 45, "sine"], [1.7, 65, "sine"], [2.2, 0, "ease_in_out"]],
                                                                        "pose.l_elbow": [[0, 0, "linear"], [0.5, -40, "ease_out"], [1.2, -70, "sine"], [1.7, -40, "sine"], [2.2, 0, "ease_in_out"]],
                                                                        "pose.r_shoulder": _osc(1, 2.2, 8, -10), "pose.neck": _osc(1, 2.2, 5, phase=1)}))
    add("talk_gesture_c", "gesture talking", _m("gesture", 1.8, True, {"pose.l_shoulder": _osc(2, 1.8, 18, 30), "pose.r_shoulder": _osc(2, 1.8, 18, -30, phase=1),
                                                                        "pose.l_elbow": [[0, -40, "linear"], [1.8, -40, "linear"]], "pose.r_elbow": [[0, 40, "linear"], [1.8, 40, "linear"]],
                                                                        "character.y": _osc(4, 1.8, 0.003)}))
    add("count_on_fingers", "gesture explaining", _m("gesture", 1.5, True, {"pose.r_shoulder": [[0, -60, "linear"], [1.5, -60, "linear"]], "pose.r_elbow": _osc(3, 1.5, 15, 130)}))
    add("flex_pulse", "gesture fitness confident", _m("gesture", 0.8, True, {"pose.l_elbow": _osc(1, 0.8, 15, 100), "pose.r_elbow": _osc(1, 0.8, 15, -100), "torso.scale_y": _osc(1, 0.8, 0.03, 1.0)}))
    add("dance_disco", "gesture music celebration", _m("gesture", 0.8, True, {"pose.r_shoulder": _seq([(0, -150), (0.4, -30), (0.8, -150)]), "pose.l_shoulder": _seq([(0, 30), (0.4, 40), (0.8, 30)]),
                                                                             "character.rot": _osc(1, 0.8, 5), "pose.r_hip": _osc(1, 0.8, 12, -15)}))
    add("dance_arm_wave", "gesture music", _m("gesture", 1.0, True, {"pose.l_shoulder": _osc(1, 1.0, 30, 100), "pose.l_elbow": _osc(1, 1.0, 40, -30, phase=1),
                                                                     "pose.r_shoulder": _osc(1, 1.0, 30, -100, phase=1), "pose.r_elbow": _osc(1, 1.0, 40, 30), "character.y": _osc(2, 1.0, 0.008)}))
    add("dance_bounce_hips", "gesture music celebration", _m("gesture", 0.6, True, {"pose.torso_lean": _osc(1, 0.6, 8),
                                                                                    "pose.l_knee": _osc(1, 0.6, 15, 15), "pose.r_knee": _osc(1, 0.6, 15, 15, phase=1), "character.y": _osc(2, 0.6, 0.008)}))
    add("walk_cycle", "gesture movement", _m("gesture", 0.9, True, {"pose.l_hip": _osc(1, 0.9, 22), "pose.r_hip": _osc(1, 0.9, 22, phase=1), "pose.l_knee": _osc(1, 0.9, 15, 15, phase=1),
                                                                   "pose.r_knee": _osc(1, 0.9, 15, 15), "pose.l_shoulder": _osc(1, 0.9, 20, phase=1), "pose.r_shoulder": _osc(1, 0.9, 20, phase=1),
                                                                   "character.y": _osc(2, 0.9, 0.004)}))
    add("run_cycle", "gesture movement fitness", _m("gesture", 0.55, True, {"pose.l_hip": _osc(1, 0.55, 40), "pose.r_hip": _osc(1, 0.55, 40, phase=1), "pose.l_knee": _osc(1, 0.55, 40, 50, phase=1),
                                                                           "pose.r_knee": _osc(1, 0.55, 40, 50), "pose.l_shoulder": _osc(1, 0.55, 45, phase=1), "pose.r_shoulder": _osc(1, 0.55, 45, phase=1),
                                                                           "pose.l_elbow": [[0, -80, "linear"], [0.55, -80, "linear"]], "pose.r_elbow": [[0, 80, "linear"], [0.55, 80, "linear"]],
                                                                           "pose.torso_lean": [[0, 8, "linear"], [0.55, 8, "linear"]], "character.y": _osc(2, 0.55, 0.01)}))
    add("march_proud", "gesture movement leader", _m("gesture", 1.0, True, {"pose.l_hip": _osc(1, 1.0, 35), "pose.r_hip": _osc(1, 1.0, 35, phase=1), "pose.l_shoulder": _osc(1, 1.0, 35, phase=1),
                                                                           "pose.r_shoulder": _osc(1, 1.0, 35, phase=1), "character.y": _osc(2, 1.0, 0.006)}))
    add("jumping_jacks", "gesture fitness", _m("gesture", 0.7, True, {"pose.l_shoulder": _seq([(0, 0), (0.35, 140), (0.7, 0)]), "pose.r_shoulder": _seq([(0, 0), (0.35, -140), (0.7, 0)]),
                                                                     "pose.l_hip": _seq([(0, 0), (0.35, 25), (0.7, 0)]), "pose.r_hip": _seq([(0, 0), (0.35, -25), (0.7, 0)]),
                                                                     "character.y": _seq([(0, 0), (0.17, -0.03), (0.35, 0), (0.52, -0.03), (0.7, 0)])}))
    add("squat_reps", "gesture fitness", _m("gesture", 1.4, True, {"pose.l_hip": _osc(1, 1.4, 35, 35), "pose.r_hip": _osc(1, 1.4, 35, -35), "pose.l_knee": _osc(1, 1.4, 50, 50),
                                                                   "pose.r_knee": _osc(1, 1.4, 50, 50), "pose.l_shoulder": _osc(1, 1.4, 40, 40), "pose.r_shoulder": _osc(1, 1.4, 40, -40)}))
    add("punch_combo", "gesture fitness sports", _m("gesture", 0.6, True, {"pose.r_shoulder": _seq([(0, 0), (0.15, -50), (0.3, 0), (0.6, 0)], "expo_out"),
                                                                          "pose.r_elbow": _seq([(0, 0), (0.15, 110), (0.3, 0), (0.6, 0)], "expo_out"),
                                                                          "pose.l_shoulder": _seq([(0, 0), (0.3, 0), (0.45, 50), (0.6, 0)], "expo_out"),
                                                                          "pose.l_elbow": _seq([(0, 0), (0.3, 0), (0.45, -110), (0.6, 0)], "expo_out")}))
    add("dumbbell_curl", "gesture fitness", _m("gesture", 1.2, True, {"pose.l_elbow": _osc(1, 1.2, 60, -60), "pose.r_elbow": _osc(1, 1.2, 60, 60)}))
    add("hammer_strike", "gesture construction work", _m("gesture", 0.6, True, {"pose.r_shoulder": _seq([(0, -160), (0.35, -70), (0.6, -160)], "expo_in"), "pose.r_elbow": _seq([(0, -70), (0.35, 0), (0.6, -70)], "expo_in")}))
    add("stir_circle", "gesture cooking", _m("gesture", 0.9, True, {"pose.r_shoulder": _osc(1, 0.9, 12, -55), "pose.r_elbow": _osc(1, 0.9, 20, -60, phase=1)}))
    add("write_scribble", "gesture education work", _m("gesture", 0.4, True, {"pose.r_elbow": _osc(2, 0.4, 8, ease_name="linear"), "pose.r_shoulder": _osc(1, 0.4, 4, ease_name="linear")}))
    add("phone_scroll", "gesture tech social_media", _m("gesture", 0.8, True, {"pose.r_elbow": _osc(1, 0.8, 6), "pose.neck": [[0, 12, "linear"], [0.8, 12, "linear"]]}))
    add("drink_sip_loop", "gesture food", _m("gesture", 2.0, True, {"pose.r_shoulder": _seq([(0, -20), (0.6, -40), (1.4, -40), (2.0, -20)]), "pose.r_elbow": _seq([(0, -60), (0.6, -140), (1.4, -140), (2.0, -60)]),
                                                                    "pose.neck": _seq([(0, 0), (0.6, -10), (1.4, -10), (2.0, 0)])}))
    add("conduct_music", "gesture music", _m("gesture", 1.0, True, {"pose.r_shoulder": _osc(2, 1.0, 25, -120), "pose.l_shoulder": _osc(1, 1.0, 15, 110), "pose.r_elbow": _osc(2, 1.0, 20, -30, phase=1)}))
    add("guitar_strum_loop", "gesture music", _m("gesture", 0.4, True, {"pose.r_elbow": _osc(1, 0.4, 25, 80, ease_name="linear"), "character.y": _osc(1, 0.4, 0.003)}))
    add("drum_hits", "gesture music", _m("gesture", 0.5, True, {"pose.l_elbow": _seq([(0, -40), (0.12, -90), (0.25, -40), (0.5, -40)], "expo_out"),
                                                                "pose.r_elbow": _seq([(0, 40), (0.25, 40), (0.37, 90), (0.5, 40)], "expo_out")}))
    add("beckon_come", "gesture communication", _m("gesture", 0.8, True, {"pose.r_shoulder": [[0, -60, "linear"], [0.8, -60, "linear"]], "pose.r_elbow": _osc(2, 0.8, 30, -60)}))
    add("bye_wave_slow", "gesture greeting sad", _m("gesture", 1.4, True, {"pose.r_shoulder": [[0, -120, "linear"], [1.4, -120, "linear"]], "pose.r_elbow": _osc(1, 1.4, 25, -20)}))
    add("salute_snap", "gesture respect", _m("gesture", 0.5, False, {"pose.r_shoulder": [[0, 0, "linear"], [0.5, -120, "expo_out"]], "pose.r_elbow": [[0, 0, "linear"], [0.5, -118, "expo_out"]]}))
    add("facepalm_slow", "gesture frustrated comedy", _m("gesture", 0.9, False, {"pose.r_shoulder": [[0, 0, "linear"], [0.9, -40, "ease_in"]], "pose.r_elbow": [[0, 0, "linear"], [0.9, -128, "ease_in"]],
                                                                                "pose.neck": [[0, 0, "linear"], [0.9, 8, "ease_in"]]}))
    add("arms_up_celebrate", "gesture celebration winner", _m("gesture", 0.6, False, {"pose.l_shoulder": [[0, 0, "linear"], [0.6, 140, "spring"]], "pose.r_shoulder": [[0, 0, "linear"], [0.6, -140, "spring"]]},
                                                            {"stiffness": 240, "damping": 11}))
    add("hands_shake_panic", "gesture scared stress", _m("gesture", 0.3, True, {"pose.l_shoulder": _osc(2, 0.3, 15, 120, ease_name="linear"), "pose.r_shoulder": _osc(2, 0.3, 15, -120, ease_name="linear", phase=1),
                                                                                "character.x": _osc(3, 0.3, 0.004, ease_name="linear")}))
    add("swim_strokes", "gesture fitness ocean", _m("gesture", 1.0, True, {"pose.l_shoulder": [[0, 0, "linear"], [0.5, 180, "linear"], [1.0, 360, "linear"]],
                                                                          "pose.r_shoulder": [[0, -180, "linear"], [0.5, -360, "linear"], [1.0, -540, "linear"]]}))
    add("sweep_motion", "gesture home work", _m("gesture", 0.8, True, {"pose.l_shoulder": _osc(1, 0.8, 20, 30), "pose.r_shoulder": _osc(1, 0.8, 20, -20), "pose.torso_lean": _osc(1, 0.8, 5, 6)}))
    add("tiptoe_sneak_loop", "gesture mystery comedy", _m("gesture", 1.0, True, {"pose.l_hip": _osc(1, 1.0, 15, 15), "pose.r_hip": _osc(1, 1.0, 15, -20, phase=1),
                                                                                "character.y": _osc(2, 1.0, 0.006)}))
    add("look_around", "gesture mystery curious", _m("gesture", 2.0, True, {"pose.neck": [[0, 0, "linear"], [0.4, 14, "ease_out"], [1.0, 14, "linear"], [1.4, -14, "ease_in_out"], [1.8, -14, "linear"], [2.0, 0, "ease_in"]]}))
    add("heartbeat_chest", "gesture love health", _m("gesture", 0.8, True, {"torso.scale_y": [[0, 1.0, "linear"], [0.1, 1.05, "ease_out"], [0.22, 1.0, "ease_in"], [0.34, 1.04, "ease_out"], [0.5, 1.0, "ease_in"],
                                                                                              [0.8, 1.0, "linear"]]}))
    add("shiver_arms_hug", "gesture weather scared", _m("gesture", 0.2, True, {"pose.l_elbow": _osc(2, 0.2, 4, -150, ease_name="linear"), "pose.r_elbow": _osc(2, 0.2, 4, 150, ease_name="linear", phase=1),
                                                                               "character.x": _osc(2, 0.2, 0.003, ease_name="linear")}))
    add("yawn_stretch", "gesture sleep tired", _m("gesture", 2.0, False, {"pose.l_shoulder": _seq([(0, 0), (0.8, 150), (1.4, 150), (2.0, 0)]), "pose.r_shoulder": _seq([(0, 0), (0.8, -150), (1.4, -150), (2.0, 0)]),
                                                                         "torso.scale_y": _seq([(0, 1.0), (0.8, 1.06), (1.4, 1.06), (2.0, 1.0)])}))
    add("kick_once", "gesture sports fitness", _m("gesture", 0.6, False, {"pose.r_hip": [[0, 0, "linear"], [0.2, -90, "expo_out"], [0.6, 0, "ease_in_out"]], "pose.torso_lean": [[0, 0, "linear"], [0.2, -10, "expo_out"],
                                                                                                                                                                         [0.6, 0, "ease_in_out"]]}))
    add("present_sweep", "gesture presenting business", _m("gesture", 1.2, False, {"pose.r_shoulder": [[0, -20, "linear"], [1.2, -85, "ease_in_out"]], "pose.r_elbow": [[0, 20, "linear"], [1.2, 25, "ease_in_out"]],
                                                                                   "character.rot": [[0, 0, "linear"], [1.2, -3, "ease_in_out"]]}))
    add("magic_cast", "gesture magic", _m("gesture", 0.8, False, {"pose.r_shoulder": [[0, -40, "linear"], [0.3, -150, "expo_out"], [0.8, -110, "ease_in_out"]], "pose.r_elbow": [[0, -60, "linear"], [0.3, 0, "expo_out"],
                                                                                                                                                                              [0.8, 0, "linear"]]}))
    return [{"id": mid, "tags": tags.split(), "json": {"id": mid, **d}} for mid, tags, d in M]
