from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from piperscribe.settings import AppSettings
from piperscribe.tts.piper_utils import check_piper_installed, iter_model_paths


class SettingsDialog(QDialog):
    """Modal settings dialog to edit theme + Piper voice parameters."""

    def __init__(self, parent, current: AppSettings) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings — PiperScribe")
        self.setModal(True)

        self._models = iter_model_paths()

        self.theme = QComboBox()
        self.theme.addItems(["System", "Light", "Dark"])
        self.theme.setCurrentIndex(0 if current.theme == "system" else (1 if current.theme == "light" else 2))

        self.voice = QComboBox()
        self.voice.setEnabled(bool(self._models))
        if not self._models:
            self.voice.addItem("(no voices found)")
        else:
            for p in self._models:
                self.voice.addItem(p.stem)

        self.model_path = QLineEdit(current.model_path or "")
        self.model_path.setPlaceholderText("Path to Piper .onnx model")

        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._browse_model)

        if current.model_path and self._models:
            try:
                mp = Path(os.path.expanduser(current.model_path)).resolve()
            except Exception:
                mp = Path(os.path.expanduser(current.model_path))
            for i, p in enumerate(self._models):
                try:
                    if p.resolve() == mp:
                        self.voice.setCurrentIndex(i)
                        break
                except Exception:
                    if str(p) == str(mp):
                        self.voice.setCurrentIndex(i)
                        break

        self.voice.currentIndexChanged.connect(self._voice_selected)

        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.5, 2.0)
        self.speed.setSingleStep(0.05)
        self.speed.setValue(float(current.speed))

        self.noise_scale = QDoubleSpinBox()
        self.noise_scale.setRange(0.0, 2.0)
        self.noise_scale.setSingleStep(0.05)
        self.noise_scale.setValue(float(current.noise_scale))

        self.noise_w = QDoubleSpinBox()
        self.noise_w.setRange(0.0, 2.0)
        self.noise_w.setSingleStep(0.05)
        self.noise_w.setValue(float(current.noise_w))

        self.auto_apply_rules = QCheckBox("Auto-apply rules on open/export")
        self.auto_apply_rules.setChecked(bool(getattr(current, "auto_apply_rules", True)))

        btn_test = QPushButton("Test Piper installation")
        btn_test.clicked.connect(self._test_piper)

        form = QFormLayout()
        form.addRow(QLabel("Theme:"), self.theme)
        form.addRow(QLabel("Voice:"), self.voice)

        model_row = QHBoxLayout()
        model_row.addWidget(self.model_path, 1)
        model_row.addWidget(btn_browse)
        form.addRow(QLabel("Model path:"), model_row)

        form.addRow(QLabel("Speed:"), self.speed)
        form.addRow(QLabel("Noise:"), self.noise_scale)
        form.addRow(QLabel("NoiseW:"), self.noise_w)
        form.addRow(QLabel("Rules:"), self.auto_apply_rules)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btn_test, alignment=Qt.AlignLeft)
        layout.addWidget(buttons)

    def _voice_selected(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._models):
            return
        self.model_path.setText(str(self._models[idx]))

    def _browse_model(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select Piper model (.onnx)",
            str(Path.home()),
            "ONNX model (*.onnx);;All files (*)",
        )
        if not path_str:
            return
        self.model_path.setText(path_str)

    def _test_piper(self) -> None:
        st = check_piper_installed()
        if not st.found:
            QMessageBox.warning(self, "Piper not found", st.error or "`piper` not found on PATH.")
            return
        QMessageBox.information(self, "Piper OK", f"Found Piper at:\n{st.path}")

    def result_settings(self) -> AppSettings:
        theme_label = self.theme.currentText().strip().lower()
        theme = {"system": "system", "light": "light", "dark": "dark"}.get(theme_label, "system")
        return AppSettings(
            theme=theme,
            model_path=self.model_path.text().strip(),
            speed=float(self.speed.value()),
            noise_scale=float(self.noise_scale.value()),
            noise_w=float(self.noise_w.value()),
                        auto_apply_rules=self.auto_apply_rules.isChecked(),
        )
