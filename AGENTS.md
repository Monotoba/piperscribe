# PiperScribe — Agent Operating Rules (Codex CLI)

## Mission
This repository contains **PiperScribe**, a PySide6 desktop app that uses Piper TTS.
The project has experienced repeated regressions due to incomplete testing and unsafe patching.
Your job as an agent is to make disciplined, verifiable progress.

**Non-negotiable:** Do not claim “done” or produce deliverables unless the quality gates pass.

---

## Global Rules

### 1) Quality gates (must pass before any commit)
From repo root, run:

1. `python -m compileall src`
2. `pytest`
3. `./run.sh` (must open the UI without a traceback)

If any gate fails:
- STOP
- Fix the failure
- Re-run the gates
- Only then proceed.

### 2) No “surgical regex patching” on corrupted files
If a file is structurally corrupted (indentation errors, partial blocks, duplicated sections),
**replace the file cleanly** rather than patching it line-by-line.

### 3) UI wiring rules (PySide6)
- Any action used in multiple places (menu + toolbar) MUST be stored on the instance:
  - `self.act_exclude`, `self.act_include`, etc.
- Every connected signal must point to an existing method.
- Avoid hidden side effects in `_build_ui()`. Keep it deterministic.

### 4) Scope control
Work in phases. Do not mix stability work with feature work.

- **Phase A (Stabilize):** Minimal MainWindow skeleton that launches.
- **Phase B (Preferences):** Dialog opens; settings persist; no feature creep.
- **Phase C (Tools & Dockables):** Tools menu + optional toolbar visibility via Preferences.
- **Phase D (Recents):** Recent Files/Projects, persisted.

Do not start a later phase until earlier phases are fully green.

### 5) Commit discipline
- Use a dedicated branch per task:
  - `fix/stabilize-mainwindow`, `feat/preferences`, `feat/rules-ui`, etc.
- Commits must be small and descriptive:
  - `fix(ui): replace corrupted MainWindow with clean skeleton`
  - `test(ui): add import/ui smoke tests`
- Never commit broken tests or broken runtime.

---

## Required Deliverables Per Task
For each completed task, provide:
1) Files changed (list)
2) Exact commands executed
3) Test results summary (what passed)
4) Any follow-up TODOs (if needed)

---

## Canonical Acceptance Tests (minimum)
- `python -m compileall src` passes
- `pytest` passes
- `./run.sh` opens UI and you can close it without errors
- Preferences opens (when implemented) from menu without exception
- Tools menu actions exist (when implemented) and do not crash

---

## Notes on Environment
- Primary dev OS: Ubuntu 24.04+
- Primary Python: project uses uv-managed venv via `./setup-prj.sh`
- GUI tests may require a display (skip appropriately in headless CI)

## Final Instruction
- Read AGENT.md before begining and task


