---
name: agent-ops-playbook-pro
description: Production operations playbook for AI agents running on OpenClaw. Covers session discipline, memory architecture with enforcement (validator script + pre-commit hooks), multi-project isolation, sub-agent spawning, cron vs heartbeat patterns, workspace organization, safety boundaries, group chat etiquette, and real failure post-mortems. Includes ready-to-use starter templates and a memory sync validator script. Use when setting up a new agent, debugging memory drift, designing multi-project workflows, or hardening agent operations. Upgrades the basics into a production system that doesn't lose state.
---

# Agent Ops Playbook Pro

The production guide for running AI agents that don't embarrass you, don't lose state, and actually get useful work done over time.

Everything here was learned from real failures — not theory. The post-mortems in Section 7 show exactly what broke and why.

See `references/` for deep dives:
- [templates.md](references/templates.md) — copy-paste starter files (AGENTS.md, SOUL.md, USER.md, HEARTBEAT.md)
- [memory-architecture.md](references/memory-architecture.md) — full memory system with multi-project isolation
- [failure-postmortems.md](references/failure-postmortems.md) — real incidents and what they taught us

---

## ⚡ 5-Minute Quick Start

Three files transform a generic chatbot into an agent that knows who it is:

```
workspace/
├── AGENTS.md     ← session startup protocol
├── SOUL.md       ← identity & personality
└── USER.md       ← who you're helping
```

Copy the starter templates from [references/templates.md](references/templates.md). Takes 5 minutes. Completely different experience from day one.

---

## 1. Session Discipline

Every session is a fresh start. The context window is finite. Bloat kills performance.

### Startup Protocol (mandatory)

```
1. Read SOUL.md — who you are
2. Read USER.md — who you're helping
3. Read memory/YYYY-MM-DD.md (today + yesterday)
4. If main session (private DM): Also read MEMORY.md
5. If group/project session: Read that project's TASKS.md + MEMORY.md
6. Assess what needs doing → act
```

Don't ask "what should I do?" Read your files. The answer is there.

### Context Window Management

- **Front-load critical reads** — before conversation history fills the window
- **Summarize, don't hoard** — extract what you need from large files, move on
- **Recognize degradation** — after 30+ exchanges, wrap up and start fresh

### Sub-Agent Decision

**Spawn when:** task is self-contained, needs parallel execution, or would bloat main session.

**Do it yourself when:** task needs back-and-forth with the user, or it's under 3 tool calls.

Give sub-agents everything they need upfront: file paths, credential locations, expected output format. They can't ask you mid-task.

---

## 2. Memory Architecture

Without memory, every session is your first day. The naive solution (one growing file) burns tokens and buries critical info. The production solution is three layers.

### Three-Layer System

| Layer | File | Purpose | Load when |
|-------|------|---------|-----------|
| Long-term | `MEMORY.md` | Curated knowledge, cross-project facts, lessons | Private sessions only |
| Daily | `memory/YYYY-MM-DD.md` | Raw session logs | Today + yesterday |
| Operational | `memory/heartbeat-state.json` | Check timestamps, prevents duplicate work | Every heartbeat |

**Read order = priority order.** Project files are authoritative. Daily notes are raw log. If they conflict, daily notes are wrong — fix them.

### The Write-Through Rule (Non-Negotiable)

Any session that changes project state MUST write to that project's TASKS.md and/or MEMORY.md **in that same turn.** Not later. Not at the nightly heartbeat. Now.

**Triggers:**
- Task completed → move to Done in TASKS.md with date
- Decision made → log in MEMORY.md with date
- Credential received → MEMORY.md immediately
- Direction change → MEMORY.md immediately

"Mental notes" don't survive session restarts. Files do. This rule exists because memory has gone out of sync multiple times without it. See [references/failure-postmortems.md](references/failure-postmortems.md).

### Sync Checkpoint

Run this mentally after every work block before replying:

```
SYNC CHECK:
- Did I change project state? → Update TASKS.md
- Did I learn something worth keeping? → Update MEMORY.md
- Did I receive credentials or tokens? → Update MEMORY.md NOW
- Sub-agent just returned? → Read output, sync to project files
```

If all four are "no" — skip it. If any is "yes" — write the files.

### Memory Sync Validator

The `scripts/memory-sync.sh` script is your enforcement layer. Run it every heartbeat.

```bash
bash scripts/memory-sync.sh
# Exit 0 = all synced
# Exit 1 = drift detected → fix before anything else
```

See the full script in [scripts/memory-sync.sh](scripts/memory-sync.sh). Install the pre-commit hook so commits fail when project files are stale.

### Multi-Project Isolation

When running multiple projects (each in its own Telegram group or channel):

```
projects/
  index.json                  ← maps group IDs to project folders
  project-alpha/
    PROJECT.md                ← what it is, goals, status
    TASKS.md                  ← active/in-progress/done
    MEMORY.md                 ← project-specific memory only
  project-beta/
    PROJECT.md
    TASKS.md
    MEMORY.md
```

**Rules:**
- Each project's MEMORY.md contains ONLY that project's context
- Global MEMORY.md stays personal — do NOT load it in group/shared sessions (security)
- In a group session: load that project's files only — don't bleed context across projects

**index.json format:**
```json
{
  "groups": {
    "-1001234567890": {"project": "project-alpha", "folder": "projects/project-alpha"},
    "-1009876543210": {"project": "project-beta", "folder": "projects/project-beta"}
  }
}
```

---

## 3. Heartbeat & Cron Patterns

Agents that only respond when spoken to are assistants. Agents that monitor and act proactively are operators.

### Heartbeats

A periodic poll — system pings you, you decide what to do.

**When to use:** multiple checks batch together, timing can drift slightly, you need conversation context.

**HEARTBEAT.md structure:**
```markdown
# HEARTBEAT.md

## Always (every heartbeat)
Run: bash scripts/memory-sync.sh
- Exit 1 = DRIFT — fix before anything else

## Task Queue
Read TASKS.md. Execute any non-blocked items autonomously.

## Periodic Checks (rotate, 2-4x/day)
- Email — urgent unread messages?
- Calendar — events in next 2 hours?
- Project status — anything blocked or failing?

## Nightly (9pm-midnight, once)
Deep memory audit: read all today's notes, update all project files, commit workspace.
```

**State tracking** (prevents re-checking within 10 minutes):
```json
{
  "lastChecks": {
    "email": "2025-01-15T14:00:00Z",
    "calendar": "2025-01-15T12:00:00Z",
    "nightlyAudit": "2025-01-15T00:00:00Z"
  }
}
```

**Reach out when:** urgent email, event < 2 hours, score drop, failed build.
**Stay quiet when:** late night (11pm-8am), nothing new, checked < 30 min ago.

### Cron Jobs

Scheduled tasks at exact times, in isolated sessions.

**When to use:** exact timing matters, task needs isolation, one-shot reminders.

**Correct format:**
```bash
openclaw cron add "task-name" --schedule "0 7 * * *" \
  --channel telegram --to "CHAT_ID" \
  --prompt "Your task prompt here"
```

⚠️ Use `--channel telegram --to "ID"` (separate flags), NOT `--channel "telegram:ID"` (combined string — delivery fails).

### The Batching Principle

Don't create 5 cron jobs for 5 periodic checks. One heartbeat with rotating checks is cheaper and simpler. Use cron only for exact-time or isolated tasks.

---

## 4. Workspace Organization

```
workspace/
├── AGENTS.md            ← session startup protocol
├── SOUL.md              ← identity & personality
├── USER.md              ← user preferences
├── MEMORY.md            ← long-term curated memory (private only)
├── TOOLS.md             ← environment-specific notes (SSH, devices, etc.)
├── HEARTBEAT.md         ← proactive check list
├── memory/
│   ├── YYYY-MM-DD.md    ← daily session logs
│   └── heartbeat-state.json
├── projects/
│   ├── index.json
│   └── <project-name>/
│       ├── PROJECT.md
│       ├── TASKS.md
│       └── MEMORY.md
├── skills/              ← installed skill packages
└── scripts/
    └── memory-sync.sh   ← memory drift validator
```

### Quick Decision Test

1. Secret or credential? → `credentials/` (chmod 600)
2. Today's event/note? → `memory/YYYY-MM-DD.md`
3. Lasting lesson? → `MEMORY.md`
4. Project state? → `projects/<name>/TASKS.md` or `MEMORY.md`
5. Device/tool/SSH note? → `TOOLS.md`

---

## 5. Safety & Permissions

### The Internal vs External Line

**Do freely:** Read files, search web, organize notes, check status, run read-only commands.

**Ask first:** Send emails/messages, make purchases, delete data, post publicly, run destructive commands.

Rule: **if it changes something in the world that can't be undone, ask first.**

```
trash > rm    ← recoverable beats gone forever
```

### Credential Handling

- Never log credentials in plain text
- Never share credentials in group/shared sessions — only in private, verified channels
- Store in a dedicated file with `chmod 600`
- Reference by location ("using the key from agent-accounts.json") — never repeat the actual value

### Group Chat Security

You have access to your user's private information. In group sessions:
- Do NOT load global MEMORY.md — it contains personal context
- Do NOT share private info, credentials, or personal details
- Load only that project's files

---

## 6. Communication Patterns

### Know When to Speak

In group chats, humans don't respond to every message. Neither should you.

**Respond when:** directly mentioned, can add genuine value, correcting misinformation.
**Stay silent when:** casual banter, someone already answered, your response would just be "yeah."

### The ACK → Plan → ETA → Execute → Report Pattern

When given a task:
1. **ACK** — confirm receipt immediately
2. **Plan** — what you'll do, in what order
3. **ETA** — honest estimate; "needs X turns" if multi-step
4. **Execute** — do the actual work in the same turn
5. **Report** — results in the same channel, don't wait to be asked

Never say "on it" and go silent. If you ACK, you deliver in the same turn or you report why you can't.

### Platform Formatting

| Platform | Rules |
|----------|-------|
| Discord | No markdown tables. Wrap URLs in `<>` to suppress embeds. |
| WhatsApp | No headers. Use **bold** or CAPS. Keep it short. |
| Telegram | Full markdown works. Tables OK. |

---

## 7. Failure Post-Mortems

These are real incidents. Each one caused a different failure mode and spawned a different rule.

Read [references/failure-postmortems.md](references/failure-postmortems.md) for the full post-mortems.

**Summary of failures:**

| Incident | Root Cause | Rule Created |
|----------|-----------|--------------|
| Credentials lost after session | Write-through skipped | Write to MEMORY.md same turn, always |
| Total exec lockout (1 hour) | `exec.host: node` with no paired nodes | Never set exec host to `node` without a paired node |
| Provider account shutdown | Single-provider dependency | Don't depend on one provider for critical infrastructure |
| Memory drift across 3 projects | Nightly heartbeat was primary write mechanism | Write-through is primary; nightly is safety net only |

---

## Quick Reference

```
SESSION START           SYNC CHECK (after work)    SPEAK IN GROUPS?
1. SOUL.md              State changed? → TASKS.md  Mentioned? → Yes
2. USER.md              Learned something? → MEM   Add value? → Yes
3. Today + yesterday    Got credentials? → MEM NOW  Banter? → Silent
4. Project files        Sub-agent done? → Sync      Already answered? → Silent
5. Act

MEMORY RULE: Want to remember it? Write it to a file. Now. Not later. Now.
SAFETY RULE: Changes the world? Ask first. trash > rm. Always.
```
