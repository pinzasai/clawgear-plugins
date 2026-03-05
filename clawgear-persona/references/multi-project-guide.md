# Multi-Project Guide

Running multiple simultaneous projects, each in its own Telegram group, with full context isolation between them.

---

## The Setup

```
workspace/
├── projects/
│   ├── index.json           ← maps group IDs to project folders
│   ├── project-alpha/
│   │   ├── PROJECT.md       ← what this project is
│   │   ├── TASKS.md         ← active/done/backlog tasks
│   │   └── MEMORY.md        ← project-specific memory only
│   └── project-beta/
│       ├── PROJECT.md
│       ├── TASKS.md
│       └── MEMORY.md
```

---

## index.json Format

```json
{
  "groups": {
    "-1001234567890": {
      "project": "project-alpha",
      "folder": "projects/project-alpha",
      "label": "Project Alpha Team"
    },
    "-1009876543210": {
      "project": "project-beta",
      "folder": "projects/project-beta",
      "label": "Project Beta Team"
    }
  }
}
```

How to find your Telegram group ID: Add @userinfobot to the group and message it. The group ID starts with `-100`.

---

## Session Startup in a Group

When a message arrives in a group channel, the agent:

1. Reads `projects/index.json`
2. Finds the group ID in the mapping
3. Loads `projects/[folder]/PROJECT.md`, `TASKS.md`, and `MEMORY.md`
4. Does NOT load global `MEMORY.md` (personal context — security boundary)
5. Stays on that project's scope for the entire session

---

## TASKS.md Format

```markdown
# [Project Name] — Tasks
_Last updated: YYYY-MM-DD_

## Active
- [ ] Task description (added YYYY-MM-DD)
- [ ] Another task

## In Progress
- [ ] Currently being worked on — started YYYY-MM-DD

## Done
- [x] Completed task (YYYY-MM-DD)
- [x] Another completed task (YYYY-MM-DD)

## Backlog
- [ ] Future idea, not yet prioritized
- [ ] Another future idea

## Blocked
- [ ] 🔐 Needs credential/approval from [person] before proceeding
```

---

## MEMORY.md Format

```markdown
# [Project Name] — Memory
_Last updated: YYYY-MM-DD_

## What This Project Is
[One paragraph: what it is, current phase, goal]

## Team
- [Name] — [role and what they own]

## Key Decisions
- YYYY-MM-DD: [Decision and why]
- YYYY-MM-DD: [Another decision]

## Credentials
- [Service]: stored in agent-accounts.json → accounts.[key]
  (Never store actual credential values here)

## Active Context
[What's happening right now — current blockers, recent changes, next milestone]

## Known Issues / Blockers
- [Issue with context]
```

---

## Write-Through Rules for Multi-Project

**In a group session:** Update that project's files before ending the session.

**In the main session (webchat/DM) doing project work:** Update THAT project's files, not just daily notes. Cross-project work in the main session still needs to write to the project files.

**After a sub-agent completes:** The spawning session reads the output and syncs to the relevant project's TASKS.md and MEMORY.md.

---

## Cross-Project Status Check

From the main session, check all projects at once:

```bash
for proj in project-alpha project-beta; do
  echo "=== $proj ===" 
  grep -E "^\- \[ \]" ~/.openclaw/workspace/projects/$proj/TASKS.md | head -5
done
```

---

## The Isolation Boundary

**Hard rules:**
- In a group session: load ONLY that project's files
- Never reference another project's details in a group session
- Never load global MEMORY.md in any shared context
- Credentials: only share in private, verified direct messages

**Why:** Other people are in those group chats. They don't need to see details from your other projects or your personal AI configuration.

---

## Adding a New Project

1. Create the folder: `mkdir -p projects/[name]`
2. Create `PROJECT.md`, `TASKS.md`, `MEMORY.md` from templates
3. Add the group ID to `index.json`
4. Commit: `git add -A && git commit -m "Add [project] project files"`

The agent will start loading it automatically on the next message from that group.
