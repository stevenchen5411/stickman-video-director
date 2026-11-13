"""Captions break on phrases, not on a fixed word count."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import caption_split as cs  # noqa: E402


def mk(text, gap_after=None, step=0.3):
    out, t = [], 0.0
    for i, w in enumerate(text.split()):
        out.append({"word": w, "start": t, "end": t + 0.25})
        t += step + ((gap_after or {}).get(i, 0.0))
    return out


def texts(groups):
    return [" ".join(w["word"] for w in g) for g in groups]


def test_breaks_at_sentence_end():
    g = texts(cs.chunks(mk("Everything you eat is built from nutrients. Know the two kinds."), 3))
    assert any(t.endswith("nutrients.") for t in g)
    assert not any(t.split()[-1].lower() in cs.WEAK for t in g if len(t.split()) > 1), g   # never ends on "from", "of"...


def test_no_group_crosses_a_sentence():
    for g in cs.chunks(mk("Carbs are your fast fuel. Your brain runs on them constantly."), 3):
        assert not any(w["word"].endswith(".") for w in g[:-1])


def test_no_orphans_and_size_limits():
    for text in ["One two three four.", "A b c d e f g.", "Healthy fats feed your hormones and slow burn energy."]:
        gs = cs.chunks(mk(text), 3)
        assert all(2 <= len(g) <= 4 for g in gs), texts(gs)


def test_pause_breaks_phrase():
    words = mk("Wait there are only two kinds", gap_after={2: 0.5})
    gs = texts(cs.chunks(words, 4))
    assert gs[0].endswith("are") and gs[1].startswith("only")


def test_comma_breaks_when_two_words_in():
    gs = texts(cs.chunks(mk("Walk, some yoga, or a workout."), 3))
    assert gs[0] == "Walk, some"[: len(gs[0])] or gs[0].endswith("yoga,") or gs[0].endswith("Walk,")


def test_single_word_and_empty():
    assert texts(cs.chunks(mk("Okay."), 3)) == ["Okay."] and cs.chunks([], 3) == []


def test_every_word_kept_in_order():
    words = mk("Protein rebuilds muscle, fixes tissue, and backs up your defenses. Eggs, fish, beans.")
    flat = [w["word"] for g in cs.chunks(words, 3) for w in g]
    assert flat == [w["word"] for w in words]
