"""Tests for WAV player detection and resolution. Named *_test.py because .gitignore excludes test_*.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from piperscribe.audio import player
from piperscribe.audio.player import (
    AUTO,
    DEFAULT,
    PLAYERS,
    build_command,
    detect_platform,
    resolve_player,
)


def _only(*available: str):
    """Fake shutil.which that finds only the named executables."""
    def which(exe: str, *args, **kwargs):
        return f"/usr/bin/{exe}" if exe in available else None
    return which


@pytest.mark.parametrize(
    ("platform", "env", "expected"),
    [
        ("win32", {}, "windows"),
        ("darwin", {}, "macos"),
        ("linux", {}, "linux"),
        ("linux", {"ANDROID_ROOT": "/system"}, "android"),
        ("freebsd13", {}, "other"),
    ],
)
def test_detect_platform(monkeypatch, platform, env, expected):
    monkeypatch.setattr(player.sys, "platform", platform)
    monkeypatch.delenv("ANDROID_ROOT", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert detect_platform() == expected


def test_default_detects_and_saves(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only("afplay"))
    result = resolve_player(DEFAULT, platform="macos")
    assert result.spec is PLAYERS["afplay"]
    assert result.save_as == "afplay"


def test_auto_detects_without_saving(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only("aplay"))
    result = resolve_player(AUTO, platform="linux")
    assert result.spec is PLAYERS["aplay"]
    assert result.save_as is None


def test_saved_player_that_is_installed_is_used_as_is(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only("ffplay", "aplay"))
    result = resolve_player("ffplay", platform="linux")
    assert result.spec is PLAYERS["ffplay"]
    assert result.save_as is None


def test_missing_saved_player_is_replaced_and_saved(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only("aplay"))
    result = resolve_player("ffplay", platform="linux")
    assert result.spec is PLAYERS["aplay"]
    assert result.save_as == "aplay"


def test_unknown_saved_name_is_replaced(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only("afplay"))
    result = resolve_player("mpv", platform="macos")
    assert result.spec is PLAYERS["afplay"]
    assert result.save_as == "afplay"


def test_no_player_installed_returns_none(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only())
    result = resolve_player(DEFAULT, platform="linux")
    assert result.spec is None
    assert result.save_as is None


def test_auto_with_no_player_does_not_save(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only())
    result = resolve_player(AUTO, platform="linux")
    assert result.spec is None
    assert result.save_as is None


def test_linux_falls_through_to_next_installed_player(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only("paplay"))
    result = resolve_player(DEFAULT, platform="linux")
    assert result.spec is PLAYERS["paplay"]


def test_android_uses_termux_player(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only("termux-media-player"))
    result = resolve_player(DEFAULT, platform="android")
    assert result.spec is PLAYERS["termux-media-player"]


def test_windows_uses_builtin_winsound_without_path_lookup(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", _only())
    result = resolve_player(DEFAULT, platform="windows")
    # The fallback runs the same interpreter, so PATH lookup is not needed.
    assert result.spec is PLAYERS["winsound"]
    assert result.spec is not None
    assert result.spec.command[0] == player.sys.executable


def test_build_command_appends_path_as_separate_argument(tmp_path: Path):
    wav = tmp_path / "my preview.wav"
    argv = build_command(PLAYERS["aplay"], wav)
    assert argv == ["aplay", "-q", str(wav)]
