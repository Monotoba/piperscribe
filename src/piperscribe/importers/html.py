from __future__ import annotations

from pathlib import Path
import re

from .base import ImportResult


def _strip_html_fallback(html: str) -> str:
    # Extremely naive fallback: remove tags, collapse whitespace.
    s = re.sub(r"(?s)<script.*?>.*?</script>", " ", html)
    s = re.sub(r"(?s)<style.*?>.*?</style>", " ", s)
    s = re.sub(r"(?s)<.*?>", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip() + "\n"


class HtmlImporter:
    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() in {".html", ".htm"}

    def import_file(self, path: Path) -> ImportResult:
        html = path.read_text(encoding="utf-8", errors="replace")

        try:
            from bs4 import BeautifulSoup  # type: ignore
        except Exception:
            return ImportResult(title=path.stem, text=_strip_html_fallback(html))

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text("\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip() + "\n"
        return ImportResult(title=path.stem, text=text)
