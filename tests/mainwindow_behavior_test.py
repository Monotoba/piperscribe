"""Behavior tests for the main window: voices, settings, audio state, generation, and saving.

Piper is replaced by a fake job, and message boxes are stubbed, so these run on CI
runners that have no Piper and no audio device.
"""
import shutil
import sys
import time
from pathlib import Path
from typing import ClassVar
from unittest import mock

import pytest
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication

from piperscribe.model.document import Document, PiperSettings

VOICE_A = "/voices/en_US-amy-medium.onnx"
VOICE_B = "/voices/en_US-lessac-medium.onnx"


def _wait_until(app, condition, timeout=10.0):
    deadline = time.time() + timeout
    while not condition() and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return condition()


class FakePiperRun(QObject):
    """Stands in for PiperRun: writes a placeholder WAV and reports success on the next tick."""

    finished = Signal(bool, str)
    calls: ClassVar[list] = []
    hold = False  # when True, the job waits until cancel() is called
    last = None

    def __init__(self, parent, settings, text, wav_path):
        super().__init__(parent)
        self.settings = settings
        self.text = text
        self.wav_path = Path(wav_path)
        self._cancelled = False
        FakePiperRun.last = self

    def start(self):
        FakePiperRun.calls.append((round(self.settings.length_scale, 3), self.settings.model_path, self.text))
        if not FakePiperRun.hold:
            self.wav_path.write_bytes(b"RIFF")
            QTimer.singleShot(0, lambda: self.finished.emit(True, ""))

    def cancel(self):
        self._cancelled = True
        QTimer.singleShot(0, lambda: self.finished.emit(False, "Cancelled"))


class _Buttons:
    """Returns one stable object per button label, and reports the discard button as clicked."""

    def __init__(self):
        self.by_label = {}

    def add(self, label, role=None):
        return self.by_label.setdefault(label, object())


@pytest.fixture
def app():
    return QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def window(app, tmp_path):
    import piperscribe.ui.main_window as mw

    buttons = _Buttons()
    with mock.patch.object(mw, "QMessageBox") as box, \
         mock.patch.object(mw, "PiperRun", FakePiperRun):
        box.return_value.addButton.side_effect = buttons.add
        box.return_value.clickedButton.side_effect = lambda: buttons.by_label["Discard Audio"]
        FakePiperRun.calls.clear()
        FakePiperRun.hold = False
        w = mw.MainWindow()
        w.show()
        app.processEvents()
        w._get_project_audio_dir = lambda: tmp_path / "audio"
        w._ensure_piper_ready = lambda: True
        w.project.piper.model_path = VOICE_A
        w.project.documents.clear()
        # Use fixed voice names, so the tests do not depend on the voices installed on the machine.
        voice_dir = tmp_path / "voices"
        voice_dir.mkdir()
        for name in ("en_US-amy-medium", "en_US-lessac-medium", "de_DE-thorsten-high"):
            (voice_dir / f"{name}.onnx").write_bytes(b"")
        w._model_index = sorted(voice_dir.glob("*.onnx"))
        w._populate_voice_combo()
        w.box = box
        yield w
        w.close()


def _doc(window, doc_id, title, text, voice=None, **piper):
    settings = PiperSettings.from_dict(window.project.piper.as_dict())
    if voice is not None:
        settings.model_path = voice
    for key, value in piper.items():
        setattr(settings, key, value)
    doc = Document(id=doc_id, title=title, text=text, piper=settings)
    window.project.documents.append(doc)
    window._refresh_view()
    return doc


def _select(window, doc):
    for row in range(window.doc_list.count()):
        if window.doc_list.item(row).data(Qt.UserRole) == doc.id:
            window.doc_list.setCurrentRow(row)
            return


def _generate(window, app, doc):
    _select(window, doc)
    window.on_generate_document_audio()
    assert _wait_until(app, lambda: window._gen is None)


# --- voice and settings -------------------------------------------------------

def test_audio_fingerprint_changes_with_voice_speed_noise_and_text(window):
    piper = PiperSettings(model_path=VOICE_A, length_scale=1.0, noise_scale=0.667, noise_w=0.8)
    base = window._audio_signature("Hello.", piper)
    assert window._audio_signature("Hello.", piper) == base
    assert window._audio_signature("Hello again.", piper) != base
    assert window._audio_signature("Hello.", PiperSettings(VOICE_B, 1.0, 0.667, 0.8)) != base
    assert window._audio_signature("Hello.", PiperSettings(VOICE_A, 1.5, 0.667, 0.8)) != base
    assert window._audio_signature("Hello.", PiperSettings(VOICE_A, 1.0, 0.5, 0.8)) != base


def test_toolbar_voice_moves_project_voice_documents_only(window):
    imported = _doc(window, "aaaa1111", "Imported", "one", voice=VOICE_A)
    custom = _doc(window, "bbbb2222", "Custom", "two", voice="/voices/de_DE-thorsten-high.onnx")
    idx = next(i for i in range(window.voice_combo.count()) if "lessac" in window.voice_combo.itemText(i))
    window.voice_combo.setCurrentIndex(idx)
    assert Path(window.project.piper.model_path).name == "en_US-lessac-medium.onnx"
    assert Path(imported.piper.model_path).name == "en_US-lessac-medium.onnx"
    assert custom.piper.model_path == "/voices/de_DE-thorsten-high.onnx"


def test_speed_change_moves_documents_on_project_speed_only(window):
    imported = _doc(window, "aaaa1111", "Imported", "one")
    custom = _doc(window, "bbbb2222", "Custom", "two", length_scale=0.8)
    window.speed.setValue(1.5)
    assert imported.piper.length_scale == pytest.approx(window.project.piper.length_scale)
    assert custom.piper.length_scale == pytest.approx(0.8)


def test_refreshing_the_window_changes_no_document(window):
    doc = _doc(window, "aaaa1111", "Imported", "one", length_scale=0.8, noise_scale=0.3)
    before = (doc.piper.length_scale, doc.piper.noise_scale, doc.piper.noise_w)
    window._refresh_view()
    assert (doc.piper.length_scale, doc.piper.noise_scale, doc.piper.noise_w) == before


def test_preview_sample_uses_the_speed_and_noise_on_the_voice_tab(window):
    from piperscribe.settings import AppSettings
    from piperscribe.ui.preferences_dialog import PreferencesDialog

    dialog = PreferencesDialog(window, AppSettings.from_dict(window._app_settings.to_dict()), "",
                               apply_callback=None, initial_tab=1)
    dialog.speed.setValue(1.25)
    dialog.noise_scale.setValue(0.4)
    dialog.noise_w.setValue(0.9)
    args = dialog._sample_piper_args(Path("/voices/x.onnx"))
    assert Path(args[1]) == Path("/voices/x.onnx")
    assert args[2:] == ["--length_scale", "0.8", "--noise_scale", "0.4", "--noise_w", "0.9"]
    dialog.close()


# --- audio state and generation ----------------------------------------------

def test_generation_records_the_fingerprint_and_path(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    assert doc.audio_path and Path(doc.audio_path).exists()
    assert doc.audio_signature
    assert window._audio_is_current(doc)
    assert FakePiperRun.calls[-1][1] == VOICE_A


def test_stale_audio_is_marked_and_regenerated_on_play(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    window.project.piper.length_scale = 1.5  # the voice settings changed after generation
    doc.piper.length_scale = 1.5
    assert not window._audio_is_current(doc)
    assert "↻" in window._audio_state(doc)[0]

    played = []
    with mock.patch.object(window, "on_play_document_audio", side_effect=lambda d: played.append(d.id)):
        _select(window, doc)
        window.on_play_audio()
        assert _wait_until(app, lambda: played)
    assert played == [doc.id]
    assert FakePiperRun.calls[-1][0] == pytest.approx(1.5, abs=1e-3)
    assert window._audio_is_current(doc)


def test_play_does_not_regenerate_current_audio(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    calls_before = len(FakePiperRun.calls)
    played = []
    with mock.patch.object(window, "on_play_document_audio", side_effect=lambda d: played.append(d.id)):
        _select(window, doc)
        window.on_play_audio()
    assert played == [doc.id]
    assert len(FakePiperRun.calls) == calls_before


def test_cancel_keeps_previous_audio(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    previous = doc.audio_path
    FakePiperRun.hold = True
    _select(window, doc)
    window.on_generate_document_audio()
    assert _wait_until(app, lambda: window._gen is not None and window._gen["run"] is not None)
    window._cancel_generation()
    assert _wait_until(app, lambda: window._gen is None)
    assert doc.audio_path == previous


# --- selection and list ---------------------------------------------------------

def test_selecting_a_document_only_highlights_it(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    other = _doc(window, "bbbb2222", "Other", "Something else.")
    played = []
    with mock.patch.object(window, "on_play_document_audio", side_effect=lambda d: played.append(d.id)):
        _select(window, other)
        _select(window, doc)  # the selection that must not start playback
        app.processEvents()
    assert played == []


def test_rebuilding_the_list_does_not_start_playback(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    played = []
    with mock.patch.object(window, "on_play_document_audio", side_effect=lambda d: played.append(d.id)):
        _select(window, doc)
        window._rebuild_document_list()
        app.processEvents()
    assert played == []


def test_document_list_marks_current_and_out_of_date_audio(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    assert window._audio_state(doc)[0] == "⚫"
    _generate(window, app, doc)
    assert window._audio_state(doc)[0] == "🔊"
    doc.piper.length_scale = 1.4
    window._refresh_document_icons()
    assert window.doc_list.item(0).text().endswith("↻ Story")


def test_opened_document_is_shown_in_the_editor(window, app, tmp_path):
    import piperscribe.ui.main_window as mw

    story = tmp_path / "story.txt"
    story.write_text("Once upon a time, the story begins here.", encoding="utf-8")
    with mock.patch.object(mw.QFileDialog, "getOpenFileNames", return_value=([str(story)], "")):
        window.on_import_documents()
    app.processEvents()
    assert window.editor.toPlainText().startswith("Once upon a time")


# --- saving and exit -------------------------------------------------------------

def test_save_audio_to_folder_copies_audio_and_updates_paths(window, app, tmp_path):
    import piperscribe.ui.main_window as mw

    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    parent = tmp_path / "saved"
    parent.mkdir()
    with mock.patch.object(mw.QFileDialog, "getExistingDirectory", return_value=str(parent)), \
         mock.patch.object(mw.QInputDialog, "getText", return_value=("My Book", True)):
        dest = window.on_save_audio_to_folder()
    assert dest == parent / "My Book"
    assert (dest / Path(doc.audio_path).name).exists()
    assert Path(doc.audio_path).parent == dest


def test_closing_with_temp_audio_can_be_cancelled(window, app):
    doc = _doc(window, "aaaa1111", "Story", "Once upon a time.")
    _generate(window, app, doc)
    # Generated audio is in the temp folder only when the audio folder is the temp folder.
    temp_dir = window._temp_audio_dir()
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / "cancel-test.wav"
    shutil.copy(doc.audio_path, temp_file)
    doc.audio_path = str(temp_file)

    buttons = window.box.return_value
    cancel = object()
    buttons.clickedButton.side_effect = lambda: cancel
    buttons.addButton.side_effect = lambda label, role=None: cancel if label == "Cancel" else object()
    from PySide6.QtGui import QCloseEvent
    event = QCloseEvent()
    window.closeEvent(event)
    assert not event.isAccepted()
    temp_file.unlink(missing_ok=True)


def test_closing_without_temp_audio_is_silent(window, app):
    from PySide6.QtGui import QCloseEvent
    event = QCloseEvent()
    window.closeEvent(event)
    assert event.isAccepted()
    assert not window.box.return_value.exec.called
