# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

**NGAI Agent Spec Templates** — a documentation-driven workflow for creating structured "Agent Specs" that turn general AI into specialized agents. This is a template/documentation project; there is no source code to build or test directly.

## Workflow

The core workflow is conversational:
1. User instructs the AI to create/edit/validate an agent spec using the `make_agent` templates.
2. AI generates or modifies `<agent>.json` (structured contract) and `<agent>.md` (narrative) files.
3. User reviews and iterates.

## Agent Spec Structure

Each agent spec consists of two files:
- `docs/agents/<agent>.json` — machine-readable contract (agent type, I/O, validation commands, test cases)
- `docs/agents/<agent>.md` — human-readable narrative (mission, pitfalls, design rationale)

Suggested project layout:
```
project/
├── src/agents/<agent>.py
├── docs/agents/<agent>.json
├── docs/agents/<agent>.md
└── tests/test_<agent>.py
```

## Tier System

- **Tier 1** — Prototypes/internal tools (~15 min, minimal fields)
- **Tier 2** — Shared/deployed services (~25 min)
- **Tier 3** — Frameworks/platform components (~40 min, all fields)

Tier determines which fields are required in `make_agent.json`.

## Key Design Decisions

- **JSON + MD split**: JSON for machine parsing (3x faster for AI agents), MD for human context
- **Validation lives in JSON**: `validation.commands` field is the single source of truth for running tests
- **One template, three tiers**: Same template scales from prototype to production

## Collaborators

- `Make-AI-Agents-Luke/` — Luke's agents (all of Luke's work goes here)
- `Make-AI-Agents-John/` — John's agents (separate collaborator, same structure)

## Creating a New Agent for Luke

Use the master templates at `Make-AI-Agents-Luke/make_agent.json` and `Make-AI-Agents-Luke/make_agent.md` as the base. Each agent gets its own subfolder:

```
Make-AI-Agents-Luke/<Agent Name>/
├── docs/agents/<agent_id>.json       # machine-readable spec
├── docs/agents/<agent_id>.md         # human-readable narrative
├── src/agents/<agent_id>.py          # implementation (if applicable)
├── tests/test_<agent_id>.py          # validation tests
└── <output_files>.md                 # agent-generated outputs live here too
```

## Design Specs (Superpowers)

Pre-build design specs for new agents live in `docs/superpowers/specs/`. These are dated design documents created *before* implementation, used to think through I/O contracts, workflow steps, and error handling:

```
docs/superpowers/specs/
└── YYYY-MM-DD-<agent-name>-design.md
```

When planning a new agent, create a design spec here first, then use it as the basis for generating the `make_agent.json` and `make_agent.md` files.

## Completed Agents

### YouTube Notes Agent (`Make-AI-Agents-Luke/YouTube Notes/`)
- **Tier**: 2 (Production)
- **Type**: `llm_agent`
- **Purpose**: Researches a topic by fetching YouTube video transcripts, then produces a structured markdown file with a synthesized teaching section and per-video summaries
- **Design spec**: `docs/superpowers/specs/2026-03-11-youtube-notes-design.md`
- **Spec files**: `docs/agents/youtube_notes.json` / `docs/agents/youtube_notes.md`
- **Example output**: `How to Use Claude Code the Best.md` (test run using written guides as transcript proxies)
- **Key implementation note**: Uses `yt-dlp` or YouTube Data API v3; requires Python 3.10+; tests in `tests/test_youtube_notes.py`
