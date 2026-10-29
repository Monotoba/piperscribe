# Contributing to PiperScribe

Thanks for helping. Bug reports, fixes, documentation, and new features are all
welcome.

By contributing, you agree that your contribution is licensed under the
[PiperScribe Attribution License](LICENSE), the same as the rest of the project.

## Reporting bugs

Open an issue and include:

- Your operating system and desktop (for example, Ubuntu 24.04 on GNOME, Wayland or X11)
- The PiperScribe version (from **Help → About**)
- The steps that cause the problem, and what you expected to happen
- Any text from the terminal, including tracebacks

For window sizing, audio playback, or Piper problems, also say which voice model
and which audio player you use (**Preferences → Voice**).

## Setting up a development environment

```bash
git clone https://github.com/Monotoba/piperscribe.git
cd piperscribe
./setup-prj.sh          # creates .venv and installs the package with dev tools
source .venv/bin/activate
```

You need [uv](https://docs.astral.sh/uv/) and the `piper` command on your PATH.
See [INSTALL.md](INSTALL.md).

## Quality gates

Every change must pass the project gates before it is committed:

```bash
./verify.sh
```

`verify.sh` runs:

1. `python -m compileall src`
2. `pytest`
3. a `MainWindow` construction check

Run `./run.sh` as well when your change touches the user interface. The UI must start without a traceback.

If you add a test file, name it `*_test.py` (for example, `tests/hidpi_test.py`).
`.gitignore` excludes `test_*.py`, so those files would not be committed.

## Coding conventions

- Match the style and comment density of the file you are editing.
- Keep changes small and focused. Don't mix refactors with new features in one commit.
- Preserve existing behavior unless the change is meant to alter it.
- In PySide6 code, store shared actions on the instance (`self.act_play`) and make sure every signal connects to a method that exists.
- Keep `_build_ui()` free of hidden side effects.

[docs/DEV_RULES.md](docs/DEV_RULES.md) has the full set of project rules.

## Commit messages

Use the conventional format, with a scope:

```
fix(ui): keep preview temp dir alive until Piper finishes writing
feat(audio): detect and resolve WAV player per platform
```

Write the subject in the imperative mood. Add a body when the reason for the
change isn't obvious from the diff.

## Branches and pull requests

- Create a branch for each task: `fix/…`, `feat/…`, or `docs/…`.
- Open a pull request against `main`.
- Describe what changed, how you tested it, and anything you could not test (for example, a window manager or audio device you don't have).
- Keep pull requests focused. Several small PRs are easier to review than one large one.

## Documentation

User-facing documentation lives in:

- [docs/USER_MANUAL.md](docs/USER_MANUAL.md): the full user manual
- `docs/help/`: the pages shown in the app under **Help → Help Contents…**

If you change a feature, update the manual in the same pull request.

## Code of conduct

Be respectful and constructive. Assume good faith. Keep discussion focused on the
code and the problem.
