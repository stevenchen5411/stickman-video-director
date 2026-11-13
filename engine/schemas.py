#!/usr/bin/env python3
"""Pydantic v2 schemas for Stickman Video Director.

Single source of truth for:
  * providers.json          (ProvidersFile)
  * library_index.json      (LibraryIndex)
  * analysis_package.json   (AnalysisPackage)

CLI:
  python3 engine/schemas.py --validate-library [PATH_TO_LIBRARY_DIR]
  python3 engine/schemas.py --validate-package PATH [--library DIR]
  python3 engine/schemas.py --validate-providers PATH
  python3 engine/schemas.py --export-schemas OUT_DIR
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1.0"

CATEGORIES: List[str] = [
    "01_characters",
    "02_poses",
    "03_expressions",
    "04_motions",
    "05_scenes",
    "06_props",
    "07_widgets",
    "08_overlays",
    "09_transitions",
    "10_caption_styles",
    "11_themes",
    "12_voices",
    "13_bgm",
    "14_sfx",
]
Category = Literal[
    "01_characters", "02_poses", "03_expressions", "04_motions", "05_scenes",
    "06_props", "07_widgets", "08_overlays", "09_transitions", "10_caption_styles",
    "11_themes", "12_voices", "13_bgm", "14_sfx",
]

GEMINI_VOICES = ["Charon", "Puck", "Fenrir", "Aoede", "Kore", "Zephyr", "Leda", "Orus", "Callirrhoe", "Autonoe", "Enceladus",
                 "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar", "Alnilam",
                 "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"]

# Post-breath pause presets (ms)
PAUSE_FAST_HOOK_MS = 80
PAUSE_SENTENCE_MS = 240
PAUSE_DRAMATIC_MS = 450

# Anti-hallucination gate: minimum share of beats carrying visual motion
MIN_VISUAL_ACTIVITY_PCT = 75.0
# Perceptual-hash similarity at/above which a forged asset counts as a duplicate
PHASH_DEDUP_THRESHOLD = 0.85

_STAGE_DIRECTION_RE = re.compile(r"\[[^\]]*\]|\*[^*]+\*")


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ---------------------------------------------------------------------------
# A. providers.json
# ---------------------------------------------------------------------------
ProviderName = Literal["claude", "gemini", "chatgpt"]


class ClaudeProvider(_Base):
    enabled: bool = True
    auth_mode: Literal["oauth_session", "api_key", "cookie_session"] = "oauth_session"
    endpoint: Optional[str] = None
    access_token: Optional[str] = None
    api_key: Optional[str] = None
    cookies: Dict[str, str] = Field(default_factory=dict)
    user_agent: Optional[str] = None
    expires_at_utc: Optional[datetime] = None
    cooldown_until_utc: Optional[datetime] = None


class GeminiProvider(_Base):
    enabled: bool = True
    auth_mode: Literal["api_key", "oauth", "api_key_and_oauth"] = "api_key_and_oauth"
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    tts_model: str = "gemini-3.8-flash-tts"
    director_model: str = "gemini-3.8-pro"
    expires_at_utc: Optional[datetime] = None
    cooldown_until_utc: Optional[datetime] = None


class ChatGPTProvider(_Base):
    enabled: bool = False
    auth_mode: Literal["oauth_pkce", "api_key", "cookie_session"] = "oauth_pkce"
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    cookies: Dict[str, str] = Field(default_factory=dict)
    user_agent: Optional[str] = None
    expires_at_utc: Optional[datetime] = None
    cooldown_until_utc: Optional[datetime] = None


class ProviderSet(_Base):
    claude: ClaudeProvider = Field(default_factory=ClaudeProvider)
    gemini: GeminiProvider = Field(default_factory=GeminiProvider)
    chatgpt: ChatGPTProvider = Field(default_factory=ChatGPTProvider)


class ProvidersFile(_Base):
    schema_version: str = SCHEMA_VERSION
    failover_order: List[ProviderName] = Field(default_factory=lambda: ["claude", "gemini", "chatgpt"])
    providers: ProviderSet = Field(default_factory=ProviderSet)

    @field_validator("failover_order")
    @classmethod
    def _unique_order(cls, v: List[str]) -> List[str]:
        if len(set(v)) != len(v):
            raise ValueError("failover_order must not contain duplicates")
        return v

    def active_order(self, now: Optional[datetime] = None) -> List[str]:
        """Enabled providers in failover order, skipping those still in cooldown."""
        now = now or datetime.now().astimezone()
        out: List[str] = []
        for name in self.failover_order:
            p = getattr(self.providers, name)
            if not p.enabled:
                continue
            cd = p.cooldown_until_utc
            if cd is not None:
                if cd.tzinfo is None:
                    cd = cd.astimezone()
                if cd > now:
                    continue
            out.append(name)
        return out


# ---------------------------------------------------------------------------
# B. library_index.json
# ---------------------------------------------------------------------------
class LibraryAsset(_Base):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_]*$")
    category: Category
    scope: Literal["global", "specific"] = "global"
    niche_tags: List[str] = Field(default_factory=list)
    file_path: str
    thumb_path: Optional[str] = None
    preview_path: Optional[str] = None      # animated preview (WebP) for moving assets
    default_voice_id: Optional[str] = None
    preview_audio_path: Optional[str] = None
    gemini_voice_name: Optional[str] = None
    usage_count: int = Field(default=0, ge=0)
    perceptual_hash: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _path_in_category(self) -> "LibraryAsset":
        if not self.file_path.startswith(self.category + "/"):
            raise ValueError(f"file_path '{self.file_path}' must live under '{self.category}/'")
        if ".." in Path(self.file_path).parts:
            raise ValueError("file_path must not contain '..'")
        return self


class LibraryIndex(_Base):
    schema_version: str = SCHEMA_VERSION
    updated_at_utc: datetime
    assets: List[LibraryAsset] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> "LibraryIndex":
        seen: set = set()
        for a in self.assets:
            if a.id in seen:
                raise ValueError(f"duplicate asset id: {a.id}")
            seen.add(a.id)
        return self

    def get(self, asset_id: str, category: Optional[str] = None) -> Optional[LibraryAsset]:
        key = (id(self.assets), len(self.assets))
        if self.__dict__.get("_id_key") != key:   # O(1) lookups; rebuilt when the asset list is replaced or grows
            self.__dict__["_id_map"] = {a.id: a for a in self.assets}
            self.__dict__["_id_key"] = key
        a = self.__dict__["_id_map"].get(asset_id)
        return a if (a is not None and (category is None or a.category == category)) else None

    def by_category(self, category: str) -> List[LibraryAsset]:
        return [a for a in self.assets if a.category == category]

    def categories_present(self) -> List[str]:
        present = {a.category for a in self.assets}
        return [c for c in CATEGORIES if c in present]


# ---------------------------------------------------------------------------
# C. analysis_package.json
# ---------------------------------------------------------------------------
PackageStatus = Literal["draft", "ready_to_generate", "rendering", "rendered", "failed"]


class SourceViralVideo(_Base):
    video_id: str
    channel: str
    outlier_multiplier: float = Field(ge=0)
    niche: str
    video_md_path: str


class RenderConfig(_Base):
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "9:16"
    theme_id: str
    caption_style_id: str
    bgm_id: str


class ViralPackaging(_Base):
    title_variants: List[str] = Field(min_length=3, max_length=3)
    cover_scene_id: str
    cover_text_hook: str


class QualityAudit(_Base):
    estimated_duration_sec: float = Field(ge=0)
    avg_beat_sec: float = Field(ge=0)
    visual_activity_pct: float = Field(ge=0, le=100)
    auto_repaired_scenes: List[str] = Field(default_factory=list)
    passed: bool

    @model_validator(mode="after")
    def _passed_matches_gate(self) -> "QualityAudit":
        if self.passed and self.visual_activity_pct < MIN_VISUAL_ACTIVITY_PCT:
            raise ValueError(
                f"passed=true but visual_activity_pct {self.visual_activity_pct} < {MIN_VISUAL_ACTIVITY_PCT}"
            )
        return self


class SourceShotRef(_Base):
    shot_id: str
    frame_path: str
    original_duration_sec: float = Field(gt=0)


class SceneCharacter(_Base):
    character_id: str
    pose_id: str
    expression_id: str
    motion_id: Optional[str] = None


class SceneEnvironment(_Base):
    scene_id: str
    transition_in_id: Optional[str] = None


class FallbackVisualAid(_Base):
    type: Literal["callout_card", "chart_bar"]
    title: str
    subtitle: Optional[str] = None
    values: Optional[List[float]] = None
    labels: Optional[List[str]] = None


class VisualAid(_Base):
    type: Literal["library_prop", "widget", "overlay_only", "callout_card", "chart_bar"] = "library_prop"
    prop_id: Optional[str] = None
    widget_id: Optional[str] = None
    overlay_id: Optional[str] = None
    fallback_visual_aid: FallbackVisualAid


class EmphasisWord(_Base):
    word: str
    stress: str
    trigger_sfx: Optional[str] = None


class Prosody(_Base):
    acting_direction: str
    pace_multiplier: float = Field(default=1.0, ge=0.5, le=2.0)
    emphasis_words: List[EmphasisWord] = Field(default_factory=list)
    post_breath_pause_ms: int = Field(default=PAUSE_SENTENCE_MS, ge=0, le=2000)
    bgm_drop_on_climax: bool = False


class Narration(_Base):
    character_id: str
    voice_profile_id: str
    text: str = Field(min_length=1)
    prosody: Prosody

    @field_validator("text")
    @classmethod
    def _verbatim_only(cls, v: str) -> str:
        if _STAGE_DIRECTION_RE.search(v):
            raise ValueError("narration text must be verbatim speech: put stage directions in prosody.acting_direction")
        return v


MAX_SPEECH_WORDS = 14


class Speech(_Base):
    """A short in-character line the stickman says himself: speech bubble + his own voice + lip-sync.

    The narrator keeps telling the story as voice-over; this is the character reacting, asking or joking.
    """
    text: str = Field(min_length=1, max_length=100)
    voice_profile_id: Optional[str] = None      # library voice id or Gemini voice name; default: contrasts the narrator
    expression_id: Optional[str] = None         # face while he talks (library 03_expressions)
    acting_direction: str = ""
    placement: Literal["before", "after"] = "after"   # relative to the narration inside the scene

    @field_validator("text")
    @classmethod
    def _short_and_verbatim(cls, v: str) -> str:
        if _STAGE_DIRECTION_RE.search(v):
            raise ValueError("speech text must be verbatim speech: put stage directions in acting_direction")
        if len(v.split()) > MAX_SPEECH_WORDS:
            raise ValueError(f"speech line too long ({len(v.split())} words, max {MAX_SPEECH_WORDS})")
        return v


class Scene(_Base):
    id: str
    source_shot_ref: SourceShotRef
    character: SceneCharacter
    environment: SceneEnvironment
    visual_aid: VisualAid
    narration: Narration
    speech: Optional[Speech] = None

    @property
    def has_motion(self) -> bool:
        return bool(self.character.motion_id or self.visual_aid.overlay_id)


class AnalysisPackage(_Base):
    package_id: str = Field(pattern=r"^[A-Za-z0-9_\-]+$")
    status: PackageStatus = "draft"
    source_viral_video: SourceViralVideo
    render_config: RenderConfig
    viral_packaging: ViralPackaging
    quality_audit: QualityAudit
    scenes: List[Scene] = Field(min_length=1)

    @model_validator(mode="after")
    def _cross_checks(self) -> "AnalysisPackage":
        ids = [s.id for s in self.scenes]
        if len(set(ids)) != len(ids):
            raise ValueError("scene ids must be unique")
        if self.viral_packaging.cover_scene_id not in ids:
            raise ValueError(f"cover_scene_id '{self.viral_packaging.cover_scene_id}' not in scenes")
        unknown = [s for s in self.quality_audit.auto_repaired_scenes if s not in ids]
        if unknown:
            raise ValueError(f"auto_repaired_scenes reference unknown scenes: {unknown}")
        if self.status == "ready_to_generate" and not self.quality_audit.passed:
            raise ValueError("status 'ready_to_generate' requires quality_audit.passed == true")
        return self

    def missing_library_refs(self, index: LibraryIndex) -> List[str]:
        """Return 'category:id' for every library reference the index cannot satisfy."""
        missing: List[str] = []

        def need(category: str, asset_id: Optional[str]) -> None:
            if asset_id and index.get(asset_id, category) is None:
                missing.append(f"{category}:{asset_id}")

        rc = self.render_config
        need("11_themes", rc.theme_id)
        need("10_caption_styles", rc.caption_style_id)
        need("13_bgm", rc.bgm_id)
        for s in self.scenes:
            need("01_characters", s.character.character_id)
            need("02_poses", s.character.pose_id)
            need("03_expressions", s.character.expression_id)
            need("04_motions", s.character.motion_id)
            need("05_scenes", s.environment.scene_id)
            need("09_transitions", s.environment.transition_in_id)
            need("06_props", s.visual_aid.prop_id)
            need("07_widgets", s.visual_aid.widget_id)
            need("08_overlays", s.visual_aid.overlay_id)
            need("12_voices", s.narration.voice_profile_id)
            if s.speech:
                need("03_expressions", s.speech.expression_id)
            for e in s.narration.prosody.emphasis_words:
                need("14_sfx", e.trigger_sfx)
        return sorted(set(missing))


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------
def load_json(path: os.PathLike | str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: os.PathLike | str, data: BaseModel | Any) -> None:
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json", exclude_none=False)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, p)


def load_library_index(library_dir: os.PathLike | str) -> LibraryIndex:
    return LibraryIndex.model_validate(load_json(Path(library_dir) / "library_index.json"))


def load_package(path: os.PathLike | str) -> AnalysisPackage:
    return AnalysisPackage.model_validate(load_json(path))


def load_providers(path: os.PathLike | str) -> ProvidersFile:
    return ProvidersFile.model_validate(load_json(path))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _default_library() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "library"


def check_library_files(library_dir: Path, index: LibraryIndex) -> List[str]:
    """Return problems: missing asset files / missing audio previews. Thumbs are checked separately."""
    problems: List[str] = []
    for a in index.assets:
        if not (library_dir / a.file_path).is_file():
            problems.append(f"missing file: {a.file_path}")
        if a.preview_audio_path and not (library_dir / a.preview_audio_path).is_file():
            problems.append(f"missing preview audio: {a.preview_audio_path}")
    return problems


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validate-library", nargs="?", const="", metavar="DIR")
    ap.add_argument("--validate-package", metavar="PATH")
    ap.add_argument("--validate-providers", metavar="PATH")
    ap.add_argument("--library", metavar="DIR", help="library dir for cross-reference checks")
    ap.add_argument("--export-schemas", metavar="OUT_DIR")
    args = ap.parse_args(argv)
    rc = 0
    did = False

    if args.validate_library is not None:
        did = True
        lib = Path(args.validate_library) if args.validate_library else _default_library()
        idx = load_library_index(lib)
        problems = check_library_files(lib, idx)
        absent = [c for c in CATEGORIES if c not in idx.categories_present()]
        if absent:
            problems.append(f"categories with no assets: {absent}")
        print(f"library OK: {len(idx.assets)} assets across {len(idx.categories_present())}/14 categories")
        for p in problems:
            print("  PROBLEM:", p)
        rc |= 1 if problems else 0

    if args.validate_package:
        did = True
        pkg = load_package(args.validate_package)
        print(f"package OK: {pkg.package_id} ({len(pkg.scenes)} scenes, status={pkg.status})")
        if args.library:
            miss = pkg.missing_library_refs(load_library_index(args.library))
            if miss:
                print("  missing library refs:", ", ".join(miss))
                rc |= 1

    if args.validate_providers:
        did = True
        prov = load_providers(args.validate_providers)
        print(f"providers OK: active order {prov.active_order()}")

    if args.export_schemas:
        did = True
        out = Path(args.export_schemas)
        out.mkdir(parents=True, exist_ok=True)
        for name, model in (
            ("providers.schema.json", ProvidersFile),
            ("library_index.schema.json", LibraryIndex),
            ("analysis_package.schema.json", AnalysisPackage),
        ):
            save_json(out / name, model.model_json_schema())
        print(f"schemas written to {out}")

    if not did:
        ap.print_help()
    return rc


if __name__ == "__main__":
    sys.exit(main())
