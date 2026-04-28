# CONTEXT.md — What keel is and why it exists

## The Problem

Agentic coding tools (aider, opencode, claude code) fail in a specific, reproducible way:

1. Agent writes a file
2. Something breaks (test, CI)
3. Agent patches the nearest thing to make the signal go green
4. It doesn't fix the root — it satisfies the metric
5. Next session: agent reads the patched code as ground truth, builds on top of it
6. Repeat 20 times → **slop fortress**: a codebase that compiles but nobody understands

This is not a model quality problem. It is a **memory and context architecture problem**, grounded in how transformers work.

## Why This Happens (The LLM Mechanics)

- Transformers have a **U-shaped attention curve**: primacy (start of context) and recency (end of context) get high attention. The middle is structurally starved — proven mathematically at random initialization, not a training artifact.
- A failing test lands at **maximum recency**. The architectural spec, if it exists at all, sits in the **dead middle**. The model does what its architecture tells it: weight the recent thing heavily. Patch the test.
- After ~40 turns, goal drift sets in. The original intent has slid fully into the middle graveyard. The agent is solving a different problem and doesn't know it.
- Context rot compounds this: performance degrades non-linearly as context grows. More context is often worse, not better.

## What keel is

**keel is a decision memory layer that wraps any terminal coding agent.**

It is not a coding agent. It does not write code. It is the harness that makes other agents reliable by giving them persistent, structured memory of architectural decisions across all sessions.

The key mechanic: **spec injection at the exact moment of file write, not at session start.**

Because file writes are when architectural damage happens, not when conversations start.

## The Architecture

### Core components

**1. Decision Memory Store** (`.keel/memory.db` — local SQLite, no infra)

Stores extracted architectural decisions from every commit:
- `decision`: what was decided
- `module`: which module/path it governs
- `confidence`: LOW / MEDIUM / HIGH
- `event_type`: NEW / REINFORCE / CONTRADICT
- `commit_hash`: provenance
- `reinforcement_count`: how many commits have confirmed this
- `last_seen_commit`: for soft decay

**2. Post-commit Extractor** (git hook, one LLM call via BYOK)

Fires after every commit. Receives: diff + commit message + existing decisions for touched file paths.

Returns JSON only. If uncertain: returns empty. Never guesses.

Classifies each finding as NEW, REINFORCE, or CONTRADICT.
- NEW + REINFORCE → stored/updated
- CONTRADICT → flagged for human review, never auto-injected

**3. Pre-write Injector** (git hook, fires before file write is committed)

Queries `.keel/memory.db` for decisions relevant to the files being touched.

Ranking: recency × confidence × reinforcement_count → top-k selected.

Injects as a user-turn message (not system prompt — proven higher compliance) immediately before the write decision.

Injection format: `"The following architectural decisions govern this module. Do not contradict unless explicitly instructed: [decisions]"`

**4. `keel status`** (human-in-the-loop, like `git status`)

Surfaces: LOW confidence decisions, CONFLICT decisions pending review.

Developer accepts / rejects / edits in ~30 seconds. Not a daily chore. Occasional sanity check.

### What keel is NOT

- Not a GUI tool
- Not a vibe-coder tool (that is a future mode, not MVP)
- Not a coding agent
- Not a cloud service — all state lives in `.keel/` inside the repo
- Not an AGENTS.md / CLAUDE.md replacement — it wraps those, it is deeper

## Target User

Terminal users who already use aider, opencode, or claude code. They type commands. They know what a git hook is. They will bring their own API key.

**Not**: Bolt/Lovable/Replit users. Not the canva crowd. That is a future mode.

## Key Design Constraints

- BYOK (bring your own key) — zero infra cost to maintain
- All state local to the repo (`.keel/` directory)
- Two LLM calls per commit cycle maximum
- No vector DB on day one — file path + module tag matching only
- Open-core: harness is MIT licensed, intelligence layer (drift scoring, team memory sync) is future closed layer
- Git is the universal abstraction — every serious agent commits via git, so git hooks are the agent-agnostic interception layer

## Name

**keel** — the structural spine of a ship. Without it, the ship drifts and capsizes. Invisible to the user, everything depends on it.

CLI verbs: `keel init` · `keel status` · `keel run [agent]` · `keel review`
