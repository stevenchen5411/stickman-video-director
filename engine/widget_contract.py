#!/usr/bin/env python3
"""Widget data contract: a widget may only appear with content written for the story, never library sample text.

* CONTENT lists, per widget type, the `data` keys that carry story content (the rest is style: tilt, speed...).
* The director fills `fallback.widget_data` with the same shape as the library widget; `coerce` validates it.
* `is_stock` says whether a widget would still show the library's sample text (then it must not be drawn).
"""
from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import schemas

CONTENT: Dict[str, tuple] = {
    "bar_chart": ("labels", "values"), "pie": ("labels", "values"), "line_chart": ("title", "values", "end_label"),
    "battery": ("value", "label"), "gauge": ("value", "label"), "donut": ("value", "label"),
    "calendar": ("label",), "countdown": ("label",), "counter": ("title", "label", "to"),
    "checklist": ("title", "items"), "ranking": ("title", "items"), "progress": ("title", "items"),
    "comparison_card": ("left", "right"), "versus": ("left", "right"), "balance_scale": ("left", "right"),
    "equation": ("parts",), "funnel": ("stages",), "timeline": ("events",), "steps": ("steps",),
    "stat_card": ("label", "value", "delta"), "price_tag": ("old", "new", "label"), "quote": ("text", "author"),
    "map_route": ("pins",),
}
MAX_LIST = 8
MAX_STR = 60


def g(obj: Any, key: str, default: Any = None) -> Any:
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def load(index: schemas.LibraryIndex, lib: Path, wid: Optional[str]) -> Optional[Dict[str, Any]]:
    e = index.get(wid, "07_widgets") if wid else None
    if not e or not e.file_path.endswith(".json"):
        return None
    try:
        return schemas.load_json(Path(lib) / e.file_path)
    except Exception:  # noqa: BLE001
        return None


def content(kind: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: data[k] for k in CONTENT.get(kind or "", ()) if k in data}


def shapes(widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """{widget type: sample content} - the shape the director must reproduce with story text."""
    out: Dict[str, Any] = {}
    for w in widgets:
        t = w.get("type")
        if t in CONTENT and t not in out:
            out[t] = content(t, w.get("data") or {})
    return out


def _compat(default: Any, new: Any, depth: int = 0) -> Optional[Any]:
    """Return `new` cleaned to the shape of `default`, or None when it does not fit."""
    if isinstance(default, bool):
        return new if isinstance(new, bool) else None
    if isinstance(default, (int, float)):
        ok = isinstance(new, (int, float)) and not isinstance(new, bool) and math.isfinite(float(new))
        return new if ok else None
    if isinstance(default, str):
        return new.strip()[:MAX_STR] if isinstance(new, str) and new.strip() else None
    if isinstance(default, list):
        if not isinstance(new, list) or not (1 <= len(new) <= MAX_LIST) or depth > 2:
            return None
        proto = default[0] if default else ""
        items = [_compat(proto, x, depth + 1) for x in new]
        return items if all(x is not None for x in items) else None
    if isinstance(default, dict):
        if not isinstance(new, dict) or set(new) < set(default):      # every key is required: no stock fill-in
            return None
        out = {k: _compat(v, new[k], depth + 1) for k, v in default.items()}
        return out if all(v is not None for v in out.values()) else None
    return None


def coerce(wj: Dict[str, Any], payload: Any) -> Optional[Dict[str, Any]]:
    """Validate the director's `widget_data` against the library widget. Returns content keys only, or None."""
    kind, data = wj.get("type"), wj.get("data") or {}
    keys = CONTENT.get(kind or "")
    if not keys or not isinstance(payload, dict):
        return None
    out: Dict[str, Any] = {}
    for k in keys:
        if k in data:
            if k not in payload:
                return None
            v = _compat(data[k], payload[k])
            if v is None:
                return None
            out[k] = v
    if "labels" in out and "values" in out and len(out["labels"]) != len(out["values"]):
        return None
    return out or None


def apply(wj: Dict[str, Any], fb: Any) -> Dict[str, Any]:
    """The widget as it will be drawn: story data first, then the simple title/values/labels mapping."""
    out = copy.deepcopy(wj)
    if fb is None:
        return out
    d = out.setdefault("data", {})
    story = coerce(wj, g(fb, "data"))
    if story:
        d.update(story)
    kind = out.get("type")
    title, sub = g(fb, "title"), g(fb, "subtitle")
    values, labels = g(fb, "values"), g(fb, "labels")
    if title and not story:
        for k in ("title", "label", "text"):
            if k in d:
                d[k] = title
                break
        if sub and "label" in d and "title" in d:
            d["label"] = sub
    if values and not story:
        if "values" in d:
            d["values"] = list(values)
            if labels:
                d["labels"] = list(labels)[: len(values)]
        elif kind == "counter":
            d["to"] = values[0]
        elif kind in ("donut", "gauge", "battery") and "value" in d:
            d["value"] = values[0]
    if labels and not values and not story:
        if kind in ("checklist", "ranking"):
            d["items"] = list(labels)[:5]
        elif kind == "steps":
            d["steps"] = list(labels)[:4]
    return out


def is_stock(wj: Dict[str, Any], fb: Any) -> bool:
    """True when the widget would still show the library's sample content (or has no content keys we know)."""
    kind = wj.get("type")
    if kind not in CONTENT:
        return False
    base = content(kind, wj.get("data") or {})
    shown = content(kind, apply(wj, fb).get("data") or {})
    # partially filled is still stock: a sample string left in any content key (e.g. new title over sample items)
    return bool(base) and any(shown.get(k) == v for k, v in base.items())
