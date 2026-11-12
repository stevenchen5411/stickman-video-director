#!/usr/bin/env python3
"""FastAPI daemon on 127.0.0.1:8765 (never binds to other interfaces).

Endpoints: GET /health, POST /pipeline/auto, GET /jobs[/{id}], GET /queue[/{package_id}], POST /forge,
POST /forge/rebuild-thumbs, POST /curate, POST /render/draft, GET /library.
Long work runs on a single background worker (jobs are serialized so Termux CPU/RAM is never oversubscribed).

Run: python3 -m uvicorn server:app --host 127.0.0.1 --port 8765   (from engine/)  or  python3 engine/server.py
"""
from __future__ import annotations

import hmac
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import common
import llm
import schemas

VERSION = "1.0.0"
HOST, PORT = "127.0.0.1", 8765
ID_PATTERN = r"^[A-Za-z0-9_\-]{1,64}$"

app = FastAPI(title="Stickman Director Engine", version=VERSION, docs_url=None, redoc_url=None, openapi_url=None)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="stickman-job")
_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


# --------------------------------------------------------------------------- token auth
# The Android app generates a random token and passes it to start_daemon.sh (env STICKMAN_TOKEN).
# When set, every endpoint except GET /health requires the X-Stickman-Token header. Unset = open (dev/tests).
def _token() -> str:
    return os.environ.get("STICKMAN_TOKEN", "")


def _token_ok(request: Request) -> bool:
    tok = _token()
    return (not tok) or hmac.compare_digest(request.headers.get("x-stickman-token", ""), tok)


@app.middleware("http")
async def token_gate(request: Request, call_next):
    if request.url.path != "/health" and not _token_ok(request):
        return JSONResponse({"detail": "invalid or missing X-Stickman-Token"}, status_code=401)
    return await call_next(request)


# --------------------------------------------------------------------------- jobs
def submit(kind: str, fn: Callable[[Callable[[str], None]], Any]) -> str:
    job_id = uuid.uuid4().hex[:12]
    job = {"id": job_id, "kind": kind, "status": "queued", "log": [], "result": None, "error": None,
           "created_at": common.utc_now_iso(), "finished_at": None}
    with _lock:
        _jobs[job_id] = job
        for old in sorted(_jobs.values(), key=lambda j: j["created_at"])[:-50]:   # keep the last 50
            if old["status"] in ("done", "failed"):
                _jobs.pop(old["id"], None)

    def say(msg: str) -> None:
        with _lock:
            job["log"].append(f"{time.strftime('%H:%M:%S')} {msg}")
            del job["log"][:-200]

    def runner() -> None:
        job["status"] = "running"
        try:
            job["result"] = fn(say)
            job["status"] = "done"
        except Exception as e:  # noqa: BLE001
            common.log.exception("job %s failed", job_id)
            job["error"], job["status"] = str(e)[:500], "failed"
        finally:
            job["finished_at"] = common.utc_now_iso()

    _executor.submit(runner)
    return job_id


# --------------------------------------------------------------------------- models
class AutoRequest(BaseModel):
    niche: str = Field("general", max_length=60)
    queries: List[str] = Field(default_factory=list, max_length=10)
    channels: List[str] = Field(default_factory=list, max_length=10)
    max_packages: int = Field(3, ge=1, le=10)
    min_multiplier: float = Field(3.0, ge=1.0, le=50.0)
    offline: bool = False


class ForgeRequest(BaseModel):
    category: str
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]{0,63}$")
    brief: str = Field("", max_length=300)
    scope: str = Field("global", pattern="^(global|specific)$")
    niche_tags: List[str] = Field(default_factory=lambda: ["general"], max_length=8)
    use_ai: bool = True


class CurateRequest(BaseModel):
    use_ai: bool = False


class RenderRequest(BaseModel):
    package_id: str = Field(pattern=ID_PATTERN)
    mode: str = Field("draft", pattern="^(draft|keyframes)$")
    placeholder_tts: Optional[bool] = None


# --------------------------------------------------------------------------- routes
def _writable(path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok")
        probe.unlink()
        return True
    except OSError:
        return False


@app.get("/health")
def health(request: Request) -> Dict[str, Any]:
    flags = {
        "python": True,
        "yt_dlp": common.have_module("yt_dlp"),
        "rea_video": common.which("rea-video") is not None,
        "pycairo": common.have_module("cairo"),
        "ffmpeg": common.which("ffmpeg") is not None,
        "shared_storage_writable": _writable(common.home()),
    }
    extra = {"cairosvg": common.have_module("cairosvg"), "google_genai": common.have_module("google.genai"),
             "youtube_transcript_api": common.have_module("youtube_transcript_api")}
    return {"status": "ok" if all(flags.values()) else "degraded", "version": VERSION, "flags": flags,
            "optional": extra, "ai_providers": llm.available(), "home": str(common.home()),
            "auth": {"required": bool(_token()), "ok": _token_ok(request)}}


class KeysRequest(BaseModel):
    keys: Dict[str, str] = Field(default_factory=dict)


@app.post("/config/keys")
def config_keys(req: KeysRequest) -> Dict[str, Any]:
    """Receive decrypted provider API keys from the Android app. Held in memory only."""
    return {"providers": llm.set_runtime_keys(req.keys)}


@app.post("/pipeline/auto")
def pipeline_auto(req: AutoRequest) -> Dict[str, str]:
    import pipeline
    return {"job_id": submit("pipeline.auto", lambda say: pipeline.run_auto(
        req.queries, req.channels, req.niche, req.max_packages, req.min_multiplier, req.offline, say=say))}


@app.get("/jobs")
def jobs() -> List[Dict[str, Any]]:
    with _lock:
        return [{k: j[k] for k in ("id", "kind", "status", "created_at", "finished_at", "error")} for j in _jobs.values()]


@app.get("/jobs/{job_id}")
def job(job_id: str) -> Dict[str, Any]:
    with _lock:
        j = _jobs.get(job_id)
    if not j:
        raise HTTPException(404, "unknown job")
    return j


@app.get("/queue")
def queue() -> List[Dict[str, Any]]:
    import pipeline
    return pipeline.list_queue()


@app.get("/queue/{package_id}")
def queue_item(package_id: str) -> Dict[str, Any]:
    import pipeline
    try:
        return pipeline.load_queued(package_id).model_dump(mode="json")
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "package not found")


@app.put("/queue/{package_id}")
def queue_save(package_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Validate + re-audit an edited package (storyboard editor), then save it atomically."""
    import audit
    try:
        path = common.queue_dir() / f"{common.safe_id(package_id)}.json"
    except ValueError:
        raise HTTPException(422, "bad package_id")
    if not path.is_file() or body.get("package_id") != package_id:
        raise HTTPException(404, "package not found or id mismatch")
    index = schemas.load_library_index(common.library_dir())
    try:
        d = audit.audit_dict(body, index)
        warnings = d.pop("_warnings", [])
        pkg = schemas.AnalysisPackage.model_validate(d)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(422, str(e)[:400])
    missing = pkg.missing_library_refs(index)
    if missing:
        raise HTTPException(422, f"unknown library refs: {missing[:5]}")
    schemas.save_json(path, pkg)
    return {"package_id": package_id, "status": pkg.status, "quality_audit": pkg.quality_audit.model_dump(mode="json"),
            "warnings": warnings}


@app.post("/forge")
def forge_asset(req: ForgeRequest) -> Dict[str, str]:
    if req.category not in schemas.CATEGORIES:
        raise HTTPException(422, "unknown category")
    import forge
    return {"job_id": submit("forge", lambda say: forge.forge_asset(
        req.category, req.id, req.brief, req.scope, req.niche_tags, use_ai=req.use_ai))}


@app.post("/forge/rebuild-thumbs")
def rebuild_thumbs() -> Dict[str, str]:
    import forge
    return {"job_id": submit("forge.rebuild_thumbs", lambda say: forge.rebuild_thumbs())}


@app.post("/curate")
def curate(req: CurateRequest) -> Dict[str, Any]:
    import curator
    return curator.curate(use_ai=req.use_ai)


@app.post("/render/draft")
def render_draft(req: RenderRequest) -> Dict[str, str]:
    import pipeline
    import render_cairo
    try:
        path = common.queue_dir() / f"{common.safe_id(req.package_id)}.json"
    except ValueError:
        raise HTTPException(422, "bad package_id")
    if not path.is_file():
        raise HTTPException(404, "package not found")
    return {"job_id": submit("render." + req.mode, lambda say: render_cairo.render_package(
        path, req.mode, common.renders_dir(), req.placeholder_tts,
        progress=lambda p: say(f"render {int(p * 100)}%") if int(p * 100) % 10 == 0 else None))}


@app.get("/library")
def library() -> Dict[str, Any]:
    return schemas.load_library_index(common.library_dir()).model_dump(mode="json")


def main() -> None:
    import uvicorn
    common.setup_logging()
    common.tmpdir()
    common.ensure_dirs()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
