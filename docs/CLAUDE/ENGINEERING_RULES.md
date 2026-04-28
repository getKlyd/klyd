# ENGINEERING_RULES.md — Non-negotiable constraints for building keel

## Language & Stack

- **Python** — matches the aider ecosystem, broadest terminal dev community
- **SQLite** via `sqlite3` stdlib — zero dependencies for the memory store
- **Click** — CLI framework, standard in Python tooling
- **No ORM** — raw SQL for the memory store, keep it readable and auditable
- **No vector DB on MVP** — file path + module tag string matching only

## Architecture Rules

### Rule 1: Two LLM calls per commit cycle. Maximum.
- Call 1 (post-commit): extraction — diff + commit message + existing relevant decisions → JSON
- Call 2 (pre-write): injection — top-k decisions for touched files → formatted string
- Any feature that requires a third call per cycle is out of scope for MVP

### Rule 2: Git hooks are the ONLY interception layer
- Do not attempt to hook into agent process internals
- Do not use file system watchers
- Do not wrap agent subprocess calls
- Git is universal across aider, opencode, claude code. Use it.

### Rule 3: Empty extraction beats bad extraction
- The extractor prompt must explicitly instruct: return empty JSON array if unsure
- Never store a decision with no clear evidence in the diff
- Conservative extraction, aggressive human review

### Rule 4: CONTRADICT decisions never auto-inject
- If the extractor classifies a finding as CONTRADICT, it is flagged in `keel status`
- It is never injected into an agent session until a human accepts or resolves it
- This is the primary guard against self-reinforcing errors

### Rule 5: Injection is a user-turn message, not a system prompt
- Proven by OpenDev research: user messages get higher recency position and compliance
- System prompt is used only for session-level context at `keel run` startup
- Per-write injection always goes as a user message

### Rule 6: All state lives in `.keel/` inside the repo
- `.keel/memory.db` — SQLite decision store
- `.keel/config.json` — API key reference, model choice, settings
- `.keel/hooks/` — installed git hook scripts
- Nothing leaves the local machine without explicit user action

### Rule 7: No magic defaults for confidence
- Confidence (LOW/MEDIUM/HIGH) comes from the LLM's own output in the extraction call
- keel does not infer or override confidence — it records what the extractor returns
- If extractor returns no confidence field → default to LOW, surface in `keel status`

### Rule 8: Module tags, not just file paths
- Every decision is tagged with the module it *governs*, not just the file it came from
- Extractor must be prompted to identify governed scope: `auth/` decision governs `auth/*` AND anything tagged `auth-dependent`
- This handles cross-module relevance without embeddings

### Rule 9: Soft decay via ranking, not deletion
- Decisions are never deleted automatically
- Ranking for injection: `recency_score × confidence_weight × reinforcement_count`
- Decisions not reinforced in 30+ commits naturally fall out of top-k
- Human can manually archive via `keel review`

### Rule 10: The spec is a view, not the source of truth
- `keel status` can render a human-readable SPEC.md from the memory store
- But SPEC.md is generated output, not input
- Source of truth is always `.keel/memory.db`

## Extraction Prompt Rules

The extraction prompt is load-bearing. These rules govern it:

1. Only identify decisions that are **clearly enacted** by the diff — not implied
2. Decisions are: data store choice, auth strategy, API boundary contract, module responsibility, dependency choice, error handling pattern
3. Decisions are NOT: variable names, formatting choices, minor refactors, test structure
4. Must classify: NEW (never seen before), REINFORCE (confirms existing), CONTRADICT (conflicts with existing)
5. Must return valid JSON or empty array `[]` — no prose
6. Schema: `[{ "decision": str, "module": str, "confidence": "LOW"|"MEDIUM"|"HIGH", "event": "NEW"|"REINFORCE"|"CONTRADICT" }]`

## Injection Prompt Rules

1. Show only top-k decisions for the specific files being touched (k=5 on MVP)
2. Format: numbered list, one line each — no prose padding
3. Preamble: `"The following architectural decisions govern this module. Do not contradict unless explicitly instructed to change them:"`
4. Never inject CONTRADICT or LOW confidence decisions without human approval
5. Append at end of message, not beginning (recency position within the message)

## Code Style

- Functions do one thing
- Every function that calls the LLM is clearly named `extract_*` or `inject_*`
- Database schema migrations are versioned in `schema/v{n}.sql`
- All git hook scripts are POSIX shell, not Python — maximum portability
- Hooks call into the keel Python CLI, they don't contain logic themselves

## What Stays Out Of MVP

- Vector embeddings / semantic search
- Team memory sync / shared decision stores
- Automatic SPEC.md generation
- Vibe mode (non-technical user onboarding)
- Web UI / dashboard
- Paid intelligence layer
- Multi-agent orchestration
