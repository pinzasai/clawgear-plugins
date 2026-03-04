---
description: Detect memory drift by comparing daily notes against project TASKS.md and MEMORY.md, then produce a sync report with exact updates needed
argument-hint: "[project-name]"
---

# Memory Audit

Catches the gap between what your agent actually did and what got written down. Reads today's and yesterday's daily notes, cross-references them against the project's TASKS.md and MEMORY.md, and produces a sync report with the exact line-level updates needed. Run this whenever you suspect a project's state files are stale — or as a daily habit before starting work.

## Usage
```
/memory-audit [project-name]
```

### Arguments
- `project-name` — Optional. Name of the project folder under `projects/`. If omitted, audits all projects found in `projects/index.json`.

## Workflow

### 1. Locate the workspace root

If ~~filesystem is connected:
- Look for `AGENTS.md` or `projects/index.json` to identify the workspace root
- Default to current working directory if not found

If no tool connected:
> Provide the path to your workspace root or paste the contents of `projects/index.json` manually.

### 2. Load daily notes

If ~~filesystem is connected:
- Read `memory/YYYY-MM-DD.md` (today)
- Read `memory/YYYY-MM-DD.md` (yesterday)
- Concatenate both into the audit window

If no tool connected:
> Paste the contents of today's and yesterday's daily note files. They live at `memory/YYYY-MM-DD.md`.

### 3. Load project state files

If project-name is provided:
- Read `projects/<project-name>/TASKS.md`
- Read `projects/<project-name>/MEMORY.md`

If project-name is omitted and ~~filesystem is connected:
- Read `projects/index.json`
- Load TASKS.md and MEMORY.md for every project listed

If no tool connected:
> Paste the contents of `projects/<project-name>/TASKS.md` and `projects/<project-name>/MEMORY.md`.

### 4. Scan daily notes for project activity

For each project in scope, scan the daily note content for:
- Task completion signals: "done", "finished", "shipped", "merged", "deployed", "completed", "resolved"
- Decision signals: "decided", "chose", "switching to", "going with", "confirmed"
- Credential/token signals: "token", "API key", "secret", "password", "credential"
- New task signals: "need to", "TODO", "backlog", "next step", "will do", "blocked by"
- Sub-agent result signals: "sub-agent returned", "agent completed", "result:", "output:"

Flag every match with the originating line from the daily note.

### 5. Cross-reference against TASKS.md

For each flagged completion from the daily notes:
- Check if the corresponding task appears in the Done section of TASKS.md with today's or yesterday's date
- If NOT found → mark as **drift item: task completed but not recorded**

For each flagged new task:
- Check if it appears anywhere in TASKS.md (Active, In-Progress, Backlog)
- If NOT found → mark as **drift item: task identified but not tracked**

### 6. Cross-reference against MEMORY.md

For each flagged decision:
- Check if it appears in MEMORY.md with a date stamp
- If NOT found → mark as **drift item: decision made but not recorded**

For each flagged credential/token:
- Verify a dated reference exists in MEMORY.md (actual value should NOT be in memory — just a reference)
- If no reference → mark as **critical drift: credential received but not logged**

### 7. Generate sync report

Produce a structured report in this format:

```
## Memory Audit Report — <project-name> — YYYY-MM-DD

### Drift Score: X items out of sync

### Critical (fix now)
- [ ] MEMORY.md: Add credential reference — "NPM token received on YYYY-MM-DD, stored in agent-accounts.json"

### Tasks to update in TASKS.md
- [ ] Move to Done: "Implement login flow" (completed per daily note YYYY-MM-DD)
- [ ] Add to Active: "Fix redirect bug after OAuth" (identified in daily note YYYY-MM-DD)

### Decisions to log in MEMORY.md
- [ ] Add entry: "Decided to use Postgres over SQLite for multi-user support (YYYY-MM-DD)"

### Already synced ✓
- Task "Set up CI pipeline" — found in Done with correct date
- Decision "Use Vercel for hosting" — found in MEMORY.md

### Proposed TASKS.md patch
[Exact text to add/move, ready to copy-paste]

### Proposed MEMORY.md patch
[Exact dated entry to append, ready to copy-paste]
```

## Output

A drift report showing:
- How many items are out of sync (the drift score)
- Exact copy-paste patches for TASKS.md and MEMORY.md
- Critical items flagged separately (credentials, decisions, blocking tasks)

If drift score is 0: confirm the project files are current and show last-updated timestamps.

Run `/sync-project` to apply the patches automatically.
