#!/usr/bin/env python3
"""Provider-failover JSON LLM client (stdlib only).

Order comes from providers.json `failover_order`. A provider is usable when an API key is available
(env var beats providers.json; `enc_v1:` values are Android-Keystore ciphertext and cannot be used here).
HTTP 429/503 puts the provider on cooldown (persisted in cache/failover_state.json) and hops to the next.
401/403 puts a provider on a longer cooldown (AUTH_COOLDOWN_SEC) and hops. Claude can run on a synced claude.ai web
session (claude_web.py) when no API key exists; a dead session raises the needs_refresh flag the app turns into a badge.
OAuth-only providers are not callable from Termux and are skipped.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import claude_web
import gemini_web
import common
import schemas

log = common.log
ENV_KEYS = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY", "chatgpt": "OPENAI_API_KEY"}
DEFAULT_COOLDOWN_SEC = 90
AUTH_COOLDOWN_SEC = 30 * 60      # 401/403: stop hammering a dead credential until the user refreshes it
SOFT_COOLDOWN_SEC = 120          # bridge down / transient 5xx


class RateLimited(Exception):
    def __init__(self, provider: str, retry_after: float = DEFAULT_COOLDOWN_SEC):
        super().__init__(f"{provider} rate limited")
        self.provider, self.retry_after = provider, retry_after


class AuthFailed(Exception):
    """HTTP 401/403 from a provider: credential rejected or blocked."""
    def __init__(self, provider: str = "http", status: int = 401):
        super().__init__(f"{provider} auth failed ({status})")
        self.provider, self.status = provider, status


class NoProvider(Exception):
    pass


def _providers() -> schemas.ProvidersFile:
    path = common.config_dir() / "providers.json"
    try:
        return schemas.load_providers(path)
    except Exception:  # missing/encrypted/invalid -> defaults, env keys still work
        return schemas.ProvidersFile()


# Keys pushed by the Android app over POST /config/keys. Memory only; never written to disk.
RUNTIME_KEYS: Dict[str, str] = {}


def set_runtime_keys(keys: Dict[str, str]) -> List[str]:
    """Replace in-memory keys (only known provider names, non-empty strings). Returns the names now held."""
    RUNTIME_KEYS.clear()
    for k, v in (keys or {}).items():
        if k in ENV_KEYS and isinstance(v, str) and v.strip():
            RUNTIME_KEYS[k] = v.strip()
    return sorted(RUNTIME_KEYS)


def api_key(name: str, prov: Optional[schemas.ProvidersFile] = None) -> Optional[str]:
    if RUNTIME_KEYS.get(name):
        return RUNTIME_KEYS[name]
    env = os.environ.get(ENV_KEYS[name])
    if env:
        return env
    prov = prov or _providers()
    val = getattr(getattr(prov.providers, name), "api_key", None)
    if val and not val.startswith("enc_v1:"):
        return val
    return None


def available(prov: Optional[schemas.ProvidersFile] = None) -> List[str]:
    prov = prov or _providers()
    return [n for n in prov.failover_order if getattr(prov.providers, n).enabled and _usable(n, prov)]


def _usable(name: str, prov: Optional[schemas.ProvidersFile] = None) -> bool:
    """API key, or (claude only) a synced claude.ai web session."""
    return bool(api_key(name, prov)) or (name == "claude" and claude_web.has_session()) or (name == "gemini" and gemini_web.has_session())


# ------------------------------------------------------------------ cooldown state
def _state_path() -> Path:
    return common.cache_dir() / "failover_state.json"


def _load_state() -> Dict[str, float]:
    try:
        return json.loads(_state_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: Dict[str, float]) -> None:
    try:
        p = _state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def set_cooldown(name: str, seconds: float) -> None:
    st = _load_state()
    st[name] = time.time() + seconds
    _save_state(st)


def in_cooldown(name: str) -> bool:
    return _load_state().get(name, 0) > time.time()


def mark_needs_refresh(name: str) -> None:
    st = _load_state()
    st[f"needs_refresh:{name}"] = time.time()
    _save_state(st)


def clear_needs_refresh(name: str) -> None:
    """Called when the app pushes a fresh session/key: drops the badge flag and the cooldown."""
    st = _load_state()
    st.pop(f"needs_refresh:{name}", None)
    st.pop(name, None)
    _save_state(st)


def status(prov: Optional[schemas.ProvidersFile] = None) -> Dict[str, Dict[str, Any]]:
    """Per-provider state for /health: ok | cooldown | needs_refresh | no_credentials."""
    prov = prov or _providers()
    st, now, out = _load_state(), time.time(), {}
    for n in ("claude", "gemini", "chatgpt"):
        left = max(0, int(st.get(n, 0) - now))
        if not _usable(n, prov):
            state = "no_credentials"
        elif f"needs_refresh:{n}" in st and left > 0:
            state = "needs_refresh"
        elif left > 0:
            state = "cooldown"
        else:
            state = "ok"
        out[n] = {"state": state, "cooldown_sec": left,
                  "via": "api_key" if api_key(n, prov) else ("web_session" if (n == "claude" and claude_web.has_session()) or (n == "gemini" and gemini_web.has_session()) else None)}
    return out


# ------------------------------------------------------------------ HTTP
def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: float = 180) -> Dict[str, Any]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        if e.code in (401, 403):
            raise AuthFailed("http", e.code)
        if e.code in (429, 503):
            ra = e.headers.get("Retry-After") if e.headers else None
            raise RateLimited("http", float(ra) if ra and ra.isdigit() else DEFAULT_COOLDOWN_SEC)
        raise RuntimeError(f"HTTP {e.code}: {body}")


def extract_json(text: str) -> Dict[str, Any]:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)
    for strict in (True, False):          # strict=False tolerates raw newlines/tabs inside strings (web Gemini does this in SVG)
        try:
            return json.loads(t, strict=strict)
        except json.JSONDecodeError:
            pass
    start, end = t.find("{"), t.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except json.JSONDecodeError:
            return json.loads(t[start:end + 1], strict=False)
    log.warning("no JSON in model output; head: %r", text[:300])
    raise ValueError("no JSON object found in model output")


def _call_gemini(key: str, model: str, system: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    data = _post_json(url, {"x-goog-api-key": key}, {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8},
    })
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_claude(key: str, model: str, system: str, prompt: str) -> str:
    data = _post_json("https://api.anthropic.com/v1/messages",
                      {"x-api-key": key, "anthropic-version": "2023-06-01"},
                      {"model": model, "max_tokens": 8000, "system": system,
                       "messages": [{"role": "user", "content": prompt}]})
    return data["content"][0]["text"]


def _call_claude_web(system: str, prompt: str) -> str:
    return claude_web.complete(system, prompt)


def _call_chatgpt(key: str, model: str, system: str, prompt: str) -> str:
    data = _post_json("https://api.openai.com/v1/chat/completions", {"Authorization": f"Bearer {key}"},
                      {"model": model, "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
    return data["choices"][0]["message"]["content"]


def call_json(system: str, prompt: str, prefer: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """Return (parsed_json, provider_name). Hops providers on 429/503/errors; raises NoProvider if none work."""
    prov = _providers()
    order = list(prov.failover_order)
    if prefer in order:
        order.remove(prefer)
        order.insert(0, prefer)
    errors: List[str] = []
    for name in order:
        cfg = getattr(prov.providers, name)
        key = api_key(name, prov)
        if not cfg.enabled or not _usable(name, prov) or in_cooldown(name):
            continue
        via_web = name in ("claude", "gemini") and not key
        try:
            if via_web:
                raw = _call_claude_web(system, prompt) if name == "claude" else gemini_web.complete(system, prompt)
            elif name == "gemini":
                raw = _call_gemini(key, os.environ.get("STICKMAN_GEMINI_MODEL", cfg.director_model), system, prompt)
            elif name == "claude":
                raw = _call_claude(key, os.environ.get("STICKMAN_CLAUDE_MODEL", "claude-sonnet-5-5"), system, prompt)
            else:
                raw = _call_chatgpt(key, os.environ.get("STICKMAN_OPENAI_MODEL", "gpt-4o"), system, prompt)
            parsed = extract_json(raw)
            if via_web:
                clear_needs_refresh(name)
            return parsed, name
        except (AuthFailed, claude_web.WebAuthError) as af:
            log.warning("%s auth failed (%s); cooling down, hopping", name, getattr(af, "status", "?"))
            set_cooldown(name, AUTH_COOLDOWN_SEC)
            if via_web:
                mark_needs_refresh(name)        # the app shows a 1-tap "Refresh Session" badge
            errors.append(f"{name}: {getattr(af, 'status', 401)}")
        except claude_web.WebRateLimited as wr:
            log.warning("claude web rate-limited; hopping (cooldown %.0fs)", wr.retry_after)
            set_cooldown(name, wr.retry_after)
            errors.append(f"{name}: 429")
        except claude_web.WebUnavailable as wu:
            log.warning("claude web unavailable: %s", str(wu)[:160])
            set_cooldown(name, SOFT_COOLDOWN_SEC)
            errors.append(f"{name}: unavailable")
        except RateLimited as rl:
            log.warning("%s rate-limited; hopping (cooldown %.0fs)", name, rl.retry_after)
            set_cooldown(name, rl.retry_after)
            errors.append(f"{name}: 429")
        except Exception as e:  # noqa: BLE001 - provider failure must not kill the pipeline
            log.warning("%s failed: %s", name, str(e)[:200])
            errors.append(f"{name}: {str(e)[:80]}")
    raise NoProvider("no usable AI provider" + (f" ({'; '.join(errors)})" if errors else ""))
