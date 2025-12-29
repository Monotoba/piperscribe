from __future__ import annotations

from dataclasses import replace
from typing import List

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from piperscribe.rules import RegexRule, test_rule


class RulesEditorWidget(QWidget):
    """Inline rule editor widget (used inside Preferences)."""

    def __init__(self, parent: QWidget | None, rules: List[RegexRule], document_text: str) -> None:
        super().__init__(parent)
        self._text = document_text
        self._rules: List[RegexRule] = [replace(r) for r in (rules or [])]

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.currentRowChanged.connect(self._load_selected)

        self.name = QLineEdit()
        self.action = QComboBox()
        self.action.addItems(["exclude", "include"])
        self.enabled = QCheckBox("Enabled")
        self.ignore_case = QCheckBox("Ignore case")
        self.multiline = QCheckBox("Multiline (^$)")
        self.dotall = QCheckBox("Dot matches newline")

        self.pattern = QPlainTextEdit()
        self.pattern.setPlaceholderText(r"Enter regex pattern…")

        self.use_document_text = QCheckBox("Use document text")
        self.use_document_text.setChecked(True)
        self.use_document_text.toggled.connect(self._toggle_test_text_source)

        self.test_text = QPlainTextEdit()
        self.test_text.setPlaceholderText("Test text will appear here...")
        self.test_text.setFixedHeight(80)  # Fixed height for 4-5 lines
        self.test_text.setReadOnly(True)  # Start as read-only when using document text
        if self._text:
            self.test_text.setPlainText(self._text)

        self.test_out = QPlainTextEdit()
        self.test_out.setReadOnly(True)

        btn_test = QPushButton("Test")
        btn_test.clicked.connect(self._test_current)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._add_rule)

        btn_dup = QPushButton("Duplicate")
        btn_dup.clicked.connect(self._duplicate_rule)

        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._delete_rule)

        left = QWidget()
        lyl = QVBoxLayout(left)
        lyl.addWidget(QLabel("Rules"))
        lyl.addWidget(self.list, 1)
        row = QHBoxLayout()
        row.addWidget(btn_add)
        row.addWidget(btn_dup)
        row.addWidget(btn_del)
        lyl.addLayout(row)

        right = QWidget()
        ryl = QVBoxLayout(right)

        form = QFormLayout()
        form.addRow("Name:", self.name)
        form.addRow("Action:", self.action)

        flags = QHBoxLayout()
        flags.addWidget(self.enabled)
        flags.addWidget(self.ignore_case)
        flags.addWidget(self.multiline)
        flags.addWidget(self.dotall)
        fw = QWidget()
        fw.setLayout(flags)
        form.addRow("Flags:", fw)

        ryl.addLayout(form)
        ryl.addWidget(QLabel("Pattern:"))
        ryl.addWidget(self.pattern, 1)

        ryl.addWidget(self.use_document_text)
        ryl.addWidget(QLabel("Test text:"))
        ryl.addWidget(self.test_text, 0)

        btnrow = QHBoxLayout()
        btnrow.addWidget(btn_test)
        btnrow.addStretch(1)
        ryl.addLayout(btnrow)

        ryl.addWidget(QLabel("Test results (up to 10 previews):"))
        ryl.addWidget(self.test_out, 1)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(splitter, 1)

        self._rebuild_list()
        if self._rules:
            self.list.setCurrentRow(0)

    def rules(self) -> List[RegexRule]:
        self._save_selected()
        return self._rules

    def set_document_text(self, text: str) -> None:
        self._text = text
        # Update test text field if using document text
        if self.use_document_text.isChecked():
            self.test_text.setPlainText(text)

    def _rebuild_list(self) -> None:
        self.list.clear()
        for r in self._rules:
            label = f"{'✓' if r.enabled else '⨯'} {r.action}: {r.name}"
            self.list.addItem(QListWidgetItem(label))

    def _idx(self) -> int:
        return self.list.currentRow()

    def _load_selected(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._rules):
            return
        r = self._rules[idx]
        self.name.setText(r.name)
        self.action.setCurrentText(r.action)
        self.enabled.setChecked(r.enabled)
        self.ignore_case.setChecked(r.ignore_case)
        self.multiline.setChecked(r.multiline)
        self.dotall.setChecked(r.dotall)
        self.pattern.setPlainText(r.pattern)
        self.test_out.setPlainText("")

    def _save_selected(self) -> None:
        idx = self._idx()
        if idx < 0 or idx >= len(self._rules):
            return
        r = self._rules[idx]
        r.name = self.name.text().strip() or "Rule"
        r.action = self.action.currentText().strip()
        r.enabled = self.enabled.isChecked()
        r.ignore_case = self.ignore_case.isChecked()
        r.multiline = self.multiline.isChecked()
        r.dotall = self.dotall.isChecked()
        r.pattern = self.pattern.toPlainText()
        self._rebuild_list()
        self.list.setCurrentRow(idx)

    def _add_rule(self) -> None:
        self._save_selected()
        self._rules.append(RegexRule(name="New rule", pattern=r"")) 
        self._rebuild_list()
        self.list.setCurrentRow(len(self._rules) - 1)

    def _duplicate_rule(self) -> None:
        self._save_selected()
        idx = self._idx()
        if idx < 0:
            return
        r = self._rules[idx]
        self._rules.append(replace(r, name=r.name + " (copy)"))
        self._rebuild_list()
        self.list.setCurrentRow(len(self._rules) - 1)

    def _delete_rule(self) -> None:
        idx = self._idx()
        if idx < 0:
            return
        del self._rules[idx]
        self._rebuild_list()
        if self._rules:
            self.list.setCurrentRow(min(idx, len(self._rules) - 1))

    def _toggle_test_text_source(self, checked: bool) -> None:
        """Toggle between document text and custom test text."""
        if checked:
            # Use document text - make read-only and populate with document
            self.test_text.setReadOnly(True)
            self.test_text.setPlainText(self._text)
        else:
            # Use custom text - make editable
            self.test_text.setReadOnly(False)
            # Keep current text if any, otherwise clear

    def _test_current(self) -> None:
        self._save_selected()
        idx = self._idx()
        if idx < 0 or idx >= len(self._rules):
            return
        r = self._rules[idx]
        # Get test text from the test_text field
        test_text = self.test_text.toPlainText()
        try:
            n, previews = test_rule(test_text, r)
        except Exception as e:
            QMessageBox.critical(self, "Regex error", str(e))
            return
        lines = [f"Matches: {n}"]
        if previews:
            lines.append("")
            lines.extend(previews)
        self.test_out.setPlainText("\n".join(lines))
