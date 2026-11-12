#!/usr/bin/env python3
"""Claude via the signed-in claude.ai web session (zero API key). UNOFFICIAL: private endpoints, may change.

Execution order (never raw urllib/requests against claude.ai: Cloudflare rejects non-browser TLS fingerprints):
  1. Android app bridge  http://127.0.0.1:8766/claude/complete  (a real Chromium WebView with the live cookie jar)
  2. curl_cffi with impersonate="chrome" + the synced User-Agent and Cookie header (when the app is not running)
Errors are typed so llm.call_json can fail over: WebAuthError (401/403), WebRateLimited (429), WebUnavailable (soft).
Session data is pushed by the app via POST /config/sessions and lives in memory only.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, Iterable, Optional

import common

log = common.log
BRIDGE_URL = os.environ.get("STICKMAN_BRIDGE_URL", "http://127.0.0.1:8766")
BASE = "https://claude.ai"
SESSION: Dict[str, str] = {}      # cookie_header, user_agent, org_id (memory only)


class WebAuthError(Exception):
    def __init__(self, status: int, msg: str = ""):
        super().__init__(f"claude web auth failed ({status}) {msg}".strip())
        self.status = status


class WebRateLimited(Exception):
    def __init__(self, retry_after: float = 90.0):
        super().__init__("claude web rate limited")
        self.retry_after = retry_after


class WebUnavailable(Exception):
    """Soft failure: bridge down / curl_cffi missing / 5xx. Caller hops to the next provider without a long cooldown."""


# ------------------------------------------------------------------ session
def set_session(cookie_header: str, user_agent: str, org_id: Optional[str] = None) -> None:
    SESSION.clear()
    SESSION.update({"cookie_header": cookie_header.strip(), "user_agent": user_agent.strip(), "org_id": (org_id or "").strip()})


def clear_session() -> None:
    SESSION.clear()


def has_session() -> bool:
    return bool(SESSION.get("cookie_header"))


# ------------------------------------------------------------------ parsing
def parse_sse(lines: Iterable[str]) -> str:
    """Tolerant SSE reader: handles the legacy {"completion": "..."} events and messages-style content_block_delta."""
    out = []
    for raw in lines:
        line = raw.strip()
        if not line.startswith("data:"):
            continue
        body = line[5:].strip()
        if not body or body == "[DONE]":
            continue
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        if obj.get("type") == "error" or "error" in obj and isinstance(obj["error"], (dict, str)):
            err = obj.get("error")
            msg = err.get("message") if isinstance(err, dict) else err
            raise RuntimeError(f"claude web error: {msg}"[:300])
        if isinstance(obj.get("completion"), str):
            out.append(obj["completion"])
        elif obj.get("type") == "content_block_delta":
            d = obj.get("delta") or {}
            if isinstance(d.get("text"), str):
                out.append(d["text"])
    return "".join(out)


def _raise_for(status: int, retry_after: Optional[str] = None, body: str = "") -> None:
    if status in (401, 403):
        raise WebAuthError(status, body[:120])
    if status == 429:
        raise WebRateLimited(float(retry_after) if retry_after and str(retry_after).isdigit() else 90.0)
    if status >= 500 or status == 0:
        raise WebUnavailable(f"HTTP {status} {body[:120]}")
    if status >= 400:
        raise RuntimeError(f"claude web HTTP {status}: {body[:160]}")


def build_prompt(system: str, prompt: str) -> str:
    return f"{system.strip()}\n\n{prompt.strip()}\n\nReply with one JSON object only. No markdown fences, no commentary."


# ------------------------------------------------------------------ path 1: Android bridge
def bridge_up(timeout: float = 1.5) -> bool:
    try:
        req = urllib.request.Request(BRIDGE_URL + "/ping", headers=_bridge_headers())
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def _bridge_headers() -> Dict[str, str]:
    tok = os.environ.get("STICKMAN_TOKEN", "")
    return {"X-Stickman-Token": tok} if tok else {}


def _bridge_complete(full_prompt: str, timeout: float) -> str:
    data = json.dumps({"prompt": full_prompt, "timeout_sec": int(timeout)}).encode("utf-8")
    req = urllib.request.Request(BRIDGE_URL + "/claude/complete", data=data, method="POST",
                                 headers={"Content-Type": "application/json", **_bridge_headers()})
    try:
        with urllib.request.urlopen(req, timeout=timeout + 15) as r:
            res: Dict[str, Any] = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):          # bridge rejected OUR token, not Claude: treat as bridge unavailable
            raise WebUnavailable("bridge token rejected")
        raise WebUnavailable(f"bridge HTTP {e.code}")
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
        raise WebUnavailable(f"bridge unreachable: {e}")
    status = int(res.get("status", 0))
    if status == 200 and res.get("text"):
        return str(res["text"])
    _raise_for(status or 0, str(res.get("retry_after") or ""), str(res.get("error") or res.get("text") or ""))
    raise WebUnavailable("empty bridge response")


# ------------------------------------------------------------------ path 2: curl_cffi
def _headers() -> Dict[str, str]:
    return {
        "User-Agent": SESSION.get("user_agent") or "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36",
        "Cookie": SESSION.get("cookie_header", ""),
        "anthropic-client-platform": "web_claude_ai",
        "Origin": BASE, "Referer": BASE + "/new", "Accept-Language": "en-US,en;q=0.9",
    }


def _direct_complete(full_prompt: str, timeout: float) -> str:
    try:
        from curl_cffi import requests as creq     # type: ignore
    except Exception:  # noqa: BLE001
        raise WebUnavailable("curl_cffi not installed (pip install curl_cffi) and the Android bridge is not running")
    if not has_session():
        raise WebAuthError(401, "no session synced from the app")
    kw = {"impersonate": "chrome", "timeout": timeout, "headers": _headers()}

    def chk(r) -> None:
        if r.status_code >= 400:
            _raise_for(r.status_code, r.headers.get("retry-after"), (r.text or "")[:200])

    org = SESSION.get("org_id")
    if not org:
        r = creq.get(BASE + "/api/organizations", **kw)
        chk(r)
        orgs = r.json()
        chat = [o for o in orgs if "chat" in (o.get("capabilities") or [])] or orgs
        if not chat:
            raise WebAuthError(403, "no organizations on this account")
        org = chat[0]["uuid"]
        SESSION["org_id"] = org
    conv = str(uuid.uuid4())
    base = f"{BASE}/api/organizations/{org}/chat_conversations"
    r = creq.post(base, json={"uuid": conv, "name": ""}, **kw)
    chk(r)
    try:
        h = {**kw["headers"], "Accept": "text/event-stream", "Content-Type": "application/json"}
        r = creq.post(f"{base}/{conv}/completion", json={"prompt": full_prompt, "timezone": "UTC", "attachments": [], "files": []},
                      impersonate="chrome", timeout=timeout, headers=h, stream=True)
        chk(r)
        text = parse_sse(l.decode("utf-8", "replace") if isinstance(l, bytes) else l for l in r.iter_lines())
    finally:
        try:
            creq.delete(f"{base}/{conv}", **kw)
        except Exception:  # noqa: BLE001
            pass
    if not text:
        raise WebUnavailable("empty completion")
    return text


# ------------------------------------------------------------------ public
def complete(system: str, prompt: str, timeout: float = 150.0) -> str:
    """Return the model text. Raises WebAuthError / WebRateLimited / WebUnavailable."""
    full = build_prompt(system, prompt)
    try:
        return _bridge_complete(full, timeout)
    except WebUnavailable as e:
        log.info("claude bridge unavailable (%s); trying curl_cffi", e)
    return _direct_complete(full, timeout)
