#!/usr/bin/env python3
"""Shared helpers: paths (Termux shared storage), temp dirs, subprocess, ids, logging."""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

log = logging.getLogger("stickman")

ABS_SHARED = Path("/storage/emulated/0/StickmanDirector")
SUBDIRS = ("config", "cache", "queue", "renders", "assets/library")
_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def setup_logging(level: int = logging.INFO) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def tmpdir() -> Path:
    """Writable temp dir. Never hardcodes /tmp (unwritable on Android): honours TMPDIR, then $PREFIX/tmp."""
    base = os.environ.get("TMPDIR")
    if not base and os.environ.get("PREFIX"):
        base = os.path.join(os.environ["PREFIX"], "tmp")
    p = Path(base) if base else Path(tempfile.gettempdir())
    p.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(p)
    return p


def repo_root() -> Path:
    env = os.environ.get("STICKMAN_REPO")
    return Path(env) if env else Path(__file__).resolve().parent.parent


def home() -> Path:
    """Shared storage root. Order: $STICKMAN_HOME, ~/storage/shared/StickmanDirector,
    /storage/emulated/0/StickmanDirector, then <repo>/.stickman_home (dev / CI)."""
    env = os.environ.get("STICKMAN_HOME")
    if env:
        return Path(env)
    termux = Path.home() / "storage" / "shared"
    if termux.is_dir():
        return termux / "StickmanDirector"
    if ABS_SHARED.parent.is_dir():
        return ABS_SHARED
    return repo_root() / ".stickman_home"


def ensure_dirs() -> Path:
    h = home()
    for sub in SUBDIRS:
        (h / sub).mkdir(parents=True, exist_ok=True)
    return h


def config_dir() -> Path:
    return home() / "config"


def queue_dir() -> Path:
    return home() / "queue"


def renders_dir() -> Path:
    return home() / "renders"


def cache_dir(video_id: Optional[str] = None) -> Path:
    base = home() / "cache"
    if video_id is None:
        return base
    return base / safe_id(video_id)


def library_dir() -> Path:
    env = os.environ.get("STICKMAN_LIBRARY")
    if env:
        return Path(env)
    shared = home() / "assets" / "library"
    if (shared / "library_index.json").is_file():
        return shared
    return repo_root() / "assets" / "library"


def safe_id(value: str) -> str:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise ValueError(f"invalid id: {value!r}")
    return value


def slugify(text: str, max_len: int = 24) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (s or "x")[:max_len].strip("_") or "x"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def which(name: str) -> Optional[str]:
    return shutil.which(name)


def ffmpeg_bin() -> str:
    p = which("ffmpeg")
    if not p:
        raise RuntimeError("ffmpeg not found (pkg install ffmpeg)")
    return p


def run(cmd: Sequence[str], timeout: Optional[float] = None, check: bool = True,
        input: Optional[bytes] = None) -> subprocess.CompletedProcess:
    log.debug("run: %s", " ".join(map(str, cmd)))
    cp = subprocess.run(list(map(str, cmd)), capture_output=True, timeout=timeout, input=input)
    if check and cp.returncode != 0:
        tail = cp.stderr.decode("utf-8", "replace")[-800:]
        raise RuntimeError(f"command failed ({cp.returncode}): {' '.join(map(str, cmd[:3]))} ...\n{tail}")
    return cp


def probe_duration(path: os.PathLike | str) -> float:
    cp = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)])
    return float(cp.stdout.decode().strip() or 0.0)


def have_module(name: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def chunks(seq: List, n: int):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]
