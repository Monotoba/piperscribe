from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QTimer, QPoint
from PySide6.QtGui import QAction, QTextCharFormat, QTextCursor, QPalette, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QDoubleSpinBox,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QProgressDialog,
)

from piperscribe.importers.registry import import_any
from piperscribe.model.document import Document, DocumentProject
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

        # Multi-document audio generation
        act_generate_all = QAction("Generate All Audio", self)
        act_generate_all.triggered.connect(self.on_generate_all_audio)
        m_file.addAction(act_generate_all)

        act_export_playlist = QAction("Export Playlist…", self)
        act_export_playlist.triggered.connect(self.on_export_playlist)
        m_file.addAction(act_export_playlist)

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

        # Splitter: document list on left, editor on right
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Document list
        doc_list_widget = QWidget()
        doc_list_layout = QVBoxLayout(doc_list_widget)
        doc_list_layout.setContentsMargins(0, 0, 0, 0)

        doc_list_layout.addWidget(QLabel("Documents:"))

        self.doc_list = QListWidget()
        self.doc_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.doc_list.currentItemChanged.connect(self._on_document_selected)
        self.doc_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.doc_list.customContextMenuRequested.connect(self._show_document_context_menu)
        doc_list_layout.addWidget(self.doc_list, 1)

        # Document management buttons
        btn_row = QHBoxLayout()
        self.btn_add_doc = QPushButton("Add")
        self.btn_add_doc.clicked.connect(self.on_add_document)
        btn_row.addWidget(self.btn_add_doc)

        self.btn_remove_doc = QPushButton("Remove")
        self.btn_remove_doc.clicked.connect(self.on_remove_document)
        btn_row.addWidget(self.btn_remove_doc)

        self.btn_move_up = QPushButton("↑")
        self.btn_move_up.clicked.connect(self.on_move_document_up)
        btn_row.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("↓")
        self.btn_move_down.clicked.connect(self.on_move_document_down)
        btn_row.addWidget(self.btn_move_down)

        doc_list_layout.addLayout(btn_row)

        splitter.addWidget(doc_list_widget)

        # Right side: Document editor
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        splitter.addWidget(self.editor)

        # Set splitter sizes: document list gets less space than editor
        splitter.setStretchFactor(0, 1)  # Document list
        splitter.setStretchFactor(1, 3)  # Editor gets more space

        layout.addWidget(splitter, 1)

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
        self._rebuild_document_list()
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

    def _on_document_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        """Handle document selection change."""
        if not current:
            self.editor.setPlainText("")
            return

        doc_id = current.data(Qt.UserRole)
        doc = self.project.get_document(doc_id)
        if not doc:
            return

        # Load document text into editor
        self.editor.setPlainText(doc.text)

        # Update exclusion formatting
        self._apply_exclusion_formatting()
        self._update_stats()

    def _rebuild_document_list(self) -> None:
        """Rebuild the document list with status icons."""
        current_id = None
        current_item = self.doc_list.currentItem()
        if current_item:
            current_id = current_item.data(Qt.UserRole)

        self.doc_list.clear()

        for doc in self.project.documents:
            # Status icons
            enabled_icon = "✓" if doc.enabled else "⨯"
            audio_icon = "🔊" if doc.audio_path else "⚫"

            # Display format: [enabled] [audio] Title
            label = f"{enabled_icon} {audio_icon} {doc.title}"

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, doc.id)
            self.doc_list.addItem(item)

            # Restore selection
            if doc.id == current_id:
                self.doc_list.setCurrentItem(item)

        # If no selection and documents exist, select first
        if not self.doc_list.currentItem() and self.doc_list.count() > 0:
            self.doc_list.setCurrentRow(0)

        # Update button states
        self._update_document_buttons()

    def _update_document_buttons(self) -> None:
        """Update enabled state of document management buttons."""
        has_selection = self.doc_list.currentItem() is not None

        self.btn_remove_doc.setEnabled(has_selection)
        self.btn_move_up.setEnabled(has_selection and self.doc_list.currentRow() > 0)
        self.btn_move_down.setEnabled(has_selection and self.doc_list.currentRow() < self.doc_list.count() - 1)

    def _show_document_context_menu(self, pos: QPoint) -> None:
        """Show context menu for document list."""
        item = self.doc_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        # Document Settings action
        settings_action = menu.addAction("Document Settings...")
        settings_action.triggered.connect(self.on_document_settings)

        menu.addSeparator()

        # Generate Audio action
        generate_action = menu.addAction("Generate Audio")
        generate_action.triggered.connect(self.on_generate_document_audio)

        # Toggle Enabled action
        doc = self._get_current_document()
        if doc:
            toggle_text = "Disable" if doc.enabled else "Enable"
            toggle_action = menu.addAction(f"{toggle_text} in Playlist")
            toggle_action.triggered.connect(self.on_toggle_document_enabled)

        menu.addSeparator()

        # Remove action
        remove_action = menu.addAction("Remove Document")
        remove_action.triggered.connect(self.on_remove_document)

        menu.exec(self.doc_list.mapToGlobal(pos))

    def _get_current_document(self) -> Document | None:
        """Get the currently selected document."""
        current_item = self.doc_list.currentItem()
        if not current_item:
            return None
        doc_id = current_item.data(Qt.UserRole)
        return self.project.get_document(doc_id)

    def _ensure_current_document(self) -> Document:
        """Get current document or create one if project is empty."""
        doc = self._get_current_document()
        if doc:
            return doc

        # No document selected - create one if project is empty
        if not self.project.documents:
            doc = Document(
                id=Document.generate_id(),
                title="Document 1",
                text="",
                piper=self.project.default_piper,
                order=0,
                enabled=True,
            )
            self.project.add_document(doc)
            self._rebuild_document_list()

        return self.project.documents[0]

    def on_add_document(self) -> None:
        """Add a new empty document to the project."""
        doc = Document(
            id=Document.generate_id(),
            title=f"Document {len(self.project.documents) + 1}",
            text="",
            piper=self.project.default_piper,
            order=len(self.project.documents),
            enabled=True,
        )
        self.project.add_document(doc)
        self._rebuild_document_list()

        # Select the new document
        for i in range(self.doc_list.count()):
            item = self.doc_list.item(i)
            if item.data(Qt.UserRole) == doc.id:
                self.doc_list.setCurrentRow(i)
                break

    def on_remove_document(self) -> None:
        """Remove the currently selected document."""
        doc = self._get_current_document()
        if not doc:
            return

        reply = QMessageBox.question(
            self,
            "Remove Document",
            f"Remove document '{doc.title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.project.remove_document(doc.id)
            self._rebuild_document_list()

    def on_move_document_up(self) -> None:
        """Move the currently selected document up in the list."""
        current_row = self.doc_list.currentRow()
        if current_row <= 0:
            return

        doc_ids = [self.doc_list.item(i).data(Qt.UserRole) for i in range(self.doc_list.count())]
        doc_ids[current_row], doc_ids[current_row - 1] = doc_ids[current_row - 1], doc_ids[current_row]

        self.project.reorder_documents(doc_ids)
        self._rebuild_document_list()
        self.doc_list.setCurrentRow(current_row - 1)

    def on_move_document_down(self) -> None:
        """Move the currently selected document down in the list."""
        current_row = self.doc_list.currentRow()
        if current_row < 0 or current_row >= self.doc_list.count() - 1:
            return

        doc_ids = [self.doc_list.item(i).data(Qt.UserRole) for i in range(self.doc_list.count())]
        doc_ids[current_row], doc_ids[current_row + 1] = doc_ids[current_row + 1], doc_ids[current_row]

        self.project.reorder_documents(doc_ids)
        self._rebuild_document_list()
        self.doc_list.setCurrentRow(current_row + 1)

    def on_document_settings(self) -> None:
        """Open settings dialog for the currently selected document."""
        doc = self._get_current_document()
        if not doc:
            return

        from piperscribe.ui.document_settings_dialog import DocumentSettingsDialog

        dlg = DocumentSettingsDialog(self, doc)
        if dlg.exec() == dlg.Accepted:
            dlg.apply_settings()
            self._rebuild_document_list()

    def on_toggle_document_enabled(self) -> None:
        """Toggle the enabled state of the currently selected document."""
        doc = self._get_current_document()
        if not doc:
            return

        doc.enabled = not doc.enabled
        self._rebuild_document_list()

    def on_generate_document_audio(self) -> None:
        """Generate audio for the currently selected document."""
        doc = self._get_current_document()
        if not doc:
            return

        if not self._ensure_piper_ready():
            return

        # Get text to synthesize (after exclusions)
        from piperscribe.model.spans import subtract_spans
        text = subtract_spans(doc.text, doc.exclusions).strip()

        if not text:
            QMessageBox.information(
                self,
                "No Text",
                "Document has no text to generate audio for (all text is excluded)."
            )
            return

        # Create audio directory
        audio_dir = self._get_project_audio_dir()
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: sanitized-title-{doc_id[:8]}.wav
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in doc.title)
        safe_title = safe_title.strip().replace(' ', '-')[:50]  # Limit length
        filename = f"{safe_title}-{doc.id[:8]}.wav"
        output_path = audio_dir / filename

        # Generate audio
        try:
            from piperscribe.tts.piper import PiperTts

            progress = QProgressDialog(
                f"Generating audio for '{doc.title}'...",
                "Cancel",
                0,
                0,
                self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            tts = PiperTts(doc.piper)
            tts.synthesize_to_wav(text, output_path)

            # Update document metadata
            doc.audio_path = str(output_path)

            # Get audio duration (simple estimate: ~150 chars per second of speech)
            doc.audio_duration = len(text) / 150.0

            progress.close()

            self._rebuild_document_list()

            QMessageBox.information(
                self,
                "Audio Generated",
                f"Audio saved to:\n{output_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Generation Failed",
                f"Failed to generate audio:\n\n{e}"
            )

    def _get_project_audio_dir(self) -> Path:
        """Get the audio directory for the current project."""
        if hasattr(self, 'current_project_path') and self.current_project_path:
            # Create audio directory next to project file
            project_path = Path(self.current_project_path)
            return project_path.parent / f"{project_path.stem}_audio"
        else:
            # Use temp directory for unsaved projects
            return Path(tempfile.gettempdir()) / "piperscribe_audio"

    def on_generate_all_audio(self) -> None:
        """Generate audio for all enabled documents in the project."""
        enabled_docs = self.project.get_playlist_order()

        if not enabled_docs:
            QMessageBox.information(
                self,
                "No Documents",
                "No enabled documents in project. Enable at least one document first."
            )
            return

        if not self._ensure_piper_ready():
            return

        # Count documents that need audio generation
        docs_to_generate = []
        for doc in enabled_docs:
            # Get text after exclusions
            from piperscribe.model.spans import subtract_spans
            text = subtract_spans(doc.text, doc.exclusions).strip()
            if text:
                docs_to_generate.append(doc)

        if not docs_to_generate:
            QMessageBox.information(
                self,
                "No Text",
                "All enabled documents have no text or all text is excluded."
            )
            return

        # Confirm generation
        reply = QMessageBox.question(
            self,
            "Generate All Audio",
            f"Generate audio for {len(docs_to_generate)} document(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        # Create audio directory
        audio_dir = self._get_project_audio_dir()
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Progress dialog
        progress = QProgressDialog(
            "Generating audio...",
            "Cancel",
            0,
            len(docs_to_generate),
            self
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        # Generate audio for each document
        from piperscribe.tts.piper import PiperTts
        from piperscribe.model.spans import subtract_spans

        success_count = 0
        errors = []

        for i, doc in enumerate(docs_to_generate):
            if progress.wasCanceled():
                break

            progress.setLabelText(f"Generating audio for '{doc.title}'... ({i+1}/{len(docs_to_generate)})")
            progress.setValue(i)

            try:
                # Get text after exclusions
                text = subtract_spans(doc.text, doc.exclusions).strip()

                # Generate filename
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in doc.title)
                safe_title = safe_title.strip().replace(' ', '-')[:50]
                filename = f"{safe_title}-{doc.id[:8]}.wav"
                output_path = audio_dir / filename

                # Generate audio
                tts = PiperTts(doc.piper)
                tts.synthesize_to_wav(text, output_path)

                # Update document metadata
                doc.audio_path = str(output_path)
                doc.audio_duration = len(text) / 150.0  # Rough estimate

                success_count += 1

            except Exception as e:
                errors.append(f"{doc.title}: {e}")

        progress.setValue(len(docs_to_generate))

        # Update UI
        self._rebuild_document_list()

        # Show results
        if errors:
            error_msg = "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more errors"

            QMessageBox.warning(
                self,
                "Generation Completed with Errors",
                f"Successfully generated: {success_count}/{len(docs_to_generate)}\n\n"
                f"Errors:\n{error_msg}"
            )
        else:
            QMessageBox.information(
                self,
                "Generation Complete",
                f"Successfully generated audio for {success_count} document(s)."
            )

    def on_export_playlist(self) -> None:
        """Export M3U and JSON playlists for the project."""
        from piperscribe.audio.playlist import (
            export_m3u_playlist,
            export_json_playlist,
            validate_playlist_export,
            get_missing_audio_documents
        )

        # Validate project is ready for export
        is_valid, error_msg = validate_playlist_export(self.project)
        if not is_valid:
            QMessageBox.warning(
                self,
                "Cannot Export Playlist",
                error_msg
            )
            return

        # Check for missing audio
        missing = get_missing_audio_documents(self.project)
        if missing:
            reply = QMessageBox.question(
                self,
                "Missing Audio",
                f"{len(missing)} enabled document(s) don't have audio:\n\n"
                f"{', '.join(missing[:5])}"
                f"{'...' if len(missing) > 5 else ''}\n\n"
                f"Generate audio now?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Yes:
                self.on_generate_all_audio()
                # Re-validate after generation
                is_valid, error_msg = validate_playlist_export(self.project)
                if not is_valid:
                    return
            elif reply == QMessageBox.Cancel:
                return
            # If No, continue with export of available audio

        # Get export location
        default_name = self.project.title or "playlist"
        default_path = Path.home() / f"{default_name}.m3u"

        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export Playlist",
            str(default_path),
            "M3U Playlist (*.m3u);;All Files (*)"
        )

        if not path_str:
            return

        playlist_path = Path(path_str).with_suffix(".m3u")
        json_path = playlist_path.with_suffix(".json")

        try:
            # Export both formats
            export_m3u_playlist(self.project, playlist_path)
            export_json_playlist(self.project, json_path)

            QMessageBox.information(
                self,
                "Playlist Exported",
                f"Playlist exported successfully:\n\n"
                f"M3U: {playlist_path}\n"
                f"JSON: {json_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export playlist:\n\n{e}"
            )

    def _sync_piper_settings_from_ui(self) -> None:
        mp = os.path.expanduser(self.model_path.text().strip())
        self.project.piper.model_path = mp
        self.project.piper.length_scale = float(self._speed_to_length_scale(self.speed.value()))
        self.project.piper.noise_scale = float(self.noise_scale.value())
        self.project.piper.noise_w = float(self.noise_w.value())

    def _recompute_exclusions(self) -> None:
        # Computed exclusions = manual + (optional) rules
        doc = self._get_current_document()
        if not doc:
            return

        if getattr(self._app_settings, "auto_apply_rules", True):
            doc.exclusions = apply_rules(
                doc.text,
                doc.manual_exclusions,
                self._app_settings.rules,
            )
        else:
            doc.exclusions = doc.manual_exclusions[:]

    def _apply_exclusion_formatting(self) -> None:
        doc = self._get_current_document()
        if not doc:
            return

        text_len = len(doc.text)
        doc.exclusions = normalize_spans(doc.exclusions, text_len)

        extra = []
        fmt = QTextCharFormat()
        fmt.setForeground(Qt.gray)
        fmt.setFontStrikeOut(True)

        for sp in doc.exclusions:
            cur = self.editor.textCursor()
            cur.setPosition(sp.start)
            cur.setPosition(sp.end, QTextCursor.KeepAnchor)
            sel = QTextEdit.ExtraSelection()
            sel.cursor = cur
            sel.format = fmt
            extra.append(sel)

        self.editor.setExtraSelections(extra)

    def _update_stats(self) -> None:
        doc = self._get_current_document()
        if not doc:
            self.stats.setText("")
            return

        total = len(doc.text)
        excl = sum(max(0, s.end - s.start) for s in doc.exclusions)
        # Calculate included text length for current document
        from piperscribe.model.spans import subtract_spans
        incl_text = subtract_spans(doc.text, doc.exclusions).strip()
        incl = len(incl_text)
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
        doc = self._get_current_document()
        doc_text = doc.text if doc else ""
        dlg = PreferencesDialog(self, current, doc_text, apply_callback=self._apply_preferences_live, initial_tab=initial_tab)
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
        # Start a new empty project (in-memory) with one empty document
        doc = Document(
            id=Document.generate_id(),
            title="Document 1",
            text="",
            piper=self.project.piper,
            order=0,
            enabled=True,
        )
        self.project = DocumentProject(
            title="Untitled Project",
            documents=[doc],
            theme=self.project.theme,
            default_piper=self.project.piper,
        )
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
        # Import a document and add it to the current project
        p = Path(path)
        try:
            res = import_any(p)
        except Exception as e:
            QMessageBox.critical(self, "Import failed", str(e))
            return

        # Create new document from imported content
        doc = Document(
            id=Document.generate_id(),
            title=res.title or p.stem,
            text=res.text,
            source_path=str(p),
            piper=self.project.default_piper,
            order=len(self.project.documents),
            enabled=True,
        )

        self.project.add_document(doc)
        self._rebuild_document_list()

        # Select the newly added document
        for i in range(self.doc_list.count()):
            item = self.doc_list.item(i)
            if item.data(Qt.UserRole) == doc.id:
                self.doc_list.setCurrentRow(i)
                break

        self._push_recent_file(str(p))

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
        doc = self._get_current_document()
        if not doc:
            return

        sp = self._selection_span()
        if not sp:
            return
        doc.manual_exclusions.append(sp)
        self._recompute_exclusions()
        self._apply_exclusion_formatting()
        self._update_stats()

    def on_include_selection(self) -> None:
        doc = self._get_current_document()
        if not doc:
            return

        sp = self._selection_span()
        if not sp:
            return
        new_excl: list[Span] = []
        for ex in normalize_spans(doc.manual_exclusions, len(doc.text)):
            if ex.end <= sp.start or ex.start >= sp.end:
                new_excl.append(ex)
            else:
                if ex.start < sp.start:
                    new_excl.append(Span(ex.start, sp.start, ex.reason))
                if ex.end > sp.end:
                    new_excl.append(Span(sp.end, ex.end, ex.reason))
        doc.manual_exclusions = new_excl
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

        doc = self._get_current_document()
        if not doc:
            return

        text = doc.text[sp.start:sp.end].strip()
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

