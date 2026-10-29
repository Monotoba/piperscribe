from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from piperscribe.rules import RegexRule, canned_rules


APP_ID = "piperscribe"
SETTINGS_FILENAME = "settings.json"


def _config_dir() -> Path:
    # XDG base dir support
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / APP_ID
    return Path.home() / ".config" / APP_ID


def settings_path() -> Path:
    return _config_dir() / SETTINGS_FILENAME


@dataclass(slots=True)
class AppSettings:
    theme: str = "system"  # system | light | dark
    model_path: str = ""
    voice_dir: str = ""  # directory scanned for voices; empty = use defaults
    speed: float = 1.0
    noise_scale: float = 0.667
    noise_w: float = 0.8
    rules: List[RegexRule] | None = None
    auto_apply_rules: bool = True
    recent_projects: list[str] | None = None
    recent_files: list[str] | None = None
    show_selection_toolbar: bool = True
    # Document appearance settings
    font_family: str = ""
    font_size: int = 0
    use_default_font: bool = True
    doc_bg_color: str = ""
    doc_text_color: str = ""
    use_default_colors: bool = True
    # Voice repositories
    voice_repositories: list[str] | None = None
    # WAV player for previews: "" = detect and save, "auto" = detect every run, or a player name
    audio_player: str = ""
    # Folder for generated audio; empty = next to the project file (temp folder if unsaved)
    audio_output_dir: str = ""

    def __post_init__(self) -> None:
        if self.rules is None:
            self.rules = canned_rules()
        if self.recent_files is None:
            self.recent_files = []
        if self.recent_projects is None:
            self.recent_projects = []
        if self.voice_repositories is None:
            self.voice_repositories = [
                "https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json"
            ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme": self.theme,
            "model_path": self.model_path,
            "voice_dir": self.voice_dir,
            "speed": float(self.speed),
            "noise_scale": float(self.noise_scale),
            "noise_w": float(self.noise_w),
            "auto_apply_rules": bool(self.auto_apply_rules),
            "show_selection_toolbar": bool(self.show_selection_toolbar),
            "recent_files": list(self.recent_files or []),
            "recent_projects": list(self.recent_projects or []),
            "font_family": str(self.font_family),
            "font_size": int(self.font_size),
            "use_default_font": bool(self.use_default_font),
            "doc_bg_color": str(self.doc_bg_color),
            "doc_text_color": str(self.doc_text_color),
            "use_default_colors": bool(self.use_default_colors),
            "voice_repositories": list(self.voice_repositories or []),
            "audio_player": str(self.audio_player),
            "audio_output_dir": str(self.audio_output_dir),
            "rules": [
                {
                    "name": r.name,
                    "pattern": r.pattern,
                    "action": r.action,
                    "enabled": r.enabled,
                    "ignore_case": r.ignore_case,
                    "multiline": r.multiline,
                    "dotall": r.dotall,
                }
                for r in (self.rules or [])
            ],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AppSettings":
        s = AppSettings()
        s.theme = str(d.get("theme", s.theme))
        s.model_path = str(d.get("model_path", s.model_path))
        s.voice_dir = str(d.get("voice_dir", s.voice_dir))
        s.speed = float(d.get("speed", s.speed))
        s.noise_scale = float(d.get("noise_scale", s.noise_scale))
        s.noise_w = float(d.get("noise_w", s.noise_w))
        s.auto_apply_rules = bool(d.get("auto_apply_rules", True))
        s.show_selection_toolbar = bool(d.get("show_selection_toolbar", True))
        s.recent_files = list(d.get("recent_files", []))
        s.recent_projects = list(d.get("recent_projects", []))
        s.font_family = str(d.get("font_family", ""))
        s.font_size = int(d.get("font_size", 0))
        s.use_default_font = bool(d.get("use_default_font", True))
        s.doc_bg_color = str(d.get("doc_bg_color", ""))
        s.doc_text_color = str(d.get("doc_text_color", ""))
        s.use_default_colors = bool(d.get("use_default_colors", True))
        s.voice_repositories = list(d.get("voice_repositories", []))
        s.audio_player = str(d.get("audio_player", ""))
        s.audio_output_dir = str(d.get("audio_output_dir", ""))
        rules_d = d.get("rules")
        if isinstance(rules_d, list):
            parsed: List[RegexRule] = []
            for rd in rules_d:
                if not isinstance(rd, dict):
                    continue
                parsed.append(
                    RegexRule(
                        name=str(rd.get("name", "Rule")),
                        pattern=str(rd.get("pattern", "")),
                        action=str(rd.get("action", "exclude")),
                        enabled=bool(rd.get("enabled", True)),
                        ignore_case=bool(rd.get("ignore_case", True)),
                        multiline=bool(rd.get("multiline", True)),
                        dotall=bool(rd.get("dotall", False)),
                    )
                )
            s.rules = parsed
        # clamp/sanitize lightly
        if s.theme not in {"system", "light", "dark"}:
            s.theme = "system"
        s.speed = min(max(s.speed, 0.5), 2.0)
        s.noise_scale = min(max(s.noise_scale, 0.0), 2.0)
        s.noise_w = min(max(s.noise_w, 0.0), 2.0)
        return s


def load_settings() -> AppSettings:
    path = settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return AppSettings.from_dict(data)
    except FileNotFoundError:
        pass
    except Exception:
        # Corrupt file: ignore but keep it for inspection
        pass
    return AppSettings()


def save_settings(settings: AppSettings) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")


def reset_settings() -> None:
    """Delete the persisted settings file, if present."""
    path = settings_path()
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except Exception:
        return
