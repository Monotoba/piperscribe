from __future__ import annotations

from pathlib import Path

from .base import ImportResult


class PdfImporter:
    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def import_file(self, path: Path) -> ImportResult:
        try:
            import fitz  # PyMuPDF
        except Exception as e:  # pragma: no cover
            raise RuntimeError("PDF import requires `PyMuPDF`. Install with: pip install PyMuPDF") from e

        doc = fitz.open(str(path))
        parts = []
        for page in doc:
            parts.append(page.get_text("text"))
        text = "\n".join(parts).strip() + "\n"
        return ImportResult(title=path.stem, text=text)
