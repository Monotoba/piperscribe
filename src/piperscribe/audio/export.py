from __future__ import annotations

from pathlib import Path

from piperscribe.model.document import DocumentProject
from piperscribe.model.spans import subtract_spans
from piperscribe.tts.piper import PiperTts


def included_text(project: DocumentProject) -> str:
    text = subtract_spans(project.text, project.exclusions)
    return text.strip() + "\n"


def export_wav(project: DocumentProject, output_wav: Path) -> Path:
    text = included_text(project)
    if not text.strip():
        raise RuntimeError("Nothing to export (all text excluded or empty).")
    tts = PiperTts(project.piper)
    tts.synthesize_to_wav(text, output_wav)
    return output_wav
