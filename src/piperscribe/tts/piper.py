from __future__ import annotations

import subprocess
from pathlib import Path

from piperscribe.model.document import PiperSettings

from .base import TtsResult
from .piper_utils import check_piper_installed


class PiperTts:
    def __init__(self, settings: PiperSettings) -> None:
        self.settings = settings

    def synthesize_to_wav(self, text: str, output_wav: Path) -> TtsResult:
        status = check_piper_installed()
        if not status.found:
            raise RuntimeError(status.error or "`piper` is not installed or not runnable.")
        if not self.settings.model_path:
            raise RuntimeError(f"Piper model is not set. Choose a voice/model in the GUI. Data: {self.settings}")
        cmd = ["piper", *self.settings.to_args(), "--output_file", str(output_wav)]
        subprocess.run(cmd, input=text, text=True, check=True)
        return TtsResult(output_wav=output_wav)
