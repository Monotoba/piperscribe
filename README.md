# PiperScribe (v0.1)

A small **PySide6** desktop app that can:

- Import **TXT / DOCX / Markdown / HTML / PDF (text-based)**
- Display extracted text
- Let you **mark selections as “excluded”** (won’t be spoken)
- Export a single **WAV** using **Piper TTS** (via the `piper` CLI)
- Select a **voice/model** from discovered Piper voices and adjust **speed**
- Choose **Theme** (System/Light/Dark)

> Notes:
> - PDF import requires `PyMuPDF` and works best on text-based PDFs. Scanned PDFs are not supported yet.
> - DOCX import requires `python-docx`.
> - Markdown/HTML import uses `markdown-it-py` + `beautifulsoup4` if installed; falls back to a simpler extractor otherwise.
> - MP3/M4A export is intentionally not included in v0.1. (Easy to add via ffmpeg later.)

## Quick start (uv)

```bash
cd piperscribe
uv venv
source .venv/bin/activate
uv pip install -e ".[importers,dev]"
pytest
PiperScribe
```

## Piper setup

This app calls `piper` as a subprocess. Verify you can run:

```bash
piper --help
```

In the app, set the **Piper model path** (e.g. `~/.local/share/piper/voices/en_US-lessac-medium.onnx`).

## Project files

The app can save a `.abproj.json` file which contains:
- source path
- extracted text
- exclusion spans
- piper settings

## Roadmap ideas (v0.2+)
- paragraph/chapter splitting and per-section export
- PDF cleanup (header/footer de-dup, de-hyphenation, multi-column ordering)
- basic OCR fallback (optional)
- audio preview via QtMultimedia (cross-platform)


## Settings persistence
PiperScribe saves your theme and voice/speed/noise settings automatically to `~/.config/piperscribe/settings.json` (or `$XDG_CONFIG_HOME/piperscribe/settings.json`).


## Settings UI
Use **Settings…** to edit theme and Piper voice parameters in one place.
Use **Reset Settings** to delete saved settings and return to defaults.


## Rules (regex include/exclude)
Use **Rules…** to add regex-based include/exclude rules (with canned URL rules). After editing, apply them to automatically exclude repeated headers/footers like website URLs, page numbers, contents, appendices, etc.


### Rule application behavior
Manual exclusions are kept separately. Rules are applied on top of manual exclusions to compute the final excluded spans used for preview/export. Use **Reapply Rules** to recompute after tweaking settings.


## Preferences
All app-wide settings (theme, voice/model, speed/noise, rule settings) are managed under **Preferences…**.


## Menus
Preferences and rule tools are available from the menu bar:
- **Edit → Preferences…**
- **Tools → Rules…** (shortcut to Preferences)
- **Tools → Reapply Rules**
- **Edit → Find…**


## Testing
Run `./setup-prj.sh` then `pytest` (tests live under `tests/`).
