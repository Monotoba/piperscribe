# PiperScribe Development Rules

This document is the human-readable version of the automation rules in `AGENTS.md`
(Codex) and `.aider.conf.yml` (Aider). Keep them consistent.

---

## Quality Gates (required)
Run from repo root before committing:

1. `python -m compileall src`
2. `pytest`
3. `./run.sh` must launch the UI without tracebacks

If any fails, fix immediately and re-run.

---

## Coding Practices

### Avoid fragile patching
If a file is corrupted (indentation errors, blocks in the wrong scope, duplicated code),
**replace it cleanly**.

### PySide6 UI wiring conventions
- Use instance attributes for shared actions:
  - `self.act_open`, `self.act_exclude`, etc.
- Every signal connection must point to a method that exists.
- Keep `_build_ui()` deterministic and side-effect free.

### Refactoring rules
- Prefer small, safe refactors with tests.
- Preserve behavior unless explicitly asked to change it.
- Don’t refactor and add new features in the same commit.

---

## Phase Plan (don’t mix phases)

### Phase A — Stabilize
- Minimal `MainWindow` that imports, constructs, and launches.

### Phase B — Preferences
- Preferences dialog exists and opens from menu.
- Tabs:
  - Appearance (theme + show selection toolbar)
  - Voice (piper voice/model + speed/noise)
  - Rules (regex list + test/apply)

### Phase C — Tools + Dockables
- Tools menu: include/exclude selection, reapply rules, import voice model
- Dockable Selection toolbar toggled via Preferences → Appearance

### Phase D — Recent Files/Projects
- File menu recents, persisted, with clear actions.

---

## Testing Strategy
Minimum tests:
- Import smoke tests (catch syntax errors)
- UI construction smoke test (skip in headless environments)

Never ship code that fails these.

