"""Registry shared by the asset-pack modules."""
from __future__ import annotations

from typing import Any, Callable, Dict, List

PROPS: List[Dict[str, Any]] = []
_SEEN: set = set()

TAG_VOCAB = {
    "general", "health", "medical", "science", "biology", "chemistry", "physics", "space", "tech", "ai", "coding",
    "computing", "data", "internet", "security", "finance", "money", "savings", "investing", "trading", "banking", "crypto",
    "web3", "business", "startup", "marketing", "career", "management", "productivity", "partnership", "logistics",
    "shopping", "ecommerce", "fashion", "luxury", "education", "history", "food", "cooking", "fitness", "sports", "nature",
    "animals", "pets", "environment", "weather", "energy", "travel", "transport", "navigation", "psychology",
    "self_improvement", "mental_health", "sleep", "relationships", "love", "family", "kids", "law", "music", "art",
    "gaming", "entertainment", "media", "podcast", "photography", "social_media", "communication", "construction",
    "industry", "agriculture", "home", "holiday", "celebration", "spooky", "mystery", "comedy", "storytelling",
    "motivation", "stoicism", "goal", "growth", "decline", "winner", "rating", "review", "time", "thinking", "idea",
    "creativity", "process", "strategy", "leader", "success", "safety", "infrastructure", "storage", "remote_work",
    "addiction", "new", "magic", "trending", "game", "adventure", "real_estate", "city", "office", "ocean", "medicine",
    "anatomy", "disease", "dental", "pharmacy", "astronomy", "geology", "archaeology", "engineering", "tools", "garden",
}


def P(pid: str, tags: str, build: Callable[[], List[str]], scope: str = "") -> None:
    """Register a prop: id, space-separated niche tags, builder returning SVG elements on a 256x256 canvas."""
    if pid in _SEEN:
        raise ValueError(f"duplicate prop id {pid}")
    _SEEN.add(pid)
    tl = [t for t in tags.split() if t]
    bad = [t for t in tl if not t.replace("_", "").isalnum() or t != t.lower()]
    if bad:
        raise ValueError(f"{pid}: malformed tags {bad}")
    sc = scope or ("global" if "general" in tl else "specific")
    PROPS.append({"id": pid, "tags": [t for t in tl if t != "general"] or ["general"], "scope": sc, "build": build})
