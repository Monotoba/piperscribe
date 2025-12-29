# Install / Setup

## Requirements
- Python 3.10+
- `uv` (recommended)
- `piper` CLI available on PATH
- Optional import support:
  - `python-docx` for DOCX
  - `PyMuPDF` for PDF (text-based)
  - `beautifulsoup4` for HTML
  - `markdown-it-py` for Markdown

## Setup (recommended: uv)
```bash
./setup-prj.sh
```

## Manual setup (pip)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[importers,dev]"
pytest
PiperScribe
```

## Piper
In the GUI, set **Piper model** to a local `.onnx` file, e.g.
`~/.local/share/piper/voices/en_US-lessac-medium.onnx`

Verify:
```bash
piper --help
```

## Linux audio preview
Preview uses `aplay` (ALSA). Install if missing:
```bash
sudo apt-get install alsa-utils
```

## Voice selection
The app will try to discover Piper voices in common directories (e.g. `~/.local/share/piper/voices`).
Use the **Voice** dropdown, or browse to a `.onnx` model manually.

## Settings persistence
Theme and Piper voice/speed/noise settings are saved automatically to `~/.config/piperscribe/settings.json` (or `$XDG_CONFIG_HOME/piperscribe/settings.json`).


## Settings UI
Use **Settings…** to edit theme and Piper voice parameters in one place.
Use **Reset Settings** to delete saved settings and return to defaults.
