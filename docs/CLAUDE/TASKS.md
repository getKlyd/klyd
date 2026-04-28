# TASKS.md — Gated build tasks for keel

Each task has a gate. If the gate fails, do not proceed. Fix and re-run until it passes.
Tasks build on each other. A failed gate anywhere means all downstream tasks are blocked.

---

## TASK-01 · Project scaffold

**What:** Set up the Python project structure.

```
keel/
├── keel/
│   ├── __init__.py
│   ├── cli.py          # Click entrypoint
│   ├── hooks.py        # Hook install/uninstall logic
│   ├── db.py           # SQLite interface
│   ├── extractor.py    # LLM extraction call
│   ├── injector.py     # Injection formatting
│   └── config.py       # Config read/write
├── hooks/
│   ├── post-commit.sh  # POSIX shell, calls keel CLI
│   └── pre-commit.sh   # POSIX shell, calls keel CLI
├── schema/
│   └── v1.sql          # Initial DB schema
├── pyproject.toml
└── README.md
```

**Gate:** `python -m keel --help` runs without error and shows a help message.

---

## TASK-02 · `keel init` installs git hooks

**What:** Implement `keel init`. It must:
- Detect `.git/` in current directory (error if not a git repo)
- Copy `hooks/post-commit.sh` → `.git/hooks/post-commit` (chmod +x)
- Copy `hooks/pre-commit.sh` → `.git/hooks/pre-commit` (chmod +x)
- Create `.keel/` directory
- Write `.keel/config.json` with empty defaults
- Print confirmation

Hooks do nothing yet except `echo "keel: [hook-name] fired"`.

**Gate:**
1. Run `keel init` in a test git repo
2. Make a commit
3. See `keel: post-commit fired` in terminal output
4. Stage a file, see `keel: pre-commit fired`
5. Both fire on an aider commit (run aider, make it write one file)

---

## TASK-03 · SQLite schema + basic CRUD

**What:** Implement the memory store in `db.py`.

Schema (`schema/v1.sql`):
```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision TEXT NOT NULL,
    module TEXT NOT NULL,
    file_patterns TEXT NOT NULL,      -- comma-separated glob patterns
    confidence TEXT NOT NULL,         -- LOW | MEDIUM | HIGH
    event_type TEXT NOT NULL,         -- NEW | REINFORCE | CONTRADICT
    reinforcement_count INTEGER DEFAULT 1,
    last_seen_commit TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    flagged INTEGER DEFAULT 0,        -- 1 = needs human review
    archived INTEGER DEFAULT 0        -- 1 = soft-deleted
);
```

Implement functions:
- `init_db(db_path)` — creates DB from schema if not exists
- `store_decision(db_path, decision_dict)` — insert row
- `get_decisions_for_files(db_path, file_list, top_k=5)` — return ranked results excluding flagged/archived
- `reinforce_decision(db_path, decision_id, commit_hash)` — increment count, update last_seen
- `flag_decision(db_path, decision_id)` — set flagged=1
- `archive_decision(db_path, decision_id)` — set archived=1

Ranking SQL: `ORDER BY (reinforcement_count * CASE confidence WHEN 'HIGH' THEN 3 WHEN 'MEDIUM' THEN 2 ELSE 1 END) DESC LIMIT ?`

**Gate:**
1. Insert 5 hardcoded decisions covering 3 different modules
2. Query for files in module A — get correct subset, correctly ranked
3. Query for files in module B — different correct subset returned
4. CONTRADICT-flagged decision does NOT appear in injection query results

---

## TASK-04 · `keel status` renders memory store

**What:** Implement `keel status` CLI command.

Output format:
```
keel status
───────────────────────────────────
DECISIONS (8 total, 1 flagged)

  auth/          JWT-only, no sessions          HIGH    ×14
  db/            Prisma ORM                     MEDIUM  ×7
  api/routes/    REST-only, no GraphQL           HIGH    ×3

⚠ NEEDS REVIEW (1)
  db/            Drizzle ORM [CONTRADICTS: Prisma ORM]   LOW
  → run `keel review` to resolve
───────────────────────────────────
```

**Gate:**
1. Insert 5 decisions manually (3 normal, 1 flagged CONTRADICT, 1 LOW confidence)
2. `keel status` output matches expected format
3. Flagged decisions appear in NEEDS REVIEW section
4. Archived decisions do NOT appear

---

## TASK-05 · BYOK config + extractor LLM call

**What:** Implement `keel config` and `extractor.py`.

- `keel config --api-key sk-...` → writes to `.keel/config.json`
- `keel config --model claude-sonnet-4-6` → writes model preference (default: claude-sonnet-4-6)
- `extract_decisions(diff, commit_message, existing_decisions, api_key, model)` → list of dicts or empty list

Extraction prompt (exact, do not improvise):
```
You are an architectural decision extractor for a software project.

You will receive a git diff, a commit message, and a list of previously recorded architectural decisions for the files touched in this diff.

Your job: identify zero or more architectural decisions that this commit clearly enacts.

Architectural decisions are: data store choice, auth strategy, API boundary contracts, module responsibility assignments, dependency/library choices, error handling patterns.

Rules:
- Only record if the diff explicitly introduces, changes, or contradicts a decision
- Do not guess. Do not infer. Only record what is clearly shown in the diff.
- If the commit is a style fix, test update, or minor refactor with no architectural significance: return []
- For each decision, classify as NEW (not seen before), REINFORCE (confirms an existing decision), or CONTRADICT (conflicts with an existing decision)
- Assign confidence: HIGH (unmistakable from diff), MEDIUM (clear but could have context), LOW (possible but uncertain)

Return ONLY valid JSON. No prose. No markdown. No explanation.
Schema: [{"decision": str, "module": str, "file_patterns": str, "confidence": "LOW"|"MEDIUM"|"HIGH", "event": "NEW"|"REINFORCE"|"CONTRADICT"}]
If no decisions: return []

EXISTING DECISIONS FOR TOUCHED FILES:
{existing_decisions}

COMMIT MESSAGE:
{commit_message}

DIFF:
{diff}
```

**Gate:**
1. Run extractor on a commit that clearly adds JWT auth → returns correct HIGH-confidence NEW decision
2. Run extractor on a CSS formatting commit → returns `[]`
3. Run extractor on a commit that adds a second ORM alongside existing one → returns CONTRADICT
4. Invalid API key → error is caught, logged to `.keel/errors.log`, hook exits 0 (never block commits)

---

## TASK-06 · Wire post-commit hook to extractor

**What:** Post-commit hook calls extractor and stores results.

Flow:
1. `post-commit.sh` calls `keel extract-commit`
2. `keel extract-commit`:
   - Gets diff: `git diff HEAD~1 HEAD`
   - Gets commit message: `git log -1 --format=%B`
   - Gets list of touched files
   - Queries existing decisions for touched files
   - Calls `extract_decisions()`
   - For each result:
     - NEW → `store_decision()`
     - REINFORCE → `reinforce_decision()` on matching existing decision
     - CONTRADICT → `store_decision()` with `flagged=True`
   - If API error → log to `.keel/errors.log`, exit silently

**Gate:**
1. Make a commit with clear JWT auth introduction → `keel status` shows new HIGH-confidence decision
2. Make a second commit that reinforces same decision → reinforcement_count increments
3. Make a commit that contradicts → flagged decision appears in NEEDS REVIEW in `keel status`
4. Intentionally break API key → commit completes normally, error in `.keel/errors.log`

---

## TASK-07 · Injection: pre-commit hook fires with decisions

**What:** Pre-commit hook retrieves relevant decisions and writes injection file.

Flow:
1. `pre-commit.sh` calls `keel prepare-injection`
2. `keel prepare-injection`:
   - Gets staged files: `git diff --cached --name-only`
   - Queries top-k decisions for those files (excludes flagged, LOW confidence unreviewed)
   - If decisions found: writes `.keel/injection.txt` with formatted message
   - If no decisions: writes empty `.keel/injection.txt`
3. `keel run aider` — before starting aider, reads `.keel/injection.txt` and prepends to initial system context or first user message

Injection format (exact):
```
[keel] Architectural decisions governing files in this session:

1. [auth/] JWT-only, no sessions. (HIGH confidence, confirmed 14 times)
2. [db/] Prisma ORM exclusively. (HIGH confidence, confirmed 7 times)
3. [api/] REST-only, no GraphQL endpoints. (HIGH confidence, confirmed 3 times)

Do not contradict these decisions unless the user explicitly instructs you to change them.
```

**Gate:**
1. Set up project with 3 stored HIGH-confidence decisions
2. Stage a file that touches all 3 modules
3. Check `.keel/injection.txt` — all 3 decisions present, correct format
4. Stage a file that touches only 1 module — only that module's decision present
5. Stage a file in a module with no decisions — injection file is empty, no errors

---

## TASK-08 · `keel review` interactive resolution

**What:** Implement `keel review` for human-in-the-loop conflict resolution.

For each flagged decision:
```
⚠ CONFLICT DETECTED
Module: db/
New:      "Drizzle ORM" (from commit abc1234)
Existing: "Prisma ORM" (HIGH confidence, ×7)

[a] Accept new decision (archive old)
[r] Reject new decision (keep old, discard this finding)
[e] Edit decision manually
[s] Skip for now
```

On accept: archive old decision, promote new one to MEDIUM confidence, unflag
On reject: archive new decision, unflag
On edit: open `$EDITOR` with decision text, save and store

**Gate:**
1. Plant a CONTRADICT decision in DB manually
2. `keel review` surfaces it correctly
3. Accept → old decision archived, new one active in `keel status`
4. Reject → new finding archived, old one unchanged
5. After resolution, `keel status` shows 0 items in NEEDS REVIEW

---

## TASK-09 · End-to-end test on a real project

**What:** Install keel on a real project (not a test fixture) and run a full cycle.

Use a small real project (a Python CLI or Node API you're building anyway).

Steps:
1. `keel init` + `keel config --api-key ...`
2. Make 5 commits with clear architectural decisions
3. `keel status` — verify correct decisions captured
4. Make a contradicting commit
5. `keel review` — resolve it
6. `keel run aider` — make aider do something that touches governed modules
7. Verify aider does not contradict injected decisions without being told to

**Gate:**
The agent demonstrably behaves differently (more architecturally consistent) with keel active than without. This is qualitative but real. If you can't tell the difference, the injection isn't working.

---

## TASK-10 · Package + README + release

**What:** Make keel installable by someone who wasn't in this conversation.

- `pyproject.toml` with correct entry point: `keel = keel.cli:main`
- `pip install keel-harness` (or whatever name is available on PyPI)
- README.md: 5-minute quickstart only. No theory. No architecture docs.
  ```
  # keel
  install → keel init → keel config --api-key sk-... → keel run aider
  ```
- GitHub repo: MIT license, open issues enabled
- `.keel/` added to `.gitignore` template (don't commit the memory store)

**Gate:**
Fresh machine, fresh virtual env. `pip install keel-harness`, `keel init`, `keel config`, `keel run aider` — works in under 5 minutes. Decisions populate after 3 commits. `keel status` shows correct state.
