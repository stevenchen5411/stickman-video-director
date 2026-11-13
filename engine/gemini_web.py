#!/usr/bin/env python3
"""Gemini via the signed-in gemini.google.com web session (zero API key). UNOFFICIAL: private endpoints, may change.

Uses curl_cffi (Chrome TLS fingerprint) with the cookie jar + WebView user agent pushed by the app (POST /config/sessions,
provider "gemini"). Flow: GET /app -> scrape the `SNlM0e` token and build label -> POST StreamGenerate -> parse the
length-prefixed JSON chunks. Errors reuse claude_web's typed exceptions so llm.call_json can fail over / flag needs_refresh.
Session data lives in memory only. Cookies are never logged.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

import claude_web
import common

log = common.log
BASE = "https://gemini.google.com"
SESSION: Dict[str, str] = {}
_TOKENS: Dict[str, Any] = {}      # at, bl, ts
WebAuthError, WebRateLimited, WebUnavailable = claude_web.WebAuthError, claude_web.WebRateLimited, claude_web.WebUnavailable


def set_session(cookie_header: str, user_agent: str) -> None:
    SESSION.clear()
    SESSION.update({"cookie_header": cookie_header.strip(), "user_agent": user_agent.strip()})
    _TOKENS.clear()


def clear_session() -> None:
    SESSION.clear()
    _TOKENS.clear()


def has_session() -> bool:
    return bool(SESSION.get("cookie_header"))


def _headers() -> Dict[str, str]:
    return {"Cookie": SESSION["cookie_header"], "User-Agent": SESSION.get("user_agent") or "Mozilla/5.0",
            "Origin": BASE, "Referer": BASE + "/", "X-Same-Domain": "1"}


def _session():
    try:
        from curl_cffi import requests as cr
    except Exception as e:  # noqa: BLE001
        raise WebUnavailable(f"curl_cffi missing: {e}")
    return cr


def parse_page(html: str) -> Dict[str, str]:
    """Pull the XSRF-ish `at` token (SNlM0e) and build label (cfb2h) from the /app HTML."""
    at = re.search(r'"SNlM0e":"(.*?)"', html)
    bl = re.search(r'"cfb2h":"(.*?)"', html)
    if not at:
        raise WebAuthError(401, "no SNlM0e token: not signed in")
    return {"at": at.group(1), "bl": bl.group(1) if bl else ""}


def _tokens(cr) -> Dict[str, str]:
    if _TOKENS.get("at") and time.time() - _TOKENS.get("ts", 0) < 900:
        return _TOKENS
    r = cr.get(BASE + "/app", headers=_headers(), impersonate="chrome", timeout=40, allow_redirects=True)
    if r.status_code in (401, 403) or "accounts.google.com" in str(r.url):
        raise WebAuthError(401, "redirected to sign-in")
    if r.status_code >= 500:
        raise WebUnavailable(f"/app HTTP {r.status_code}")
    _TOKENS.update(parse_page(r.text), ts=time.time())
    return _TOKENS


def parse_response(body: str) -> str:
    """StreamGenerate returns `)]}'` then length-prefixed JSON arrays; each holds an inner JSON string with the reply at [4][0][1][0].
    The LAST chunk carrying text is the full answer (earlier ones are partial)."""
    text = ""
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("["):
            continue
        try:
            outer = json.loads(line)
        except ValueError:
            continue
        for item in outer if isinstance(outer, list) else []:
            if isinstance(item, list) and len(item) > 2 and item[0] == "wrb.fr" and isinstance(item[2], str):
                try:
                    inner = json.loads(item[2])
                    cand = inner[4][0][1][0]
                    if isinstance(cand, str) and cand:
                        text = cand
                except (ValueError, IndexError, TypeError):
                    continue
    return text


def complete(system: str, prompt: str, timeout: float = 150) -> str:
    if not has_session():
        raise WebUnavailable("no gemini web session")
    cr = _session()
    tok = _tokens(cr)
    full = f"{system}\n\n{prompt}".strip() if system else prompt
    freq = json.dumps([None, json.dumps([[full], None, [None, None, None]])])
    url = f"{BASE}/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
    params = {"bl": tok.get("bl", ""), "_reqid": str(int(time.time()) % 900000 + 100000), "rt": "c", "hl": "en"}
    r = cr.post(url, params=params, data={"f.req": freq, "at": tok["at"]}, impersonate="chrome", timeout=timeout,
                headers={**_headers(), "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
    if r.status_code in (401, 403):
        _TOKENS.clear()
        raise WebAuthError(r.status_code)
    if r.status_code == 429:
        raise WebRateLimited(float(r.headers.get("Retry-After", 90) or 90))
    if r.status_code >= 400:
        _TOKENS.clear()
        raise WebUnavailable(f"StreamGenerate HTTP {r.status_code}")
    out = parse_response(r.text)
    if not out:
        _TOKENS.clear()
        raise WebUnavailable("empty Gemini web reply (format changed or session expired)")
    return out
