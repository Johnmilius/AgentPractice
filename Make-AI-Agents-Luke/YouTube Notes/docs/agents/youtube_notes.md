# YouTube Notes Agent

## Mission

The YouTube Notes agent turns a topic request into a structured, self-contained learning document. Given a subject, it finds relevant YouTube videos, reads their transcripts, and produces a markdown file that first teaches you what you need to know about the topic, then backs that up with per-video summaries and direct links with timestamp callouts.

The agent is designed to be additive — if you've already researched a topic, running it again appends new findings to your existing notes rather than starting over.

---

## How to Use It

Start a conversation with:

> "Use the YouTube Notes agent. I want to learn about [topic]."

The agent will then ask you:
1. **What audience level?** (beginner / intermediate / advanced) — this controls how the teaching section is written
2. **How many videos?** (default: 5)
3. **Where to save the output?** (default: `Make-AI-Agents-Luke/YouTube Notes/<topic>.md`)

From there, it handles everything: searching, fetching transcripts, summarizing, and writing the file.

---

## Output Structure

```
# [Topic]

## What You Should Know About [Topic]
<synthesized teaching doc, written at your audience level>

---

## Video Summaries

### 1. [Video Title]
**Link**: https://youtube.com/watch?v=...
**Key Points**:
- ...
- ...
**Timestamp Highlights**:
- [0:42] — ...
- [3:15] — ...

### 2. [Video Title]
...
```

---

## Pitfalls

- **Token cost scales with transcript length.** Very long videos (1h+) produce large transcripts. If you're researching a broad topic, prefer `num_videos = 3` to keep costs down on your first pass.
- **Transcript quality varies.** Auto-generated captions can have errors, especially for technical jargon, names, or heavy accents. The agent summarizes what it finds — verify anything critical.
- **Not all videos have transcripts.** The agent skips these automatically and finds replacements, but for very niche topics the search pool may be small. You may get fewer videos than requested.
- **YouTube search is not a peer-review filter.** High view counts signal popularity, not accuracy. The teaching doc reflects what the videos say — always validate technical claims from a primary source.

---

## Design Rationale

- **Transcripts over video processing** — reading transcript text is far more token-efficient than processing video frames or audio
- **Single LLM agent** — a simple sequential loop is easier to debug and cheaper to run than a multi-agent pipeline
- **Recency + views ranking** — balances freshness (relevant to fast-moving topics) with quality signal (popular videos tend to be clearer)
- **Additive file behavior** — lets your notes grow over time without losing prior research

---

## Implementation Notes

- Uses `yt-dlp` or YouTube Data API v3 for transcript and metadata retrieval
- Requires Python 3.10+
- Tests live in `tests/test_youtube_notes.py` and should validate the three core test cases defined in `youtube_notes.json`
