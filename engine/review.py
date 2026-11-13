"""Review of forged assets: list pending, build a sync plan, mark approved, reject (delete)."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import common
import schemas

FILE_KEYS = ("file_path", "thumb_path", "preview_path", "preview_audio_path")


def is_pending(asset: schemas.LibraryAsset) -> bool:
    return asset.meta.get("review") == "pending"


def list_pending(lib: Optional[Path] = None) -> List[Dict[str, Any]]:
    lib = Path(lib) if lib else common.library_dir()
    index = schemas.load_library_index(lib)
    return [{"id": a.id, "category": a.category, "scope": a.scope, "niche_tags": a.niche_tags,
             "thumb_path": a.thumb_path, "file_path": a.file_path}
            for a in index.assets if is_pending(a)]


def used_by(asset_id: str, queue: Optional[Path] = None) -> List[str]:
    queue = Path(queue) if queue else common.queue_dir()
    out = []
    for p in sorted(queue.glob("pkg_*.json")):
        try:
            if f'"{asset_id}"' in p.read_text(encoding="utf-8"):
                out.append(p.stem)
        except OSError:
            pass
    return out


def _pending_entries(index: schemas.LibraryIndex, ids: List[str]) -> List[schemas.LibraryAsset]:
    found = {a.id: a for a in index.assets if is_pending(a)}
    missing = [i for i in ids if i not in found]
    if missing:
        raise ValueError(f"not pending: {missing}")
    return [found[i] for i in ids]


def _clean(entry: schemas.LibraryAsset) -> Dict[str, Any]:
    d = entry.model_dump(mode="json", exclude_none=True)
    meta = dict(d.get("meta") or {})
    meta.pop("review", None)
    d["meta"] = meta
    return d


def approve_plan(ids: List[str], repo_index: Dict[str, Any], lib: Optional[Path] = None) -> Dict[str, Any]:
    """Files to upload (repo-relative paths under assets/library) and the merged index for the repo."""
    lib = Path(lib) if lib else common.library_dir()
    index = schemas.load_library_index(lib)
    entries = _pending_entries(index, ids)
    merged = dict(repo_index)
    assets = {a["id"]: a for a in merged.get("assets", [])}
    files = []
    for e in entries:
        assets[e.id] = _clean(e)
        for k in FILE_KEYS:
            rel = getattr(e, k)
            if rel and (lib / rel).is_file():
                files.append({"path": rel, "b64": base64.b64encode((lib / rel).read_bytes()).decode()})
    merged["assets"] = list(assets.values())
    merged["updated_at_utc"] = index.updated_at_utc.isoformat()
    return {"files": files, "index": merged, "ids": ids}


def mark_approved(ids: List[str], lib: Optional[Path] = None) -> Dict[str, Any]:
    lib = Path(lib) if lib else common.library_dir()
    index = schemas.load_library_index(lib)
    for e in _pending_entries(index, ids):
        e.meta.pop("review", None)
    schemas.save_json(lib / "library_index.json", index)
    return {"approved": ids}


def reject(ids: List[str], lib: Optional[Path] = None, queue: Optional[Path] = None) -> Dict[str, Any]:
    lib = Path(lib) if lib else common.library_dir()
    index = schemas.load_library_index(lib)
    entries = _pending_entries(index, ids)
    blocked = {e.id: used_by(e.id, queue) for e in entries if used_by(e.id, queue)}
    if blocked:
        return {"rejected": [], "blocked": blocked}
    for e in entries:
        for k in FILE_KEYS:
            rel = getattr(e, k)
            if rel:
                (lib / rel).unlink(missing_ok=True)
    gone = {e.id for e in entries}
    index.assets = [a for a in index.assets if a.id not in gone]
    schemas.save_json(lib / "library_index.json", index)
    return {"rejected": sorted(gone), "blocked": {}}
