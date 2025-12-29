#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[verify] Running PiperScribe quality gates…"

# If your project expects the uv venv to exist, this makes the run reproducible.
# If setup-prj.sh is slow and you don't want it every time, comment this out.
if [[ -x "./setup-prj.sh" ]]; then
  echo "[verify] Ensuring environment is ready via ./setup-prj.sh"
  ./setup-prj.sh
fi

echo "[verify] 1/3 python -m compileall src"
python -m compileall src

echo "[verify] 2/3 pytest"
source .venv/bin/activate
pytest

echo "[verify] 3/3 import smoke (MainWindow import/construct)"
python - <<'PY'
from piperscribe.ui.main_window import MainWindow
try:
    # Constructing MainWindow without a QApplication may fail in some Qt configs.
    # We create one if needed.
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    w = MainWindow()
    w.close()
except Exception as e:
    raise SystemExit(f"[verify] MainWindow construct failed: {e}") from e
print("[verify] MainWindow construct OK")
PY

echo "[verify] ✅ All gates passed."

