from __future__ import annotations

from pathlib import Path

from .base import ImportResult


class DocxImporter:
    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() == ".docx"

    def import_file(self, path: Path) -> ImportResult:
        try:
            import docx  # python-docx
        except Exception as e:  # pragma: no cover
            raise RuntimeError("DOCX import requires `python-docx`. Install with: pip install python-docx") from e

        d = docx.Document(str(path))
        parts = []
        for p in d.paragraphs:
            parts.append(p.text)
        text = "\n".join(parts).strip() + "\n"
        return ImportResult(title=path.stem, text=text)
