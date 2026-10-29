from __future__ import annotations

from pathlib import Path
from typing import List

from .base import Importer, ImportResult
from .docx import DocxImporter
from .html import HtmlImporter
from .markdown import MarkdownImporter
from .pdf import PdfImporter
from .txt import TxtImporter


def default_importers() -> List[Importer]:
    return [
        PdfImporter(),
        DocxImporter(),
        MarkdownImporter(),
        HtmlImporter(),
        TxtImporter(),
    ]


def import_any(path: Path) -> ImportResult:
    for imp in default_importers():
        if imp.can_import(path):
            return imp.import_file(path)
    raise RuntimeError(f"No importer for: {path.suffix}")
