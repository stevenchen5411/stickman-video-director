#!/usr/bin/env python3
"""Schema + seed-library tests (run: python3 -m pytest engine/tests)."""
import copy
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine"))

import schemas  # noqa: E402

LIB = ROOT / "assets" / "library"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_analysis_package.json"


def _pkg():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_library_has_all_14_categories_and_files():
    idx = schemas.load_library_index(LIB)
    assert idx.categories_present() == schemas.CATEGORIES
    assert schemas.check_library_files(LIB, idx) == []


def test_sfx_under_one_and_half_seconds():
    idx = schemas.load_library_index(LIB)
    for a in idx.by_category("14_sfx"):
        assert a.meta["duration_sec"] < 1.5, a.id


def test_sample_package_valid_and_resolves_against_library():
    pkg = schemas.AnalysisPackage.model_validate(_pkg())
    assert pkg.missing_library_refs(schemas.load_library_index(LIB)) == []


def test_narration_rejects_stage_directions():
    d = _pkg()
    d["scenes"][0]["narration"]["text"] = "[whispers] Every snooze"
    with pytest.raises(ValidationError):
        schemas.AnalysisPackage.model_validate(d)


def test_requires_three_titles_and_known_cover_scene():
    d = _pkg()
    d["viral_packaging"]["title_variants"] = d["viral_packaging"]["title_variants"][:2]
    with pytest.raises(ValidationError):
        schemas.AnalysisPackage.model_validate(d)
    d = _pkg()
    d["viral_packaging"]["cover_scene_id"] = "scene_99"
    with pytest.raises(ValidationError):
        schemas.AnalysisPackage.model_validate(d)


def test_audit_gate_and_fallback_required():
    d = _pkg()
    d["quality_audit"]["visual_activity_pct"] = 60
    with pytest.raises(ValidationError):
        schemas.AnalysisPackage.model_validate(d)
    d = _pkg()
    del d["scenes"][0]["visual_aid"]["fallback_visual_aid"]
    with pytest.raises(ValidationError):
        schemas.AnalysisPackage.model_validate(d)


def test_source_shot_ref_required():
    d = copy.deepcopy(_pkg())
    del d["scenes"][0]["source_shot_ref"]
    with pytest.raises(ValidationError):
        schemas.AnalysisPackage.model_validate(d)


def test_providers_defaults_and_failover():
    prov = schemas.ProvidersFile()
    assert prov.failover_order == ["claude", "gemini", "chatgpt"]
    assert prov.active_order() == ["claude", "gemini"]  # chatgpt disabled by default
    with pytest.raises(ValidationError):
        schemas.ProvidersFile(failover_order=["claude", "claude"])


def test_duplicate_library_ids_rejected():
    idx = json.loads((LIB / "library_index.json").read_text(encoding="utf-8"))
    idx["assets"].append(copy.deepcopy(idx["assets"][0]))
    with pytest.raises(ValidationError):
        schemas.LibraryIndex.model_validate(idx)
