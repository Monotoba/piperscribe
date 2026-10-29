"""Build the main window without a display or Piper, the way CI runs it."""
import sys
from unittest import mock

from PySide6.QtWidgets import QApplication


def test_main_window_builds_and_closes():
    app = QApplication.instance() or QApplication(sys.argv)
    import piperscribe.ui.main_window as main_window

    # On CI runners Piper is not installed, and the window would show a blocking warning.
    with mock.patch.object(main_window, "QMessageBox"):
        window = main_window.MainWindow()
        window.show()
        app.processEvents()
        assert window.windowTitle().startswith("PiperScribe v")
        window.close()
