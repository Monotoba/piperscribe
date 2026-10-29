#!/usr/bin/env bash
# Install PiperScribe from this checkout on Linux.
#
# Creates ./.venv if it is missing, installs the package in editable mode, and
# checks the system tools PiperScribe calls out to. Safe to re-run.
#
# Usage: ./install-linux.sh [--dev]
#   --dev  also install the dev extras (pytest, ruff, mypy)
set -euo pipefail

cd "$(dirname "$0")"

EXTRAS="importers"
for arg in "$@"; do
  case "$arg" in
    --dev) EXTRAS="importers,dev" ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

info() { printf '[install] %s\n' "$*"; }
warn() { printf '[install] WARNING: %s\n' "$*" >&2; }
die()  { printf '[install] ERROR: %s\n' "$*" >&2; exit 1; }

# True if the interpreter is Python 3.10 or newer.
is_supported_python() {
  "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

find_python() {
  local candidate
  for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && is_supported_python "$candidate"; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

VENV_DIR=".venv"
VENV_PY="$VENV_DIR/bin/python"

info "[1/5] Python environment"
if [[ -x "$VENV_PY" ]]; then
  info "Reusing existing $VENV_DIR"
elif command -v uv >/dev/null 2>&1; then
  info "Creating $VENV_DIR with uv"
  uv venv --python ">=3.10" "$VENV_DIR"
else
  PY="$(find_python)" || die "Python 3.10+ not found. Install it from https://www.python.org/downloads/ or install uv from https://docs.astral.sh/uv/"
  info "Creating $VENV_DIR with $PY"
  "$PY" -m venv "$VENV_DIR"
fi

info "[2/5] Installing PiperScribe (editable, extras: $EXTRAS)"
if command -v uv >/dev/null 2>&1; then
  uv pip install --python "$VENV_PY" -e ".[$EXTRAS]"
else
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install -e ".[$EXTRAS]"
fi

info "[3/5] Checking system tools"
if command -v piper >/dev/null 2>&1; then
  info "Found piper: $(command -v piper)"
else
  warn "'piper' is not on PATH. The app opens without it, but Preview and Export need it."
  warn "Install Piper from https://github.com/rhasspy/piper/releases and put it on PATH."
fi


# Qt 6.5+ needs libxcb-cursor to load its X11/XWayland platform plugin.
LDCONFIG="$(command -v ldconfig || echo /sbin/ldconfig)"
LIBS="$("$LDCONFIG" -p 2>/dev/null || true)"
case "$LIBS" in
  *libxcb-cursor.so.0*) ;;
  *) warn "libxcb-cursor0 not found. Qt may fail to start: sudo apt-get install libxcb-cursor0" ;;
esac

VOICE_DIR="$HOME/.local/share/piper/voices"
mkdir -p "$VOICE_DIR"
info "Voice folder: $VOICE_DIR"

info "[4/5] Choosing the audio player"
"$VENV_PY" -m piperscribe.audio.player \
  || warn "Could not choose an audio player. You can choose one later in Preferences → Voice."

info "[5/5] Verifying the install"
"$VENV_PY" -c 'import PySide6, piperscribe.ui.main_window' \
  || die "PiperScribe failed to import. See the error above."

info "Done. Start PiperScribe with:"
echo "  ./run.sh"
echo "  or: ./$VENV_DIR/bin/piperscribe"
