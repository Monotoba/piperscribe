from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFontComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from piperscribe.audio.player import AUTO, build_command, player_names, resolve_player
from piperscribe.model.document import PiperSettings
from piperscribe.settings import AppSettings, reset_settings
from piperscribe.tts.piper_utils import check_piper_installed, iter_model_paths
from piperscribe.ui.rules_editor import RulesEditorWidget


class PreferencesDialog(QDialog):
    """Preferences dialog for all app-wide settings."""

    def __init__(self, parent, current: AppSettings, document_text: str, apply_callback=None, initial_tab: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences — PiperScribe")
        self.setModal(True)
        # Set very conservative size to fit on small screens
        self.resize(750, 450)
        self.setMaximumHeight(500)

        self._text = document_text
        self._apply_callback = apply_callback
        self._current = current
        self._selected_model_path: str = current.model_path or ""
        self._models = self._discover_models(current.voice_dir)

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

        # Font settings
        self.use_default_font = QCheckBox("Use default font")
        self.use_default_font.setChecked(current.use_default_font)
        gf.addRow("", self.use_default_font)

        font_row = QHBoxLayout()
        self.font_family = QFontComboBox()
        if current.font_family:
            font = QFont(current.font_family)
            self.font_family.setCurrentFont(font)
        font_row.addWidget(self.font_family, 1)

        self.font_size = QSpinBox()
        self.font_size.setRange(6, 72)
        self.font_size.setValue(current.font_size if current.font_size > 0 else 12)
        self.font_size.setSuffix(" pt")
        font_row.addWidget(self.font_size)
        gf.addRow("Font:", font_row)

        # Enable/disable font controls based on checkbox
        def toggle_font_controls(checked: bool):
            self.font_family.setEnabled(not checked)
            self.font_size.setEnabled(not checked)
        self.use_default_font.toggled.connect(toggle_font_controls)
        toggle_font_controls(self.use_default_font.isChecked())

        # Color settings
        self.use_default_colors = QCheckBox("Use default colors")
        self.use_default_colors.setChecked(current.use_default_colors)
        gf.addRow("", self.use_default_colors)

        self._bg_color = current.doc_bg_color or "#ffffff"
        self._text_color = current.doc_text_color or "#000000"

        color_row = QHBoxLayout()
        self.btn_bg_color = QPushButton("Background")
        self.btn_bg_color.clicked.connect(self._choose_bg_color)
        self._update_color_button(self.btn_bg_color, self._bg_color)
        color_row.addWidget(self.btn_bg_color)

        self.btn_text_color = QPushButton("Text")
        self.btn_text_color.clicked.connect(self._choose_text_color)
        self._update_color_button(self.btn_text_color, self._text_color)
        color_row.addWidget(self.btn_text_color)
        color_row.addStretch(1)
        gf.addRow("Colors:", color_row)

        # Enable/disable color controls based on checkbox
        def toggle_color_controls(checked: bool):
            self.btn_bg_color.setEnabled(not checked)
            self.btn_text_color.setEnabled(not checked)
        self.use_default_colors.toggled.connect(toggle_color_controls)
        toggle_color_controls(self.use_default_colors.isChecked())

        gl.addLayout(gf)
        gl.addStretch(1)
        self.tabs.addTab(general, "Appearance")

        # --- Voice tab ---
        voice = QWidget()
        vl = QVBoxLayout(voice)
        vf = QFormLayout()

        self.voice = QComboBox()
        self.voice.setToolTip("Select the default voice from voices found in the directory below")

        self.voice_dir = QLineEdit(current.voice_dir or "")
        self.voice_dir.setPlaceholderText("~/.local/share/piper/voices  (leave blank for defaults)")
        self.voice_dir.editingFinished.connect(self._on_voice_dir_changed)
        btn_browse_dir = QPushButton("Browse…")
        btn_browse_dir.clicked.connect(self._browse_voice_dir)

        dir_row = QHBoxLayout()
        dir_row.addWidget(self.voice_dir, 1)
        dir_row.addWidget(btn_browse_dir)

        vf.addRow("Default voice:", self.voice)
        vf.addRow("Voice directory:", dir_row)

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

        self.audio_player = QComboBox()
        self.audio_player.setToolTip(
            "Program used to play previews. Default finds one for this system and saves it; "
            "Auto finds one on every run."
        )
        self.audio_player.addItem("Default (detect and save)", "")
        self.audio_player.addItem("Auto (detect every run)", AUTO)
        for name in player_names():
            self.audio_player.addItem(name, name)
        player_index = self.audio_player.findData(current.audio_player or "")
        self.audio_player.setCurrentIndex(max(player_index, 0))
        vf.addRow("Audio player:", self.audio_player)

        # Where generated audio is written. Empty = next to the project file.
        self.audio_output_dir = QLineEdit(current.audio_output_dir or "")
        self.audio_output_dir.setPlaceholderText("Empty: next to the project file")
        self.audio_output_dir.setToolTip(
            "Folder for generated audio. Leave empty to keep audio in a folder next to the project file."
        )
        btn_output_browse = QPushButton("Browse…")
        btn_output_browse.clicked.connect(self._browse_audio_output_dir)
        output_row = QHBoxLayout()
        output_row.addWidget(self.audio_output_dir, 1)
        output_row.addWidget(btn_output_browse)
        vf.addRow("Audio folder:", output_row)

        vl.addLayout(vf)

        # Voice management buttons
        btn_test_piper = QPushButton("Test Piper Installation")
        btn_test_piper.clicked.connect(self._test_piper)

        btn_test_voice = QPushButton("Test Selected Voice")
        btn_test_voice.clicked.connect(self._test_voice)

        btn_browse_voices = QPushButton("Browse && Download Voices…")
        btn_browse_voices.clicked.connect(self._browse_voices)

        btn_delete_voice = QPushButton("Delete Selected Voice")
        btn_delete_voice.clicked.connect(self._delete_voice)

        hl1 = QHBoxLayout()
        hl1.addWidget(btn_test_piper)
        hl1.addWidget(btn_test_voice)
        hl1.addStretch(1)
        vl.addLayout(hl1)

        hl2 = QHBoxLayout()
        hl2.addWidget(btn_browse_voices)
        hl2.addWidget(btn_delete_voice)
        hl2.addStretch(1)
        vl.addLayout(hl2)

        vl.addStretch(1)
        self.tabs.addTab(voice, "Voice")

        # Populate the voice dropdown from the configured directory
        self.voice.currentIndexChanged.connect(self._voice_selected)
        self._refresh_voice_list()

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

        # Wrap tabs in scroll area to ensure dialog fits on any screen
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.tabs)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area, 1)
        layout.addWidget(buttons)

        # Set initial tab
        self.tabs.setCurrentIndex(initial_tab)


    def _discover_models(self, voice_dir: str) -> list[Path]:
        vd = (voice_dir or "").strip()
        if vd:
            return iter_model_paths([Path(vd).expanduser()])
        return iter_model_paths()

    def _browse_voice_dir(self) -> None:
        start = self.voice_dir.text().strip() or str(Path.home() / ".local/share/piper/voices")
        path = QFileDialog.getExistingDirectory(self, "Select voice models directory", start)
        if not path:
            return
        self.voice_dir.setText(path)
        self._on_voice_dir_changed()

    def _on_voice_dir_changed(self) -> None:
        self._models = self._discover_models(self.voice_dir.text())
        self._refresh_voice_list()

    def _voice_selected(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._models):
            return
        self._selected_model_path = str(self._models[idx])

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

    def _sample_piper_args(self, model_path: Path) -> list[str]:
        """Piper arguments for the sample, using the speed and noise shown on this tab."""
        speed = max(0.1, float(self.speed.value()))
        return PiperSettings(
            model_path=str(model_path),
            length_scale=1.0 / speed,
            noise_scale=float(self.noise_scale.value()),
            noise_w=float(self.noise_w.value()),
        ).to_args()

    def _browse_audio_output_dir(self) -> None:
        start = self.audio_output_dir.text().strip() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Choose a folder for generated audio", start)
        if chosen:
            self.audio_output_dir.setText(chosen)

    def _test_voice(self) -> None:
        """Test the selected voice with sample text."""
        import tempfile

        # Check Piper is installed
        st = check_piper_installed()
        if not st.found:
            QMessageBox.warning(self, "Piper not found", st.error or "`piper` not found on PATH.")
            return

        # Get selected voice model path
        model_path = (self._selected_model_path or "").strip()
        if not model_path:
            QMessageBox.warning(self, "No Voice Selected", "Please select a voice model first.")
            return

        model_path_expanded = Path(model_path).expanduser()
        if not model_path_expanded.exists():
            QMessageBox.warning(self, "Voice Not Found", f"Voice model file not found:\n{model_path}")
            return

        # Sample text for testing
        sample_text = "Hello! This is a test of the selected voice. How does it sound?"

        # Create temp file for audio output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            # Run Piper to generate sample audio
            import subprocess
            result = subprocess.run(
                ["piper", *self._sample_piper_args(model_path_expanded), "--output_file", wav_path],
                input=sample_text.encode('utf-8'),
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='replace')
                QMessageBox.critical(self, "Piper Error", f"Failed to generate audio:\n{error_msg}")
                return

            # Play with the player chosen in Voice settings, or the one found for this system
            resolution = resolve_player(self.audio_player.currentData() or "")
            if resolution.spec is None:
                QMessageBox.information(
                    self,
                    "Audio Generated",
                    f"Audio generated successfully but no audio player was found.\n\nFile saved to: {wav_path}"
                )
            else:
                try:
                    subprocess.run(build_command(resolution.spec, Path(wav_path)), check=True, timeout=10)
                except Exception as e:
                    QMessageBox.warning(self, "Playback Error", f"Failed to play audio:\n{e}")

        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, "Timeout", "Voice test timed out.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to test voice:\n{e}")
        finally:
            # Clean up temp file
            try:
                Path(wav_path).unlink()
            except Exception:
                pass

    def _refresh_voice_list(self) -> None:
        """Refresh the voice dropdown list from the configured voice directory."""
        self._models = self._discover_models(self.voice_dir.text())
        self.voice.blockSignals(True)
        self.voice.clear()
        if not self._models:
            self.voice.addItem("(no voices found)")
            self.voice.setEnabled(False)
        else:
            self.voice.setEnabled(True)
            for p in self._models:
                self.voice.addItem(p.stem)
            if self._selected_model_path:
                self._sync_voice_from_path(self._selected_model_path)
        self.voice.blockSignals(False)
        # If nothing matched but we have models, snap selection to first
        if self._models and self.voice.currentIndex() < 0:
            self.voice.setCurrentIndex(0)
            self._selected_model_path = str(self._models[0])

    def _browse_voices(self) -> None:
        """Open voice browser dialog."""
        from piperscribe.ui.voice_browser import VoiceBrowserDialog

        dlg = VoiceBrowserDialog(self, self._current.voice_repositories)
        # Connect signal to refresh voice list immediately when download completes
        dlg.voice_downloaded.connect(self._refresh_voice_list)
        # Refresh after dialog closes (covers the case of multiple downloads)
        dlg.exec()
        self._refresh_voice_list()

    def _delete_voice(self) -> None:
        """Delete the selected voice model."""
        model_path = (self._selected_model_path or "").strip()
        if not model_path:
            QMessageBox.warning(self, "No Voice Selected", "Please select a voice model to delete.")
            return

        model_path_expanded = Path(model_path).expanduser()
        if not model_path_expanded.exists():
            QMessageBox.warning(self, "Voice Not Found", f"Voice model file not found:\n{model_path}")
            return

        # Confirm deletion
        voice_name = model_path_expanded.stem
        resp = QMessageBox.question(
            self,
            "Delete Voice",
            f"Are you sure you want to delete this voice?\n\n{voice_name}\n\nThis will delete:\n- {model_path_expanded.name}\n- {model_path_expanded.name}.json (if present)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if resp != QMessageBox.Yes:
            return

        try:
            # Delete .onnx file
            model_path_expanded.unlink()

            # Delete .onnx.json file if it exists
            json_file = Path(str(model_path_expanded) + ".json")
            if json_file.exists():
                json_file.unlink()

            QMessageBox.information(self, "Voice Deleted", f"Voice '{voice_name}' has been deleted.")

            # Clear current selection and refresh voice list
            self._selected_model_path = ""
            self._refresh_voice_list()

        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", f"Failed to delete voice:\n{e}")

    def _update_color_button(self, button: QPushButton, color_hex: str) -> None:
        """Update button style to show the selected color."""
        button.setStyleSheet(f"background-color: {color_hex}; color: {'#000000' if self._is_light_color(color_hex) else '#ffffff'};")

    def _is_light_color(self, color_hex: str) -> bool:
        """Check if a color is light (for contrast)."""
        try:
            color = QColor(color_hex)
            # Calculate perceived brightness
            brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
            return brightness > 128
        except Exception:
            return True

    def _choose_bg_color(self) -> None:
        """Open color dialog for background color."""
        color = QColorDialog.getColor(QColor(self._bg_color), self, "Choose Background Color")
        if color.isValid():
            self._bg_color = color.name()
            self._update_color_button(self.btn_bg_color, self._bg_color)

    def _choose_text_color(self) -> None:
        """Open color dialog for text color."""
        color = QColorDialog.getColor(QColor(self._text_color), self, "Choose Text Color")
        if color.isValid():
            self._text_color = color.name()
            self._update_color_button(self.btn_text_color, self._text_color)

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
            model_path=(self._selected_model_path or "").strip(),
            voice_dir=self.voice_dir.text().strip(),
            speed=float(self.speed.value()),
            noise_scale=float(self.noise_scale.value()),
            noise_w=float(self.noise_w.value()),
            rules=self.rules_editor.rules(),
            auto_apply_rules=self.auto_apply_rules.isChecked(),
            show_selection_toolbar=self.show_selection_toolbar.isChecked(),
            font_family=self.font_family.currentFont().family(),
            font_size=int(self.font_size.value()),
            use_default_font=self.use_default_font.isChecked(),
            doc_bg_color=self._bg_color,
            doc_text_color=self._text_color,
            use_default_colors=self.use_default_colors.isChecked(),
            audio_player=self.audio_player.currentData() or "",
            audio_output_dir=self.audio_output_dir.text().strip(),
        )
