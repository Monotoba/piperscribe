#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="piperscribe"
echo "[$PROJECT_NAME] Setup starting…"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: 'uv' not found. Install uv first (recommended)."
  echo "See: https://docs.astral.sh/uv/"
  exit 1
fi

echo "[1/5] Creating or reusing uv virtual environment…"
uv venv --allow-existing

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/5] Installing dependencies…"
uv pip install -e ".[importers,dev]"

echo "[3/5] Running tests…"
pytest

echo "[4/5] Running ruff (non-fatal if not configured)…"
ruff check . || true

echo "[5/5] Done."
echo "Run: source .venv/bin/activate && piperscribe"
