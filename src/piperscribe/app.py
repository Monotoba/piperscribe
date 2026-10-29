from __future__ import annotations

import os
import sys

# Workaround for Wayland HDPI menu alignment.
# Disabling the fractional-scale-v1 protocol forces Qt to use integer-based
# surface scaling, which resolves the coordinate mismatch that causes
# popups to jump to the right (e.g., File opening under Tools).
os.environ["QT_WAYLAND_FRACTIONAL_SCALE"] = "0"

from PySide6.QtWidgets import QApplication, QProxyStyle, QMessageBox # noqa: E402
from piperscribe.hidpi import clamp_after_show, prepare_qt_hidpi, restore_or_clamp_window # noqa: E402
from piperscribe.ui.main_window import MainWindow, MenuOffsetStyle # noqa: E402


def main() -> None:
    # Must run before QApplication is constructed.
    prepare_qt_hidpi()

    app = QApplication(sys.argv)

    # Apply the custom style to fix menu alignment issues, especially on HDPI displays.
    app.setStyle(MenuOffsetStyle())

    w = MainWindow()
    w.resize(1100, 750)
    restore_or_clamp_window(w)
    w.show()
    clamp_after_show(w)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
