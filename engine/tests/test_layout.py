"""Layout solver: captions/props/widgets must never collide with the character, for any anchor or aspect."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import layout  # noqa: E402
import render_cairo as rc  # noqa: E402

STYLE = {"size_ratio": 0.07, "position_y": 0.68, "case": "upper", "max_words_per_line": 3}


def _pts(W, H, anchor_x, anchor_y, joints=None):
    rig = dict(rc.DEFAULT_RIG)
    U = 0.44 * H
    pts = rc.rig_points(rig, {**rc.DEFAULT_POSE, **(joints or {})}, U, (anchor_x * W, anchor_y * H))
    return pts, rig["head_radius"] * U, rig["line_width"] * U


@pytest.mark.parametrize("W,H", [(480, 854), (1080, 1920), (1280, 720), (720, 720)])
@pytest.mark.parametrize("ax,ay", [(0.5, 0.78), (0.3, 0.7), (0.7, 0.8), (0.5, 0.62), (0.5, 0.86)])
def test_no_overlap_any_anchor(W, H, ax, ay):
    pts, hr, lw = _pts(W, H, ax, ay)
    lay = layout.solve(W, H, pts, hr, lw, caption_style=STYLE, has_widget=True, has_prop=True)
    assert layout.check(lay) == []


def test_caption_moves_below_feet_when_it_hit_the_legs():
    pts, hr, lw = _pts(480, 854, 0.5, 0.78)
    lay = layout.solve(480, 854, pts, hr, lw, caption_style=STYLE)
    assert lay.caption.y >= lay.char.b - 1e-6
    assert lay.caption.b <= 854 * layout.SAFE_BOTTOM + 1


def test_caption_kept_when_clear_of_the_character():
    pts, hr, lw = _pts(480, 854, 0.5, 0.45)          # character high in the frame
    lay = layout.solve(480, 854, pts, hr, lw, caption_style=STYLE)
    assert abs(lay.caption_y - 0.68 * 854) < 1e-6 and lay.char_dy == 0.0


def test_character_lifted_only_when_no_room_and_within_limit():
    pts, hr, lw = _pts(480, 854, 0.5, 0.93)
    lay = layout.solve(480, 854, pts, hr, lw, caption_style=STYLE)
    assert -layout.MAX_LIFT * 854 - 1e-6 <= lay.char_dy <= 0


def test_prop_goes_to_the_roomier_side():
    pts, hr, lw = _pts(480, 854, 0.25, 0.78)
    assert layout.solve(480, 854, pts, hr, lw, has_prop=True).prop_side == "right"
    pts, hr, lw = _pts(480, 854, 0.75, 0.78)
    assert layout.solve(480, 854, pts, hr, lw, has_prop=True).prop_side == "left"


def test_widget_stays_above_head():
    pts, hr, lw = _pts(480, 854, 0.5, 0.6)
    lay = layout.solve(480, 854, pts, hr, lw, has_widget=True)
    assert lay.widget.b <= lay.head.y or layout.check(lay) == []


def test_check_reports_a_real_overlap():
    pts, hr, lw = _pts(480, 854, 0.5, 0.78)
    lay = layout.solve(480, 854, pts, hr, lw, caption_style=STYLE)
    lay.caption = layout.Rect(0, lay.char.y, 480, 80)
    assert "caption overlaps the character" in layout.check(lay)
