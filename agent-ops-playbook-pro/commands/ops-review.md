---
description: Full agent ops health check covering memory sync status, task queue backlog, sub-agent results, security posture, and proposed next actions
argument-hint: "[scope]"
---

# Ops Review

A structured health check for your agent operation. Covers everything that can go wrong in a production agent setup — stale memory, forgotten tasks, pending sub-agent results, security risks, and communication gaps. Run daily for a quick pulse, weekly for a full audit.

## Usage
```
/ops-review [scope]
```

### Arguments
- `scope` — Optional. One of:
  - `daily` — Quick check: memory sync status, top 3 active tasks, any blocking issues (default)
  - `weekly` — Medium check: all active projects, task velocity, memory health, any recurring failures
  - `full` — Complete audit: everything in weekly + security posture, sub-agent history, communication review, proposed system changes

## Workflow

### 1. Load workspace state

If ~~filesystem is connected:
- Read `projects/index.json` to get all active projects
- For each project: read TASKS.md and MEMORY.md
- Read today's and yesterday's daily notes
- Read `memory/heartbeat-state.json`

If no tool connected:
> Provide the contents of `projects/index.json`, each project's TASKS.md and MEMORY.md, and today's daily note. Or paste the most relevant project files.

### 2. Memory sync check (all scopes)

For each active project:
- Check TASKS.md last-modified date — is it current? (same day or yesterday)
- Check MEMORY.md last-modified date — when was the last entry?
- Quick-scan daily notes for project mentions with no corresponding TASKS.md update

Output per project:
```
[project-name]  TASKS.md: ✅ current | ⚠️ 2 days stale | 🔴 5+ days stale
                MEMORY.md: ✅ current | ⚠️ stale
                Drift items: X found
```

### 3. Task queue backlog (all scopes)

For each project in scope:

**daily scope:** Show only Active and In-Progress tasks
**weekly/full scope:** Show Active, In-Progress, and Backlog

Flag:
- Tasks with no activity for 3+ days → `[STALE]`
- Tasks marked `[BLOCKED]` → surface blocker explicitly
- Tasks marked In-Progress with no recent daily note mention → possibly abandoned, needs attention

### 4. Sub-agent results pending (daily + weekly + full)

If ~~filesystem is connected:
- Look for output files from sub-agents (common patterns: `output/`, `results/`, `*-output.md`, `*-results.txt`)
- Check if those results have been synced back to project TASKS.md/MEMORY.md
- Flag any unsynced results

If no tool connected:
> Check your workspace manually for any output files from sub-agents that haven't been integrated into project files.

### 5. Security posture check (weekly + full only)

Review the following (from memory files, not live system access):
- Were any credentials mentioned in daily notes? Are they referenced (not stored) in MEMORY.md?
- Are there any plain-text secrets in TASKS.md or daily notes? Flag them for removal.
- Was any external action (email, tweet, public post) taken without user approval? Note it.
- Are plugin sources all from trusted registries? (shopclawmart.com, clawhub.com)

### 6. Communication review (full scope only)

- When was the last close-the-loop message sent to the human?
- Are there completed tasks that were never reported back?
- Any group session work that the human might not know about?

### 7. Generate the ops report

**Daily format:**
```
## Ops Review — Daily — YYYY-MM-DD

### Memory Health
[project] TASKS.md ✅ | MEMORY.md ✅
[project] TASKS.md ⚠️ (2 days) | MEMORY.md ✅ → run /memory-audit project

### Active Work
- [project] Task X — in progress, last updated YYYY-MM-DD
- [project] Task Y — BLOCKED: waiting on API access

### Blockers / Flags
- [project] Task Z: stale for 4 days — still relevant?

### Proposed next actions
1. Run /memory-audit [project] to fix 3 drift items
2. Unblock Task Y — follow up on API access request
3. [Next most impactful action]
```

**Weekly format:** Adds task velocity (tasks completed this week), MEMORY.md growth check, recurring failure patterns from daily notes.

**Full format:** Adds security posture section, communication review, proposed system improvements (e.g., "consider moving X to heartbeat", "SOUL.md needs updating based on observed behavior").

### 8. Send to chat (optional, full scope)

If ~~chat is connected and scope is `full`:
- Send a condensed version (5–8 lines) of the ops report to the configured chat channel
- Format for the platform (Slack: plain text, no markdown tables)

If ~~chat not connected:
> To send this report to Slack/Telegram, connect ~~chat and re-run with `full` scope.

## Output

A structured ops report appropriate to the scope, ending with concrete proposed next actions ranked by impact. The goal is not just a status dump — it's a prioritized action list you can execute immediately.
