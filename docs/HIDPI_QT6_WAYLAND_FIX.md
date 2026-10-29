# HiDPI and Wayland window sizing (PySide6 / Qt6)

## Affected machine

ASUS ProArt P16 (H7606WV), Ubuntu GNOME, HiDPI display, Wayland with fractional scaling.

## Symptoms

1. PySide6/Qt6 windows may open oversized under Wayland/HiDPI.
2. PiperScribe opens at a usable size, then grows to about 2x the screen after a document is opened.

## Cause

- Qt6 uses logical (device-independent) pixels. Do not multiply sizes for HiDPI by hand.
- Do not set `QT_SCALE_FACTOR` globally unless you are testing it. It stacks on top of Qt's own scaling.
- Wayland fractional scaling can interact badly with PySide6 on this hardware.
- Document content used to determine the top-level window's size, so a tall preview pushed the window past the screen.

## Workaround

Launch with `./run-piperscribe-safe.sh`. Under Wayland it sets `QT_QPA_PLATFORM=xcb`, clears the dangerous scale variables, and sets `QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough`.

## Application fix

- `src/piperscribe/hidpi.py`:
  - `prepare_qt_hidpi()` runs before `QApplication` is created and clears the scale variables.
  - `clamp_window_to_screen()` fits the window to 92% of width and 90% of height of the available screen area, with a 760x520 minimum that never exceeds the screen.
  - `restore_or_clamp_window()` restores saved geometry if it is valid, then always clamps.
  - `clamp_after_show()` clamps again at 0 ms and 100 ms, because window managers can adjust the frame after show.
- `app.py` calls these at startup. `MainWindow.clamp_to_available_screen()` runs after each document load.

## Verification

```bash
echo "$XDG_SESSION_TYPE"
env | grep -E '^(QT|GDK|GIO|XDG)_' | sort
QT_QPA_PLATFORM=xcb ./.venv/bin/piperscribe
./run-piperscribe-safe.sh
./.venv/bin/python -m pytest tests/hidpi_test.py
```

Manual checks: the app opens at a usable size; opening TXT, MD, PDF, DOCX, or ODT does not grow the window past the screen; Preferences, Help, Voice Browser, and Document Settings remain usable.
