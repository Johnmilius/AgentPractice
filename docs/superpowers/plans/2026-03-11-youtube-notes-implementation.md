# YouTube Notes Agent — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI Python agent that searches YouTube, fetches transcripts, and synthesizes a structured markdown teaching doc on any topic.

**Architecture:** Single Python script (`youtube_notes.py`) with clearly separated functions for each workflow step. YouTube Data API v3 handles search and ranking. `youtube-transcript-api` fetches captions. Claude Haiku summarizes individual videos; Claude Sonnet synthesizes the final teaching doc.

**Tech Stack:** Python 3.10+, `anthropic`, `google-api-python-client`, `youtube-transcript-api`, `python-dotenv`, `pytest`, `pytest-mock`

**Spec:** `docs/superpowers/specs/2026-03-11-youtube-notes-design.md`

---

## Chunk 1: Folder Restructure

### Task 1: Restructure YouTube Notes folder and update spec

**Files:**
- Move: `Make-AI-Agents-Luke/YouTube Notes/How to Use Claude Code the Best.md` → `Make-AI-Agents-Luke/YouTube Notes/notes/How to Use Claude Code the Best.md`
- Modify: `Make-AI-Agents-Luke/YouTube Notes/docs/agents/youtube_notes.json`
- Create: `Make-AI-Agents-Luke/YouTube Notes/requirements.txt`
- Create: `Make-AI-Agents-Luke/YouTube Notes/notes/` (directory)
- Create: `Make-AI-Agents-Luke/YouTube Notes/src/agents/` (directory)
- Create: `Make-AI-Agents-Luke/YouTube Notes/tests/` (directory)

- [ ] **Step 1: Create the new folder structure**

```bash
mkdir -p "Make-AI-Agents-Luke/YouTube Notes/notes"
mkdir -p "Make-AI-Agents-Luke/YouTube Notes/src/agents"
mkdir -p "Make-AI-Agents-Luke/YouTube Notes/tests"
```

- [ ] **Step 2: Move the existing notes file into notes/**

```bash
mv "Make-AI-Agents-Luke/YouTube Notes/How to Use Claude Code the Best.md" \
   "Make-AI-Agents-Luke/YouTube Notes/notes/How to Use Claude Code the Best.md"
```

- [ ] **Step 3: Update default output path in youtube_notes.json**

In `Make-AI-Agents-Luke/YouTube Notes/docs/agents/youtube_notes.json`, update:

```json
"default": "Make-AI-Agents-Luke/YouTube Notes/notes/<topic>.md"
```

Also update the config block:
```json
"config": {
  "default_num_videos": 5,
  "default_output_path": "Make-AI-Agents-Luke/YouTube Notes/notes/",
  ...
}
```

- [ ] **Step 4: Create requirements.txt**

Create `Make-AI-Agents-Luke/YouTube Notes/requirements.txt`:

```
anthropic>=0.40.0
google-api-python-client>=2.100.0
youtube-transcript-api>=0.6.2
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-mock>=3.12.0
```

- [ ] **Step 5: Verify final folder structure**

```
Make-AI-Agents-Luke/
├── make_agent.json
├── make_agent.md
└── YouTube Notes/
    ├── docs/agents/
    │   ├── youtube_notes.json
    │   └── youtube_notes.md
    ├── notes/
    │   └── How to Use Claude Code the Best.md
    ├── src/agents/
    │   └── (empty, ready for youtube_notes.py)
    ├── tests/
    │   └── (empty, ready for test_youtube_notes.py)
    └── requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add "Make-AI-Agents-Luke/"
git commit -m "chore: restructure YouTube Notes folder — add src/, tests/, notes/"
```

---

## Chunk 2: Pure Utility Functions (No API Calls)

### Task 2: Implement and test pure utility functions

These functions have no external dependencies — test them first.

**Files:**
- Create: `Make-AI-Agents-Luke/YouTube Notes/src/agents/youtube_notes.py`
- Create: `Make-AI-Agents-Luke/YouTube Notes/tests/test_youtube_notes.py`

**Functions covered in this task:**
- `check_existing_file(path)` → `Optional[str]`
- `transcript_to_text(transcript)` → `str`
- `rank_videos(videos)` → `list[dict]`
- `format_output(topic, audience_level, teaching_doc, summaries, timestamp_highlights)` → `str`
- `write_output(path, content, existing_content)` → `None`

---

- [ ] **Step 1: Write failing tests for utility functions**

Create `Make-AI-Agents-Luke/YouTube Notes/tests/test_youtube_notes.py`:

```python
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile
import os
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
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    videos = [
        {"id": "a", "view_count": 100, "published_at": (now - timedelta(days=30)).isoformat()},
        {"id": "b", "view_count": 10000, "published_at": (now - timedelta(days=300)).isoformat()},
        {"id": "c", "view_count": 5000, "published_at": (now - timedelta(days=10)).isoformat()},
    ]
    ranked = rank_videos(videos)
    assert isinstance(ranked, list)
    assert len(ranked) == 3
    # highest ranked should be c (high views + very recent)
    assert ranked[0]["id"] == "c"


def test_rank_videos_handles_zero_views():
    from datetime import datetime, timezone, timedelta
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
```

- [ ] **Step 2: Run tests — verify they all fail**

```bash
cd "Make-AI-Agents-Luke/YouTube Notes"
pytest tests/test_youtube_notes.py -v
```

Expected: `ModuleNotFoundError` (youtube_notes.py doesn't exist yet)

- [ ] **Step 3: Create youtube_notes.py with the utility functions**

Create `Make-AI-Agents-Luke/YouTube Notes/src/agents/youtube_notes.py`:

```python
#!/usr/bin/env python3
"""
YouTube Notes Agent
Researches a topic via YouTube transcripts and produces a structured markdown teaching doc.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Pure utility functions (no external API calls)
# ---------------------------------------------------------------------------

def check_existing_file(output_path: Path) -> Optional[str]:
    """Return existing file content if it exists, else None."""
    if output_path.exists():
        return output_path.read_text(encoding="utf-8")
    return None


def transcript_to_text(transcript: list[dict]) -> str:
    """Flatten transcript segments into a single string."""
    return " ".join(seg["text"] for seg in transcript)


def rank_videos(videos: list[dict]) -> list[dict]:
    """
    Rank videos by weighted score: 60% view count, 40% recency.
    Both signals are normalized to [0, 1].
    """
    if not videos:
        return videos

    max_views = max(v["view_count"] for v in videos) or 1
    now_ts = datetime.now(timezone.utc).timestamp()

    for v in videos:
        pub_ts = datetime.fromisoformat(
            v["published_at"].replace("Z", "+00:00")
        ).timestamp()
        age_days = (now_ts - pub_ts) / 86400
        recency_score = max(0.0, 1.0 - age_days / 365)
        view_score = v["view_count"] / max_views
        v["rank_score"] = 0.6 * view_score + 0.4 * recency_score

    return sorted(videos, key=lambda v: v["rank_score"], reverse=True)


def format_output(
    topic: str,
    audience_level: str,
    teaching_doc: str,
    summaries: list[dict],
    timestamp_highlights: dict,
) -> str:
    """Format the final markdown document."""
    date = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# {topic}",
        f"",
        f"*Generated by YouTube Notes Agent — {date}*",
        f"*Sources: {len(summaries)} videos | Audience: {audience_level.capitalize()}*",
        f"",
        f"---",
        f"",
        teaching_doc,
        f"",
        f"---",
        f"",
        f"## Video Summaries",
        f"",
    ]

    for i, summary in enumerate(summaries, 1):
        lines += [
            f"### {i}. {summary['title']}",
            f"**Channel:** {summary['channel']}",
            f"**Link:** [{summary['url']}]({summary['url']})",
            f"",
            f"**Key Points:**",
        ]
        for point in summary["key_points"]:
            lines.append(point)

        highlights = timestamp_highlights.get(summary["id"], [])
        if highlights:
            lines += ["", "**Timestamp Highlights:**"]
            for h in highlights:
                lines.append(f"- {h}")

        lines.append("")

    lines.append("*Run this agent again on the same topic to append new sources.*")
    return "\n".join(lines)


def write_output(
    output_path: Path, content: str, existing_content: Optional[str]
) -> None:
    """Write a new file or append to an existing one."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if existing_content is not None:
        date = datetime.now().strftime("%Y-%m-%d")
        separator = f"\n\n---\n\n## New Research — {date}\n\n"
        output_path.write_text(existing_content + separator + content, encoding="utf-8")
    else:
        output_path.write_text(content, encoding="utf-8")
```

- [ ] **Step 4: Run tests — verify they all pass**

```bash
cd "Make-AI-Agents-Luke/YouTube Notes"
pytest tests/test_youtube_notes.py -v
```

Expected: All 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add "Make-AI-Agents-Luke/YouTube Notes/src/" "Make-AI-Agents-Luke/YouTube Notes/tests/"
git commit -m "feat: add youtube_notes utility functions with tests"
```

---

## Chunk 3: YouTube API Integration

### Task 3: Implement and test YouTube search

**Files:**
- Modify: `Make-AI-Agents-Luke/YouTube Notes/src/agents/youtube_notes.py`
- Modify: `Make-AI-Agents-Luke/YouTube Notes/tests/test_youtube_notes.py`

- [ ] **Step 1: Write failing test for search_youtube**

Append to `tests/test_youtube_notes.py`:

```python
from unittest.mock import patch, MagicMock
from youtube_notes import search_youtube


def test_search_youtube_returns_ranked_videos():
    mock_search_response = {
        "items": [
            {"id": {"videoId": "vid1"}, "snippet": {}},
            {"id": {"videoId": "vid2"}, "snippet": {}},
        ]
    }
    mock_stats_response = {
        "items": [
            {
                "id": "vid1",
                "snippet": {"title": "Video One", "channelTitle": "Chan A", "publishedAt": "2025-01-01T00:00:00Z"},
                "statistics": {"viewCount": "10000"},
            },
            {
                "id": "vid2",
                "snippet": {"title": "Video Two", "channelTitle": "Chan B", "publishedAt": "2024-06-01T00:00:00Z"},
                "statistics": {"viewCount": "500"},
            },
        ]
    }

    with patch("youtube_notes.build") as mock_build:
        mock_yt = MagicMock()
        mock_build.return_value = mock_yt
        mock_yt.search().list().execute.return_value = mock_search_response
        mock_yt.videos().list().execute.return_value = mock_stats_response

        results = search_youtube("python decorators", max_results=5)

    assert len(results) == 2
    assert results[0]["id"] == "vid1"  # more views + more recent wins
    assert results[0]["url"] == "https://www.youtube.com/watch?v=vid1"
    assert "title" in results[0]
    assert "rank_score" in results[0]
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/test_youtube_notes.py::test_search_youtube_returns_ranked_videos -v
```

Expected: FAIL — `ImportError: cannot import name 'search_youtube'`

- [ ] **Step 3: Implement search_youtube**

Append to `youtube_notes.py` (after imports, add `from googleapiclient.discovery import build`):

```python
from googleapiclient.discovery import build

YOUTUBE_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY")

def search_youtube(topic: str, max_results: int = 20) -> list[dict]:
    """Search YouTube and return videos ranked by recency + views."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    search_response = youtube.search().list(
        q=topic,
        part="id,snippet",
        type="video",
        maxResults=max_results,
        videoDuration="medium",
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response["items"]]

    stats_response = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids),
    ).execute()

    videos = []
    for item in stats_response["items"]:
        stats = item.get("statistics", {})
        snippet = item["snippet"]
        videos.append({
            "id": item["id"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "published_at": snippet["publishedAt"],
            "view_count": int(stats.get("viewCount", 0)),
            "url": f"https://www.youtube.com/watch?v={item['id']}",
        })

    return rank_videos(videos)
```

- [ ] **Step 4: Run test — verify it passes**

```bash
pytest tests/test_youtube_notes.py::test_search_youtube_returns_ranked_videos -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add "Make-AI-Agents-Luke/YouTube Notes/src/" "Make-AI-Agents-Luke/YouTube Notes/tests/"
git commit -m "feat: add YouTube search with ranking"
```

---

### Task 4: Implement and test transcript fetching

**Files:**
- Modify: `Make-AI-Agents-Luke/YouTube Notes/src/agents/youtube_notes.py`
- Modify: `Make-AI-Agents-Luke/YouTube Notes/tests/test_youtube_notes.py`

- [ ] **Step 1: Write failing tests for fetch_transcript**

Append to `tests/test_youtube_notes.py`:

```python
from youtube_notes import fetch_transcript


def test_fetch_transcript_returns_list_on_success():
    mock_transcript = [{"text": "Hello", "start": 0.0, "duration": 1.0}]
    with patch("youtube_notes.YouTubeTranscriptApi.get_transcript", return_value=mock_transcript):
        result = fetch_transcript("abc123")
    assert result == mock_transcript


def test_fetch_transcript_returns_none_when_disabled():
    from youtube_transcript_api import TranscriptsDisabled
    with patch("youtube_notes.YouTubeTranscriptApi.get_transcript", side_effect=TranscriptsDisabled("abc")):
        result = fetch_transcript("abc123")
    assert result is None


def test_fetch_transcript_returns_none_on_any_error():
    with patch("youtube_notes.YouTubeTranscriptApi.get_transcript", side_effect=Exception("network error")):
        result = fetch_transcript("abc123")
    assert result is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_youtube_notes.py -k "fetch_transcript" -v
```

Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement fetch_transcript**

Append to `youtube_notes.py`:

```python
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


def fetch_transcript(video_id: str) -> Optional[list[dict]]:
    """Fetch transcript for a video. Returns None if unavailable."""
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception:
        return None
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_youtube_notes.py -k "fetch_transcript" -v
```

Expected: All 3 PASS

- [ ] **Step 5: Commit**

```bash
git add "Make-AI-Agents-Luke/YouTube Notes/src/" "Make-AI-Agents-Luke/YouTube Notes/tests/"
git commit -m "feat: add transcript fetching with graceful skip on missing captions"
```

---

## Chunk 4: AI Summarization + Synthesis

### Task 5: Implement and test video summarization and teaching doc synthesis

**Files:**
- Modify: `Make-AI-Agents-Luke/YouTube Notes/src/agents/youtube_notes.py`
- Modify: `Make-AI-Agents-Luke/YouTube Notes/tests/test_youtube_notes.py`

- [ ] **Step 1: Write failing tests for summarize_video and synthesize_teaching_doc**

Append to `tests/test_youtube_notes.py`:

```python
from youtube_notes import summarize_video, synthesize_teaching_doc, get_timestamp_highlights


def test_summarize_video_returns_key_points(mocker):
    mock_response = MagicMock()
    mock_response.content[0].text = "- Point one\n- Point two\n- Point three"
    mocker.patch("youtube_notes.ANTHROPIC_CLIENT.messages.create", return_value=mock_response)

    video = {"id": "v1", "title": "Test Video", "channel": "Chan", "url": "https://yt.com"}
    result = summarize_video(video, "This is the transcript text.")

    assert "key_points" in result
    assert len(result["key_points"]) == 3
    assert result["key_points"][0] == "- Point one"
    assert result["title"] == "Test Video"  # original fields preserved


def test_synthesize_teaching_doc_returns_string(mocker):
    mock_response = MagicMock()
    mock_response.content[0].text = "## What You Should Know\nHere is the teaching content."
    mocker.patch("youtube_notes.ANTHROPIC_CLIENT.messages.create", return_value=mock_response)

    summaries = [{
        "title": "Test Video",
        "key_points": ["- Point one"],
    }]
    result = synthesize_teaching_doc("Python", "beginner", summaries)
    assert "What You Should Know" in result


def test_get_timestamp_highlights_returns_list(mocker):
    mock_response = MagicMock()
    mock_response.content[0].text = "[1:30] — Key concept explained\n[4:00] — Common mistake shown"
    mocker.patch("youtube_notes.ANTHROPIC_CLIENT.messages.create", return_value=mock_response)

    transcript = [{"text": "Hello", "start": i * 10.0, "duration": 5.0} for i in range(20)]
    result = get_timestamp_highlights(transcript, "", "Test Video")

    assert isinstance(result, list)
    assert len(result) == 2
    assert "[1:30]" in result[0]
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_youtube_notes.py -k "summarize or synthesize or highlights" -v
```

Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement AI functions**

Append to `youtube_notes.py`:

```python
from anthropic import Anthropic

ANTHROPIC_CLIENT = Anthropic()


def summarize_video(video: dict, transcript_text: str) -> dict:
    """Summarize a single video's transcript into bullet points using Claude Haiku."""
    response = ANTHROPIC_CLIENT.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": (
                f"Summarize this YouTube video transcript into 4-5 key bullet points.\n"
                f"Be specific and concrete — no filler.\n\n"
                f"Video title: {video['title']}\n\n"
                f"Transcript: {transcript_text[:8000]}\n\n"
                f"Return only the bullet points, each starting with '- '."
            ),
        }],
    )
    key_points = [
        line.strip()
        for line in response.content[0].text.strip().split("\n")
        if line.strip().startswith("-")
    ]
    return {**video, "key_points": key_points}


def get_timestamp_highlights(
    transcript: list[dict], _summary: str, video_title: str
) -> list[str]:
    """Identify 3-4 key timestamp moments from a transcript using Claude Haiku."""
    segments = []
    for seg in transcript[::10]:
        mins = int(seg["start"] // 60)
        secs = int(seg["start"] % 60)
        segments.append(f"[{mins}:{secs:02d}] {seg['text']}")

    condensed = "\n".join(segments[:100])

    response = ANTHROPIC_CLIENT.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": (
                f"Video: \"{video_title}\"\n\n"
                f"Transcript samples with timestamps:\n{condensed}\n\n"
                f"Identify 3-4 key moments worth highlighting.\n"
                f"Format each as: [M:SS] — brief description\n"
                f"Return only the timestamp lines, nothing else."
            ),
        }],
    )
    lines = response.content[0].text.strip().split("\n")
    return [line.strip() for line in lines if line.strip() and "[" in line]


def synthesize_teaching_doc(
    topic: str, audience_level: str, summaries: list[dict]
) -> str:
    """Write a cross-video teaching section using Claude Sonnet."""
    combined = "\n\n".join(
        f"Video: {s['title']}\nKey points:\n" + "\n".join(s["key_points"])
        for s in summaries
    )
    level_guidance = {
        "beginner": "explain concepts simply, use analogies, avoid jargon",
        "intermediate": "assume basics are known, focus on nuance and technique",
        "advanced": "focus on edge cases, trade-offs, and deep insights",
    }.get(audience_level, "explain clearly")

    response = ANTHROPIC_CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": (
                f"Write the teaching section of a research document about \"{topic}\".\n"
                f"Audience: {audience_level} ({level_guidance}).\n\n"
                f"You reviewed {len(summaries)} YouTube videos. Key points from each:\n\n"
                f"{combined}\n\n"
                f"Write a clear teaching section titled '## What You Should Know About {topic}'.\n"
                f"Use markdown headers and bullets. Be concrete and useful. 600-800 words."
            ),
        }],
    )
    return response.content[0].text.strip()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_youtube_notes.py -k "summarize or synthesize or highlights" -v
```

Expected: All 3 PASS

- [ ] **Step 5: Run all tests to verify nothing is broken**

```bash
pytest tests/test_youtube_notes.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add "Make-AI-Agents-Luke/YouTube Notes/src/" "Make-AI-Agents-Luke/YouTube Notes/tests/"
git commit -m "feat: add AI summarization and teaching doc synthesis"
```

---

## Chunk 5: Main Runner + Integration Tests

### Task 6: Implement main runner and spec integration tests (TC_01, TC_02, TC_03)

**Files:**
- Modify: `Make-AI-Agents-Luke/YouTube Notes/src/agents/youtube_notes.py`
- Modify: `Make-AI-Agents-Luke/YouTube Notes/tests/test_youtube_notes.py`

- [ ] **Step 1: Write integration tests matching the 3 spec test cases**

Append to `tests/test_youtube_notes.py`:

```python
from youtube_notes import run


# Shared mock helpers
def _mock_search_results():
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    return [
        {
            "id": f"vid{i}",
            "title": f"Video {i}",
            "channel": "Test Chan",
            "url": f"https://youtube.com/watch?v=vid{i}",
            "published_at": (now - timedelta(days=i * 10)).isoformat(),
            "view_count": 1000 * i,
            "rank_score": 1.0 - i * 0.1,
        }
        for i in range(1, 8)
    ]


def _mock_transcript():
    return [{"text": f"Word {i}", "start": float(i), "duration": 1.0} for i in range(50)]


def _mock_summary(video):
    return {**video, "key_points": ["- Key point one", "- Key point two"]}


# TC_01: Happy path — creates new file
def test_tc01_creates_new_file(tmp_path, mocker):
    output_path = tmp_path / "Python decorators.md"
    inputs = {
        "topic": "Python decorators",
        "audience_level": "beginner",
        "num_videos": 3,
        "output_path": output_path,
    }

    mocker.patch("youtube_notes.prompt_user", return_value=inputs)
    mocker.patch("youtube_notes.search_youtube", return_value=_mock_search_results())
    mocker.patch("youtube_notes.fetch_transcript", return_value=_mock_transcript())
    mocker.patch("youtube_notes.summarize_video", side_effect=_mock_summary)
    mocker.patch("youtube_notes.get_timestamp_highlights", return_value=["[0:10] — Key moment"])
    mocker.patch("youtube_notes.synthesize_teaching_doc", return_value="## What You Should Know\nContent here.")

    run()

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# Python decorators" in content
    assert "Video 1" in content
    assert "Key point one" in content
    assert "## Video Summaries" in content


# TC_02: Existing file — appends without overwriting
def test_tc02_appends_to_existing_file(tmp_path, mocker):
    output_path = tmp_path / "Python decorators.md"
    output_path.write_text("# Original Notes\nThis was here first.", encoding="utf-8")

    inputs = {
        "topic": "Python decorators",
        "audience_level": "beginner",
        "num_videos": 3,
        "output_path": output_path,
    }

    mocker.patch("youtube_notes.prompt_user", return_value=inputs)
    mocker.patch("youtube_notes.search_youtube", return_value=_mock_search_results())
    mocker.patch("youtube_notes.fetch_transcript", return_value=_mock_transcript())
    mocker.patch("youtube_notes.summarize_video", side_effect=_mock_summary)
    mocker.patch("youtube_notes.get_timestamp_highlights", return_value=[])
    mocker.patch("youtube_notes.synthesize_teaching_doc", return_value="## New teaching content.")

    run()

    content = output_path.read_text(encoding="utf-8")
    assert "# Original Notes" in content          # original preserved
    assert "This was here first." in content       # original preserved
    assert "New teaching content" in content       # new content appended


# TC_03: No transcripts available — warns and handles gracefully
def test_tc03_warns_when_insufficient_transcripts(tmp_path, mocker, capsys):
    output_path = tmp_path / "obscure topic.md"
    inputs = {
        "topic": "obscure niche topic",
        "audience_level": "intermediate",
        "num_videos": 5,
        "output_path": output_path,
    }

    mocker.patch("youtube_notes.prompt_user", return_value=inputs)
    mocker.patch("youtube_notes.search_youtube", return_value=_mock_search_results()[:3])
    # Only first video has a transcript, rest return None
    mocker.patch("youtube_notes.fetch_transcript", side_effect=[_mock_transcript(), None, None])
    mocker.patch("youtube_notes.summarize_video", side_effect=_mock_summary)
    mocker.patch("youtube_notes.get_timestamp_highlights", return_value=[])
    mocker.patch("youtube_notes.synthesize_teaching_doc", return_value="## Teaching.")

    run()

    captured = capsys.readouterr()
    assert "Warning" in captured.out or "warning" in captured.out.lower()
    assert output_path.exists()  # still produces output with what it found
```

- [ ] **Step 2: Run integration tests — verify they fail**

```bash
pytest tests/test_youtube_notes.py -k "tc0" -v
```

Expected: FAIL — `ImportError: cannot import name 'run'` and `cannot import name 'prompt_user'`

- [ ] **Step 3: Implement prompt_user and run()**

Append to `youtube_notes.py`:

```python
DEFAULT_NUM_VIDEOS = 5
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "notes"


def prompt_user() -> dict:
    """Collect runtime inputs interactively."""
    print("\n=== YouTube Notes Agent ===\n")

    topic = input("What topic do you want to learn about? ").strip()

    print("\nAudience level?")
    print("  1. Beginner\n  2. Intermediate\n  3. Advanced")
    choice = input("Enter 1, 2, or 3 (default: 1): ").strip() or "1"
    audience_level = {"1": "beginner", "2": "intermediate", "3": "advanced"}.get(choice, "beginner")

    num_str = input(f"\nHow many videos? (default: {DEFAULT_NUM_VIDEOS}): ").strip()
    num_videos = int(num_str) if num_str.isdigit() else DEFAULT_NUM_VIDEOS

    default_path = DEFAULT_OUTPUT_DIR / f"{topic}.md"
    path_str = input(f"\nOutput path? (default: {default_path}): ").strip()
    output_path = Path(path_str) if path_str else default_path

    return {
        "topic": topic,
        "audience_level": audience_level,
        "num_videos": num_videos,
        "output_path": output_path,
    }


def run() -> None:
    """Main agent entrypoint."""
    inputs = prompt_user()
    topic = inputs["topic"]
    audience_level = inputs["audience_level"]
    num_videos = inputs["num_videos"]
    output_path = inputs["output_path"]

    existing_content = check_existing_file(output_path)
    if existing_content:
        print(f"\nExisting notes found at {output_path} — will append new content.")

    print(f"\nSearching YouTube for '{topic}'...")
    candidates = search_youtube(topic, max_results=num_videos * 4)

    summaries = []
    timestamp_highlights = {}
    fetched = 0

    for candidate in candidates:
        if fetched >= num_videos:
            break

        print(f"Fetching transcript: {candidate['title'][:60]}...")
        transcript = fetch_transcript(candidate["id"])

        if transcript is None:
            print("  No transcript — skipping.")
            continue

        transcript_text = transcript_to_text(transcript)
        summary = summarize_video(candidate, transcript_text)
        highlights = get_timestamp_highlights(transcript, "", candidate["title"])

        summaries.append(summary)
        timestamp_highlights[candidate["id"]] = highlights
        fetched += 1
        print(f"  Done ({fetched}/{num_videos})")

    if not summaries:
        print("\nNo transcripts found for any candidates. Try a broader topic.")
        return

    if fetched < num_videos:
        print(f"\nWarning: Only found {fetched} videos with transcripts (requested {num_videos}).")

    print("\nSynthesizing teaching document...")
    teaching_doc = synthesize_teaching_doc(topic, audience_level, summaries)
    content = format_output(topic, audience_level, teaching_doc, summaries, timestamp_highlights)
    write_output(output_path, content, existing_content)

    print(f"\nDone! Notes saved to: {output_path}")


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run integration tests — verify they pass**

```bash
pytest tests/test_youtube_notes.py -k "tc0" -v
```

Expected: All 3 PASS (TC_01, TC_02, TC_03)

- [ ] **Step 5: Run the full test suite**

```bash
pytest tests/test_youtube_notes.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Smoke test the real CLI (requires API keys)**

```bash
cd "Make-AI-Agents-Luke/YouTube Notes"
pip install -r requirements.txt
YOUTUBE_DATA_API_KEY=<your_key> python src/agents/youtube_notes.py
```

Enter "Python decorators", "beginner", "3" when prompted. Verify the output file appears in `notes/`.

- [ ] **Step 7: Final commit**

```bash
git add "Make-AI-Agents-Luke/YouTube Notes/"
git commit -m "feat: complete youtube_notes agent — runner, prompts, and integration tests"
```

---

## Final Folder Structure

After all tasks complete:

```
Make-AI-Agents-Luke/
├── make_agent.json
├── make_agent.md
└── YouTube Notes/
    ├── docs/agents/
    │   ├── youtube_notes.json
    │   └── youtube_notes.md
    ├── notes/
    │   └── How to Use Claude Code the Best.md
    ├── src/agents/
    │   └── youtube_notes.py
    ├── tests/
    │   └── test_youtube_notes.py
    └── requirements.txt
```
