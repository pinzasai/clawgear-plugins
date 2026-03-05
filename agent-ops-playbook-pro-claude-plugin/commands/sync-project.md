---
description: Update a project's TASKS.md and MEMORY.md with a status update, then commit the changes via git
argument-hint: "<project-name> <status-update>"
---

# Sync Project

Applies a status update to a project's state files — marks tasks complete, adds new ones, logs decisions to MEMORY.md — and commits everything in one shot. This is the write half of the memory system. Run it every time you complete a unit of work, make a decision, or receive something worth remembering.

## Usage
```
/sync-project <project-name> <status-update>
```

### Arguments
- `project-name` — The project folder name under `projects/` (e.g., `my-saas`, `clawarmor`)
- `status-update` — Free-text description of what changed. Can include multiple items. Examples:
  - `"Completed: user auth flow. Decision: using JWTs not sessions. Next: build dashboard"`
  - `"Shipped PR #42. Blocked on: API rate limits from provider"`
  - `"Sub-agent finished research. Key finding: competitor uses edge functions"`

## Workflow

### 1. Load current project files

If ~~filesystem is connected:
- Read `projects/<project-name>/TASKS.md`
- Read `projects/<project-name>/MEMORY.md`
- Check last-modified timestamps of both files

If no tool connected:
> Paste the current contents of `projects/<project-name>/TASKS.md` and `projects/<project-name>/MEMORY.md`.

### 2. Parse the status-update

Extract structured items from the free-text status-update:

**Completion signals** → items to move to Done in TASKS.md
- Keywords: "completed", "done", "shipped", "merged", "finished", "closed", "resolved", "deployed"

**New task signals** → items to add to Active or Backlog in TASKS.md
- Keywords: "next:", "todo:", "need to", "backlog:", "will do", "queued:"

**Blocker signals** → items to flag in TASKS.md with [BLOCKED] tag
- Keywords: "blocked on", "blocked by", "waiting for", "depends on"

**Decision signals** → entries to add to MEMORY.md
- Keywords: "decided", "decision:", "chose", "going with", "switching to", "confirmed"

**Discovery signals** → entries to add to MEMORY.md
- Keywords: "key finding:", "learned:", "discovered:", "note:", "important:"

**Credential signals** → entries to add to MEMORY.md (reference only, never the actual value)
- Keywords: "token", "api key", "secret", "credential", "password"

### 3. Update TASKS.md

If ~~filesystem is connected:

For each completion item:
- Find the task in Active or In-Progress sections (fuzzy match on keywords)
- Move it to the Done section with format: `- [x] <task> — completed YYYY-MM-DD`
- If task not found in Active/In-Progress → add it directly to Done (it was done ad-hoc)

For each new task:
- If it looks like something needed soon → add to Active: `- [ ] <task>`
- If it's future work → add to Backlog: `- [ ] <task>`

For each blocker:
- Find the blocked task and append: ` [BLOCKED: <reason>]`
- Or add as new item: `- [ ] <task> [BLOCKED: <reason>]`

If no tool connected:
> Here are the exact edits to make to TASKS.md: [output diff-style changes]

### 4. Update MEMORY.md

If ~~filesystem is connected:

Append a new dated entry to `projects/<project-name>/MEMORY.md`:

```
## Update — YYYY-MM-DD

[For each decision item]
**Decision:** <decision text>

[For each discovery item]
**Finding:** <finding text>

[For each credential reference]
**Credential received:** <name/type only — e.g., "GitHub deploy token"> — stored in agent-accounts.json
```

Only add a MEMORY.md entry if there's at least one decision, discovery, or credential item. Pure task completions don't need a MEMORY.md entry.

If no tool connected:
> Here is the exact text to append to MEMORY.md: [output ready-to-paste block]

### 5. Commit the changes

If ~~git is connected:
- Stage the changed files: `projects/<project-name>/TASKS.md` and `projects/<project-name>/MEMORY.md`
- Commit with message: `sync(<project-name>): <one-line summary of status-update>`
- Push if a remote is configured

If ~~git not connected:
> Run this to commit manually:
> ```
> git add projects/<project-name>/TASKS.md projects/<project-name>/MEMORY.md
> git commit -m "sync(<project-name>): <summary>"
> ```

### 6. Update daily note

If ~~filesystem is connected:
- Append a timestamped entry to today's daily note (`memory/YYYY-MM-DD.md`):
  ```
  ### [HH:MM] Synced: <project-name>
  <status-update text>
  ```

## Output

Confirmation of what was written:

```
✅ Synced: <project-name> — YYYY-MM-DD HH:MM

TASKS.md changes:
  → Moved to Done: "<task 1>", "<task 2>"
  → Added to Active: "<task 3>"
  → Flagged blocked: "<task 4>"

MEMORY.md changes:
  → Added update entry with 1 decision, 1 finding

Git:
  → Committed: sync(<project-name>): <summary>
  → Pushed to origin/main ✓
```

If no changes were needed (nothing to update): say so explicitly rather than making a no-op commit.
