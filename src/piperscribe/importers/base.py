from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ImportResult:
    title: str
    text: str


class Importer(Protocol):
    def can_import(self, path: Path) -> bool: ...
    def import_file(self, path: Path) -> ImportResult: ...
