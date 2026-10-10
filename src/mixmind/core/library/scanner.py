"""Dependency-free scanner for supported local audio files."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"}
)


def scan_audio_files(folder: str | Path, *, recursive: bool = True) -> list[Path]:
    """Return supported audio files sorted case-insensitively; never modify or upload them."""
    root = Path(folder).expanduser()
    if not root.is_dir():
        return []
    try:
        iterator = root.rglob("*") if recursive else root.iterdir()
        paths = [
            path for path in iterator
            if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ]
    except OSError:
        return []
    return sorted(paths, key=lambda path: str(path).casefold())
