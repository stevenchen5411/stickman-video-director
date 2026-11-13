import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gemini_web as g  # noqa: E402
import llm  # noqa: E402


def chunk(text):
    inner = json.dumps([None, None, None, None, [["rc_1", [text]]]])
    return json.dumps([["wrb.fr", None, inner]])


def test_parse_page_and_missing_token():
    assert g.parse_page('x"SNlM0e":"TOK123"y"cfb2h":"boq_bl"') == {"at": "TOK123", "bl": "boq_bl"}
    with pytest.raises(g.WebAuthError):
        g.parse_page("<html>sign in</html>")


def test_parse_response_takes_last_full_chunk():
    body = ")]}'\n\n12\n" + chunk("par") + "\n40\n" + chunk('{"ok": true}') + "\n"
    assert g.parse_response(body) == '{"ok": true}'
    assert g.parse_response("garbage") == ""


def test_session_wiring(monkeypatch):
    g.clear_session()
    assert not g.has_session()
    g.set_session("SID=a; __Secure-1PSID=b", "UA")
    assert g.has_session()
    monkeypatch.setattr(llm, "api_key", lambda *a, **k: None)
    assert llm._usable("gemini")
    g.clear_session()
    assert not llm._usable("gemini")


def test_complete_without_session_is_soft_failure():
    g.clear_session()
    with pytest.raises(g.WebUnavailable):
        g.complete("sys", "hi")


def test_extract_json_tolerates_raw_newlines():
    raw = '```json\n{"svg": "<svg>\n<g/></svg>", "anchors": {"seat": [1, 2]}}\n```'
    assert llm.extract_json(raw)["anchors"]["seat"] == [1, 2]


def test_model_header_and_unwrap():
    h = g.model_header("flash")["x-goog-ext-525001261-jspb"]
    assert json.loads(h)[4] == g.MODELS["flash"][0] and g.model_header("nope") == {}
    import forge
    assert forge._SYSTEM.endswith("repeat the task or rules.")


def test_autolink_cleanup():
    raw = '<svg xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)"></svg>'
    assert g._AUTOLINK.sub(r"\1", raw) == '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
