import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "agents"))
from youtube_notes import (
    check_existing_file,
    transcript_to_text,
    rank_videos,
    format_output,
    write_output,
)


# --- check_existing_file ---

def test_check_existing_file_returns_none_when_missing(tmp_path):
    path = tmp_path / "nonexistent.md"
    assert check_existing_file(path) is None


def test_check_existing_file_returns_content_when_exists(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# Existing Notes", encoding="utf-8")
    result = check_existing_file(path)
    assert result == "# Existing Notes"


# --- transcript_to_text ---

def test_transcript_to_text_joins_segments():
    transcript = [
        {"text": "Hello", "start": 0.0, "duration": 1.0},
        {"text": "world", "start": 1.0, "duration": 1.0},
    ]
    result = transcript_to_text(transcript)
    assert result == "Hello world"


def test_transcript_to_text_empty():
    assert transcript_to_text([]) == ""


# --- rank_videos ---

def test_rank_videos_returns_sorted_list():
    now = datetime.now(timezone.utc)
    videos = [
        {"id": "a", "view_count": 100, "published_at": (now - timedelta(days=30)).isoformat()},
        {"id": "b", "view_count": 10000, "published_at": (now - timedelta(days=300)).isoformat()},
        {"id": "c", "view_count": 5000, "published_at": (now - timedelta(days=10)).isoformat()},
    ]
    ranked = rank_videos(videos)
    assert isinstance(ranked, list)
    assert len(ranked) == 3
    assert ranked[0]["id"] == "c"  # high views + very recent


def test_rank_videos_handles_zero_views():
    now = datetime.now(timezone.utc)
    videos = [
        {"id": "a", "view_count": 0, "published_at": (now - timedelta(days=1)).isoformat()},
    ]
    ranked = rank_videos(videos)
    assert ranked[0]["id"] == "a"


# --- format_output ---

def test_format_output_contains_topic():
    summaries = [{
        "id": "abc123",
        "title": "Test Video",
        "channel": "Test Channel",
        "url": "https://youtube.com/watch?v=abc123",
        "key_points": ["- Point one", "- Point two"],
    }]
    result = format_output(
        topic="Python",
        audience_level="beginner",
        teaching_doc="## What You Should Know\nThis is the teaching doc.",
        summaries=summaries,
        timestamp_highlights={"abc123": ["[1:00] — Key moment"]},
    )
    assert "# Python" in result
    assert "Test Video" in result
    assert "Point one" in result
    assert "[1:00] — Key moment" in result
    assert "beginner" in result.lower() or "Beginner" in result


def test_format_output_no_highlights():
    summaries = [{
        "id": "xyz",
        "title": "Vid",
        "channel": "Chan",
        "url": "https://youtube.com/watch?v=xyz",
        "key_points": ["- A point"],
    }]
    result = format_output("Topic", "intermediate", "Teaching.", summaries, {})
    assert "Timestamp Highlights" not in result


# --- write_output ---

def test_write_output_creates_new_file(tmp_path):
    path = tmp_path / "notes.md"
    write_output(path, "# New Content", existing_content=None)
    assert path.read_text(encoding="utf-8") == "# New Content"


def test_write_output_appends_to_existing(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# Existing", encoding="utf-8")
    write_output(path, "# New Research", existing_content="# Existing")
    content = path.read_text(encoding="utf-8")
    assert "# Existing" in content
    assert "# New Research" in content


def test_write_output_creates_parent_dirs(tmp_path):
    path = tmp_path / "deep" / "nested" / "notes.md"
    write_output(path, "# Content", existing_content=None)
    assert path.exists()
