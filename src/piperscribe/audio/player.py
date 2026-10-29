"""Choose and build the command that plays a WAV file on this system."""
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


# Setting values. Empty means "detect now and save the result". AUTO means
# "detect on every run and never save". A saved name that is missing from this
# system is re-detected and replaced.
DEFAULT = ""
AUTO = "auto"

# Runs with the same interpreter as the app, so it needs no external tool.
_WINSOUND_CODE = "import sys, winsound; winsound.PlaySound(sys.argv[1], winsound.SND_FILENAME)"


@dataclass(frozen=True, slots=True)
class PlayerSpec:
    name: str
    command: tuple[str, ...]  # program and fixed arguments; the WAV path is appended


PLAYERS: dict[str, PlayerSpec] = {
    spec.name: spec
    for spec in (
        PlayerSpec("winsound", (sys.executable, "-c", _WINSOUND_CODE)),
        PlayerSpec("afplay", ("afplay",)),
        PlayerSpec("aplay", ("aplay", "-q")),
        PlayerSpec("pw-play", ("pw-play",)),
        PlayerSpec("paplay", ("paplay",)),
        PlayerSpec("ffplay", ("ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet")),
        PlayerSpec("termux-media-player", ("termux-media-player", "play")),
    )
}

# Names to try, in order, for each platform.
PLATFORM_PLAYERS: dict[str, tuple[str, ...]] = {
    "windows": ("winsound",),
    "macos": ("afplay",),
    "linux": ("aplay", "pw-play", "paplay", "ffplay"),
    "android": ("termux-media-player",),
    "other": (),
}


@dataclass(frozen=True, slots=True)
class Resolution:
    spec: PlayerSpec | None  # None when no player is available
    save_as: str | None  # value to store in settings, or None to leave settings alone


def detect_platform() -> str:
    # Check Android first: Python on Android can report sys.platform as "linux".
    if sys.platform == "android" or "ANDROID_ROOT" in os.environ:
        return "android"
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return "other"


def player_names() -> list[str]:
    return sorted(PLAYERS)


def _usable(spec: PlayerSpec) -> bool:
    program = spec.command[0]
    if os.path.isabs(program):
        return os.path.exists(program)
    return shutil.which(program) is not None


def _first_usable(platform: str) -> PlayerSpec | None:
    for name in PLATFORM_PLAYERS.get(platform, ()):
        spec = PLAYERS[name]
        if _usable(spec):
            return spec
    return None


def resolve_player(setting: str, platform: str | None = None) -> Resolution:
    """Pick the player to use for this run.

    ``setting`` is the saved value: a player name, ``AUTO``, or ``DEFAULT``.
    """
    setting = (setting or DEFAULT).strip()
    platform = platform or detect_platform()

    if setting and setting != AUTO:
        spec = PLAYERS.get(setting)
        if spec is not None and _usable(spec):
            return Resolution(spec, None)
        # Unknown or missing player: detect again and save the replacement.

    found = _first_usable(platform)
    if setting == AUTO:
        return Resolution(found, None)
    return Resolution(found, found.name if found else None)


def build_command(spec: PlayerSpec, wav_path: Path) -> list[str]:
    return [*spec.command, str(wav_path)]
