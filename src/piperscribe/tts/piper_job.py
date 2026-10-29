"""Run one Piper synthesis in the background, so the window stays responsive."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from piperscribe.model.document import PiperSettings


class PiperRun(QObject):
    """Synthesize ``text`` to ``wav_path`` with ``piper`` and report the result.

    ``finished`` is emitted exactly once, with ``(ok, message)``. The message is empty on
    success, ``"Cancelled"`` after :meth:`cancel`, and the reason otherwise.
    """

    finished = Signal(bool, str)

    def __init__(self, parent: QObject, settings: PiperSettings, text: str, wav_path: Path) -> None:
        super().__init__(parent)
        self._text = text
        self._wav_path = wav_path
        self._cancelled = False
        self._done = False

        self._proc = QProcess(self)
        self._proc.setProgram("piper")
        self._proc.setArguments([*settings.to_args(), "--output_file", str(wav_path)])
        self._proc.setProcessChannelMode(QProcess.MergedChannels)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(self._on_error)

    def start(self) -> None:
        self._proc.start()
        self._proc.write(self._text.encode("utf-8"))
        self._proc.closeWriteChannel()

    def cancel(self) -> None:
        self._cancelled = True
        if self._proc.state() != QProcess.NotRunning:
            self._proc.kill()
            self._proc.waitForFinished(3000)
        else:
            self._report(False, "Cancelled")

    def _report(self, ok: bool, message: str) -> None:
        if self._done:
            return
        self._done = True
        self.finished.emit(ok, message)

    def _on_finished(self, exit_code: int, _exit_status) -> None:
        if self._cancelled:
            self._report(False, "Cancelled")
            return
        if exit_code != 0 or not self._wav_path.exists():
            output = bytes(self._proc.readAllStandardOutput()).decode(errors="replace").strip()
            # Piper often prints a traceback; the last line is the actual error.
            lines = [line for line in output.splitlines() if line.strip()]
            self._report(False, lines[-1] if lines else f"piper exited with code {exit_code}")
            return
        self._report(True, "")

    def _on_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.FailedToStart:
            self._report(False, "piper could not be started. Check that it is on your PATH.")
