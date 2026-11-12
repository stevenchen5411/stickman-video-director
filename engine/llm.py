#!/usr/bin/env python3
"""Provider-failover JSON LLM client (stdlib only).

Order comes from providers.json `failover_order`. A provider is usable when an API key is available
(env var beats providers.json; `enc_v1:` values are Android-Keystore ciphertext and cannot be used here).
HTTP 429/503 puts the provider on cooldown (persisted in cache/failover_state.json) and hops to the next.
Session-cookie / OAuth-only providers are not callable from Termux and are skipped.
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

import common
import schemas

log = common.log
ENV_KEYS = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY", "chatgpt": "OPENAI_API_KEY"}
DEFAULT_COOLDOWN_SEC = 90


class RateLimited(Exception):
    def __init__(self, provider: str, retry_after: float = DEFAULT_COOLDOWN_SEC):
        super().__init__(f"{provider} rate limited")
        self.provider, self.retry_after = provider, retry_after


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
    return [n for n in prov.failover_order if getattr(prov.providers, n).enabled and api_key(n, prov)]


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


# ------------------------------------------------------------------ HTTP
def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: float = 180) -> Dict[str, Any]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        if e.code in (429, 503):
            ra = e.headers.get("Retry-After") if e.headers else None
            raise RateLimited("http", float(ra) if ra and ra.isdigit() else DEFAULT_COOLDOWN_SEC)
        raise RuntimeError(f"HTTP {e.code}: {body}")


def extract_json(text: str) -> Dict[str, Any]:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start >= 0 and end > start:
        return json.loads(t[start:end + 1])
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
        if not cfg.enabled or not key or in_cooldown(name):
            continue
        try:
            if name == "gemini":
                raw = _call_gemini(key, os.environ.get("STICKMAN_GEMINI_MODEL", cfg.director_model), system, prompt)
            elif name == "claude":
                raw = _call_claude(key, os.environ.get("STICKMAN_CLAUDE_MODEL", "claude-sonnet-5-5"), system, prompt)
            else:
                raw = _call_chatgpt(key, os.environ.get("STICKMAN_OPENAI_MODEL", "gpt-4o"), system, prompt)
            return extract_json(raw), name
        except RateLimited as rl:
            log.warning("%s rate-limited; hopping (cooldown %.0fs)", name, rl.retry_after)
            set_cooldown(name, rl.retry_after)
            errors.append(f"{name}: 429")
        except Exception as e:  # noqa: BLE001 - provider failure must not kill the pipeline
            log.warning("%s failed: %s", name, str(e)[:200])
            errors.append(f"{name}: {str(e)[:80]}")
    raise NoProvider("no usable AI provider" + (f" ({'; '.join(errors)})" if errors else ""))
