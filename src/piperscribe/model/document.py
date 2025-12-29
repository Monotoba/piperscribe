from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .spans import Span


@dataclass(slots=True)
class PiperSettings:
    model_path: str = ""
    length_scale: float = 1.0
    noise_scale: float = 0.667
    noise_w: float = 0.8

    def to_args(self) -> list[str]:
        args = []
        if self.model_path:
            args += ["--model", self.model_path]
        args += ["--length_scale", str(self.length_scale)]
        args += ["--noise_scale", str(self.noise_scale)]
        args += ["--noise_w", str(self.noise_w)]
        return args


@dataclass(slots=True)
class DocumentProject:
    source_path: Optional[str] = None
    title: str = "Untitled"
    text: str = ""
    manual_exclusions: List[Span] = field(default_factory=list)
    exclusions: List[Span] = field(default_factory=list)
    piper: PiperSettings = field(default_factory=PiperSettings)
    theme: str = "system"  # system | light | dark

    def as_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "title": self.title,
            "text": self.text,
            "manual_exclusions": [{"start": s.start, "end": s.end, "reason": s.reason} for s in self.manual_exclusions],
            "exclusions": [{"start": s.start, "end": s.end, "reason": s.reason} for s in self.exclusions],
            "theme": self.theme,
            "piper": {
                "model_path": self.piper.model_path,
                "length_scale": self.piper.length_scale,
                "noise_scale": self.piper.noise_scale,
                "noise_w": self.piper.noise_w,
            },
        }

    @staticmethod
    def from_dict(d: dict) -> "DocumentProject":
        proj = DocumentProject()
        proj.source_path = d.get("source_path")
        proj.title = d.get("title", proj.title)
        proj.text = d.get("text", "")
        if "manual_exclusions" in d:
            proj.manual_exclusions = [Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("manual_exclusions", [])]
        else:
            # Backward compat: treat legacy exclusions as manual
            proj.manual_exclusions = [Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("exclusions", [])]
        # Keep exclusions field for backward compat display; callers will recompute as needed.
        proj.exclusions = [Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("exclusions", [])]
        p = d.get("piper", {}) or {}
        proj.theme = str(d.get("theme", "system"))
        proj.piper = PiperSettings(
            model_path=str(p.get("model_path", "")),
            length_scale=float(p.get("length_scale", 1.0)),
            noise_scale=float(p.get("noise_scale", 0.667)),
            noise_w=float(p.get("noise_w", 0.8)),
        )
        return proj
