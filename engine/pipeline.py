#!/usr/bin/env python3
"""Autonomous Phase-1 orchestration (no FastAPI dependency, so it is unit-testable and CLI-runnable).

scout -> curator gap report -> (limited) forge of missing assets -> per outlier: forensics -> director (remix,
voice casting, prosody) -> forge missing refs -> audit/auto-repair -> queue/<package_id>.json

CLI: python3 engine/pipeline.py --niche stoicism --query "stoicism" --channel https://youtube.com/@x --max 3
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import common
import schemas

log = common.log
Logger = Callable[[str], None]


def queued_video_ids() -> set:
    out = set()
    for p in common.queue_dir().glob("pkg_*.json"):
        try:
            out.add(json.loads(p.read_text(encoding="utf-8"))["source_viral_video"]["video_id"])
        except Exception:  # noqa: BLE001
            continue
    return out


def list_queue() -> List[Dict[str, Any]]:
    items = []
    for p in sorted(common.queue_dir().glob("pkg_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            items.append({"package_id": d["package_id"], "status": d["status"],
                          "title": d["viral_packaging"]["title_variants"][0],
                          "niche": d["source_viral_video"]["niche"],
                          "outlier_multiplier": d["source_viral_video"]["outlier_multiplier"],
                          "scenes": len(d["scenes"]), "duration_sec": d["quality_audit"]["estimated_duration_sec"],
                          "visual_activity_pct": d["quality_audit"]["visual_activity_pct"],
                          "passed": d["quality_audit"]["passed"], "path": str(p)})
        except Exception as e:  # noqa: BLE001
            log.warning("bad queue file %s: %s", p.name, e)
    return items


def load_queued(package_id: str) -> schemas.AnalysisPackage:
    return schemas.load_package(common.queue_dir() / f"{common.safe_id(package_id)}.json")


def run_auto(queries: List[str], channels: List[str], niche: str, max_packages: int = 3,
             min_multiplier: float = 3.0, offline: bool = False, max_forge: int = 3,
             say: Logger = print) -> Dict[str, Any]:
    import curator
    import director
    import forge
    import scout

    common.ensure_dirs()
    say(f"scouting niche '{niche}' (>= {min_multiplier}x outliers)")
    outliers = scout.scout(queries, channels, niche, min_multiplier)
    say(f"{len(outliers)} outlier videos found")

    report = curator.curate(outliers, use_ai=not offline)
    forged = []
    for req in [r for r in report["requests"] if r["scope"] == "specific"][:max_forge]:
        say(f"forging {req['category']}:{req['id']}")
        forged.append(forge.forge_asset(req["category"], req["id"], req["brief"], req["scope"], req["niche_tags"],
                                        use_ai=not offline))

    done = queued_video_ids()
    queued, failed = [], []
    for o in outliers:
        if len(queued) >= max_packages:
            break
        if o["video_id"] in done:
            continue
        say(f"directing {o['video_id']} ({o['outlier_multiplier']}x, {o['channel']})")
        try:
            pkg = director.direct(o["video_id"], source=o, offline=offline)
            queued.append({"package_id": pkg.package_id, "status": pkg.status, "video_id": o["video_id"]})
        except Exception as e:  # noqa: BLE001 - one bad video must not stop the batch
            log.exception("director failed for %s", o["video_id"])
            failed.append({"video_id": o["video_id"], "error": str(e)[:200]})
            say(f"  failed: {str(e)[:120]}")
    return {"outliers": len(outliers), "queued": queued, "failed": failed, "forged": forged,
            "gaps": {"global": len(report["global_gaps"]), "specific": len(report["specific_gaps"])}}


def main(argv: Optional[List[str]] = None) -> int:
    common.setup_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--niche", default="general")
    ap.add_argument("--query", action="append", default=[])
    ap.add_argument("--channel", action="append", default=[])
    ap.add_argument("--max", type=int, default=3)
    ap.add_argument("--min-multiplier", type=float, default=3.0)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args(argv)
    print(json.dumps(run_auto(a.query, a.channel, a.niche, a.max, a.min_multiplier, a.offline), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
