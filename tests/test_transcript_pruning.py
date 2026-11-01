"""Tests for transcript session retention and pruning."""

import tempfile
from pathlib import Path
from transcript_writer import TranscriptWriter


def test_transcript_prunes_to_max_sessions(tmp_path: Path):
    """Verify that only the newest max_sessions sessions are kept."""
    # Create 30 fake sessions with 3 files each
    for i in range(1, 31):
        ts = f"20261101_{i:06d}"
        for kind in ("original", "translation", "all"):
            file_path = tmp_path / f"livetrans_{ts}_{kind}.txt"
            file_path.write_text(f"Session {i} {kind}", encoding="utf-8")

    assert len(list(tmp_path.glob("livetrans_*.txt"))) == 90

    # Initialize TranscriptWriter with max_sessions=25 (default)
    writer = TranscriptWriter(tmp_path, max_sessions=25)

    remaining_files = list(tmp_path.glob("livetrans_*.txt"))
    assert len(remaining_files) == 75  # 25 sessions * 3 files

    # The 5 oldest sessions (1..5) should be deleted
    for i in range(1, 6):
        ts = f"20261101_{i:06d}"
        for kind in ("original", "translation", "all"):
            assert not (tmp_path / f"livetrans_{ts}_{kind}.txt").exists()

    # The newest 25 sessions (6..30) should remain intact
    for i in range(6, 31):
        ts = f"20261101_{i:06d}"
        for kind in ("original", "translation", "all"):
            assert (tmp_path / f"livetrans_{ts}_{kind}.txt").exists()

    writer.close()


def test_transcript_preserves_non_livetrans_files(tmp_path: Path):
    """Verify user files and other notes in transcripts dir are never pruned."""
    custom_file = tmp_path / "notes.txt"
    custom_file.write_text("important user notes", encoding="utf-8")
    gitkeep = tmp_path / ".gitkeep"
    gitkeep.write_text("", encoding="utf-8")

    # Create 5 sessions
    for i in range(1, 6):
        ts = f"20261101_{i:06d}"
        for kind in ("original", "translation", "all"):
            (tmp_path / f"livetrans_{ts}_{kind}.txt").write_text("data", encoding="utf-8")

    # Prune keeping only 2
    writer = TranscriptWriter(tmp_path, max_sessions=2)

    assert custom_file.exists()
    assert custom_file.read_text(encoding="utf-8") == "important user notes"
    assert gitkeep.exists()

    # Only sessions 4 and 5 remain (2 * 3 = 6 files)
    assert len(list(tmp_path.glob("livetrans_*.txt"))) == 6
    writer.close()


def test_transcript_active_session_never_pruned(tmp_path: Path):
    """Verify that the currently active session is preserved even if pruning is triggered."""
    writer = TranscriptWriter(tmp_path, max_sessions=2)
    # Open an active session and write
    writer.write_original(1, "12:00:00", "hello")

    # Prune with max_sessions=1
    deleted = writer.prune_old_transcripts(max_sessions=1)
    paths = writer.session_paths()
    for p in paths.values():
        assert Path(p).exists()

    writer.close()


def test_transcript_prune_noop_when_under_limit(tmp_path: Path):
    """No files are deleted if total sessions are within the limit."""
    for i in range(1, 10):
        ts = f"20261101_{i:06d}"
        (tmp_path / f"livetrans_{ts}_all.txt").write_text("data", encoding="utf-8")

    writer = TranscriptWriter(tmp_path, max_sessions=25)
    assert len(list(tmp_path.glob("*.txt"))) == 9
    writer.close()
