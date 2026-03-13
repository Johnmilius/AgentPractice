# YouTube Notes Agent — Design Spec
**Date**: 2026-03-11
**Tier**: 2 (Production)
**Type**: `llm_agent`
**Location**: `Make-AI-Agents-Luke/YouTube Notes/`

---

## 1. Purpose

An agent that researches a user-specified topic by finding and reading YouTube video transcripts, then produces a structured markdown file that:
1. Teaches the user about the topic (synthesized across all videos, written at their requested level)
2. Provides per-video summaries with YouTube links and timestamp highlights

---

## 2. I/O Contract

### Inputs (collected via runtime prompts)
| Field | Type | Default | Description |
|---|---|---|---|
| `topic` | string | — | Topic to research |
| `audience_level` | string | — | beginner / intermediate / advanced |
| `num_videos` | integer | 5 | Number of videos to synthesize |
| `output_path` | string | `Make-AI-Agents-Luke/YouTube Notes/<topic>.md` | Where to save the output |

### Outputs
- Markdown file at `output_path` containing:
  - Synthesized teaching section ("What you should know about X")
  - Per-video summaries with YouTube URL and timestamp highlights

### Side Effects
- If `<topic>.md` already exists: appends new findings
- If it does not exist: creates from scratch

---

## 3. Core Workflow

1. **Prompt user** — collect topic, audience level, num_videos (default 5), output path (default YouTube Notes folder)
2. **Check for existing file** — if `<topic>.md` exists, load it for append mode
3. **Search YouTube** — query for topic, rank results by recency + view count, pull top candidates
4. **Fetch transcripts** — use `yt-dlp` or YouTube Data API; skip videos with no transcript and pull next candidate until `num_videos` valid videos are found
5. **Summarize each video** — extract key points and timestamp highlights
6. **Synthesize** — write teaching doc section pitched at the user's audience level, drawing across all videos
7. **Write output** — save/append markdown file

---

## 4. Error Handling

| Scenario | Behavior |
|---|---|
| Video has no transcript | Skip silently, pull next candidate |
| Fewer than `num_videos` transcripts found after exhausting search | Warn user, proceed with what was found |
| Output file already exists | Append new content, do not overwrite |

---

## 5. Validation

| Test | Expected Result |
|---|---|
| Topic = "Python decorators", audience = beginner, num_videos = 3 | File created with teaching section + 3 video summaries + links |
| Run same topic again | Existing file detected, new content appended |
| All top results lack transcripts | Agent keeps searching; warns user if results exhausted |

**Validation command**: `pytest tests/test_youtube_notes.py`

---

## 6. Design Decisions

- **Single LLM agent** (not multi-agent pipeline) — simpler, fewer tokens, easier to debug
- **Transcripts over metadata** — accurate content at minimal token cost vs. watching video or using descriptions only
- **Recency + views ranking** — balances freshness and quality signal
- **Additive file behavior** — prevents losing prior research while allowing the doc to grow over time
