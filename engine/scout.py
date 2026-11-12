#!/usr/bin/env python3
"""yt-dlp outlier scout: videos whose views >= 3.0x their channel's median views.

CLI: python3 engine/scout.py --query "stoicism" --channel https://youtube.com/@x --niche stoicism --limit 30
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

import common

log = common.log
MIN_MULTIPLIER = 3.0


def _ydl(opts: Dict[str, Any]):
    import yt_dlp  # lazy: not installed in CI sandboxes
    base = {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True,
            "extract_flat": "in_playlist", "js_runtimes": {"node": {}}}
    base.update(opts)
    return yt_dlp.YoutubeDL(base)


def normalize_entry(e: Dict[str, Any], channel_hint: str = "") -> Optional[Dict[str, Any]]:
    vid = e.get("id")
    views = e.get("view_count")
    if not vid or not isinstance(views, (int, float)) or views <= 0:
        return None
    thumbs = e.get("thumbnails") or []
    return {
        "video_id": vid,
        "title": e.get("title") or "",
        "channel": e.get("channel") or e.get("uploader") or channel_hint or "unknown",
        "channel_url": e.get("channel_url") or e.get("uploader_url") or "",
        "views": int(views),
        "duration_sec": float(e.get("duration") or 0),
        "upload_date": e.get("upload_date") or "",
        "thumbnail": (thumbs[-1].get("url") if thumbs else e.get("thumbnail")) or "",
        "url": e.get("webpage_url") or e.get("url") or f"https://www.youtube.com/watch?v={vid}",
    }


def fetch_channel_videos(channel_url: str, limit: int = 30) -> List[Dict[str, Any]]:
    url = channel_url.rstrip("/")
    if not url.endswith(("/videos", "/shorts")):
        url += "/videos"
    with _ydl({"playlistend": limit}) as ydl:
        info = ydl.extract_info(url, download=False) or {}
    hint = info.get("channel") or info.get("uploader") or info.get("title") or channel_url
    out = []
    for e in info.get("entries") or []:
        n = normalize_entry(e or {}, hint)
        if n:
            n["channel_url"] = n["channel_url"] or channel_url
            out.append(n)
    return out


def fetch_search(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    with _ydl({}) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False) or {}
    return [n for e in (info.get("entries") or []) if (n := normalize_entry(e or {}))]


def compute_outliers(entries: Iterable[Dict[str, Any]], min_multiplier: float = MIN_MULTIPLIER,
                     min_sample: int = 5, min_duration: float = 0.0,
                     max_duration: float = 1e9) -> List[Dict[str, Any]]:
    """Group by channel, compare each video's views to the channel median. Pure function."""
    by_channel: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for e in entries:
        by_channel[e.get("channel_url") or e.get("channel") or "unknown"].append(e)
    result: List[Dict[str, Any]] = []
    for _, vids in by_channel.items():
        if len(vids) < min_sample:
            continue
        median = statistics.median(v["views"] for v in vids)
        if median <= 0:
            continue
        for v in vids:
            mult = v["views"] / median
            dur = v.get("duration_sec", 0)
            if mult >= min_multiplier and (not dur or min_duration <= dur <= max_duration):
                result.append({**v, "channel_median_views": int(median), "outlier_multiplier": round(mult, 2)})
    result.sort(key=lambda r: r["outlier_multiplier"], reverse=True)
    return result


def scout(queries: Iterable[str] = (), channels: Iterable[str] = (), niche: str = "general",
          min_multiplier: float = MIN_MULTIPLIER, per_channel: int = 30, max_channels: int = 8,
          min_duration: float = 20, max_duration: float = 1200) -> List[Dict[str, Any]]:
    """Crawl channels (and channels surfaced by searches), return outliers tagged with `niche`."""
    chan_urls: List[str] = list(channels)
    for q in queries:
        try:
            for r in fetch_search(q, 15):
                if r["channel_url"] and r["channel_url"] not in chan_urls:
                    chan_urls.append(r["channel_url"])
        except Exception as e:  # noqa: BLE001
            log.warning("search %r failed: %s", q, e)
    entries: List[Dict[str, Any]] = []
    for cu in chan_urls[:max_channels]:
        try:
            entries.extend(fetch_channel_videos(cu, per_channel))
        except Exception as e:  # noqa: BLE001
            log.warning("channel %s failed: %s", cu, e)
    outliers = compute_outliers(entries, min_multiplier, min_duration=min_duration, max_duration=max_duration)
    for o in outliers:
        o["niche"] = niche
    save_scout(outliers)
    return outliers


def save_scout(outliers: List[Dict[str, Any]]) -> None:
    p = common.cache_dir() / "scout" / "latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"updated_at_utc": common.utc_now_iso(), "outliers": outliers}, indent=2),
                 encoding="utf-8")


def load_scout() -> List[Dict[str, Any]]:
    p = common.cache_dir() / "scout" / "latest.json"
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("outliers", [])


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", action="append", default=[])
    ap.add_argument("--channel", action="append", default=[])
    ap.add_argument("--niche", default="general")
    ap.add_argument("--min-multiplier", type=float, default=MIN_MULTIPLIER)
    ap.add_argument("--limit", type=int, default=30)
    a = ap.parse_args(argv)
    common.ensure_dirs()
    out = scout(a.query, a.channel, a.niche, a.min_multiplier, a.limit)
    print(json.dumps(out[:20], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
