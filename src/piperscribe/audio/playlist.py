"""Playlist export functionality for multi-document projects."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from piperscribe.model.document import DocumentProject


def export_m3u_playlist(project: DocumentProject, playlist_path: Path) -> None:
    """
    Export M3U playlist with relative audio paths.

    The M3U format is a simple text-based playlist format:
    - First line: #EXTM3U (header)
    - For each track:
      - #EXTINF:{duration},{title}
      - {path_to_audio_file}

    Args:
        project: DocumentProject with documents containing audio
        playlist_path: Path where the .m3u file will be saved
    """
    lines = ["#EXTM3U\n"]

    for doc in project.get_playlist_order():
        # Skip documents without generated audio
        if not doc.audio_path or not Path(doc.audio_path).exists():
            continue

        # Duration in seconds (integer)
        duration = int(doc.audio_duration)
        title = doc.title

        # Make path relative to playlist location
        audio_path = Path(doc.audio_path)
        try:
            rel_path = audio_path.relative_to(playlist_path.parent)
        except ValueError:
            # If paths are on different drives or can't be made relative, use absolute
            rel_path = audio_path

        # Add EXTINF metadata and file path
        lines.append(f"#EXTINF:{duration},{title}\n")
        lines.append(f"{rel_path}\n")

    # Write playlist file
    playlist_path.write_text("".join(lines), encoding="utf-8")


def export_json_playlist(project: DocumentProject, json_path: Path) -> None:
    """
    Export JSON playlist with rich metadata.

    The JSON format includes detailed information about the project
    and each document, useful for custom players or analysis tools.

    Args:
        project: DocumentProject with documents containing audio
        json_path: Path where the .json file will be saved
    """
    # Calculate total duration
    total_duration = sum(
        d.audio_duration
        for d in project.get_playlist_order()
        if d.audio_path
    )

    # Build playlist structure
    playlist: Dict[str, Any] = {
        "project_title": project.title,
        "format_version": "1.0",
        "total_duration": round(total_duration, 2),
        "document_count": len(project.get_playlist_order()),
        "documents": []
    }

    for doc in project.get_playlist_order():
        # Skip documents without generated audio
        if not doc.audio_path or not Path(doc.audio_path).exists():
            continue

        doc_info: Dict[str, Any] = {
            "id": doc.id,
            "title": doc.title,
            "order": doc.order,
            "audio_path": doc.audio_path,
            "duration": round(doc.audio_duration, 2),
        }

        # Add optional fields
        if doc.source_path:
            doc_info["source_path"] = doc.source_path

        # Add text statistics
        doc_info["text_length"] = len(doc.text)
        doc_info["exclusions_count"] = len(doc.exclusions)

        # Add TTS settings used
        doc_info["tts_settings"] = {
            "model_path": doc.piper.model_path,
            "length_scale": doc.piper.length_scale,
            "noise_scale": doc.piper.noise_scale,
            "noise_w": doc.piper.noise_w,
        }

        playlist["documents"].append(doc_info)

    # Write JSON file with pretty formatting
    json_path.write_text(
        json.dumps(playlist, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def get_missing_audio_documents(project: DocumentProject) -> List[str]:
    """
    Get list of enabled document titles that don't have audio.

    Args:
        project: DocumentProject to check

    Returns:
        List of document titles missing audio
    """
    missing = []
    for doc in project.get_playlist_order():
        if not doc.audio_path or not Path(doc.audio_path).exists():
            missing.append(doc.title)
    return missing


def validate_playlist_export(project: DocumentProject) -> tuple[bool, str]:
    """
    Validate that project is ready for playlist export.

    Args:
        project: DocumentProject to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if project has any enabled documents
    enabled_docs = project.get_playlist_order()
    if not enabled_docs:
        return False, "No enabled documents in project. Enable at least one document."

    # Check if any documents have audio
    docs_with_audio = [
        d for d in enabled_docs
        if d.audio_path and Path(d.audio_path).exists()
    ]

    if not docs_with_audio:
        return False, "No documents have generated audio. Generate audio first."

    return True, ""
