from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from piperscribe.settings import AppSettings, reset_settings
from piperscribe.tts.piper_utils import check_piper_installed, iter_model_paths
from piperscribe.ui.rules_editor import RulesEditorWidget


class PreferencesDialog(QDialog):
    """Preferences dialog for all app-wide settings."""

    def __init__(self, parent, current: AppSettings, document_text: str, apply_callback=None, initial_tab: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences — PiperScribe")
        self.setModal(True)

        self._text = document_text
        self._apply_callback = apply_callback
        self._current = current
        self._models = iter_model_paths()

        self.tabs = QTabWidget()

        # --- General tab ---
        general = QWidget()
        gl = QVBoxLayout(general)
        gf = QFormLayout()
        self.theme = QComboBox()
        self.theme.addItems(["System", "Light", "Dark"])
        self.theme.setCurrentIndex(0 if current.theme == "system" else (1 if current.theme == "light" else 2))
        gf.addRow("Theme:", self.theme)
        self.show_selection_toolbar = QCheckBox("Show selection toolbar (Exclude/Include/Preview/Stop)")
        self.show_selection_toolbar.setChecked(bool(getattr(current, "show_selection_toolbar", True)))
        gf.addRow("Selection tools:", self.show_selection_toolbar)
        gl.addLayout(gf)
        gl.addStretch(1)
        self.tabs.addTab(general, "Appearance")

        # --- Voice tab ---
        voice = QWidget()
        vl = QVBoxLayout(voice)
        vf = QFormLayout()

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

        row = QHBoxLayout()
        row.addWidget(self.model_path, 1)
        row.addWidget(btn_browse)

        vf.addRow("Voice:", self.voice)
        vf.addRow("Model path:", row)

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

        vf.addRow("Speed:", self.speed)
        vf.addRow("Noise:", self.noise_scale)
        vf.addRow("NoiseW:", self.noise_w)

        self.auto_apply_rules = QCheckBox("Auto-apply rules on open/export")
        self.auto_apply_rules.setChecked(bool(getattr(current, "auto_apply_rules", True)))
        vf.addRow("Rules:", self.auto_apply_rules)

        vl.addLayout(vf)

        btn_test = QPushButton("Test Piper installation")
        btn_test.clicked.connect(self._test_piper)

        hl = QHBoxLayout()
        hl.addWidget(btn_test)
        hl.addStretch(1)
        vl.addLayout(hl)
        vl.addStretch(1)
        self.tabs.addTab(voice, "Voice")

        # Align voice dropdown to model_path when possible
        self.voice.currentIndexChanged.connect(self._voice_selected)
        self._sync_voice_from_path(current.model_path)

        # --- Rules tab ---
        rules = QWidget()
        rl = QVBoxLayout(rules)

        self.btn_reapply_hint = QLabel(
            "Configure regex rules to automatically exclude repeated content like headers, footers, URLs, etc.\n"
            "Rules are applied when you click 'Reapply Rules' in the Tools menu."
        )
        self.btn_reapply_hint.setWordWrap(True)
        rl.addWidget(self.btn_reapply_hint)
        rl.addSpacing(12)

        self.rules_editor = RulesEditorWidget(self, current.rules or [], document_text)
        rl.addWidget(self.rules_editor, 1)
        rl.addSpacing(12)

        self.btn_reset = QPushButton("Reset Settings to Defaults")
        self.btn_reset.clicked.connect(self._reset_settings_clicked)
        rl.addWidget(self.btn_reset, alignment=Qt.AlignLeft)

        self.tabs.addTab(rules, "Rules")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._apply_now)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(buttons)

        # Set initial tab
        self.tabs.setCurrentIndex(initial_tab)


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
        self._sync_voice_from_path(path_str)

    def _voice_selected(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._models):
            return
        self.model_path.setText(str(self._models[idx]))

    def _sync_voice_from_path(self, model_path: str | None) -> None:
        if not model_path or not self._models:
            return
        try:
            mp = Path(model_path).expanduser().resolve()
        except Exception:
            mp = Path(model_path).expanduser()
        for i, p in enumerate(self._models):
            try:
                if p.resolve() == mp:
                    self.voice.setCurrentIndex(i)
                    return
            except Exception:
                if str(p) == str(mp):
                    self.voice.setCurrentIndex(i)
                    return

    def _test_piper(self) -> None:
        st = check_piper_installed()
        if not st.found:
            QMessageBox.warning(self, "Piper not found", st.error or "`piper` not found on PATH.")
            return
        QMessageBox.information(self, "Piper OK", f"Found Piper at:\n{st.path}")
    def _apply_now(self) -> None:
        if self._apply_callback is None:
            return
        self._apply_callback(self.result_settings())

    def _reset_settings_clicked(self) -> None:
        resp = QMessageBox.question(
            self,
            "Reset settings",
            "Delete your saved settings file and reset to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return
        reset_settings()
        QMessageBox.information(self, "Reset complete", "Settings were reset. Click OK to close, then reopen Preferences.")

    def result_settings(self) -> AppSettings:
        theme_label = self.theme.currentText().strip().lower()
        theme = {"system": "system", "light": "light", "dark": "dark"}.get(theme_label, "system")
        return AppSettings(
            theme=theme,
            model_path=self.model_path.text().strip(),
            speed=float(self.speed.value()),
            noise_scale=float(self.noise_scale.value()),
            noise_w=float(self.noise_w.value()),
            rules=self.rules_editor.rules(),
            auto_apply_rules=self.auto_apply_rules.isChecked(),
            show_selection_toolbar=self.show_selection_toolbar.isChecked(),
        )
