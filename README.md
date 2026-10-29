# PiperScribe

[![CI](https://github.com/Monotoba/piperscribe/actions/workflows/ci.yml/badge.svg)](https://github.com/Monotoba/piperscribe/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Monotoba/piperscribe?label=release)](https://github.com/Monotoba/piperscribe/releases/latest)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![License: PAL 1.0](https://img.shields.io/badge/license-PAL%201.0-blue)](LICENSE)

PiperScribe is a desktop app for turning documents into speech. It uses
[Piper TTS](https://github.com/rhasspy/piper) to generate audio, so it runs
offline, and it is built with PySide6 (Qt 6).

Use it to make audiobooks, course audio, or spoken versions of documents. Mark
the parts you don't want read (headers, footers, URLs), manage several documents
in one project, preview a passage before generating the whole thing, and export
WAV audio or a playlist.

## Features

- Import **TXT, DOCX, Markdown, HTML, and text-based PDF** files.
- Mark text as **excluded** (not spoken) or **included**, by hand or with regex rules.
- Manage several documents in one project, reorder them, and enable or disable each one for the playlist.
- Choose a **Piper voice** per document, browse and download voices, and adjust speed and voice variation.
- **Preview** a selected passage before generating the full audio.
- **Generate** audio for one document or all enabled documents.
- Play generated audio in the app, with a choice of system WAV player.
- Export a **WAV** file or an **M3U + JSON playlist**.
- Light, dark, or system theme.

## Installation

See [INSTALL.md](INSTALL.md) for full steps. You need Python 3.10 or later and
the `piper` command on your PATH.

Quick start on Linux or macOS:

```bash
git clone https://github.com/Monotoba/piperscribe.git
cd piperscribe
./setup-prj.sh
./run.sh
```

Windows users can run `install-windows.bat` or `install-windows.ps1`.

On Wayland with HiDPI scaling, the window can open too large. Use
`./run-piperscribe-safe.sh` instead. See
[docs/HIDPI_QT6_WAYLAND_FIX.md](docs/HIDPI_QT6_WAYLAND_FIX.md).

## Documentation

- **[User Manual](docs/USER_MANUAL.md)**: the full guide to using PiperScribe.
- [Getting started](docs/help/getting-started.md) and [troubleshooting](docs/help/troubleshooting.md): also shown in the app under **Help → Help Contents…**.
- [INSTALL.md](INSTALL.md): installation and setup.
- [CHANGELOG.md](CHANGELOG.md): what changed in each release.

## Contributing

Bug reports, fixes, and improvements are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

PiperScribe is released under the **PiperScribe Attribution License (PAL) 1.0**.
See [LICENSE](LICENSE). In short:

- It is free to use, copy, modify, and distribute.
- You must keep the copyright and credit the author ("Monotoba") and the project.
- You may not charge for the software, its packaging, its media or delivery, or access to it.
- Output you generate with it (audio, text) is yours to use however you like.

This is a custom license, not an OSI-approved open-source license. Third-party
components keep their own licenses, including Piper TTS, PySide6, and PyMuPDF.
