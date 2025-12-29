from __future__ import annotations

from pathlib import Path

from .base import ImportResult
from .html import HtmlImporter


class MarkdownImporter:
    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".markdown"}

    def import_file(self, path: Path) -> ImportResult:
        md = path.read_text(encoding="utf-8", errors="replace")

        try:
            from markdown_it import MarkdownIt  # type: ignore
            md_parser = MarkdownIt("commonmark", {"html": False})
            html = md_parser.render(md)
            tmp = path.with_suffix(".html.__tmp__")
            tmp.write_text(html, encoding="utf-8")
            try:
                res = HtmlImporter().import_file(tmp)
                return ImportResult(title=path.stem, text=res.text)
            finally:
                try:
                    tmp.unlink()
                except OSError:
                    pass
        except Exception:
            import re
            s = re.sub(r"(?s)```.*?```", "", md)
            s = re.sub(r"(?m)^#{1,6}\s+", "", s)
            s = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", s)
            s = re.sub(r"[*_`~]", "", s)
            s = re.sub(r"\n\s*\n+", "\n\n", s).strip() + "\n"
            return ImportResult(title=path.stem, text=s)
