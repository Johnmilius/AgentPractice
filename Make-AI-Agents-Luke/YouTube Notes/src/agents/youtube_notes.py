"""
youtube_notes.py — Core utility functions for the YouTube Notes agent.

Provides pure data-transformation helpers (no external API calls):
  - check_existing_file: read a file if it exists
  - transcript_to_text: flatten a transcript segment list to a string
  - rank_videos: score and sort videos by views + recency
  - format_output: build the final markdown document
  - write_output: write or append to an output file
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# check_existing_file
# ---------------------------------------------------------------------------

def check_existing_file(path: Path) -> Optional[str]:
    """Return the file's text content if it exists, else None."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


# ---------------------------------------------------------------------------
# transcript_to_text
# ---------------------------------------------------------------------------

def transcript_to_text(transcript: list[dict]) -> str:
    """Join the `text` field of each transcript segment with spaces."""
    return " ".join(seg["text"] for seg in transcript)


# ---------------------------------------------------------------------------
# rank_videos
# ---------------------------------------------------------------------------

def rank_videos(videos: list[dict]) -> list[dict]:
    """
    Rank videos by a weighted score:
      60% normalised view_count + 40% recency (1-year exponential decay).

    Returns the list sorted descending by rank_score.
    """
    if not videos:
        return []

    now = datetime.now(timezone.utc)
    max_views = max(v["view_count"] for v in videos) or 1  # avoid /0

    def _score(video: dict) -> float:
        # Normalise views
        view_score = video["view_count"] / max_views

        # Recency: age in days, clipped to [0, 1] with 1-year decay
        published_raw = video["published_at"]
        # Handle both offset-aware and offset-naive ISO strings
        published = datetime.fromisoformat(published_raw)
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age_days = (now - published).total_seconds() / 86400
        recency_score = max(0.0, 1.0 - age_days / 365)

        return 0.6 * view_score + 0.4 * recency_score

    scored = [(v, _score(v)) for v in videos]
    scored.sort(key=lambda t: t[1], reverse=True)

    # Attach rank_score to each video dict (non-destructive copy not required
    # by the spec, but convenient for callers)
    result = []
    for video, score in scored:
        entry = dict(video)
        entry["rank_score"] = score
        result.append(entry)

    return result


# ---------------------------------------------------------------------------
# format_output
# ---------------------------------------------------------------------------

def format_output(
    topic: str,
    audience_level: str,
    teaching_doc: str,
    summaries: list[dict],
    timestamp_highlights: dict,
) -> str:
    """
    Build the final markdown notes document.

    Structure:
        # {topic}
        *Audience level: {audience_level}* | Generated: {date}
        ---
        {teaching_doc}
        ---
        ## Video Summaries
        ### {title}
        ...
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines: list[str] = []

    # Header
    lines.append(f"# {topic}")
    lines.append(f"*Audience level: {audience_level}* | Generated: {today}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Teaching doc
    lines.append(teaching_doc)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Video summaries
    lines.append("## Video Summaries")
    lines.append("")

    for summary in summaries:
        vid_id = summary["id"]
        lines.append(f"### {summary['title']}")
        lines.append(f"**Channel:** {summary['channel']}")
        lines.append(f"**Link:** {summary['url']}")
        lines.append("")

        # Key points
        lines.append("**Key Points:**")
        for point in summary.get("key_points", []):
            lines.append(point)
        lines.append("")

        # Optional timestamp highlights
        highlights = timestamp_highlights.get(vid_id)
        if highlights:
            lines.append("**Timestamp Highlights:**")
            for hl in highlights:
                lines.append(hl)
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# write_output
# ---------------------------------------------------------------------------

def write_output(
    output_path: Path,
    content: str,
    existing_content: Optional[str],
) -> None:
    """
    Write `content` to `output_path`.

    If `existing_content` is not None the file already exists; append
    `content` under a dated separator rather than overwriting.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if existing_content is not None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        separator = f"\n\n---\n\n## Appended {today}\n\n"
        output_path.write_text(
            existing_content + separator + content,
            encoding="utf-8",
        )
    else:
        output_path.write_text(content, encoding="utf-8")
