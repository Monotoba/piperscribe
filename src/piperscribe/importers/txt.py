from __future__ import annotations

from pathlib import Path

from .base import ImportResult


class TxtImporter:
    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() in {".txt", ".text"}

    def import_file(self, path: Path) -> ImportResult:
        raw = path.read_text(encoding="utf-8", errors="replace")
        title = path.stem
        return ImportResult(title=title, text=raw)
