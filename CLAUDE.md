# Stickman Video Director — Claude Code operational memory

Repo: `stevenchen5411/stickman-video-director` (GitHub). Android package: `com.near.stickmandirector`.
Three-node pipeline: plain-Kotlin Android app  <->  Termux Python daemon (`127.0.0.1:8775`)  <->  GitHub Actions.
Read this file first on every turn; update the milestone checklist when a milestone is confirmed.

## 1. Split workflow (Termux `aarch64` vs GitHub Actions CI)

| Area | Where it is verified | How |
|---|---|---|
| `engine/` Python + `assets/` | **Locally in Termux** | `python3 -m py_compile`, `pytest`, FastAPI `/health`, `python3 engine/forge.py --rebuild-thumbs` (pycairo 256x256) |
| `android-app/` Kotlin/Gradle | **GitHub Actions only** | `git add . && git commit -m "..." && git push`, then `gh run watch` on `.github/workflows/build-apk.yml`; fix any CI compiler error immediately and push again |

- NEVER install the Android SDK or run `./gradlew assembleDebug` in Termux.
- Every time Kotlin/Gradle files change: commit, push, watch the run.

## 2. Termux rules

- Shebangs: `#!/usr/bin/env bash`, `#!/usr/bin/env python3`. Never `/bin/bash`, `/usr/bin/python3`.
- Never write to `/tmp`. Use `$TMPDIR` (fallback `$PREFIX/tmp`); in Python use `tempfile` after setting `TMPDIR`.
- Shared storage root: `/storage/emulated/0/StickmanDirector/` == `~/storage/shared/StickmanDirector/` (both must resolve).
  Subfolders: `config/` (providers.json), `cache/<video_id>/{VIDEO.md,shots/}`, `queue/` (analysis_package.json bundles), `renders/`, `assets/library/`.
- Code resolves the root via `STICKMAN_HOME` env if set, else `~/storage/shared/StickmanDirector`, else `/storage/emulated/0/StickmanDirector`.
- `engine/` modules are run as scripts (`python3 engine/<mod>.py`) and import siblings directly (`import schemas`).

## 3. Android rules (plain Kotlin)

- `targetSdk = 36`, `minSdk = 29`.
- 100% programmatic SDK views (`FrameLayout`, `LinearLayout`, `ScrollView`, `RecyclerView`, `GradientDrawable`, `TextView`, `ImageView`).
- ZERO XML layouts (only `AndroidManifest.xml` + minimal `res/values/strings.xml`). ZERO Jetpack Compose.
- Edge-to-edge via `ViewCompat.setOnApplyWindowInsetsListener`. `OnBackInvokedCallback` enabled ONLY while a sub-screen/modal sheet is open, disabled at tab root so predictive back works natively.
- Deps: OkHttp, WorkManager, androidx.browser (Custom Tabs), androidx.security:security-crypto, RecyclerView.

## 4. Engine contracts (keep consistent across modules)

- `engine/schemas.py` is the single source of truth: `ProvidersFile`, `LibraryIndex`, `AnalysisPackage`. Kotlin `DirectorModels.kt` mirrors it (`python3 engine/schemas.py --export-schemas DIR` writes JSON Schemas).
- Gemini TTS: `google-genai`, `genai.Client(http_options={"api_version": "v1beta"})`, `client.interactions.create(...)`, model `gemini-3.8-flash-tts`. Acting direction goes ONLY in `speech_metadata={"style": ...}`; `text` stays verbatim (schemas.py rejects `[stage directions]` in narration text). Voice Design via `client.voices` (`type="prompted"`, `store=True`).
- Forensics: `JuneYaooo/rea-video` (installed by `pip install git+https://github.com/JuneYaooo/rea-video`). Its README does not document the CLI or `VIDEO.md`; read its `docs/cli.md` in Milestone 2 before writing `forensics.py` and adapt (generate `VIDEO.md` + per-shot midpoint frames; fall back to ffmpeg scene detection if the CLI differs).
- Rendering: pycairo composites in RAM, raw `RGBA` frames pipe into FFmpeg stdin (`-f rawvideo -pix_fmt rgba`). Never write per-frame PNGs.
- `render_cairo.py` CLI: `--package PATH` + one of `--keyframes-only | --draft-480p | --hd-1080p60`, `--out DIR`. It runs audio-first (TTS -> audio_master -> frame count from real vocal timestamps -> video). `render-hd.yml` calls exactly this.
- Pause constants: 80 ms fast hook, 240 ms sentence, 450 ms dramatic beat. 15 ms cosine acrossfade, -48 dB room tone, SFX -12 dB, BGM sidechain -20 dB, `loudnorm=I=-14:TP=-1.0:LRA=7`.
- Library dedup threshold: 85% perceptual-hash similarity. Seed `perceptual_hash` values are content-SHA1 prefixes until `forge.py --rebuild-thumbs` replaces them with real pHashes.
- GitHub sync: assets/library is mirrored between shared storage and the repo. Cloud renders read the package from `queue/<package_id>.json` in the repo (pushed by the Android app via Contents API) and are triggered by `repository_dispatch` type `render-hd` (payload: `package_path`).
- Secrets for Actions: `GEMINI_API_KEY`. Releases: tag `render-<package_id>`, assets `<package_id>.mp4` + `<package_id>_cover.jpg`.

## 4a. Engine as built (Milestone 2)

- Extra modules beyond the original tree: `common.py` (paths/tmp/ffmpeg), `llm.py` (provider failover JSON client, stdlib HTTP), `pipeline.py` (autonomous Phase-1 orchestration, used by `/pipeline/auto`).
- AI credentials the engine can use: env `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`, or a plaintext `api_key` in `config/providers.json`. Values prefixed `enc_v1:` are Android-Keystore ciphertext and CANNOT be decrypted in Termux; OAuth-session/cookie providers are skipped by the engine. Open decision for M3: how the app hands usable keys to Termux (e.g. a `providers.runtime.json` the app writes, or env via RUN_COMMAND).
- Without any usable AI provider `director.py` produces `draft` packages from the transcript (never `ready_to_generate`); TTS falls back to a placeholder formant voice so drafts/keyframes still render.
- `rea-video` has no VIDEO.md output: `forensics.py` runs `rea-video decompose VIDEO -o DIR --no-packaging`, parses `breakdown.json` tolerantly, falls back to ffmpeg scene detection, and writes VIDEO.md + `shots.json` itself.
- `audio_master.py` computes the -20 dB BGM ducking as an explicit envelope from the voice track (exact depth), then FFmpeg does the voice chain, mix and two-pass `loudnorm`.
- Run (Termux): `python3 engine/forge.py --rebuild-thumbs`, `python3 -m pytest engine/tests -q`, daemon: `~/.stickman/start_daemon.sh` then `curl 127.0.0.1:8775/health`.
- Tests use `engine/tests/fake_cairo.py` only when real pycairo is missing; real pycairo is used automatically in Termux.

## 4b. Seed library formats

`python3 bootstrap/seed_assets.py` regenerates the 61 seed assets + `library_index.json` (idempotent). JSON assets carry a `format` key (`stickman_rig/v1`, `pose/v1`, `expression/v1`, `viseme_set/v1`, `motion/v1`, `layered_scene/v1` (normalized rect/circle/poly/line primitives in back/mid/ground), `widget/v1`, `overlay/v1`, `transition/v1`, `caption_style/v1`, `theme/v1`, `voice_persona/v1`). Theme colors are referenced as `theme.<key>`. Voice previews are synthetic placeholders. Thumbnails in `.thumbs/` are generated by `forge.py --rebuild-thumbs` (M2; needs pycairo, not available in the cloud sandbox).

## 5. Naming

The owner's username is `near`: new projects/repos/packages use `near`, not a personal first name. Package root is `com.near.stickmandirector`. The GitHub account that hosts this repo is `stevenchen5411` (explicit instruction).

## 4c. Android as built (Milestone 3)

- Toolchain: AGP 8.13.2, Gradle 8.14.3 (wrapper jar committed), Kotlin 2.2.20 via `org.jetbrains.kotlin.android`, jvmToolchain 17. AGP 9 deliberately avoided (built-in Kotlin incompatibility).
- Plain `android.app.Activity` + `Theme.DeviceDefault.NoActionBar` (no appcompat, no theme XML). Only XML: AndroidManifest + strings.xml. Cleartext allowed in the manifest for 127.0.0.1.
- Secrets: `SecureStore` (EncryptedSharedPreferences). `providers.json` is written with `enc_v1:` Keystore ciphertext (unreadable in Termux), so plaintext API keys are pushed to the daemon's memory via token-protected `POST /config/keys` (`llm.RUNTIME_KEYS`, never on disk).
- Daemon token: app generates it, passes it as arg 1 of `start_daemon.sh` (arg 2 `restart` replaces a running daemon). Server requires `X-Stickman-Token` on everything except `/health`; `/health.auth = {required, ok}`.
- Auth layers: RFC 8414 -> GitHub `auth_endpoints.json` -> WebView cookie sniffer -> API key. OAuth layers need a `client_id` (shipped null), so today they fall through to layers 3/4. Google blocks OAuth in WebViews and Custom Tab cookies are not shared with the WebView: Gemini should use an API key.
- GitHub: PAT only (no device flow). Gate unlocks only when AI >= 1 provider, daemon reachable with accepted token, and PAT has push on the repo.
- Back handling: `BackScope` registers `OnBackInvokedCallback` only while a sheet/sub-screen is open (API 33+); `onBackPressed` fallback below that.
- Unverified until CI: every Kotlin file (no SDK in the sandbox). `gh` auth was invalid in the sandbox, so nothing is pushed.

## 4d. Workspace UI as built (Milestone 4)

- `MainActivity` -> `ConnectGateScreen` -> `workspace/MainWorkspaceView` (bottom nav: Scout / Studio / Library / System). Sub-screens (`AnalysisDetailView`, `StoryboardEditorView`, `PlayerScreen`) stack over the tabs; sheets (`BottomSheet`) sit above them. `BackScope` owns back only while any of these is open.
- Studio: `GET /queue` list -> package detail (titles, audit, scenes). Edits go through `PUT /queue/{id}` (new endpoint: re-audit with `audit.audit_dict`, pydantic validate, reject unknown library refs, atomic save).
- Renders: draft = `POST /render/draft` job -> `renders/<id>_draft.mp4`; HD = push `queue/<id>.json` via Contents API -> `repository_dispatch render-hd` -> poll release `render-<id>` every 20 s (screen must stay open; "Fetch finished cloud render" resumes) -> `renders/<id>.mp4`.
- Library: `GET /library`, thumbnails read from shared storage `assets/library/.thumbs`, forge / rebuild-thumbs / curate via jobs.
- Reopening the gate from System uses `autoUnlock=false` so it does not bounce back.
- Unverified until CI: all Kotlin (29 files). Local check was brace balance + `Ui.*` symbol existence only.

## 4e. Claude web session (zero API key), as built

- UNOFFICIAL: uses claude.ai private endpoints with the user's own session cookie; may break or be blocked, and Anthropic's consumer terms restrict automated access outside the API. Best-effort fallback only.
- Sign-in: layer-3 WebView sniffer, then in-WebView `fetch('/api/organizations')` to verify the session (and let Cloudflare issue `cf_clearance`) BEFORE reporting "captured". Stores the full cookie jar, WebView user agent and `orgId` (written to providers.json as claude `endpoint`).
- Execution order in `engine/claude_web.py`: (1) Android bridge `127.0.0.1:8766/claude/complete` (hidden WebView in a foreground service = real Chromium TLS + live cookies, token `X-Stickman-Token`); (2) `curl_cffi` impersonate chrome with the synced cookie header + UA (`POST /config/sessions`, memory only); never raw urllib/requests to claude.ai.
- Failover (`llm.call_json`): 401/403 -> 30 min cooldown + `needs_refresh:claude` flag; 429 -> Retry-After cooldown; bridge/curl_cffi unavailable -> 2 min soft cooldown. Order comes from providers.json `failover_order` (claude, gemini, chatgpt). `/health` returns `ai_status` per provider and `claude_bridge`.
- App: `MainWorkspaceView` banner "Refresh Session" appears while `ai_status.claude == needs_refresh` (polled every 30 s); one tap reopens the sniffer, re-saves, restarts the bridge service, pushes the session.
- An API key, if present, still wins over the web session for Claude.

## 6. Milestone checklist

Milestones run sequentially; after each one, verify, summarize, and WAIT for the user's confirmation.

- [x] M1 (built + verified, awaiting user confirmation) Foundation, CI/CD, bootstrap, seed library (CLAUDE.md, workflows, auth_endpoints.json, setup_termux.sh, requirements.txt, schemas.py, 14-category seed assets + library_index.json)
- [x] M2 (built; verified in sandbox, awaiting Termux run + user confirmation) Autonomous Python engine (server, scout, forensics, director, curator, forge, audit, tts_expressive, audio_master, render_cairo) + `forge.py --rebuild-thumbs` + py_compile + pytest
- [x] M3 (written; NOT yet compiled: needs CI, see 4c) Android Gradle setup, gate, self-healing auth, bridges (build.gradle.kts, wrapper, manifest, DirectorModels, AuthSelfHealer, WebViewSnifferDialog, ProviderFailoverPool, TokenRefreshWorker, TermuxDiagnostics, TermuxClient, GitHubApiClient, ConnectGateScreen)
- [x] M4 (written; NOT yet compiled; CI still pending, see 4d) Programmatic 4-tab UI + CI green (MainActivity, MainWorkspaceView, Scout/Studio/Library/System tabs, AnalysisDetailView, StoryboardEditorView) — push and `gh run watch` until APK builds

## 4f. Canvas TTS provider (personal, non-commercial)

- Enable: `STICKMAN_TTS_PROVIDER=canvas` (default unchanged). Env: `CANVAS_TTS_URL` (default `http://127.0.0.1:8767`, never 8765), optional `CANVAS_TTS_TOKEN` (sent as `X-Canvas-Token`). Code: `engine/canvas_tts.py`, hooked in `tts_expressive.synth_line`.
- API repo `~/personal-canvas-tts-api`: start `bash ~/personal-canvas-tts-api/scripts/start_daemon.sh`, stop `scripts/stop_daemon.sh`, log `~/.canvas-tts/daemon.log`. `/health` needs `browser_alive`, `signed_in`, `iframe_attached`.
- Queue rules: one request at a time, >= 2.5 s cooldown (kept in `canvas_tts.py`), never parallel; max 2000 chars per request (we split by sentence at <= 1000); requests take tens of seconds, 300 s timeout, one retry on 502/504.
- Voices: gender follows the voice. Female: Zephyr Kore Aoede Leda Callirrhoe Autonoe Despina Erinome. Male: Puck Charon Fenrir Orus Enceladus Iapetus Umbriel Algieba. Style = 30 Indonesian emotion labels (Bercerita, Berwibawa, Ceria, Tenang, Marah, ...). Per-line style comes from `acting_direction` keywords, else the character default, else Bercerita.
- Optional map `<STICKMAN_HOME>/config/canvas_voices.json`: `{"<character_id or voice_profile_id>": {"voice": "Kore", "style": "Ceria"}}`.
- Fallback: if Canvas is down / signed out / errors, the line uses the normal provider; logged as `CANVAS TTS UNAVAILABLE` and shown in engine `/health` -> `canvas_tts` (`up`, `signed_in`, `calibrated`, `needs_refresh`, `fallback`).
- Calibration: `GET /inspect` (rewrites selectors.json + voices.json), confirm `calibrated: true` in `/voices`; if `signed_in` is false the user syncs Google cookies via `POST /auth/session` (never commit cookies). Re-run `/inspect` when Canvas changes.
- Check: `python3 canvas_demo/demo.py` (2 characters, 2 styles).
