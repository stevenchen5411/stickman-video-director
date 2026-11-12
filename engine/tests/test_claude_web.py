"""Claude web-session path: SSE parsing, the Android bridge, typed errors and provider failover."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import claude_web
import llm


def test_parse_sse_legacy_and_messages_formats():
    legacy = ['event: completion', 'data: {"completion": "Hel"}', '', 'data: {"completion": "lo"}']
    assert claude_web.parse_sse(legacy) == "Hello"
    modern = ['data: {"type":"message_start"}', 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"{\\"a\\":"}}',
              'data: {"type":"content_block_delta","delta":{"text":" 1}"}}', 'data: [DONE]']
    assert claude_web.parse_sse(modern) == '{"a": 1}'


def test_parse_sse_error_event_raises():
    with pytest.raises(RuntimeError):
        claude_web.parse_sse(['data: {"type":"error","error":{"message":"overloaded"}}'])


@pytest.mark.parametrize("status,exc", [(401, claude_web.WebAuthError), (403, claude_web.WebAuthError),
                                        (429, claude_web.WebRateLimited), (503, claude_web.WebUnavailable)])
def test_status_mapping(status, exc):
    with pytest.raises(exc):
        claude_web._raise_for(status, "30")


class _Bridge(BaseHTTPRequestHandler):
    reply = {"status": 200, "text": '{"ok": true}'}

    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true}')

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
        body = json.dumps(_Bridge.reply).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)


@pytest.fixture()
def bridge(monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), _Bridge)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(claude_web, "BRIDGE_URL", f"http://127.0.0.1:{srv.server_port}")
    yield _Bridge
    srv.shutdown()


def test_bridge_success_and_typed_failures(bridge):
    assert claude_web.bridge_up()
    bridge.reply = {"status": 200, "text": '{"ok": true}'}
    assert claude_web.complete("sys", "user") == '{"ok": true}'
    bridge.reply = {"status": 403, "error": "cloudflare"}
    with pytest.raises(claude_web.WebAuthError):
        claude_web.complete("s", "u")
    bridge.reply = {"status": 429, "retry_after": 45}
    with pytest.raises(claude_web.WebRateLimited) as e:
        claude_web.complete("s", "u")
    assert e.value.retry_after == 45


def test_no_bridge_and_no_curl_cffi_is_soft_unavailable(monkeypatch):
    monkeypatch.setattr(claude_web, "BRIDGE_URL", "http://127.0.0.1:9")
    monkeypatch.setitem(__import__("sys").modules, "curl_cffi", None)       # force ImportError
    with pytest.raises(claude_web.WebUnavailable):
        claude_web.complete("s", "u", timeout=2)


def _setup(monkeypatch):
    for k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    llm.set_runtime_keys({"gemini": "g-key-123456"})
    claude_web.set_session("sessionKey=abc", "UA/1.0", "org-1")
    llm.clear_needs_refresh("claude")


@pytest.mark.parametrize("exc,flag", [(claude_web.WebAuthError(403), True), (claude_web.WebAuthError(401), True),
                                      (claude_web.WebRateLimited(60), False)])
def test_claude_web_failure_hops_to_gemini(monkeypatch, exc, flag):
    _setup(monkeypatch)

    def boom(system, prompt, timeout=150):
        raise exc
    monkeypatch.setattr(claude_web, "complete", boom)
    monkeypatch.setattr(llm, "_call_gemini", lambda *a, **k: '{"from": "gemini"}')
    out, who = llm.call_json("s", "p")
    assert who == "gemini" and out == {"from": "gemini"}
    st = llm.status()["claude"]
    assert st["state"] == ("needs_refresh" if flag else "cooldown") and st["cooldown_sec"] > 0
    # next call skips claude entirely while cooling down
    monkeypatch.setattr(claude_web, "complete", lambda *a, **k: pytest.fail("claude must be skipped"))
    assert llm.call_json("s", "p")[1] == "gemini"
    llm.set_runtime_keys({}); claude_web.clear_session(); llm.clear_needs_refresh("claude")


def test_claude_web_is_primary_when_healthy_and_session_resets_badge(monkeypatch):
    _setup(monkeypatch)
    monkeypatch.setattr(claude_web, "complete", lambda s, p, timeout=150: '```json\n{"who": "claude"}\n```')
    assert llm.call_json("s", "p") == ({"who": "claude"}, "claude")
    assert llm.status()["claude"]["via"] == "web_session"
    llm.mark_needs_refresh("claude"); llm.set_cooldown("claude", 100)
    assert llm.status()["claude"]["state"] == "needs_refresh"
    claude_web.set_session("sessionKey=new", "UA/1.0"); llm.clear_needs_refresh("claude")
    assert llm.status()["claude"]["state"] == "ok"
    llm.set_runtime_keys({}); claude_web.clear_session()
