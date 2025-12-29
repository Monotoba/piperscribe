# Verification Log

Append a new entry whenever you complete a meaningful change set.
This is a “paper trail” that prevents regressions and false claims.

---

## Template

### YYYY-MM-DD — <short description>
- Branch: `<branch-name>`
- Summary:
  - <what changed in 1–3 bullets>
- Commands run:
  - `python -m compileall src` ✅/❌
  - `pytest` ✅/❌
  - `./run.sh` ✅/❌
- Notes:
  - <anything notable: skipped tests, environment, follow-ups>

---

## Example Entry

### 2025-12-24 — Stabilize MainWindow
- Branch: `fix/stabilize-mainwindow`
- Summary:
  - Replaced corrupted main_window.py with minimal skeleton
  - Added import/UI smoke tests
- Commands run:
  - `python -m compileall src` ✅
  - `pytest` ✅
  - `./run.sh` ✅
- Notes:
  - UI smoke test uses pytest.importorskip("PySide6") for headless runs

