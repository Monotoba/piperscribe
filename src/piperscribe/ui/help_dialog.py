"""Help Dialog for displaying Markdown help files."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
)


class HelpDialog(QDialog):
    """Dialog for browsing and displaying help documentation."""

    def __init__(self, parent, initial_topic: str = "getting-started"):
        super().__init__(parent)
        self.setWindowTitle("Help — PiperScribe")
        self.setModal(False)  # Allow interaction with main window while help is open
        self.resize(900, 600)
        self.setMaximumHeight(700)

        self.help_files: Dict[str, Path] = {}
        self.current_topic = initial_topic

        self._build_ui()
        self._load_help_files()
        self._select_initial_topic()

    def _build_ui(self):
        """Build the dialog UI with navigation and content areas."""
        layout = QVBoxLayout(self)

        # Splitter: topic list on left, content browser on right
        splitter = QSplitter(Qt.Horizontal)

        # Left side: topic navigation
        self.topic_list = QListWidget()
        self.topic_list.setMaximumWidth(250)
        self.topic_list.currentItemChanged.connect(self._on_topic_selected)
        splitter.addWidget(self.topic_list)

        # Right side: content display
        self.content_browser = QTextBrowser()
        self.content_browser.setReadOnly(True)
        self.content_browser.setOpenExternalLinks(True)  # Open external links in browser
        splitter.addWidget(self.content_browser)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_help_files(self):
        """Load all markdown help files from docs/help directory."""
        # Find help directory relative to this module
        help_dir = Path(__file__).parent.parent.parent.parent / "docs" / "help"

        if not help_dir.exists():
            self.content_browser.setHtml(
                "<h1>Help Files Not Found</h1>"
                f"<p>Could not find help directory at: <code>{help_dir}</code></p>"
                "<p>Help files may not be installed.</p>"
            )
            return

        # Load all .md files
        for md_file in sorted(help_dir.glob("*.md")):
            # Create display name from filename
            topic_name = md_file.stem.replace("-", " ").title()
            self.help_files[topic_name] = md_file

            # Add to topic list
            item = QListWidgetItem(topic_name)
            item.setData(Qt.UserRole, md_file.stem)  # Store original filename
            self.topic_list.addItem(item)

        if not self.help_files:
            self.content_browser.setHtml(
                "<h1>No Help Files Found</h1>"
                f"<p>The help directory exists but contains no .md files.</p>"
                f"<p>Location: <code>{help_dir}</code></p>"
            )

    def _select_initial_topic(self):
        """Select the initial topic in the navigation list."""
        # Try to find and select the initial topic
        for i in range(self.topic_list.count()):
            item = self.topic_list.item(i)
            if item.data(Qt.UserRole) == self.current_topic:
                self.topic_list.setCurrentItem(item)
                return

        # If not found, select first item
        if self.topic_list.count() > 0:
            self.topic_list.setCurrentRow(0)

    def _on_topic_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None):
        """Handle topic selection change."""
        if not current:
            return

        topic_name = current.text()
        help_file = self.help_files.get(topic_name)

        if not help_file or not help_file.exists():
            self.content_browser.setHtml(
                f"<h1>Error</h1><p>Help file not found: {topic_name}</p>"
            )
            return

        try:
            markdown_content = self._load_markdown_file(help_file)
            html_content = self._markdown_to_html(markdown_content)
            self.content_browser.setHtml(html_content)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error Loading Help",
                f"Failed to load help file '{topic_name}':\n{e}"
            )

    def _load_markdown_file(self, path: Path) -> str:
        """Load markdown content from file."""
        return path.read_text(encoding="utf-8")

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML using markdown-it-py."""
        try:
            from markdown_it import MarkdownIt
            md_parser = MarkdownIt()
            html = md_parser.render(markdown)

            # Wrap in HTML with basic styling
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                        padding: 20px;
                        max-width: 900px;
                    }}
                    h1 {{
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                        margin-top: 24px;
                    }}
                    h2 {{
                        color: #34495e;
                        margin-top: 20px;
                        border-bottom: 1px solid #ecf0f1;
                        padding-bottom: 5px;
                    }}
                    h3 {{
                        color: #7f8c8d;
                        margin-top: 16px;
                    }}
                    code {{
                        background-color: #f4f4f4;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: 'Courier New', Courier, monospace;
                        font-size: 13px;
                    }}
                    pre {{
                        background-color: #2c3e50;
                        color: #ecf0f1;
                        padding: 15px;
                        border-radius: 5px;
                        overflow-x: auto;
                    }}
                    pre code {{
                        background-color: transparent;
                        color: inherit;
                        padding: 0;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 16px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #3498db;
                        color: white;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    a {{
                        color: #3498db;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                    ul, ol {{
                        padding-left: 30px;
                    }}
                    li {{
                        margin: 6px 0;
                    }}
                    blockquote {{
                        border-left: 4px solid #3498db;
                        padding-left: 16px;
                        margin: 16px 0;
                        color: #7f8c8d;
                    }}
                </style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """
        except ImportError:
            # Fallback if markdown-it-py is not available
            return f"""
            <h1>Markdown Parser Not Available</h1>
            <p>The markdown-it-py library is required to display help content.</p>
            <p>Install with: <code>pip install markdown-it-py</code></p>
            <h2>Raw Content:</h2>
            <pre>{markdown}</pre>
            """
        except Exception as e:
            return f"""
            <h1>Error Parsing Markdown</h1>
            <p>Failed to convert markdown to HTML: {e}</p>
            <h2>Raw Content:</h2>
            <pre>{markdown}</pre>
            """
