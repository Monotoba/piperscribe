from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QTimer
from PySide6.QtGui import QAction, QTextCharFormat, QTextCursor, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QDoubleSpinBox,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QProgressDialog,
)

from piperscribe.importers.registry import import_any
from piperscribe.model.document import DocumentProject
from piperscribe.model.spans import Span, normalize_spans
from piperscribe.rules import apply_rules
from piperscribe.audio.export import included_text
from piperscribe.tts.piper_utils import check_piper_installed, iter_model_paths, choose_default_model
from piperscribe.settings import AppSettings, load_settings, save_settings
from piperscribe.ui.preferences_dialog import PreferencesDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PiperScribe v0.1.20")

        self.project = DocumentProject()
        self._app_settings = load_settings()
        # Apply persisted defaults before scanning voices
        self.project.theme = self._app_settings.theme
        self.project.piper.model_path = self._app_settings.model_path
        self.project.piper.length_scale = float(self._speed_to_length_scale(self._app_settings.speed))
        self.project.piper.noise_scale = self._app_settings.noise_scale
        self.project.piper.noise_w = self._app_settings.noise_w
        self._model_index: list[Path] = []

        self._tts_proc: QProcess | None = None
        self._play_proc: QProcess | None = None
        self._progress: QProgressDialog | None = None

        self._build_ui()
        self._init_piper_environment()
        self._refresh_view()

    def _build_ui(self) -> None:
        # Menus
        menubar = self.menuBar()
        m_file = menubar.addMenu("&File")
        m_edit = menubar.addMenu("&Edit")
        m_tools = menubar.addMenu("&Tools")
        m_help = menubar.addMenu("&Help")
        menubar.setNativeMenuBar(False)

        # Recent
        self._menu_recent_files = m_file.addMenu("Recent Files")
        self._menu_recent_projects = m_file.addMenu("Recent Projects")
        self._menu_recent_files.aboutToShow.connect(self._rebuild_recent_files_menu)
        self._menu_recent_projects.aboutToShow.connect(self._rebuild_recent_projects_menu)

        # Selection actions (Tools menu + optional dockable toolbar)
        self.act_exclude = QAction("Exclude selection", self)
        self.act_exclude.triggered.connect(self.on_exclude_selection)

        self.act_include = QAction("Include selection", self)
        self.act_include.triggered.connect(self.on_include_selection)

        self.act_preview = QAction("Preview selection", self)
        self.act_preview.triggered.connect(self.on_preview_selection)

        self.act_stop = QAction("Stop", self)
        self.act_stop.triggered.connect(self.on_stop_preview)

        act_new_project = QAction("New Project", self)
        act_new_project.setShortcut("Ctrl+N")
        act_new_project.triggered.connect(self.on_new_project)
        m_file.addAction(act_new_project)

        act_open = QAction("Open…", self)
        act_open.triggered.connect(self.on_open)
        m_file.addAction(act_open)

        act_save_proj = QAction("Save Project…", self)
        act_save_proj.triggered.connect(self.on_save_project)
        m_file.addAction(act_save_proj)

        act_load_proj = QAction("Load Project…", self)
        act_load_proj.triggered.connect(self.on_load_project)
        m_file.addAction(act_load_proj)

        act_close_proj = QAction("Close Project", self)
        act_close_proj.triggered.connect(self.on_close_project)
        m_file.addAction(act_close_proj)

        m_file.addSeparator()

        act_export = QAction("Export WAV…", self)
        act_export.triggered.connect(self.on_export_wav)
        m_file.addAction(act_export)

        m_file.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        act_prefs = QAction("Preferences…", self)
        act_prefs.triggered.connect(self.on_preferences)
        m_edit.addAction(act_prefs)

        act_find = QAction("Find…", self)
        act_find.setShortcut("Ctrl+F")
        act_find.triggered.connect(self.on_find)
        m_edit.addAction(act_find)

        # Tools menu
        m_tools.addAction(self.act_exclude)
        m_tools.addAction(self.act_include)
        m_tools.addAction(self.act_preview)
        m_tools.addAction(self.act_stop)
        m_tools.addSeparator()

        act_rules = QAction("Rules…", self)
        act_rules.triggered.connect(self.on_rules)
        m_tools.addAction(act_rules)

        act_reapply = QAction("Reapply Rules", self)
        act_reapply.triggered.connect(self.on_reapply_rules)
        m_tools.addAction(act_reapply)

        m_tools.addSeparator()
        act_import_voice = QAction("Import Voice Model…", self)
        act_import_voice.triggered.connect(self.on_import_voice_model)
        m_tools.addAction(act_import_voice)

        act_browse_voices = QAction("Browse && Download Voices…", self)
        act_browse_voices.triggered.connect(self.on_browse_voices)
        m_tools.addAction(act_browse_voices)

        # Help menu
        act_help_contents = QAction("Help Contents…", self)
        act_help_contents.setShortcut("F1")
        act_help_contents.triggered.connect(self.on_help_contents)
        m_help.addAction(act_help_contents)

        m_help.addSeparator()

        act_about = QAction("About PiperScribe", self)
        act_about.triggered.connect(self.on_about)
        m_help.addAction(act_about)

        # Dockable selection toolbar (toggle in Preferences → Appearance)
        self.selection_tb = QToolBar("Selection Tools", self)
        self.selection_tb.setMovable(True)
        self.selection_tb.setFloatable(True)
        self.selection_tb.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        self.selection_tb.addAction(self.act_exclude)
        self.selection_tb.addAction(self.act_include)
        self.selection_tb.addAction(self.act_preview)
        self.selection_tb.addAction(self.act_stop)

        self.addToolBar(Qt.TopToolBarArea, self.selection_tb)
        self.selection_tb.setVisible(bool(getattr(self._app_settings, "show_selection_toolbar", True)))

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # NOTE: You previously wanted these moved into Preferences.
        # They are still here for now; move later once Preferences is complete.

        settings_row = QHBoxLayout()
        layout.addLayout(settings_row)

        settings_row.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.setToolTip("Select a Piper .onnx voice/model discovered on this system")
        self.voice_combo.currentIndexChanged.connect(self.on_voice_selected)
        settings_row.addWidget(self.voice_combo)

        settings_row.addWidget(QLabel("Model path:"))
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("~/.local/share/piper/voices/xxx.onnx")
        self.model_path.editingFinished.connect(self.on_settings_changed)
        settings_row.addWidget(self.model_path, 1)

        btn_browse_model = QPushButton("Browse…")
        btn_browse_model.clicked.connect(self.on_browse_model)
        settings_row.addWidget(btn_browse_model)

        settings_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.theme_combo.setToolTip("Choose app theme. System uses your desktop theme.")
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        settings_row.addWidget(self.theme_combo)

        speed_row = QHBoxLayout()
        layout.addLayout(speed_row)

        speed_row.addWidget(QLabel("Speed:"))
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.5, 2.0)
        self.speed.setSingleStep(0.05)
        self.speed.setValue(1.0)
        self.speed.setToolTip("Higher = faster. Maps to Piper length_scale inversely.")
        self.speed.valueChanged.connect(self.on_settings_changed)
        speed_row.addWidget(self.speed)

        speed_row.addWidget(QLabel("Noise:"))
        self.noise_scale = QDoubleSpinBox()
        self.noise_scale.setRange(0.0, 2.0)
        self.noise_scale.setSingleStep(0.05)
        self.noise_scale.setValue(0.667)
        self.noise_scale.valueChanged.connect(self.on_settings_changed)
        speed_row.addWidget(self.noise_scale)

        speed_row.addWidget(QLabel("NoiseW:"))
        self.noise_w = QDoubleSpinBox()
        self.noise_w.setRange(0.0, 2.0)
        self.noise_w.setSingleStep(0.05)
        self.noise_w.setValue(0.8)
        self.noise_w.valueChanged.connect(self.on_settings_changed)
        speed_row.addWidget(self.noise_w)

        buttons = QHBoxLayout()
        layout.addLayout(buttons)

        self.btn_exclude = QPushButton("Exclude selection")
        self.btn_exclude.clicked.connect(self.on_exclude_selection)
        buttons.addWidget(self.btn_exclude)

        self.btn_include = QPushButton("Include selection")
        self.btn_include.clicked.connect(self.on_include_selection)
        buttons.addWidget(self.btn_include)

        self.btn_preview = QPushButton("Preview selection")
        self.btn_preview.clicked.connect(self.on_preview_selection)
        buttons.addWidget(self.btn_preview)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.on_stop)
        buttons.addWidget(self.btn_stop)

        buttons.addStretch(1)

        self.stats = QLabel("")
        self.stats.setTextInteractionFlags(Qt.TextSelectableByMouse)
        buttons.addWidget(self.stats)

        # Find bar (Ctrl+F)
        self.find_bar = QWidget()
        fb = QHBoxLayout(self.find_bar)
        fb.setContentsMargins(0, 0, 0, 0)
        fb.addWidget(QLabel("Find:"))
        self.find_text = QLineEdit()
        self.find_text.setPlaceholderText("Search…")
        self.find_text.returnPressed.connect(self.on_find_next)
        fb.addWidget(self.find_text, 1)
        btn_prev = QPushButton("Prev")
        btn_prev.clicked.connect(self.on_find_prev)
        fb.addWidget(btn_prev)
        btn_next = QPushButton("Next")
        btn_next.clicked.connect(self.on_find_next)
        fb.addWidget(btn_next)
        btn_close = QPushButton("×")
        btn_close.setFixedWidth(28)
        btn_close.clicked.connect(lambda: self.find_bar.setVisible(False))
        fb.addWidget(btn_close)
        self.find_bar.setVisible(False)
        layout.addWidget(self.find_bar)

        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        layout.addWidget(self.editor, 1)

    def _init_piper_environment(self) -> None:
        status = check_piper_installed()
        if not status.found:
            QMessageBox.warning(
                self,
                "Piper not found",
                "The `piper` command was not found on PATH.\n\n"
                "Install Piper and ensure `piper --help` works in a terminal.\n"
                "You can still import and mark exclusions, but Preview/Export will fail until Piper is installed.",
            )

        self._model_index = iter_model_paths()
        self.voice_combo.clear()
        if not self._model_index:
            self.voice_combo.addItem("(no voices found)")
            self.voice_combo.setEnabled(False)
        else:
            self.voice_combo.setEnabled(True)
            for p in self._model_index:
                self.voice_combo.addItem(p.stem)

            if self.project.piper.model_path:
                self._select_voice_by_path(self.project.piper.model_path)
            else:
                default = choose_default_model(self._model_index)
                if default:
                    self._set_model_path(str(default))

    def _select_voice_by_path(self, model_path: str) -> None:
        try:
            mp = Path(os.path.expanduser(model_path)).resolve()
        except Exception:
            mp = Path(os.path.expanduser(model_path))
        for i, p in enumerate(self._model_index):
            try:
                if p.resolve() == mp:
                    self.voice_combo.setCurrentIndex(i)
                    return
            except Exception:
                if str(p) == str(mp):
                    self.voice_combo.setCurrentIndex(i)
                    return

    def _set_model_path(self, path: str) -> None:
        self.model_path.setText(path)
        self._sync_piper_settings_from_ui()

    def on_voice_selected(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._model_index):
            return
        self._set_model_path(str(self._model_index[idx]))
        self._persist_app_settings()

    def _refresh_view(self) -> None:
        self.editor.setPlainText(self.project.text)
        self._apply_theme(self.project.theme)
        self._apply_document_appearance()
        self.model_path.setText(self.project.piper.model_path)
        # Theme combo
        t = (self.project.theme or "system").lower()
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(0 if t == "system" else (1 if t == "light" else 2))
        self.theme_combo.blockSignals(False)
        self.speed.setValue(self._length_scale_to_speed(self.project.piper.length_scale))
        self.noise_scale.setValue(self.project.piper.noise_scale)
        self.noise_w.setValue(self.project.piper.noise_w)

        if self._model_index and self.project.piper.model_path:
            self._select_voice_by_path(self.project.piper.model_path)

        self._recompute_exclusions()
        self._apply_exclusion_formatting()
        self._update_stats()

    @staticmethod
    def _speed_to_length_scale(speed: float) -> float:
        speed = max(0.1, float(speed))
        return 1.0 / speed

    @staticmethod
    def _length_scale_to_speed(length_scale: float) -> float:
        ls = max(0.1, float(length_scale))
        return 1.0 / ls

    def on_settings_changed(self, _val=None) -> None:
        self._sync_piper_settings_from_ui()
        self._persist_app_settings()

    def _sync_piper_settings_from_ui(self) -> None:
        mp = os.path.expanduser(self.model_path.text().strip())
        self.project.piper.model_path = mp
        self.project.piper.length_scale = float(self._speed_to_length_scale(self.speed.value()))
        self.project.piper.noise_scale = float(self.noise_scale.value())
        self.project.piper.noise_w = float(self.noise_w.value())

    def _recompute_exclusions(self) -> None:
        # Computed exclusions = manual + (optional) rules
        if getattr(self._app_settings, "auto_apply_rules", True):
            self.project.exclusions = apply_rules(
                self.project.text,
                self.project.manual_exclusions,
                self._app_settings.rules,
            )
        else:
            self.project.exclusions = self.project.manual_exclusions[:]

    def _apply_exclusion_formatting(self) -> None:
        text_len = len(self.project.text)
        self.project.exclusions = normalize_spans(self.project.exclusions, text_len)

        extra = []
        fmt = QTextCharFormat()
        fmt.setForeground(Qt.gray)
        fmt.setFontStrikeOut(True)

        for sp in self.project.exclusions:
            cur = self.editor.textCursor()
            cur.setPosition(sp.start)
            cur.setPosition(sp.end, QTextCursor.KeepAnchor)
            sel = QTextEdit.ExtraSelection()
            sel.cursor = cur
            sel.format = fmt
            extra.append(sel)

        self.editor.setExtraSelections(extra)

    def _update_stats(self) -> None:
        total = len(self.project.text)
        excl = sum(max(0, s.end - s.start) for s in self.project.exclusions)
        incl = len(included_text(self.project))
        self.stats.setText(f"Chars: total={total} excluded={excl} included~={incl}")

    # ---------------- Theme ----------------

    def _apply_theme(self, theme: str) -> None:
        # theme: "system" | "light" | "dark"
        app = QApplication.instance()
        if app is None:
            return

        t = (theme or "system").strip().lower()
        if t not in {"system", "light", "dark"}:
            t = "system"

        # Fusion style gives consistent palette behavior across platforms.
        try:
            app.setStyle("Fusion")
        except Exception:
            pass

        if t == "system":
            app.setPalette(app.style().standardPalette())
            return

        pal = QPalette(app.style().standardPalette())

        if t == "light":
            app.setPalette(pal)
            return

        # Dark palette
        dark = QPalette()
        dark.setColor(QPalette.Window, QColor(53, 53, 53))
        dark.setColor(QPalette.WindowText, Qt.white)
        dark.setColor(QPalette.Base, QColor(35, 35, 35))
        dark.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark.setColor(QPalette.ToolTipBase, Qt.white)
        dark.setColor(QPalette.ToolTipText, Qt.white)
        dark.setColor(QPalette.Text, Qt.white)
        dark.setColor(QPalette.Button, QColor(53, 53, 53))
        dark.setColor(QPalette.ButtonText, Qt.white)
        dark.setColor(QPalette.BrightText, Qt.red)
        dark.setColor(QPalette.Link, QColor(42, 130, 218))
        dark.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(dark)

    def _apply_document_appearance(self) -> None:
        """Apply custom font and color settings to the document editor."""
        # Apply font settings
        if not self._app_settings.use_default_font:
            if self._app_settings.font_family or self._app_settings.font_size > 0:
                from PySide6.QtGui import QFont
                font = self.editor.font()
                if self._app_settings.font_family:
                    font.setFamily(self._app_settings.font_family)
                if self._app_settings.font_size > 0:
                    font.setPointSize(self._app_settings.font_size)
                self.editor.setFont(font)
        else:
            # Reset to default font
            from PySide6.QtGui import QFont
            self.editor.setFont(QFont())

        # Apply color settings
        if not self._app_settings.use_default_colors:
            if self._app_settings.doc_bg_color or self._app_settings.doc_text_color:
                stylesheet = ""
                if self._app_settings.doc_bg_color:
                    stylesheet += f"background-color: {self._app_settings.doc_bg_color}; "
                if self._app_settings.doc_text_color:
                    stylesheet += f"color: {self._app_settings.doc_text_color}; "
                self.editor.setStyleSheet(stylesheet)
        else:
            # Reset to default colors
            self.editor.setStyleSheet("")

    def on_theme_changed(self, _idx: int) -> None:
        label = self.theme_combo.currentText().strip().lower()
        theme = {"system": "system", "light": "light", "dark": "dark"}.get(label, "system")
        self.project.theme = theme
        self._apply_theme(theme)
        self._persist_app_settings()

    def _persist_app_settings(self) -> None:
        # Persist theme + voice/model + speed/noise settings to user config.
        self._sync_piper_settings_from_ui()
        s = AppSettings(
            theme=self.project.theme,
            model_path=self.project.piper.model_path,
            speed=float(self.speed.value()),
            noise_scale=float(self.noise_scale.value()),
            noise_w=float(self.noise_w.value()),
            rules=self._app_settings.rules,
            auto_apply_rules=self._app_settings.auto_apply_rules,
            show_selection_toolbar=self._app_settings.show_selection_toolbar,
            font_family=self._app_settings.font_family,
            font_size=self._app_settings.font_size,
            use_default_font=self._app_settings.use_default_font,
            doc_bg_color=self._app_settings.doc_bg_color,
            doc_text_color=self._app_settings.doc_text_color,
            use_default_colors=self._app_settings.use_default_colors,
            recent_files=self._app_settings.recent_files,
            recent_projects=self._app_settings.recent_projects,
        )
        try:
            save_settings(s)
            self._app_settings = s
        except Exception:
            pass

    def _set_busy(self, busy: bool, message: str = "Working…") -> None:
        self.btn_stop.setEnabled(busy)
        if busy:
            if self._progress is None:
                self._progress = QProgressDialog(message, "Cancel", 0, 0, self)
                self._progress.setWindowModality(Qt.WindowModal)
                self._progress.setAutoClose(True)
                self._progress.setAutoReset(True)
                self._progress.canceled.connect(self.on_stop)
            else:
                self._progress.setLabelText(message)
            self._progress.show()
        else:
            if self._progress is not None:
                self._progress.hide()

    def _kill_process(self, proc: QProcess | None) -> None:
        if proc is None:
            return
        if proc.state() != QProcess.NotRunning:
            proc.kill()

    def on_stop(self) -> None:
        self._kill_process(self._tts_proc)
        self._kill_process(self._play_proc)
        self._tts_proc = None
        self._play_proc = None
        self._set_busy(False)

    def _apply_preferences_live(self, new: AppSettings) -> None:
        # Apply preferences without closing dialog
        self.project.theme = new.theme
        self.model_path.setText(new.model_path)
        self.speed.setValue(new.speed)
        self.noise_scale.setValue(new.noise_scale)
        self.noise_w.setValue(new.noise_w)
        self._app_settings.rules = new.rules
        self._app_settings.auto_apply_rules = getattr(new, "auto_apply_rules", True)
        # Update font/color settings
        self._app_settings.font_family = new.font_family
        self._app_settings.font_size = new.font_size
        self._app_settings.use_default_font = new.use_default_font
        self._app_settings.doc_bg_color = new.doc_bg_color
        self._app_settings.doc_text_color = new.doc_text_color
        self._app_settings.use_default_colors = new.use_default_colors
        if self._model_index and new.model_path:
            self._select_voice_by_path(new.model_path)
        self._apply_theme(new.theme)
        self._apply_document_appearance()
        self._persist_app_settings()
        self._recompute_exclusions()
        self._apply_exclusion_formatting()
        self._update_stats()

    def on_preferences(self, initial_tab: int = 0) -> None:
        # Reflect current UI into a settings object
        self._sync_piper_settings_from_ui()
        current = AppSettings(
            theme=self.project.theme,
            model_path=self.project.piper.model_path,
            speed=float(self.speed.value()),
            noise_scale=float(self.noise_scale.value()),
            noise_w=float(self.noise_w.value()),
            rules=self._app_settings.rules,
            auto_apply_rules=getattr(self._app_settings, "auto_apply_rules", True),
        )
        dlg = PreferencesDialog(self, current, self.project.text, apply_callback=self._apply_preferences_live, initial_tab=initial_tab)
        if dlg.exec() != dlg.Accepted:
            return
        new = dlg.result_settings()
        # Apply
        self.project.theme = new.theme
        self.model_path.setText(new.model_path)
        self.speed.setValue(new.speed)
        self.noise_scale.setValue(new.noise_scale)
        self.noise_w.setValue(new.noise_w)
        self._app_settings.rules = new.rules
        self._app_settings.auto_apply_rules = new.auto_apply_rules
        # Update font/color settings
        self._app_settings.font_family = new.font_family
        self._app_settings.font_size = new.font_size
        self._app_settings.use_default_font = new.use_default_font
        self._app_settings.doc_bg_color = new.doc_bg_color
        self._app_settings.doc_text_color = new.doc_text_color
        self._app_settings.use_default_colors = new.use_default_colors
        if self._model_index and new.model_path:
            self._select_voice_by_path(new.model_path)
        self._apply_theme(new.theme)
        self._apply_document_appearance()
        self._persist_app_settings()
        self._recompute_exclusions()
        self._apply_exclusion_formatting()
        self._update_stats()

    def on_find(self) -> None:
        self.find_bar.setVisible(True)
        self.find_text.setFocus()
        self.find_text.selectAll()

    def on_find_next(self) -> None:
        needle = self.find_text.text()
        if needle:
            self.editor.find(needle)

    def on_find_prev(self) -> None:
        from PySide6.QtGui import QTextDocument
        needle = self.find_text.text()
        if needle:
            self.editor.find(needle, QTextDocument.FindBackward)

    def on_new_project(self) -> None:
        # Start a new empty project (in-memory)
        self.project = DocumentProject(
            source_path="",
            title="",
            text="",
            manual_exclusions=[],
            exclusions=[],
            piper=self.project.piper,
            theme=self.project.theme,
        )
        self.editor.setPlainText("")
        self._refresh_view()

    def on_close_project(self) -> None:
        self.on_new_project()

    def _push_recent_file(self, path: str) -> None:
        p = str(path)
        items = list(getattr(self._app_settings, "recent_files", []) or [])
        if p in items:
            items.remove(p)
        items.insert(0, p)
        self._app_settings.recent_files = items[:10]
        self._persist_app_settings()

    def _push_recent_project(self, path: str) -> None:
        p = str(path)
        items = list(getattr(self._app_settings, "recent_projects", []) or [])
        if p in items:
            items.remove(p)
        items.insert(0, p)
        self._app_settings.recent_projects = items[:10]
        self._persist_app_settings()

    def _rebuild_recent_files_menu(self) -> None:
        self._menu_recent_files.clear()
        items = list(getattr(self._app_settings, "recent_files", []) or [])
        if not items:
            a = self._menu_recent_files.addAction("(none)")
            a.setEnabled(False)
            return
        for p in items:
            act = self._menu_recent_files.addAction(p)
            act.triggered.connect(lambda checked=False, path=p: self._open_recent_file(path))
        self._menu_recent_files.addSeparator()
        act_clear = self._menu_recent_files.addAction("Clear Recent Files")
        act_clear.triggered.connect(self._clear_recent_files)

    def _rebuild_recent_projects_menu(self) -> None:
        self._menu_recent_projects.clear()
        items = list(getattr(self._app_settings, "recent_projects", []) or [])
        if not items:
            a = self._menu_recent_projects.addAction("(none)")
            a.setEnabled(False)
            return
        for p in items:
            act = self._menu_recent_projects.addAction(p)
            act.triggered.connect(lambda checked=False, path=p: self._open_recent_project(path))
        self._menu_recent_projects.addSeparator()
        act_clear = self._menu_recent_projects.addAction("Clear Recent Projects")
        act_clear.triggered.connect(self._clear_recent_projects)

    def _clear_recent_files(self) -> None:
        self._app_settings.recent_files = []
        self._persist_app_settings()
        self._rebuild_recent_files_menu()

    def _clear_recent_projects(self) -> None:
        self._app_settings.recent_projects = []
        self._persist_app_settings()
        self._rebuild_recent_projects_menu()

    def _open_recent_file(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            QMessageBox.warning(self, "Missing file", f"File not found:\n{path}")
            return
        self._open_document_path(str(p))
        self._push_recent_file(str(p))

    def _open_recent_project(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            QMessageBox.warning(self, "Missing file", f"Project not found:\n{path}")
            return
        self._load_project_from_path(str(p))
        self._push_recent_project(str(p))

    def on_import_voice_model(self) -> None:
        """Import a Piper voice model (.onnx) into ~/.local/share/piper/voices."""
        src, _ = QFileDialog.getOpenFileName(
            self,
            "Import Piper voice (.onnx)",
            str(Path.home()),
            "ONNX model (*.onnx);;All files (*)",
        )
        if not src:
            return
        src_p = Path(src)
        dst_dir = Path.home() / ".local" / "share" / "piper" / "voices"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src_p.name
        try:
            import shutil
            shutil.copy2(src_p, dst)
            sidecar = Path(str(src_p) + ".json")
            if sidecar.exists():
                shutil.copy2(sidecar, Path(str(dst) + ".json"))
        except Exception as e:
            QMessageBox.critical(self, "Import failed", str(e))
            return
        QMessageBox.information(self, "Imported", f"Imported voice model to:\n{dst}")

    def on_browse_voices(self) -> None:
        """Open the voice browser to download voices from repositories."""
        from piperscribe.ui.voice_browser import VoiceBrowserDialog

        dlg = VoiceBrowserDialog(self, self._app_settings.voice_repositories)
        dlg.exec()

        # Refresh voice list after dialog closes (in case new voices were downloaded)
        self._model_index = iter_model_paths()
        self.voice_combo.clear()
        if not self._model_index:
            self.voice_combo.addItem("(no voices found)")
            self.voice_combo.setEnabled(False)
        else:
            self.voice_combo.setEnabled(True)
            for p in self._model_index:
                self.voice_combo.addItem(p.stem)
            if self.project.piper.model_path:
                self._select_voice_by_path(self.project.piper.model_path)

    def on_help_contents(self) -> None:
        """Open the help documentation dialog."""
        from piperscribe.ui.help_dialog import HelpDialog

        dlg = HelpDialog(self)
        dlg.exec()

    def on_about(self) -> None:
        """Display the About dialog with version information."""
        QMessageBox.about(
            self,
            "About PiperScribe",
            "PiperScribe v0.1.20\n\n"
            "A PySide6 GUI for text-to-speech with Piper.\n\n"
            "Piper TTS: https://github.com/rhasspy/piper\n"
            "Documentation: Press F1 for help"
        )

    def _open_document_path(self, path: str) -> None:
        # Placeholder: this method is referenced by recent-file menu.
        # Current importer path for "open document" uses import_any().
        p = Path(path)
        try:
            res = import_any(p)
        except Exception as e:
            QMessageBox.critical(self, "Import failed", str(e))
            return
        self.project = DocumentProject(
            source_path=str(p),
            title=res.title,
            text=res.text,
            manual_exclusions=[],
            exclusions=[],
            piper=self.project.piper,
            theme=self.project.theme,
        )
        self.editor.setPlainText(self.project.text)
        self._refresh_view()

    def _load_project_from_path(self, path: str) -> None:
        """Load a project file from disk."""
        p = Path(path)
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            self.project = DocumentProject.from_dict(d)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", str(e))
            return
        self.setWindowTitle(f"PiperScribe v0.1.20 — {self.project.title}")
        self.editor.setPlainText(self.project.text)
        self._init_piper_environment()
        self._refresh_view()

    def on_open(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open document",
            str(Path.home()),
            "Documents (*.txt *.text *.docx *.md *.markdown *.html *.htm *.pdf);;All files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            res = import_any(path)
        except Exception as e:
            QMessageBox.critical(self, "Import failed", str(e))
            return

        self.project = DocumentProject(
            source_path=str(path),
            title=res.title,
            text=res.text,
            manual_exclusions=[],
            exclusions=[],
            piper=self.project.piper,
            theme=self.project.theme,
        )
        self.setWindowTitle(f"PiperScribe v0.1.20 — {self.project.title}")
        self._refresh_view()
        self._push_recent_file(str(path))

    def on_save_project(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save project",
            str(Path.home() / (self.project.title or "project")),
            "Audiobook Project (*.abproj.json);;JSON (*.json)",
        )
        if not path_str:
            return
        path = Path(path_str)
        if not path.name.endswith(".abproj.json"):
            path = path.with_suffix(path.suffix + ".abproj.json") if path.suffix else path.with_suffix(".abproj.json")
        try:
            self._sync_piper_settings_from_ui()
            path.write_text(json.dumps(self.project.as_dict(), indent=2), encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return
        QMessageBox.information(self, "Saved", f"Saved:\n{path}")
        self._push_recent_project(str(path))

    def on_load_project(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load project",
            str(Path.home()),
            "Audiobook Project (*.abproj.json *.json);;All files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            self.project = DocumentProject.from_dict(d)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", str(e))
            return

        self.setWindowTitle(f"PiperScribe v0.1.20 — {self.project.title}")
        self._init_piper_environment()
        self._refresh_view()
        self._push_recent_project(str(path))

    def on_browse_model(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select Piper model (.onnx)",
            str(Path.home()),
            "ONNX model (*.onnx);;All files (*)",
        )
        if not path_str:
            return
        self._set_model_path(path_str)
        if self._model_index:
            self._select_voice_by_path(path_str)
        self._persist_app_settings()

    def _selection_span(self) -> Span | None:
        cur = self.editor.textCursor()
        if not cur.hasSelection():
            return None
        start = min(cur.selectionStart(), cur.selectionEnd())
        end = max(cur.selectionStart(), cur.selectionEnd())
        if end <= start:
            return None
        return Span(start, end, "user")

    def on_exclude_selection(self) -> None:
        sp = self._selection_span()
        if not sp:
            return
        self.project.manual_exclusions.append(sp)
        self._recompute_exclusions()
        self._apply_exclusion_formatting()
        self._update_stats()

    def on_include_selection(self) -> None:
        sp = self._selection_span()
        if not sp:
            return
        new_excl: list[Span] = []
        for ex in normalize_spans(self.project.manual_exclusions, len(self.project.text)):
            if ex.end <= sp.start or ex.start >= sp.end:
                new_excl.append(ex)
            else:
                if ex.start < sp.start:
                    new_excl.append(Span(ex.start, sp.start, ex.reason))
                if ex.end > sp.end:
                    new_excl.append(Span(sp.end, ex.end, ex.reason))
        self.project.manual_exclusions = new_excl
        self._recompute_exclusions()
        self._apply_exclusion_formatting()
        self._update_stats()

    def _ensure_piper_ready(self) -> bool:
        status = check_piper_installed()
        if not status.found:
            QMessageBox.critical(self, "Piper not found", status.error or "`piper` not found on PATH.")
            return False
        self._sync_piper_settings_from_ui()
        mp = self.project.piper.model_path
        if not mp:
            QMessageBox.critical(self, "Voice not set", "Choose a voice/model first.")
            return False
        if not Path(mp).expanduser().exists():
            QMessageBox.critical(self, "Voice not found", f"Model file does not exist:\n{mp}")
            return False
        return True

    def _start_tts_process(self, text: str, wav_path: Path, done_cb) -> None:
        self.on_stop()
        self._set_busy(True, "Converting text to speech…")

        args = [
            "--model", self.project.piper.model_path,
            "--length_scale", str(self.project.piper.length_scale),
            "--noise_scale", str(self.project.piper.noise_scale),
            "--noise_w", str(self.project.piper.noise_w),
            "--output_file", str(wav_path),
        ]

        proc = QProcess(self)
        proc.setProgram("piper")
        proc.setArguments(args)
        proc.setProcessChannelMode(QProcess.MergedChannels)

        def on_finished(exit_code: int, _exit_status) -> None:
            self._tts_proc = None
            self._set_busy(False)
            if exit_code != 0:
                msg = bytes(proc.readAllStandardOutput()).decode(errors="replace").strip()
                QMessageBox.critical(self, "Piper failed", msg or f"piper exited with code {exit_code}")
                return
            done_cb()

        proc.finished.connect(on_finished)
        proc.start()
        proc.write(text.encode("utf-8"))
        proc.closeWriteChannel()
        self._tts_proc = proc

    def _start_playback(self, wav_path: Path) -> None:
        proc = QProcess(self)
        proc.setProgram("aplay")
        proc.setArguments([str(wav_path)])
        proc.setProcessChannelMode(QProcess.MergedChannels)

        self._set_busy(True, "Playing preview… (Stop to cancel)")

        def on_finished(_exit_code: int, _exit_status) -> None:
            self._play_proc = None
            self._set_busy(False)

        proc.finished.connect(on_finished)
        proc.start()
        self._play_proc = proc

    def on_stop_preview(self) -> None:
        """Stop the current preview playback/tts job."""
        self.on_stop()

    def on_preview_selection(self) -> None:
        sp = self._selection_span()
        if not sp:
            QMessageBox.information(self, "Preview", "Select some text first.")
            return
        if not self._ensure_piper_ready():
            return

        text = self.project.text[sp.start:sp.end].strip()
        if not text:
            return

        td = tempfile.TemporaryDirectory()
        wav = Path(td.name) / "preview.wav"

        def after_tts() -> None:
            self._start_playback(wav)

        def cleanup_later() -> None:
            if self._play_proc is None or self._play_proc.state() == QProcess.NotRunning:
                td.cleanup()
            else:
                QTimer.singleShot(500, cleanup_later)

        QTimer.singleShot(500, cleanup_later)
        self._start_tts_process(text + "\n", wav, after_tts)

    def on_export_wav(self) -> None:
        if not self._ensure_piper_ready():
            return

        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export WAV",
            str(Path.home() / f"{self.project.title or 'output'}.wav"),
            "WAV audio (*.wav)",
        )
        if not path_str:
            return

        out = Path(path_str)
        if out.suffix.lower() != ".wav":
            out = out.with_suffix(".wav")

        self._recompute_exclusions()
        text = included_text(self.project).strip()
        if not text:
            QMessageBox.critical(self, "Nothing to export", "All text is excluded or empty.")
            return

        def after_tts() -> None:
            QMessageBox.information(self, "Export complete", f"Wrote:\n{out}")

        self._start_tts_process(text + "\n", out, after_tts)

    def on_rules(self) -> None:
        # Shortcut: open Preferences on the Rules tab
        self.on_preferences(initial_tab=2)

    def on_reapply_rules(self) -> None:
        self._recompute_exclusions()
        self._apply_exclusion_formatting()
        self._update_stats()

