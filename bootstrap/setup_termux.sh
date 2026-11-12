#!/usr/bin/env bash
# Stickman Video Director — idempotent Termux bootstrap.
# One-line setup:
#   curl -fsSL https://raw.githubusercontent.com/stevenchen5411/stickman-video-director/main/bootstrap/setup_termux.sh | bash
# (Private repo? clone it first, then run: bash bootstrap/setup_termux.sh)
set -uo pipefail

REPO_OWNER="${REPO_OWNER:-stevenchen5411}"
REPO_NAME="${REPO_NAME:-stickman-video-director}"
REPO_URL="${REPO_URL:-https://github.com/${REPO_OWNER}/${REPO_NAME}.git}"
REPO_DIR="${REPO_DIR:-$HOME/${REPO_NAME}}"
PORT="${STICKMAN_PORT:-8765}"

say()  { printf '\033[1;36m[setup]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }

# --- Termux sanity -----------------------------------------------------------
: "${PREFIX:=/data/data/com.termux/files/usr}"
[ -d "$PREFIX" ] || die "This script must run inside Termux (PREFIX not found)."

# Android has no writable /tmp: use $TMPDIR (default $PREFIX/tmp).
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
mkdir -p "$TMPDIR"

# --- 1. allow-external-apps (lets the Android app use RUN_COMMAND) ----------
say "Enabling allow-external-apps"
mkdir -p "$HOME/.termux"
PROPS="$HOME/.termux/termux.properties"
touch "$PROPS"
if grep -qE '^[[:space:]]*#?[[:space:]]*allow-external-apps' "$PROPS"; then
  sed -i -E 's|^[[:space:]]*#?[[:space:]]*allow-external-apps.*|allow-external-apps = true|' "$PROPS"
else
  printf '\nallow-external-apps = true\n' >> "$PROPS"
fi
command -v termux-reload-settings >/dev/null 2>&1 && termux-reload-settings || warn "termux-reload-settings missing (install termux-api/termux-tools)"

# --- 2. Shared storage -------------------------------------------------------
say "Setting up shared storage"
if [ ! -d "$HOME/storage/shared" ]; then
  command -v termux-setup-storage >/dev/null 2>&1 && termux-setup-storage || warn "termux-setup-storage unavailable"
  for _ in $(seq 1 30); do [ -d "$HOME/storage/shared" ] && break; sleep 1; done
fi
[ -d "$HOME/storage/shared" ] || die "Shared storage not granted. Approve the storage prompt, then re-run this script."

SHARED="$HOME/storage/shared/StickmanDirector"
ABS_SHARED="/storage/emulated/0/StickmanDirector"
mkdir -p "$SHARED"/{config,cache,queue,renders,assets/library}
if [ -d "$ABS_SHARED" ]; then
  say "Shared root resolves at both $SHARED and $ABS_SHARED"
else
  warn "$ABS_SHARED not visible from Termux (normal on some devices); using $SHARED"
fi
( : > "$SHARED/.write_test" ) 2>/dev/null && rm -f "$SHARED/.write_test" || die "Shared storage is not writable: $SHARED"

# --- 3. Packages -------------------------------------------------------------
say "Installing packages (this can take a while on first run)"
pkg update -y >/dev/null 2>&1 || warn "pkg update reported an error"
pkg install -y python ffmpeg git curl gh clang make pkg-config rust binutils \
  libcairo python-numpy python-scipy python-pillow libffi openssl termux-api \
  || warn "Some pkg installs failed; check output above"
pkg install -y ttf-dejavu >/dev/null 2>&1 || warn "ttf-dejavu not installed; captions will use the default font"

# --- 4. Repo -----------------------------------------------------------------
SRC_DIR=""
if [ -f "$(dirname "${BASH_SOURCE[0]:-$0}")/../engine/requirements.txt" ] 2>/dev/null; then
  SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  REPO_DIR="$SRC_DIR"
  say "Using existing checkout: $REPO_DIR"
elif [ -d "$REPO_DIR/.git" ]; then
  say "Updating $REPO_DIR"
  git -C "$REPO_DIR" pull --ff-only || warn "git pull failed; continuing with local copy"
else
  say "Cloning $REPO_URL"
  git clone "$REPO_URL" "$REPO_DIR" || die "git clone failed (private repo? run 'gh auth login' first)"
fi

# --- 5. Python deps ----------------------------------------------------------
say "Installing Python dependencies"
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install -r "$REPO_DIR/engine/requirements.txt" || warn "Some Python packages failed to install"
# Optional: browser-grade TLS for the claude.ai web-session fallback when the Android bridge is not running.
python3 -m pip install curl_cffi || warn "curl_cffi not installed; the Claude web session will rely on the Android app bridge only"
python3 -m pip install "git+https://github.com/JuneYaooo/rea-video" || warn "rea-video not installed; forensics will fall back to ffmpeg scene detection"

# --- 6. Sync seed library into shared storage (never overwrite user edits) ---
say "Syncing asset library to shared storage"
cp -a -n "$REPO_DIR/assets/library/." "$SHARED/assets/library/" 2>/dev/null || warn "library sync incomplete"

# --- 7. Daemon launcher + wake-lock -----------------------------------------
say "Installing daemon launcher"
mkdir -p "$HOME/.stickman"
LAUNCHER="$HOME/.stickman/start_daemon.sh"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
# Starts the Stickman engine on 127.0.0.1:${PORT} (idempotent; safe to call from RUN_COMMAND).
export TMPDIR="\${TMPDIR:-${PREFIX}/tmp}"
mkdir -p "\$TMPDIR"
export STICKMAN_HOME="${SHARED}"
export STICKMAN_REPO="${REPO_DIR}"
# Usage: start_daemon.sh [TOKEN] [restart]   (the app passes its per-install token; "restart" replaces a running daemon)
if [ -n "\${1:-}" ]; then export STICKMAN_TOKEN="\$1"; fi
if [ "\${2:-}" = "restart" ] && [ -f "\$HOME/.stickman/daemon.pid" ]; then
  kill "\$(cat "\$HOME/.stickman/daemon.pid")" 2>/dev/null; sleep 1
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock
if curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "already running"; exit 0
fi
cd "${REPO_DIR}/engine" || exit 1
nohup python3 -m uvicorn server:app --host 127.0.0.1 --port ${PORT} \\
  >> "\$HOME/.stickman/daemon.log" 2>&1 &
echo \$! > "\$HOME/.stickman/daemon.pid"
echo "started pid \$(cat "\$HOME/.stickman/daemon.pid")"
EOF
chmod +x "$LAUNCHER"

# Optional Termux:Boot autostart
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/stickman-daemon" <<EOF
#!/usr/bin/env bash
"$LAUNCHER"
EOF
chmod +x "$HOME/.termux/boot/stickman-daemon"

command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock

if [ -f "$REPO_DIR/engine/server.py" ]; then
  say "Starting daemon on 127.0.0.1:${PORT}"
  "$LAUNCHER" || warn "daemon launch failed; see $HOME/.stickman/daemon.log"
  sleep 2
  if curl -fsS --max-time 3 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    say "Health check OK"
  else
    warn "Health check not responding yet; see $HOME/.stickman/daemon.log"
  fi
else
  warn "engine/server.py not present yet (arrives in Milestone 2); daemon launcher is installed and will work once it exists."
fi

say "Done. Shared storage: $SHARED"
