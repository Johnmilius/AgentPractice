# Agent Spec Template — Luke's NGAI Agents

## What This Is

This is the master template for creating agent specs in Luke's workspace. Every agent under `Make-AI-Agents-Luke/` should have two files built from these templates:

- `docs/agents/<agent_id>.json` — machine-readable contract (built from `make_agent.json`)
- `docs/agents/<agent_id>.md` — human-readable narrative (built from this file)

Together these form an **Agent Spec**: a complete, consistent description of what an agent does, how to use it, and how to validate it.

---

## How to Create a New Agent Spec

Tell Claude Code:

> "Using the `make_agent` templates in `Make-AI-Agents-Luke/`, create a new Tier [1|2|3] agent spec for '[Agent Name]'. The agent's code will be in `Make-AI-Agents-Luke/[Agent Name]/src/agents/<agent_id>.py`."

Claude will ask you questions to fill in the spec, then generate both files.

---

## Folder Layout (per agent)

```
Make-AI-Agents-Luke/
└── <Agent Name>/
    ├── docs/agents/
    │   ├── <agent_id>.json     ← machine contract
    │   └── <agent_id>.md       ← this narrative
    ├── src/agents/
    │   └── <agent_id>.py       ← your implementation
    └── tests/
        └── test_<agent_id>.py  ← mirrors validation.test_cases from JSON
```

---

## Narrative Template

When writing the `.md` for a new agent, follow this structure:

---

# [Agent Name]

## Mission

[One paragraph: what problem does this agent solve, and who is it for? Be specific about the outcome, not just the process.]

---

## How to Use It

[Tell the user exactly how to invoke this agent. Include the opening prompt they should use, and list any runtime questions the agent will ask them.]

---

## Output

[Describe what the agent produces. If it's a file, show the structure. If it's an API response, show an example shape.]

---

## Pitfalls

[List 3-5 specific, realistic things that can go wrong or produce bad results. Be honest about limitations.]

---

## Design Rationale

[Explain the 2-3 biggest design decisions and why they were made. Focus on trade-offs, not just "we chose X".]

---

## Implementation Notes

[List external tools, APIs, environment variables, and runtime requirements needed to run this agent.]

---

## Tier Guidelines

| Tier | Use When | Required Sections |
|---|---|---|
| **1** (Prototype) | Personal use, testing ideas, internal tools | agent_id, tier, agent_type, description, io_contract, workflow, validation (1 test case) |
| **2** (Production) | Shared with others, deployed, called by other systems | + error_handling, dependencies, auth, config, 2+ test cases |
| **3** (Complex) | Platform components, frameworks, multi-agent orchestration | + observability, scaling, 3+ test cases |

---

## Prompting Patterns

**Create a new spec:**
> "Using the `make_agent` templates, create a new Tier 2 agent spec for a '[Name]' agent. The code will be in `Make-AI-Agents-Luke/[Name]/src/agents/<id>.py`."

**Edit an existing spec:**
> "Using the `make_agent` templates, load the existing spec for '[Name]'. Update [section] to [change]."

**Validate a spec:**
> "Review `<agent_id>.json`. Does it meet Tier 2 requirements? List any missing fields."

**Understand a spec:**
> "Summarize the key mission and pitfalls from `<agent_id>.md`."
