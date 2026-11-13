"""Default motion layer: emphasis pulse, camera drift, prop entrances."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motion_layer as ml  # noqa: E402

WORDS = [{"word": "Protein", "start": 0.0, "end": 0.4}, {"word": "rebuilds", "start": 0.5, "end": 0.9},
         {"word": "muscle,", "start": 1.0, "end": 1.5}, {"word": "fixes", "start": 1.6, "end": 1.9},
         {"word": "tissue.", "start": 2.0, "end": 2.5}]


def test_emphasis_times_match_words_and_phrases():
    assert ml.emphasis_times(WORDS, ["muscle", "fixes tissue", "absent"]) == [1.0, 1.6]


def test_pulse_peaks_then_fades():
    assert ml.pulse(1.0, [1.0]) == 1.0
    assert 0.0 < ml.pulse(1.2, [1.0]) < 1.0
    assert ml.pulse(0.9, [1.0]) == 0.0 and ml.pulse(1.0 + ml.PULSE_SEC + 0.01, [1.0]) == 0.0


def test_drift_grows_slowly_and_alternates():
    s0, x0 = ml.drift(0.0, 4.0, 0, None)
    s1, x1 = ml.drift(4.0, 4.0, 0, None)
    assert s0 == 1.0 and x0 == 0.0 and abs(s1 - (1 + ml.DRIFT_SCALE)) < 1e-9 and x1 > 0
    assert ml.drift(4.0, 4.0, 1, None)[1] < 0
    assert ml.drift(99.0, 4.0, 0, None)[0] <= 1 + ml.DRIFT_SCALE + 1e-9


def test_no_drift_when_motion_already_moves_the_camera():
    cam = {"tracks": [{"target": "camera.scale", "keys": []}]}
    assert ml.drift(3.0, 4.0, 0, cam) == (1.0, 0.0)
    assert ml.drift(3.0, 4.0, 0, {"tracks": [{"target": "character.x", "keys": []}]})[0] > 1.0


def test_entrance_variants_cover_all_three_and_end_in_place():
    seen = {ml.entrance_variant(n) for n in ["running_shoe", "avocado", "egg_fried", "lungs", "burger", "brain_simple"]}
    assert seen == {0, 1, 2}
    for v in (0, 1, 2):
        assert ml.entrance_offset(v, 1.0, 480, 854, 1) == (0.0, 0.0)
    assert ml.entrance_offset(1, 0.0, 480, 854, -1)[0] < 0 and ml.entrance_offset(2, 0.0, 480, 854, 1)[1] < 0
