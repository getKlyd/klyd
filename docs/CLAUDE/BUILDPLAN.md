# BUILDPLAN.md — How keel gets built

## Phase 0: Skeleton (no LLM, no memory)

Goal: prove the git hook interception works across aider and opencode before writing a single line of memory logic.

- `keel init` installs post-commit and pre-commit hooks into `.git/hooks/`
- Hooks fire and log to stdout: "keel: post-commit hook fired" / "keel: pre-write hook fired"
- `keel run aider` starts aider in a subprocess and confirms hooks fire on every commit
- Nothing stored. Nothing injected. Just proof the plumbing works.

**Gate: hooks fire reliably on aider commits and opencode commits. If not, nothing else matters.**

---

## Phase 1: Memory Store

Goal: store and retrieve decisions. No LLM yet — use hardcoded test decisions.

- Design and create `.keel/memory.db` SQLite schema
- `decisions` table: id, decision, module, file_patterns, confidence, event_type, reinforcement_count, last_seen_commit, created_at, archived
- Implement: `store_decision()`, `get_decisions_for_files()`, `reinforce_decision()`, `flag_contradict()`
- Implement: ranking query (recency × confidence × reinforcement_count → top-k)
- `keel status` renders decisions in terminal: table view with confidence and event type
- Manual test: insert 5 hardcoded decisions, query for a file path, confirm correct top-k returned

**Gate: correct decisions returned for a given file path, ranked correctly, CONTRADICT ones excluded from injection query.**

---

## Phase 2: Extraction (LLM in the loop)

Goal: the post-commit hook calls the extractor LLM and stores the result.

- Wire BYOK: `keel config --api-key sk-...` stores key in `.keel/config.json`
- Implement `extract_decisions(diff, commit_message, existing_decisions)` → parsed JSON
- Extraction prompt finalized and hardened (see ENGINEERING_RULES.md)
- Post-commit hook: get diff (`git diff HEAD~1 HEAD`), get existing decisions for touched files, call extractor, store results
- CONTRADICT events → stored with `flagged=True`, surfaces in `keel status`
- Test: make 5 different commits with clear architectural decisions, verify correct extraction

**Gate: extractor correctly returns empty on ambiguous commits, correctly identifies NEW/REINFORCE/CONTRADICT on clear architectural commits. Zero false positives on pure formatting/style commits.**

---

## Phase 3: Injection (closing the loop)

Goal: relevant decisions injected as user message before agent write.

- Pre-commit hook: get list of files staged (`git diff --cached --name-only`), query top-k decisions for those paths
- Format injection message (see ENGINEERING_RULES.md injection format)
- Inject by writing to a temp file that `keel run` reads and prepends to the agent's next user turn
- `keel run aider` — confirm injected decisions appear in aider context before commit
- Test: set up a project with 3 stored decisions, make a change that touches governed modules, verify correct decisions injected

**Gate: injection appears in agent context. Agent demonstrably does not contradict an injected HIGH-confidence decision without explicit user override.**

---

## Phase 4: `keel review` (human-in-the-loop)

Goal: developer can manage the memory store without touching the database.

- `keel status` — shows: pending CONTRADICT decisions, LOW confidence decisions, decision count by module
- `keel review` — interactive prompt: shows each flagged decision, developer chooses accept / reject / edit
- `keel review --module auth/` — filter by module
- Accepted CONTRADICTs: resolve the conflict (old decision archived, new one promoted)
- Rejected findings: archived, not injected

**Gate: full cycle works — contradiction detected, surfaced in status, resolved via review, resolution reflected in next injection.**

---

## Phase 5: Hardening & Release

Goal: stable enough for other aider/opencode users to install and use.

- `pip install keel-harness` (package name TBD — `keel` may be taken)
- README with 5-minute quickstart: install → `keel init` → `keel config` → `keel run aider`
- Handle edge cases: empty repos, no commits yet, extractor API errors (fail silently, log to `.keel/errors.log`)
- MIT license, open source on GitHub
- Test on 3 different real projects: a Python CLI, a Node API, a React app

**Gate: a developer who has never seen keel can install it and have it running with aider in under 5 minutes. Decision memory populates after 3 commits. `keel status` shows correct state.**

---

## Future (Post-MVP, not in scope now)

- Semantic retrieval with embeddings (cross-module relevance without module tags)
- Vibe mode: non-technical user onboarding with plain-English interview
- Team memory sync: shared `.keel/` store for multi-developer repos
- Auto-generated SPEC.md view from memory store
- Paid intelligence layer: drift scoring, pattern analysis across projects
- `keel run opencode` native integration (opencode has an extension API)
