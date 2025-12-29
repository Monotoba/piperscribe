from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TtsResult:
    output_wav: Path


class TtsEngine(Protocol):
    def synthesize_to_wav(self, text: str, output_wav: Path) -> TtsResult: ...
