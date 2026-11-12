#!/usr/bin/env python3
"""Shot-cut forensics: download 480p source, transcript, shot cuts, per-shot midpoint frames, VIDEO.md.

Cuts come from JuneYaooo/rea-video (`rea-video decompose VIDEO -o DIR --no-packaging` -> breakdown.json).
rea-video does not emit VIDEO.md, so this module renders VIDEO.md itself from its cuts. If rea-video is
missing/fails/returns nothing, ffmpeg scene detection is used instead (cut_source recorded in shots.json).

Outputs under cache/<video_id>/: source.mp4, rea/, shots/shot_NN.jpg, shots.json, VIDEO.md.
CLI: python3 engine/forensics.py VIDEO_ID [--channel X] [--no-rea]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import common

log = common.log
MIN_SHOT_SEC = 0.6
SCENE_THRESHOLD = 0.30

_START_KEYS = ("start_sec", "start", "start_time", "t_start", "begin", "from", "t0")
_END_KEYS = ("end_sec", "end", "end_time", "t_end", "to", "t1")
_LIST_KEYS = ("shots", "segments", "cuts", "scenes", "timeline")


# --------------------------------------------------------------------------- pure helpers
def parse_scene_times(ffmpeg_stderr: str) -> List[float]:
    """Extract cut times (seconds) from ffmpeg `select=gt(scene,x),showinfo` stderr."""
    return sorted({round(float(m), 3) for m in re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", ffmpeg_stderr)})


def shots_from_cuts(cuts: List[float], duration: float, min_len: float = MIN_SHOT_SEC) -> List[Tuple[float, float]]:
    """Turn cut timestamps into contiguous (start, end) spans; merge spans shorter than min_len."""
    points = [0.0] + [c for c in sorted(cuts) if 0 < c < duration] + [duration]
    spans = [(a, b) for a, b in zip(points, points[1:]) if b - a > 1e-3]
    merged: List[Tuple[float, float]] = []
    for s, e in spans:
        if merged and (e - s) < min_len:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    if len(merged) > 1 and (merged[0][1] - merged[0][0]) < min_len:
        merged[1] = (merged[0][0], merged[1][1])
        merged.pop(0)
    return merged


def _first(d: Dict[str, Any], keys) -> Optional[float]:
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            m = re.fullmatch(r"(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)", v.strip())
            if m:
                h, mnt, s = m.groups()
                return int(h or 0) * 3600 + int(mnt) * 60 + float(s)
            try:
                return float(v)
            except ValueError:
                pass
    return None


def _find_shot_list(obj: Any) -> Optional[List[Dict[str, Any]]]:
    if isinstance(obj, dict):
        for k in _LIST_KEYS:
            v = obj.get(k)
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                if any(_first(x, _START_KEYS) is not None for x in v):
                    return v
        for v in obj.values():
            r = _find_shot_list(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_shot_list(v)
            if r:
                return r
    return None


def extract_shots_from_breakdown(data: Any, duration: float) -> List[Dict[str, Any]]:
    """Tolerant parser for rea-video breakdown.json (per-shot start/end + render type)."""
    items = _find_shot_list(data)
    if not items:
        return []
    starts = [(_first(x, _START_KEYS), _first(x, _END_KEYS), x) for x in items]
    starts = [t for t in starts if t[0] is not None]
    scale = 1.0
    peak = max([(s or 0) for s, _, _ in starts] + [(e or 0) for _, e, _ in starts] + [0])
    if duration and peak > duration * 20:  # looks like milliseconds
        scale = 0.001
    out = []
    for i, (s, e, x) in enumerate(starts):
        s = s * scale
        if e is None:
            e = starts[i + 1][0] * scale if i + 1 < len(starts) else duration
        else:
            e = e * scale
        out.append({"start": s, "end": min(e, duration) if duration else e,
                    "render_type": x.get("render_type") or x.get("type")})
    return [o for o in out if o["end"] - o["start"] > 1e-3]


def align_transcript(transcript: List[Dict[str, Any]], shots: List[Dict[str, Any]]) -> None:
    for sh in shots:
        sh["transcript"] = " ".join(
            t["text"].strip() for t in transcript
            if sh["start_sec"] <= t["start"] + t.get("duration", 0) / 2 < sh["end_sec"]).strip()


def render_video_md(meta: Dict[str, Any], shots: List[Dict[str, Any]]) -> str:
    lines = [f"# VIDEO.md — {meta.get('title') or meta['video_id']}", "",
             f"- video_id: `{meta['video_id']}`", f"- channel: {meta.get('channel', '')}",
             f"- duration_sec: {meta['duration_sec']:.2f}", f"- shots: {len(shots)}",
             f"- cut_source: {meta['cut_source']}", "", "## Shots", "",
             "| shot_id | start | end | dur | render_type | frame |", "|---|---|---|---|---|---|"]
    for s in shots:
        lines.append(f"| {s['shot_id']} | {s['start_sec']:.2f} | {s['end_sec']:.2f} | {s['duration_sec']:.2f} "
                     f"| {s.get('render_type') or '-'} | {Path(s['frame_path']).name} |")
    lines += ["", "## Per-shot transcript", ""]
    for s in shots:
        lines.append(f"### {s['shot_id']} ({s['start_sec']:.2f}s–{s['end_sec']:.2f}s)")
        lines.append(s.get("transcript") or "_(no speech)_")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- IO steps
def download_source(video_id: str, dest_dir: Path) -> Path:
    existing = sorted(dest_dir.glob("source.*"))
    existing = [p for p in existing if p.suffix not in (".part", ".ytdl")]
    if existing:
        return existing[0]
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "outtmpl": str(dest_dir / "source.%(ext)s"),
            "format": "best[height<=480][ext=mp4]/best[height<=480]/worst",
            "merge_output_format": "mp4", "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True) or {}
    files = [p for p in dest_dir.glob("source.*") if p.suffix not in (".part", ".ytdl")]
    if not files:
        raise RuntimeError("download produced no file")
    (dest_dir / "yt_meta.json").write_text(json.dumps({
        "title": info.get("title"), "channel": info.get("channel") or info.get("uploader"),
        "view_count": info.get("view_count")}), encoding="utf-8")
    return files[0]


def fetch_transcript(video_id: str, langs=("en",)) -> List[Dict[str, Any]]:
    from youtube_transcript_api import YouTubeTranscriptApi
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=list(langs))
        return [{"text": s.text, "start": float(s.start), "duration": float(s.duration)} for s in fetched]
    except AttributeError:  # youtube-transcript-api < 1.0
        raw = YouTubeTranscriptApi.get_transcript(video_id, languages=list(langs))
        return [{"text": r["text"], "start": float(r["start"]), "duration": float(r["duration"])} for r in raw]


def run_rea_video(src: Path, out_dir: Path, duration: float) -> List[Dict[str, Any]]:
    exe = common.which("rea-video")
    if not exe:
        return []
    try:
        common.run([exe, "decompose", str(src), "-o", str(out_dir), "--no-packaging"], timeout=1200)
        bj = out_dir / "breakdown.json"
        return extract_shots_from_breakdown(json.loads(bj.read_text(encoding="utf-8")), duration)
    except Exception as e:  # noqa: BLE001
        log.warning("rea-video failed (%s); falling back to ffmpeg scene detection", str(e)[:200])
        return []


def ffmpeg_scene_cuts(src: Path, threshold: float = SCENE_THRESHOLD) -> List[float]:
    cp = common.run([common.ffmpeg_bin(), "-hide_banner", "-i", str(src), "-vf",
                     f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"], check=False)
    return parse_scene_times(cp.stderr.decode("utf-8", "replace"))


def extract_frame(src: Path, t: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    common.run([common.ffmpeg_bin(), "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(src),
                "-frames:v", "1", "-vf", "scale=-2:480", "-q:v", "3", str(out)])


# --------------------------------------------------------------------------- main API
def analyze(video_id: str, channel: str = "", title: str = "", use_rea: bool = True,
            force: bool = False) -> Dict[str, Any]:
    """Full forensics for one video; cached. Returns the shots.json dict."""
    cdir = common.cache_dir(video_id)
    cdir.mkdir(parents=True, exist_ok=True)
    cached = cdir / "shots.json"
    if cached.is_file() and not force:
        return json.loads(cached.read_text(encoding="utf-8"))

    src = download_source(video_id, cdir)
    duration = common.probe_duration(src)
    try:
        transcript = fetch_transcript(video_id)
    except Exception as e:  # noqa: BLE001
        log.warning("no transcript for %s: %s", video_id, str(e)[:120])
        transcript = []

    cut_source = "rea-video"
    spans = run_rea_video(src, cdir / "rea", duration) if use_rea else []
    if not spans:
        cut_source = "ffmpeg-scene"
        spans = [{"start": s, "end": e, "render_type": None}
                 for s, e in shots_from_cuts(ffmpeg_scene_cuts(src), duration)]
    else:
        merged = shots_from_cuts([sp["start"] for sp in spans], duration)
        rtypes = {round(sp["start"], 2): sp.get("render_type") for sp in spans}
        spans = [{"start": s, "end": e, "render_type": rtypes.get(round(s, 2))} for s, e in merged]
    if not spans:
        spans = [{"start": 0.0, "end": duration, "render_type": None}]

    shots: List[Dict[str, Any]] = []
    for i, sp in enumerate(spans, 1):
        sid = f"shot_{i:02d}"
        mid = (sp["start"] + sp["end"]) / 2
        frame = cdir / "shots" / f"{sid}.jpg"
        extract_frame(src, mid, frame)
        shots.append({"shot_id": sid, "start_sec": round(sp["start"], 3), "end_sec": round(sp["end"], 3),
                      "duration_sec": round(sp["end"] - sp["start"], 3), "mid_sec": round(mid, 3),
                      "frame_path": str(frame), "render_type": sp.get("render_type")})
    align_transcript(transcript, shots)

    meta = {"video_id": video_id, "channel": channel, "title": title, "duration_sec": duration,
            "cut_source": cut_source, "source_path": str(src)}
    result = {**meta, "video_md_path": str(cdir / "VIDEO.md"), "transcript": transcript, "shots": shots}
    (cdir / "VIDEO.md").write_text(render_video_md(meta, shots), encoding="utf-8")
    cached.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def load(video_id: str) -> Dict[str, Any]:
    return json.loads((common.cache_dir(video_id) / "shots.json").read_text(encoding="utf-8"))


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video_id")
    ap.add_argument("--channel", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--no-rea", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    common.ensure_dirs()
    r = analyze(a.video_id, a.channel, a.title, use_rea=not a.no_rea, force=a.force)
    print(f"{r['video_id']}: {len(r['shots'])} shots via {r['cut_source']} -> {r['video_md_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
