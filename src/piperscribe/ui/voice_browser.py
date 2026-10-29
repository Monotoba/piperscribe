"""Voice Browser Dialog for downloading Piper TTS voices."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class VoiceFetchThread(QThread):
    """Background thread to fetch voice listings."""

    finished = Signal(dict)  # Emits voice data
    error = Signal(str)  # Emits error message

    def __init__(self, repo_url: str):
        super().__init__()
        self.repo_url = repo_url

    def run(self):
        """Fetch voice data from repository."""
        try:
            with urllib.request.urlopen(self.repo_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class VoiceDownloadThread(QThread):
    """Background thread to download a voice model."""

    progress = Signal(int, int)  # current, total bytes
    finished = Signal()
    error = Signal(str)

    def __init__(self, url: str, dest_path: Path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        """Download file with progress reporting."""
        try:
            self.dest_path.parent.mkdir(parents=True, exist_ok=True)

            req = urllib.request.Request(self.url)
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(self.dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class VoiceBrowserDialog(QDialog):
    """Dialog for browsing and downloading Piper TTS voices."""

    voice_downloaded = Signal()  # Emitted when a voice download completes

    def done(self, result: int) -> None:
        # Qt aborts if a QThread is destroyed while it runs, so stop the workers first.
        for thread in (getattr(self, "fetch_thread", None), self.current_download):
            if thread is not None and thread.isRunning():
                thread.requestInterruption()
                thread.wait(5000)
        super().done(result)

    def __init__(self, parent, voice_repos: list[str]):
        super().__init__(parent)
        self.setWindowTitle("Voice Browser — PiperScribe")
        self.setModal(True)
        self.resize(900, 600)

        self.voice_repos = voice_repos or []
        self.voice_data: Dict[str, Any] = {}
        self.current_download: VoiceDownloadThread | None = None

        self._build_ui()
        self._fetch_voices()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Search/filter bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Filter:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by language, name, or quality...")
        self.search_box.textChanged.connect(self._filter_voices)
        search_layout.addWidget(self.search_box, 1)
        layout.addLayout(search_layout)

        # Splitter: voice list | details
        splitter = QSplitter(Qt.Horizontal)

        # Voice list
        self.voice_list = QListWidget()
        self.voice_list.currentItemChanged.connect(self._on_voice_selected)
        splitter.addWidget(self.voice_list)

        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        self.voice_details = QTextEdit()
        self.voice_details.setReadOnly(True)
        details_layout.addWidget(self.voice_details)

        # Download button and progress
        self.btn_download = QPushButton("Download Voice")
        self.btn_download.clicked.connect(self._download_voice)
        self.btn_download.setEnabled(False)
        details_layout.addWidget(self.btn_download)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        details_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        details_layout.addWidget(self.progress_label)

        splitter.addWidget(details_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        # Status label
        self.status_label = QLabel("Loading voices...")
        layout.addWidget(self.status_label)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fetch_voices(self):
        """Fetch voice listings from repositories."""
        if not self.voice_repos:
            self.status_label.setText("No voice repositories configured.")
            return

        self.status_label.setText(f"Loading voices from {len(self.voice_repos)} repositories...")

        # Fetch from first repository (can be extended to support multiple)
        self.fetch_thread = VoiceFetchThread(self.voice_repos[0])
        self.fetch_thread.finished.connect(self._on_voices_loaded)
        self.fetch_thread.error.connect(self._on_fetch_error)
        self.fetch_thread.start()

    def _on_voices_loaded(self, data: dict):
        """Handle loaded voice data."""
        self.voice_data = data
        self._populate_voice_list()
        self.status_label.setText(f"Loaded {len(data)} voices")

    def _on_fetch_error(self, error: str):
        """Handle fetch error."""
        self.status_label.setText(f"Error loading voices: {error}")
        QMessageBox.warning(self, "Fetch Error", f"Failed to load voices:\n{error}")

    def _populate_voice_list(self):
        """Populate the voice list widget."""
        self.voice_list.clear()
        for key, voice in sorted(self.voice_data.items()):
            lang = voice.get('language', {}).get('name_english', 'Unknown')
            name = voice.get('name', 'Unknown')
            quality = voice.get('quality', 'unknown')
            speakers = voice.get('num_speakers', 1)

            display = f"{lang} - {name} ({quality})"
            if speakers > 1:
                display += f" [{speakers} speakers]"

            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, key)
            self.voice_list.addItem(item)

    def _filter_voices(self, text: str):
        """Filter voice list based on search text."""
        text = text.lower()
        for i in range(self.voice_list.count()):
            item = self.voice_list.item(i)
            visible = text in item.text().lower()
            item.setHidden(not visible)

    def _on_voice_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None):
        """Handle voice selection."""
        if not current:
            self.voice_details.clear()
            self.btn_download.setEnabled(False)
            return

        key = current.data(Qt.UserRole)
        voice = self.voice_data.get(key, {})

        # Display voice details
        lang = voice.get('language', {})
        details = []
        details.append(f"<h3>{voice.get('name', 'Unknown')}</h3>")
        details.append(f"<b>Language:</b> {lang.get('name_english', 'Unknown')} ({lang.get('code', 'unknown')})")
        details.append(f"<b>Quality:</b> {voice.get('quality', 'unknown')}")
        details.append(f"<b>Speakers:</b> {voice.get('num_speakers', 1)}")

        files = voice.get('files', {})
        onnx_files = [f for f in files.keys() if f.endswith('.onnx')]
        if onnx_files:
            size_bytes = files[onnx_files[0]].get('size_bytes', 0)
            size_mb = size_bytes / (1024 * 1024)
            details.append(f"<b>Size:</b> {size_mb:.1f} MB")

        self.voice_details.setHtml("<br>".join(details))
        self.btn_download.setEnabled(True)

    def _download_voice(self):
        """Download the selected voice."""
        current = self.voice_list.currentItem()
        if not current:
            return

        key = current.data(Qt.UserRole)
        voice = self.voice_data.get(key, {})
        files = voice.get('files', {})

        # Find .onnx and .onnx.json files
        onnx_file = None
        json_file = None
        for file_path in files.keys():
            if file_path.endswith('.onnx') and not file_path.endswith('.onnx.json'):
                onnx_file = file_path
            elif file_path.endswith('.onnx.json'):
                json_file = file_path

        if not onnx_file:
            QMessageBox.warning(self, "Download Error", "No .onnx file found for this voice.")
            return

        # Prepare download
        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        dest_dir = Path.home() / ".local" / "share" / "piper" / "voices"

        # Start downloading .onnx file
        self.btn_download.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_label.setText(f"Downloading {Path(onnx_file).name}...")

        dest_path = dest_dir / Path(onnx_file).name
        self.current_download = VoiceDownloadThread(base_url + onnx_file, dest_path)
        self.current_download.progress.connect(self._on_download_progress)
        self.current_download.finished.connect(lambda: self._on_download_finished(json_file, base_url, dest_dir))
        self.current_download.error.connect(self._on_download_error)
        self.current_download.start()

    def _on_download_progress(self, current: int, total: int):
        """Update download progress."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            mb_current = current / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.progress_label.setText(f"Downloading... {mb_current:.1f} / {mb_total:.1f} MB")

    def _on_download_finished(self, json_file: str | None, base_url: str, dest_dir: Path):
        """Handle download completion."""
        if json_file:
            # Download the .onnx.json file too
            dest_path = dest_dir / Path(json_file).name
            self.progress_label.setText(f"Downloading {Path(json_file).name}...")
            self.current_download = VoiceDownloadThread(base_url + json_file, dest_path)
            self.current_download.finished.connect(self._on_all_downloads_finished)
            self.current_download.error.connect(self._on_download_error)
            self.current_download.start()
        else:
            self._on_all_downloads_finished()

    def _on_all_downloads_finished(self):
        """Handle completion of all downloads."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.btn_download.setEnabled(True)
        self.status_label.setText("Download complete!")

        # Emit signal to notify parent dialog to refresh voice list
        self.voice_downloaded.emit()

        QMessageBox.information(self, "Success", "Voice model downloaded successfully!\n\nThe voice is now available in the Voice dropdown.")

    def _on_download_error(self, error: str):
        """Handle download error."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.btn_download.setEnabled(True)
        self.status_label.setText(f"Download error: {error}")
        QMessageBox.critical(self, "Download Error", f"Failed to download voice:\n{error}")
