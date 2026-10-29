# Changelog

## 0.1.21 - 2026-10-28

### Added
- Audio player selection. PiperScribe finds a WAV player for your platform:
  Windows (`winsound`), macOS (`afplay`), Linux (`aplay`, `pw-play`, `paplay`,
  `ffplay`), and Android (`termux-media-player`). Choose one, or leave it on
  **Auto**, in **Preferences → Voice**.
- Install scripts for Linux (`install-linux.sh`), macOS (`install-macos.sh`),
  and Windows (`install-windows.bat`, `install-windows.ps1`).
- `run-piperscribe-safe.sh`, a launcher for Wayland with HiDPI scaling.
- The window is kept inside the available screen area, at startup and after a document is opened.
- A user manual (`docs/USER_MANUAL.md`), a license, and a contributing guide.
- **Audio folder** setting in **Preferences → Voice**. Generated audio is saved there, so it doesn't depend on the project being saved first.
- **File → Save Audio to Folder…** copies every document's audio into a folder you name.
- PiperScribe warns you before quitting, starting a new project, or opening another project when audio exists only in the temporary folder. You can save it, discard it, or cancel.
- **Help → Help Contents…** now includes the User Manual.
- **File → Open Document(s)…** (Ctrl+O) does the same as Import, so you can open a file without creating or saving a project.
- The toolbar voice dropdown now changes the voice of every document that uses the project voice. Before, documents kept the voice they were imported with, so the change had no effect.
- Speed, noise scale, and noise W changes on the Voice tab now reach documents that use the project values. Before, documents kept the values they were imported with.
- **Test Selected Voice** now uses the speed and noise values shown on the Voice tab. Before, it always used Piper's defaults.
- **Play** checks audio freshness before resuming a paused player, so a changed voice or speed is applied. Audio is regenerated only when it is out of date.
- **Play** regenerates audio when the voice, speed, noise settings, or text changed since it was made. Before, changing the voice had no effect until audio was generated again.

### Changed
- **Play** on the toolbar generates audio first if the document has none, shows
  the usual progress and result dialogs, and then plays it.
- The Document Settings dialog uses the same audio player as the rest of the app.
- The project includes earlier in-progress changes to the main window and
  preferences, which were committed together with this release.

### Fixed
- The window grew to about twice the screen size after a document was opened.
  The cause was the status line, whose minimum width followed its text. It now wraps.
- Right-clicking a document raised `NameError`.
- **Preview selection** failed with `FileNotFoundError` for the WAV file. The temp
  directory was deleted before Piper finished writing into it.
- `setup-prj.sh` failed when `.venv` already existed, which blocked every commit
  in the pre-commit gate.

## 0.1.20 - 2025-12-29

Baseline before the 0.1.21 work. Tag: `v0.1.20`.
