from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


DEFAULT_VOICE_DIRS = [
    Path("~/.local/share/piper/voices").expanduser(),
    Path("~/share/piper/voices").expanduser(),
    Path("/usr/share/piper-voices"),
    Path("/usr/local/share/piper-voices"),
]


@dataclass(frozen=True, slots=True)
class PiperInstallStatus:
    found: bool
    path: Optional[str]
    error: Optional[str] = None


def check_piper_installed() -> PiperInstallStatus:
    exe = shutil.which("piper")
    if not exe:
        return PiperInstallStatus(found=False, path=None, error="`piper` not found on PATH.")
    # Quick sanity: ensure it can run
    try:
        subprocess.run([exe, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception as e:
        return PiperInstallStatus(found=False, path=exe, error=f"`piper` exists but failed to run: {e}")
    return PiperInstallStatus(found=True, path=exe, error=None)


def iter_model_paths(search_dirs: Iterable[Path] = DEFAULT_VOICE_DIRS) -> List[Path]:
    models: List[Path] = []
    for d in search_dirs:
        try:
            if d.exists() and d.is_dir():
                models.extend(sorted(d.glob("*.onnx")))
        except OSError:
            continue
    # Deduplicate by resolved path (best effort)
    seen = set()
    out: List[Path] = []
    for p in models:
        try:
            key = str(p.resolve())
        except OSError:
            key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def choose_default_model(models: List[Path]) -> Optional[Path]:
    if not models:
        return None
    # Prefer "en_US-lessac-medium.onnx" if present (common default)
    for p in models:
        if p.name == "en_US-lessac-medium.onnx":
            return p
    return models[0]
