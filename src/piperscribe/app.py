from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from piperscribe.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1100, 750)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
