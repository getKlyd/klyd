# PROMPTING_TEMPLATE.md — Resume keel development fast

Copy the relevant block. Do not paste the whole file.

---

## BLOCK A · Starting a new task

```
I'm building keel — a decision memory harness for terminal coding agents (aider, opencode).

Core mechanic: git hooks intercept commits → LLM extracts architectural decisions → stored in local SQLite → injected as user-turn messages before file writes.

Stack: Python, Click CLI, SQLite (no ORM), POSIX shell hooks, BYOK (Anthropic API).

I'm on TASK-[N]: [paste task title and What section from TASKS.md]

Gate I need to pass: [paste gate from that task]

[paste any relevant existing code if the task builds on prior work]

Let's build it.
```

---

## BLOCK B · Debugging a failing gate

```
I'm building keel. Working on TASK-[N].

Gate is failing. Here's what's happening:

Expected: [what the gate says should happen]
Actual: [what is actually happening]

Relevant code:
[paste the specific file/function that's failing — not the whole project]

Error output:
[paste error]

Fix only the failing behavior. Don't refactor anything else.
```

---

## BLOCK C · Resuming after a break (no context)

```
I'm building keel — a git-hook-based architectural decision memory layer for aider/opencode.

State:
- Completed tasks: TASK-01 through TASK-[N]
- Current task: TASK-[N+1]: [title]
- All gates up to TASK-[N] are passing

Key files:
- keel/db.py — SQLite interface (decisions table, store/get/reinforce/flag/archive)
- keel/extractor.py — LLM extraction call
- keel/injector.py — injection formatting
- keel/cli.py — Click CLI (init, config, status, review, run, extract-commit, prepare-injection)
- hooks/post-commit.sh — calls `keel extract-commit`
- hooks/pre-commit.sh — calls `keel prepare-injection`

[paste current task's What + Gate from TASKS.md]

[paste any specific file content that's directly relevant]
```

---

## BLOCK D · Asking for a design decision

```
I'm building keel (decision memory harness for coding agents).

Constraint: [relevant rule from ENGINEERING_RULES.md — paste it]

I'm deciding between:
A) [option A]
B) [option B]

Which fits the constraints better and why? One paragraph, no fluff.
```

---

## Rules for using these blocks

- Never paste CONTEXT.md, ENGINEERING_RULES.md, or BUILDPLAN.md in full — too long, hurts attention
- Always paste the specific gate you're working toward
- Always paste the specific code that's failing, not the whole file
- One task at a time. Don't ask about TASK-05 while on TASK-03.
- If something is working, don't touch it. Paste only what's broken.
