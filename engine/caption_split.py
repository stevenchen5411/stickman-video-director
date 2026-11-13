#!/usr/bin/env python3
"""Caption chunking by phrase: break at sentence ends, commas/colons and speech pauses, then balance each phrase
into chunks of 2..max words (never a lone orphan word unless the phrase is a single word)."""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List

HARD = re.compile(r"[.!?…]['\")\]]*$")
SOFT = re.compile(r"[,;:—–-]['\")\]]*$")
PAUSE_SEC = 0.30
WEAK = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "from", "with", "and", "or", "but", "your", "my", "our",
        "their", "his", "her", "its", "is", "are", "was", "be", "as", "than", "that", "by", "into", "so"}


def _weak(w: Dict[str, Any]) -> bool:
    t = str(w.get("word", ""))
    return t.lower().strip("\"'") in WEAK and not SOFT.search(t) and not HARD.search(t)


def split_phrases(words: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    out: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = []
    for i, w in enumerate(words):
        cur.append(w)
        text = str(w.get("word", ""))
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["start"] - w["end"]) if nxt else 0.0
        if nxt is None or HARD.search(text) or gap > PAUSE_SEC or (SOFT.search(text) and len(cur) >= 2):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def balance(phrase: List[Dict[str, Any]], max_words: int) -> List[List[Dict[str, Any]]]:
    n, per = len(phrase), max(1, max_words)
    if n <= per:
        return [phrase]
    k = math.ceil(n / per)
    base, extra = divmod(n, k)
    out, i = [], 0
    for j in range(k):
        size = base + (1 if j < extra else 0)
        out.append(phrase[i:i + size])
        i += size
    for j in range(len(out) - 1):                    # do not end a caption on "of", "the", "from"...
        if len(out[j]) > 1 and _weak(out[j][-1]) and len(out[j + 1]) < per + 1:
            out[j + 1] = [out[j].pop()] + out[j + 1]
    return out


def chunks(words: List[Dict[str, Any]], max_words: int = 3) -> List[List[Dict[str, Any]]]:
    """Caption groups for one scene. A single trailing word is merged into the previous group of the same sentence
    when that keeps it within max_words + 1."""
    groups: List[List[Dict[str, Any]]] = []
    for ph in split_phrases(words):
        groups.extend(balance(ph, max_words))
    merged: List[List[Dict[str, Any]]] = []
    for g in groups:
        if len(g) == 1 and merged and len(merged[-1]) < max_words + 1 and not HARD.search(str(merged[-1][-1].get("word", ""))) \
                and g[0]["start"] - merged[-1][-1]["end"] <= PAUSE_SEC:
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
    return merged
