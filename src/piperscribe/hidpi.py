"""Window sizing helpers for HiDPI and Wayland setups.

Qt geometry is in device-independent (logical) pixels, so every size here is
compared against ``availableGeometry()`` and never scaled by hand. See
docs/HIDPI_QT6_WAYLAND_FIX.md for the background.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QByteArray, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

# Env vars that multiply sizes on top of Qt's own HiDPI handling.
DANGEROUS_SCALE_VARS = (
    "QT_SCALE_FACTOR",
    "QT_SCREEN_SCALE_FACTORS",
    "QT_AUTO_SCREEN_SCALE_FACTOR",
    "QT_ENABLE_HIGHDPI_SCALING",
)


def prepare_qt_hidpi() -> None:
    """Call before QApplication is constructed."""
    for name in DANGEROUS_SCALE_VARS:
        os.environ.pop(name, None)
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def clamp_size_to_available(
    current_width: int,
    current_height: int,
    available_width: int,
    available_height: int,
    minimum_width: int = 760,
    minimum_height: int = 520,
    width_ratio: float = 0.92,
    height_ratio: float = 0.90,
) -> tuple[int, int]:
    """Return a window size that fits inside the available screen area."""
    max_width = int(available_width * width_ratio)
    max_height = int(available_height * height_ratio)
    # The preferred minimum must never force the window past the screen.
    min_width = min(minimum_width, max_width)
    min_height = min(minimum_height, max_height)
    width = max(min_width, min(current_width, max_width))
    height = max(min_height, min(current_height, max_height))
    return width, height


def _screen_for(window: QWidget):
    return window.screen() or QGuiApplication.primaryScreen()


def clamp_window_to_screen(window: QWidget) -> None:
    """Shrink the window if needed, then move it back onto the screen."""
    screen = _screen_for(window)
    if screen is None:
        return
    available = screen.availableGeometry()
    width, height = clamp_size_to_available(
        window.width(), window.height(), available.width(), available.height()
    )
    window.resize(width, height)

    x = max(available.left(), min(window.x(), available.right() - width + 1))
    y = max(available.top(), min(window.y(), available.bottom() - height + 1))
    window.move(x, y)


def restore_or_clamp_window(window: QWidget, geometry: QByteArray | None = None) -> None:
    """Restore saved geometry when it is valid, then always clamp it."""
    if geometry is not None:
        window.restoreGeometry(geometry)
    clamp_window_to_screen(window)


def clamp_after_show(window: QWidget) -> None:
    """Clamp again after show, since window managers may adjust the frame."""
    QTimer.singleShot(0, lambda: clamp_window_to_screen(window))
    QTimer.singleShot(100, lambda: clamp_window_to_screen(window))
