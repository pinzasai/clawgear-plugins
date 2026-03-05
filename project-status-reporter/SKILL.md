---
name: project-status-reporter
description: Generate a cross-project status report by reading all project TASKS.md and MEMORY.md files, running the memory sync validator, and producing a concise summary of what's active, blocked, done recently, and what needs attention. Use when Alberto asks "what's the status of all projects", during heartbeats for a quick health check, or before planning sessions. Workspace: ~/.openclaw/workspace/projects/
---

# Project Status Reporter

Generate a concise cross-project status snapshot.

## Projects Index

All active projects live under `~/.openclaw/workspace/projects/`:
- `clawarmor/` — Security auditing tool for OpenClaw agents
- `comfy/` — ComfyUI Cloud marketing & growth
- `security-copywriter/` — Twitter/X content strategy for Alberto
- `best-coder-alive/` — Pending brief

Full project list: `~/.openclaw/workspace/projects/index.json`

## Status Report Workflow

### Step 1: Run memory sync validator
```bash
bash ~/.openclaw/workspace/scripts/memory-sync.sh
```
- Exit 0 = all synced → continue
- Exit 1 = drift detected → fix stale files first, then report

### Step 2: Read each project's TASKS.md
For each project directory, read `TASKS.md` and extract:
- **Active tasks** (unchecked `- [ ]`)
- **Blocked items** (anything marked 🔐 or flagged as waiting on external input)
- **Recently completed** (checked `- [x]` with recent dates)
- **Backlog** count (how many items queued)

### Step 3: Format the report

Use this template:
```
## 📊 Project Status — [DATE]

### 🛡️ ClawArmor
- Active: [list]
- Blocked/Waiting: [list or "none"]
- Done recently: [last 1-2 items]

### 🎨 Comfy
...

### ✍️ Security Copywriter
...

### 💻 Best Coder Alive
...

---
Memory sync: ✅ clean / ⚠️ [what was stale]
```

### Step 4: Surface blockers and next actions
After the summary, add:
- **Immediate actions I can take now** (no Alberto input needed)
- **Needs Alberto** (decisions, approvals, or info required)

## Quick Commands

```bash
# Check all TASKS.md at once
for proj in clawarmor comfy security-copywriter best-coder-alive; do
  echo "=== $proj ===" && grep -E "^\- \[[ x]\]" ~/.openclaw/workspace/projects/$proj/TASKS.md 2>/dev/null | head -10
done

# Check for recent done items (last 7 days)
grep -r "$(date -v-7d +%Y-%m-%d)\|$(date +%Y-%m-%d)" ~/.openclaw/workspace/projects/*/TASKS.md 2>/dev/null
```

## When to Use

- **Every heartbeat**: Quick check — any stale tasks? Any autonomous work I can start?
- **On demand**: When Alberto asks "what's the status?" or "what are we working on?"
- **Before planning sessions**: Full report with backlog review

## Report Tone

Keep it tight — 3-5 lines per project. Alberto reads this fast. Lead with blockers and wins, not a wall of status text.
