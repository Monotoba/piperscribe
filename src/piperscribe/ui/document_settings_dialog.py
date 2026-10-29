"""Document Settings Dialog for per-document TTS configuration."""
from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from piperscribe.model.document import Document, PiperSettings
from piperscribe.tts.piper_utils import check_piper_installed, iter_model_paths


class DocumentSettingsDialog(QDialog):
    """Dialog for editing per-document TTS settings."""

    def __init__(self, parent, document: Document):
        super().__init__(parent)
        self.document = document
        self.setWindowTitle(f"Document Settings — {document.title}")
        self.setModal(True)
        self.resize(600, 400)

        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Document info
        info_group = QGroupBox("Document Information")
        info_layout = QFormLayout(info_group)

        self.title_edit = QLineEdit()
        self.title_edit.setText(self.document.title)
        info_layout.addRow("Title:", self.title_edit)

        if self.document.source_path:
            source_label = QLabel(self.document.source_path)
            source_label.setWordWrap(True)
            info_layout.addRow("Source:", source_label)

        layout.addWidget(info_group)

        # TTS Settings
        tts_group = QGroupBox("Text-to-Speech Settings")
        tts_layout = QFormLayout(tts_group)

        # Voice model path
        voice_row = QHBoxLayout()
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("Path to .onnx model")
        voice_row.addWidget(self.model_path, 1)

        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._browse_model)
        voice_row.addWidget(self.btn_browse)

        tts_layout.addRow("Voice Model:", voice_row)

        # Speed (Length Scale)
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.1, 3.0)
        self.speed.setSingleStep(0.1)
        self.speed.setDecimals(1)
        self.speed.setSuffix("x")
        tts_layout.addRow("Speed:", self.speed)

        # Noise Scale
        self.noise_scale = QDoubleSpinBox()
        self.noise_scale.setRange(0.0, 2.0)
        self.noise_scale.setSingleStep(0.05)
        self.noise_scale.setDecimals(2)
        tts_layout.addRow("Noise Scale:", self.noise_scale)

        # Noise W
        self.noise_w = QDoubleSpinBox()
        self.noise_w.setRange(0.0, 2.0)
        self.noise_w.setSingleStep(0.05)
        self.noise_w.setDecimals(2)
        tts_layout.addRow("Noise W:", self.noise_w)

        layout.addWidget(tts_group)

        # Test voice button
        test_row = QHBoxLayout()
        test_row.addStretch()
        self.btn_test = QPushButton("Test Voice")
        self.btn_test.clicked.connect(self._test_voice)
        test_row.addWidget(self.btn_test)
        layout.addLayout(test_row)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self):
        """Load document settings into UI."""
        self.model_path.setText(self.document.piper.model_path)

        # Convert length_scale to speed (speed = 1.0 / length_scale)
        length_scale = self.document.piper.length_scale
        speed = 1.0 / length_scale if length_scale > 0 else 1.0
        self.speed.setValue(speed)

        self.noise_scale.setValue(self.document.piper.noise_scale)
        self.noise_w.setValue(self.document.piper.noise_w)

    def _browse_model(self):
        """Browse for voice model file."""
        from PySide6.QtWidgets import QFileDialog

        # Get available model paths
        model_index = iter_model_paths()
        if not model_index:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "No Voices Found",
                "No voice models found.\n\n"
                "Download voices using Tools → Browse & Download Voices."
            )
            return

        # Show model selection dialog (simplified - just show paths)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Voice Model",
            str(Path.home()),
            "ONNX Models (*.onnx);;All Files (*)"
        )

        if path:
            self.model_path.setText(path)

    def _test_voice(self):
        """Test the selected voice with sample text."""
        from PySide6.QtWidgets import QMessageBox

        status = check_piper_installed()
        if not status.found:
            QMessageBox.warning(
                self,
                "Piper Not Found",
                "Piper TTS is not installed or not found on PATH.\n\n"
                "Install Piper to test voice synthesis."
            )
            return

        model_path = self.model_path.text().strip()
        if not model_path or not Path(model_path).exists():
            QMessageBox.warning(
                self,
                "Invalid Model",
                "Please select a valid voice model file (.onnx)."
            )
            return

        # Create test settings from current UI values
        test_settings = PiperSettings(
            model_path=model_path,
            length_scale=1.0 / self.speed.value(),  # Convert speed back to length_scale
            noise_scale=self.noise_scale.value(),
            noise_w=self.noise_w.value(),
        )

        # Generate and play test audio
        try:
            from piperscribe.tts.piper import PiperTts

            test_text = "Hello! This is a test of the selected voice."

            with tempfile.TemporaryDirectory() as td:
                wav_path = Path(td) / "test.wav"

                tts = PiperTts(test_settings)
                tts.synthesize_to_wav(test_text, wav_path)

                # Play the audio
                self._play_audio(wav_path)

                QMessageBox.information(
                    self,
                    "Voice Test",
                    "Voice test completed successfully!"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test Failed",
                f"Failed to test voice:\n\n{e}"
            )

    def _play_audio(self, wav_path: Path):
        """Play audio file with the player chosen in settings, or the one found for this system."""
        import subprocess

        from piperscribe.audio.player import build_command, resolve_player
        from piperscribe.settings import load_settings

        resolution = resolve_player(load_settings().audio_player)
        if resolution.spec is None:
            return  # No player available; the test result is still reported
        try:
            subprocess.run(build_command(resolution.spec, wav_path), check=False)
        except Exception:
            pass  # Silent fail if playback not available

    def apply_settings(self):
        """Apply settings from dialog to document."""
        self.document.title = self.title_edit.text().strip() or "Untitled"

        # Update TTS settings
        self.document.piper.model_path = self.model_path.text().strip()
        self.document.piper.length_scale = 1.0 / self.speed.value()  # Convert speed to length_scale
        self.document.piper.noise_scale = self.noise_scale.value()
        self.document.piper.noise_w = self.noise_w.value()
