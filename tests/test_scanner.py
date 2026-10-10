from pathlib import Path

from mixmind.core.library.scanner import scan_audio_files


def test_scan_audio_files_filters_extensions_and_sorts(tmp_path: Path) -> None:
    (tmp_path / "zeta.MP3").write_bytes(b"")
    (tmp_path / "alpha.wav").write_bytes(b"")
    (tmp_path / "notes.txt").write_text("not audio", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "track.flac").write_bytes(b"")
    assert [path.name for path in scan_audio_files(tmp_path)] == [
        "alpha.wav", "track.flac", "zeta.MP3"
    ]


def test_scan_audio_files_non_recursive(tmp_path: Path) -> None:
    (tmp_path / "root.mp3").write_bytes(b"")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "inner.mp3").write_bytes(b"")
    assert [path.name for path in scan_audio_files(tmp_path, recursive=False)] == ["root.mp3"]


def test_scan_audio_files_missing_folder(tmp_path: Path) -> None:
    assert scan_audio_files(tmp_path / "missing") == []
