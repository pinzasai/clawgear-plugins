# Memory Architecture — Deep Dive

The three-layer memory system explained in detail, with implementation patterns, maintenance cycles, and multi-project isolation.

---

## Why Three Layers

A single MEMORY.md file that grows indefinitely has two failure modes:
1. **Too small** — critical info gets overwritten or lost
2. **Too large** — burns tokens on every load, buries the signal in noise

Three layers solve this by giving each type of information a home:

| Layer | Size target | Update frequency | Loaded when |
|-------|------------|-----------------|-------------|
| MEMORY.md | < 200 lines | Every few days | Private sessions |
| memory/YYYY-MM-DD.md | Unlimited | Every session | Today + yesterday |
| heartbeat-state.json | < 20 lines | Every heartbeat | Every heartbeat |

---

## Layer 1: MEMORY.md (Curated Long-Term)

**What goes here:**
- Who the user is (name, timezone, communication style)
- Active projects and their current phase
- Key decisions and why they were made
- Credential references (location, not values)
- Lessons learned that apply cross-project
- Tool/environment facts (model names, binary paths, known issues)

**What stays out:**
- Project-specific task lists → project TASKS.md
- Day-to-day session logs → daily notes
- Temporary state → heartbeat-state.json
- Raw credential values → never in any file loaded into context

**Maintenance cycle:**
- Add to it any time you learn something worth keeping (same-turn write-through)
- Prune it weekly — remove info that's now in project files or no longer relevant
- Keep it under 200 lines; if it grows past that, something should be in project files instead

**Security:** Only load MEMORY.md in private, verified sessions (direct DM with the user). Never in group chats, Discord servers, or sessions others can see. It contains personal context.

---

## Layer 2: Daily Notes (Raw Session Log)

**Format:** `memory/YYYY-MM-DD.md`

**What goes here:** Everything that happened today. Raw. Unfiltered. Don't curate — just log.

```markdown
# 2025-01-15

## Session 1 (9:00 AM)
- Deployed v2.3.1. Migration ran clean.
- Client meeting moved to Wednesday.

## Sub-agent: feature-builder
- Built auth endpoint. 3 tests passing, 1 failing (timeout).
- Output: /tmp/feature-builder-output.md

## Decisions
- Chose Postgres. Needs concurrent writes.

## Tomorrow
- Check Safari fix in production logs
```

**When to read:** Today + yesterday at session start. That's your immediate context.

**When to stop reading:** Anything older than 2 days is noise for daily work. If you need to reconstruct older history, read specific dates — don't load the whole archive.

**Archival:** Daily notes don't need to be deleted. After 30 days, they're effectively archived — you won't read them unless debugging a specific past incident.

---

## Layer 3: heartbeat-state.json (Operational State)

Prevents wasted work and duplicate checks.

```json
{
  "lastChecks": {
    "email": "2025-01-15T14:00:00Z",
    "calendar": "2025-01-15T12:00:00Z",
    "weather": null,
    "nightlyAudit": "2025-01-15T00:00:00Z"
  },
  "runningTasks": {
    "feature-builder": {
      "startedAt": "2025-01-15T13:30:00Z",
      "tmuxSession": "feature-builder",
      "description": "Building auth endpoint"
    }
  }
}
```

Update timestamps after each check. Read before checking — if less than 10 minutes since last check, skip it.

---

## Multi-Project Isolation

When running multiple simultaneous projects (each in its own group/channel):

### The Isolation Principle

Each project has its own memory. Context doesn't bleed between projects. A session in the "Project Alpha" group only loads Project Alpha's files.

```
projects/
  index.json                        ← group → project mapping
  project-alpha/
    PROJECT.md                      ← mission, goals, current phase
    TASKS.md                        ← task list (source of truth)
    MEMORY.md                       ← project-specific memory ONLY
  project-beta/
    PROJECT.md
    TASKS.md
    MEMORY.md
```

### Startup in a Group Session

```
1. Read projects/index.json
2. Find your group/channel ID
3. Load that project's PROJECT.md, TASKS.md, MEMORY.md
4. DO NOT load global MEMORY.md
5. Stay on that project's scope
```

### Cross-Project Work in Main Session

When the main session (private DM) does work for a specific project, update THAT project's files — not just daily notes.

Example: Alberto and I discuss Comfy strategy in webchat → update `projects/comfy/MEMORY.md` with the decision, even though we're not in the Comfy group.

### The Staleness Check

When reading a project's TASKS.md at session start, cross-check against daily notes:

1. Scan today's and yesterday's daily notes for mentions of this project
2. If daily notes describe completed work that isn't in TASKS.md → files are stale
3. Fix TASKS.md before reporting status

This catches write-throughs that slipped through during previous sessions.

---

## Memory Sync Enforcement

Three layers of enforcement prevent drift:

### Layer 1: Real-Time (Primary)

The SYNC CHECK run mentally after every work block. This is the primary mechanism. See AGENTS.md.

### Layer 2: Heartbeat Validator (Secondary)

`scripts/memory-sync.sh` runs every heartbeat. It:
- Reads daily notes for each project
- Checks if mentioned projects have been updated today
- Exits 1 if drift detected (agent must fix before doing anything else)

```bash
bash scripts/memory-sync.sh
# Exit 0 = synced
# Exit 1 = drift → fix first
```

### Layer 3: Pre-Commit Hook (Safety Net)

Blocks git commits when project files are stale. Installed in `.git/hooks/pre-commit`.

```bash
#!/bin/bash
bash scripts/memory-sync.sh
```

If the nightly audit is finding most of the drift, the real-time system is broken. Debug the write-through discipline first.

---

## Troubleshooting Memory Issues

**"Agent doesn't remember decisions from last session"**
→ Write-through was skipped. Add SYNC CHECK discipline. Check if MEMORY.md or project files were actually updated.

**"Memory files are growing too large"**
→ MEMORY.md shouldn't hold project-specific state. Move it to project MEMORY.md files. Archive or summarize old daily notes.

**"Two sessions wrote conflicting state"**
→ Use git to see the conflict. The most recent meaningful update wins. Add a git commit after every significant work block to create checkpoints.

**"Nightly audit always finds drift"**
→ Real-time write-through is broken. The agent is treating the nightly audit as the primary write mechanism. Review and fix session discipline.

**"Agent loads wrong project in group chat"**
→ Check index.json mapping. Verify the group ID matches. Check that group session startup loads project files, not global MEMORY.md.
