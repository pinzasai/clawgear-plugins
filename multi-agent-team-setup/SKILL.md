---
name: multi-agent-team-setup
version: 2.0.0
price: 44
description: Spin up a structured multi-agent OpenClaw org with CEO agent, specialist agents, inter-agent routing, and department memory. Turnkey system -- installed in under 30 minutes.
tags: [multi-agent, orchestration, team, autonomous, CEO]
---

# Multi-Agent Team Setup

**Turn the concept into a running org in 30 minutes.**

You watched the video. You understand the idea. CEO agent delegates to Engineering, Engineering spawns specialists, specialists complete tasks, outputs flow back up the chain. The whole thing runs autonomously.

This skill gives you every file, script, and pattern you need to make that real — today.

---

## ✅ First 30 Minutes — Do This Now

Skip the theory. Here's what you actually do:

```
[ ] Step 1: Copy file structure to workspace (5 min)
      mkdir -p CEO agents/engineering/output agents/distribution/output scripts
      cp templates from this skill into those directories

[ ] Step 2: Edit CEO/SOUL.md — set your business context (5 min)
      Replace the example org (Acme Software) with your own
      Update delegation rules to match your departments

[ ] Step 3: Customize department SOUL.md files (5 min)
      agents/engineering/SOUL.md — update stack + domain
      agents/distribution/SOUL.md — update channels + audience

[ ] Step 4: Run validate_setup.sh (2 min)
      bash scripts/validate_setup.sh
      Fix any ❌ before proceeding

[ ] Step 5: Spawn your first specialist (3 min)
      ./scripts/spawn_specialist.sh engineering "audit current codebase and list top 3 risks" output/audit.md

[ ] Step 6: Read output, consolidate (5 min)
      cat agents/engineering/output/audit.md
      ./scripts/consolidate_outputs.sh

[ ] Step 7: Set up CEO reporting cron (5 min)
      openclaw cron add --schedule "0 18 * * *" \
        --message "Run ./scripts/consolidate_outputs.sh. If any items need human attention, report to Telegram." \
        --channel telegram --to "YOUR_TELEGRAM_ID"
```

If validate_setup.sh passes and your first specialist output looks coherent, you're running a multi-agent org. Everything else in this skill is detail.

---

## Why Multi-Agent Beats Single-Agent

A single agent managing a complex org is a bottleneck. It context-switches constantly, loses depth on any single domain, and eventually starts making shallow decisions because it's carrying too much.

Multi-agent solves this with specialization:

| Problem | Single-Agent | Multi-Agent |
|---|---|---|
| Context depth | Shallow across all domains | Deep per role |
| Parallel work | Sequential only | True parallel execution |
| Memory isolation | Everything bleeds together | Per-department memory |
| Accountability | Fuzzy | Clear role ownership |
| Scaling | Hard wall | Add agents, not complexity |

**The real unlock:** department memory. Each specialist reads its department's memory on spawn, executes with full context, writes output, and the next specialist inherits that accumulated intelligence. The org gets smarter with every cycle.

---

## The Hierarchy Pattern

```
HUMAN (you)
    │
    ▼
CEO AGENT
    │  delegates tasks, synthesizes reports, pings human
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
ENGINEERING HEAD   DISTRIBUTION HEAD   [YOUR DEPT]
    │                  │
    ▼                  ▼
SPECIALISTS        SPECIALISTS
(spawned on-demand) (spawned on-demand)
```

**CEO agent** — persistent, always-on. Reads project state. Delegates. Synthesizes. Reports to you.

**Department heads** — semi-persistent. Each has its own SOUL.md, MEMORY.md, and output folder. Spawned by CEO for department-level work.

**Specialists** — ephemeral. Spawned by department heads for specific tasks. They execute, write output, terminate.

---

## The Spawn-Brief-Execute-Report Loop

This is the atomic unit of multi-agent work. Every delegation follows this pattern:

```
1. SPAWN     → CEO spawns dept head with full brief
2. BRIEF     → Dept head reads department MEMORY.md for context
3. EXECUTE   → Dept head spawns specialist(s) as needed
4. WRITE     → Specialist writes output to agents/<dept>/output/<task>.md
5. CONSOLIDATE → Dept head reads outputs, updates MEMORY.md
6. REPORT    → Dept head reports to CEO
7. UPDATE    → CEO updates CEO/MEMORY.md, pings human if needed
```

Every step writes to a file. Files are the communication layer. No step depends on another agent being "online" — it just reads the files.

---

## File Structure

Copy this exact structure to your workspace:

```
your-workspace/
├── CEO/
│   ├── SOUL.md            ← CEO identity and delegation rules
│   ├── MEMORY.md          ← Cross-org state, active projects, decisions
│   └── TASKS.md           ← CEO-level task queue
├── agents/
│   ├── TASKS.md           ← Cross-department task tracker
│   ├── engineering/
│   │   ├── SOUL.md        ← Engineering head identity
│   │   ├── MEMORY.md      ← Engineering department context
│   │   └── output/        ← Specialist outputs land here
│   ├── distribution/
│   │   ├── SOUL.md        ← Distribution head identity
│   │   ├── MEMORY.md      ← Distribution department context
│   │   └── output/        ← Specialist outputs land here
│   └── [your-dept]/
│       ├── SOUL.md
│       ├── MEMORY.md
│       └── output/
└── scripts/
    ├── spawn_specialist.sh
    ├── autonomous_meeting.sh
    ├── consolidate_outputs.sh
    └── validate_setup.sh
```

---

## File Templates

> **These are fully filled-in examples for Acme Software, a B2B SaaS company.**
> Adapt names, stack, and channels to your own org. The structure is the product.

---

### `CEO/SOUL.md`

```markdown
# CEO SOUL.md — Acme Software

You are the CEO agent for Acme Software, a B2B SaaS company building developer tooling.

## Your Job
You do not execute tasks. You delegate, synthesize, and report.

Every task that comes to you gets routed to the right department.
Every department output gets synthesized into org-level decisions.
Every significant decision gets reported to the human (Alex, CEO).

## Delegation Rules
- Code, infrastructure, integrations, debugging, architecture → agents/engineering/
- Content, SEO, social media, email campaigns, partnerships → agents/distribution/
- Cross-department decisions → resolve in CEO/MEMORY.md first, then decide
- Anything requiring human judgment → ping Alex immediately, don't guess

## Spawning Pattern
When delegating to a department head:
1. Read agents/TASKS.md — what's active, what's blocked
2. Read agents/<dept>/MEMORY.md — what context does this dept have
3. Construct a brief: current state + specific task + expected output format
4. Run: openclaw agent --message "$BRIEF" --json to get the department head response
5. Parse the reply and write output to agents/<dept>/output/<task-slug>.md
6. Read output, update CEO/MEMORY.md with key decisions
7. Report to Alex with: what was decided, why, proposed next action

## Report Format (to human)
**COMPLETED:** [what was done — 1 sentence]
**DECISION:** [key decision made, if any — 1 sentence]
**NEXT:** [what you recommend doing next — 1 sentence]
**NEED:** [what you need from Alex, if anything — or "Nothing, proceeding"]

## Memory Rules
- Read CEO/MEMORY.md at the start of every session
- Write every significant decision to CEO/MEMORY.md before reporting
- Never report to Alex something that isn't already written to memory

## What You Are Not
- You are not a specialist. Don't write code. Don't write copy. Delegate.
- You are not a bottleneck. Route fast. Trust your department heads.
- You are not a yes-machine. If a plan looks wrong, say so.
```

---

### `CEO/MEMORY.md`

```markdown
# CEO Memory — Acme Software

_Last updated: 2026-01-15_

## Active Projects
- **v2 API Launch** — targeting Q1 2026, owned by Engineering
- **Developer Blog** — weekly cadence, owned by Distribution
- **Beta Customer Onboarding** — 12 customers, cross-department

## Key Decisions (most recent first)
- 2026-01-15: Chose REST over GraphQL for v2 API. Reason: team familiarity + simpler client integration for beta customers.
- 2026-01-10: Shifted distribution focus to Dev.to + LinkedIn. Twitter engagement too low for B2B audience.
- 2026-01-05: Decided to delay mobile SDK to Q2 to keep v2 API timeline on track.

## Current Blockers
- Engineering blocked on OAuth implementation — needs decision on provider (Auth0 vs. self-hosted)
- Distribution waiting on Engineering for API docs before publishing v2 announcement post

## What Alex (Human) Is Watching
- v2 API launch date — locked at March 1
- Beta customer retention rate — currently 83%, target 90%
- Blog post publish rate — currently 1/week, target 2/week

## Org Health
- Engineering velocity: good — shipping weekly
- Distribution output: slow — needs more specialist spawns
- CEO reporting: daily digest at 6pm via cron
```

---

### `agents/engineering/SOUL.md`

```markdown
# Engineering Head SOUL.md — Acme Software

You are the Engineering Head for Acme Software.

## Your Domain
Everything technical: TypeScript/Node.js backend, PostgreSQL, REST API design, Docker/Railway deployment, GitHub CI/CD, integration debugging, architecture decisions.

## Your Job
You own the engineering backlog. When the CEO delegates an engineering task:
1. Read agents/engineering/MEMORY.md — full department context
2. Break the task into specialist sub-tasks if needed
3. For each sub-task, spawn a specialist using openclaw agent --message "$BRIEF" --json
4. Read specialist outputs from agents/engineering/output/
5. Synthesize into a department-level output
6. Update agents/engineering/MEMORY.md with what was built/decided
7. Report back to CEO

## What You Know
- Current stack: TypeScript + Node.js backend, React frontend, PostgreSQL on Railway
- Active work: v2 REST API (80% complete), auth module being refactored
- Last deploy: 2026-01-14, shipped user roles + permissions
- Known issues: rate limiting not yet implemented, N+1 query in /users/list endpoint

## Specialist Spawn Pattern
For any task requiring focused execution, spawn a specialist with:
- The specific task (narrow scope, single output)
- The relevant MEMORY.md context
- The output file path (agents/engineering/output/<task-slug>.md)
- A scope limit ("write working code only" / "keep under 400 words")

## Output Format (to CEO)
**BUILT/DECIDED:** [what engineering produced — 1 sentence]
**STATUS:** working | blocked | needs-review
**MEMORY UPDATED:** yes | no — [what was added if yes]
**ESCALATE:** [anything that needs CEO or Alex's attention, or "nothing"]
```

---

### `agents/engineering/MEMORY.md`

```markdown
# Engineering Department Memory — Acme Software

_Last updated: 2026-01-15_

## Current Codebase State
- **Main repo:** github.com/acme/acme-api (private)
- **Stack:** TypeScript, Node.js 20, Express, PostgreSQL 15, Prisma ORM
- **Deploy target:** Railway (prod) + Railway staging
- **Last deploy:** 2026-01-14 — shipped user roles + permissions (PR #47)
- **Current branch:** feature/v2-api (in progress)

## Active Work
| Task | Status | Notes |
|------|--------|-------|
| v2 REST API | 80% complete | Auth endpoints done, resource endpoints in progress |
| Auth module refactor | In progress | Moving from sessions to stateless JWT |
| Rate limiting | Not started | Blocked on decision: per-user vs per-IP |
| OAuth integration | Blocked | Need decision: Auth0 ($) vs. self-hosted Keycloak |

## Architecture Decisions
- **REST over GraphQL (2026-01-15):** Simpler for beta customers, team knows Express well
- **Prisma ORM (2026-01-03):** Chosen for type safety + migration tooling over raw SQL
- **Railway over Heroku (2025-12-01):** 60% cheaper at current scale, equivalent DX

## Known Issues / Technical Debt
- N+1 query in GET /users/list — impact: slow on orgs >100 users, fix: add includes to Prisma query
- No rate limiting — impact: DoS risk, fix: add express-rate-limit before public launch
- Hardcoded CORS origins in config.ts — fix: move to environment variable

## Integrations
| Integration | Status | Notes |
|-------------|--------|-------|
| Stripe | Active | Webhooks at /webhooks/stripe, test mode only |
| SendGrid | Active | Transactional email for auth flows |
| Sentry | Active | Error tracking, alerts go to #engineering-alerts |
| Auth0 | Evaluating | Decision needed before OAuth implementation |

## Recent Outputs
- 2026-01-14: User roles implementation — agents/engineering/output/user-roles-2026-01-14.md
- 2026-01-10: API v2 architecture review — agents/engineering/output/v2-arch-review.md

## What The Next Specialist Needs To Know
The v2 API uses a new route structure: /api/v2/<resource>. The old /api/v1 routes still work but are deprecated. All new work goes on the feature/v2-api branch. Don't touch anything in src/v1/ — it's frozen until deprecation notice goes out.
```

---

### `agents/distribution/SOUL.md`

```markdown
# Distribution Head SOUL.md — Acme Software

You are the Distribution Head for Acme Software.

## Your Domain
Everything that puts the product in front of developers: Dev.to articles, LinkedIn posts, SEO content, email newsletters, community engagement (Hacker News, Reddit /r/devops), partnership outreach.

## Your Job
You own the distribution backlog. When the CEO delegates a distribution task:
1. Read agents/distribution/MEMORY.md — full department context
2. Break the task into specialist sub-tasks
3. For each sub-task, run: openclaw agent --message "$BRIEF" --json and write output to agents/distribution/output/
4. Synthesize specialist outputs into a distribution-level result
5. Update agents/distribution/MEMORY.md with what was shipped/learned
6. Report back to CEO

## Audience
- **Primary:** Backend developers (Node.js, Python, Go) at 10-200 person companies
- **Voice:** Technical, direct, no marketing fluff. Show don't tell.
- **Avoid:** Buzzwords, vague benefits, enterprise-speak

## Specialist Spawn Pattern
Spawn narrow specialists:
- Content writer: "Write one Dev.to article intro about X for Node.js developers"
- SEO specialist: "Find 5 keywords for [topic] targeting developers, with search volume estimate"
- Email specialist: "Write subject line + preview text variants for [campaign name]"

Each specialist gets: task + audience context + brand voice notes + output path.

## Output Format (to CEO)
**SHIPPED/PLANNED:** [what distribution produced or queued — 1 sentence]
**CHANNEL:** [where it's going / what's live]
**MEMORY UPDATED:** yes | no — [what was added if yes]
**ESCALATE:** [anything needing CEO or Alex's attention, or "nothing"]
```

---

### `agents/distribution/MEMORY.md`

```markdown
# Distribution Department Memory — Acme Software

_Last updated: 2026-01-15_

## Active Channels
| Channel | Cadence | Last Post | Performance |
|---------|---------|-----------|-------------|
| Dev.to | Weekly | 2026-01-13 | Avg 800 views, 40 reactions |
| LinkedIn | 3x/week | 2026-01-15 | Avg 200 impressions, 12 clicks |
| Email newsletter | Bi-weekly | 2026-01-08 | 340 subscribers, 28% open rate |
| Hacker News | Ad hoc | 2025-12-20 | 1 Show HN, 47 points |

## Content That Worked
- "How we cut our API response time by 60%" — 2,100 Dev.to views (best ever)
- "5 Prisma mistakes we made so you don't have to" — 1,400 views, 89 reactions
- LinkedIn posts with code snippets: 3x engagement vs text-only

## Content That Flopped
- Generic "tips for Node.js developers" — 200 views, algorithm ignored it
- Promotional posts about features — near-zero engagement from devs

## Upcoming Content Queue
- [ ] "Building stateless auth with JWT in Express" (tied to v2 launch, needs Engineering sign-off)
- [ ] "Why we chose REST over GraphQL for our v2 API" (decision blog post, ready to write)
- [ ] Newsletter: v2 beta preview (needs product screenshots from Engineering)

## SEO Notes
- Target keywords: "node.js api best practices", "express typescript setup", "prisma orm tutorial"
- Domain authority: low — focus on long-tail keywords for now
- Best performing tag on Dev.to: #node + #typescript combo

## What The Next Specialist Needs To Know
Always write for developers first. No "streamline your workflow" language. Use real code examples when possible. The audience responds to honesty about tradeoffs — "here's why we chose X even though Y is more popular."
```

---

### `agents/TASKS.md`

```markdown
# Cross-Department Task Tracker — Acme Software

_Last updated: 2026-01-15_

## Active Tasks

| Task | Dept | Priority | Status | Due | Notes |
|------|------|----------|--------|-----|-------|
| OAuth provider decision | engineering | HIGH | Blocked | 2026-01-17 | Need CEO decision: Auth0 vs Keycloak |
| Fix N+1 query in /users/list | engineering | MED | Queued | 2026-01-20 | 3-hour fix |
| Write JWT auth blog post | distribution | HIGH | Queued | 2026-01-22 | Needs eng input on code examples |
| v2 API announcement draft | distribution | HIGH | Waiting | 2026-02-20 | Waiting on Engineering to finish docs |

## Blocked

| Task | Dept | Blocked By | Since |
|------|------|------------|-------|
| OAuth integration | engineering | Decision on Auth0 vs Keycloak | 2026-01-12 |
| v2 API announcement | distribution | Engineering API docs not ready | 2026-01-10 |

## Completed This Week

| Task | Dept | Completed | Output |
|------|------|-----------|--------|
| User roles + permissions | engineering | 2026-01-14 | agents/engineering/output/user-roles-2026-01-14.md |
| LinkedIn post: Prisma tips | distribution | 2026-01-13 | agents/distribution/output/linkedin-prisma-tips.md |

## Backlog

- [ ] Rate limiting implementation — engineering — before public launch
- [ ] Hacker News Show HN post — distribution — after v2 API launch
- [ ] Mobile SDK — engineering — Q2 2026, deprioritized
- [ ] SEO audit of docs site — distribution — low priority
```

---

## Scripts

### Script 1: `validate_setup.sh`

**Run this first.** Catches every common setup failure before it wastes your time.

```bash
#!/bin/bash
# validate_setup.sh — Run this after installation to verify everything is wired
# Usage: bash scripts/validate_setup.sh

set -euo pipefail

echo "🔍 Validating Multi-Agent Team Setup..."
echo ""

ERRORS=0

# Check OpenClaw CLI available
if ! command -v openclaw &>/dev/null; then
  echo "❌ openclaw CLI not found — install OpenClaw first"
  ERRORS=$((ERRORS+1))
else
  echo "✅ openclaw CLI found: $(openclaw --version 2>/dev/null || echo 'version unknown')"
fi

# Check required directories
for dir in CEO agents/engineering agents/distribution scripts; do
  if [ -d "$dir" ]; then
    echo "✅ $dir exists"
  else
    echo "❌ Missing directory: $dir — run: mkdir -p $dir"
    ERRORS=$((ERRORS+1))
  fi
done

# Check required files
for f in CEO/SOUL.md CEO/MEMORY.md agents/engineering/SOUL.md agents/engineering/MEMORY.md agents/distribution/SOUL.md agents/distribution/MEMORY.md agents/TASKS.md; do
  if [ -f "$f" ]; then
    echo "✅ $f exists"
  else
    echo "⚠️  Missing: $f — copy from skill templates"
    ERRORS=$((ERRORS+1))
  fi
done

# Check output directories exist
for dir in agents/engineering/output agents/distribution/output; do
  if [ -d "$dir" ]; then
    echo "✅ $dir exists"
  else
    echo "⚠️  Missing output dir: $dir — run: mkdir -p $dir"
    ERRORS=$((ERRORS+1))
  fi
done

# Check scripts are executable
for script in scripts/spawn_specialist.sh scripts/consolidate_outputs.sh scripts/validate_setup.sh; do
  if [ -f "$script" ]; then
    if [ -x "$script" ]; then
      echo "✅ $script is executable"
    else
      echo "⚠️  $script not executable — run: chmod +x scripts/*.sh"
      ERRORS=$((ERRORS+1))
    fi
  else
    echo "⚠️  Missing script: $script"
    ERRORS=$((ERRORS+1))
  fi
done

# Check for placeholder text that wasn't replaced
echo ""
echo "🔎 Checking for unfilled placeholders..."
PLACEHOLDER_FOUND=0
for f in CEO/SOUL.md agents/engineering/SOUL.md agents/distribution/SOUL.md; do
  if [ -f "$f" ] && grep -q "Acme Software" "$f" 2>/dev/null; then
    echo "⚠️  $f still contains example org name 'Acme Software' — update with your org"
    PLACEHOLDER_FOUND=$((PLACEHOLDER_FOUND+1))
  fi
done
if [ $PLACEHOLDER_FOUND -eq 0 ]; then
  echo "✅ No unfilled example placeholders found"
fi

# Test openclaw agent connectivity
echo ""
echo "🔌 Testing OpenClaw gateway connection..."
if openclaw agent --message "Reply with exactly: PING_OK" --json >/dev/null 2>&1; then
  echo "✅ Gateway responding — openclaw agent works"
else
  echo "❌ Gateway not responding — run: openclaw gateway start"
  ERRORS=$((ERRORS+1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ All checks passed. Your multi-agent org is ready."
  echo ""
  echo "Next step:"
  echo "  ./scripts/spawn_specialist.sh engineering 'list top 3 engineering priorities' agents/engineering/output/first-run.md"
else
  echo "❌ $ERRORS issue(s) found. Fix them before spawning agents."
  echo "   Most issues are quick — missing dirs and chmod are 30-second fixes."
fi

exit $ERRORS
```

---

### Script 2: `spawn_specialist.sh`

Spawns a specialist agent with full context injection. This is the core delegation mechanism.

```bash
#!/usr/bin/env bash
# spawn_specialist.sh
# Usage: ./scripts/spawn_specialist.sh <department> "<task description>" <output_file>
#
# Example:
#   ./scripts/spawn_specialist.sh engineering "Refactor auth module for stateless JWT" agents/engineering/output/auth-refactor.md

set -euo pipefail

DEPT="${1:?Usage: spawn_specialist.sh <department> '<task>' <output_file>}"
TASK="${2:?Provide a task description}"
OUTPUT_FILE="${3:?Provide an output file path}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

SOUL_FILE="$WORKSPACE_DIR/agents/$DEPT/SOUL.md"
MEMORY_FILE="$WORKSPACE_DIR/agents/$DEPT/MEMORY.md"
TASKS_FILE="$WORKSPACE_DIR/agents/TASKS.md"
OUTPUT_DIR="$WORKSPACE_DIR/agents/$DEPT/output"
FULL_OUTPUT="$WORKSPACE_DIR/$OUTPUT_FILE"

# Validate department exists
if [ ! -d "$WORKSPACE_DIR/agents/$DEPT" ]; then
  echo "ERROR: Department '$DEPT' not found at agents/$DEPT" >&2
  echo "Available departments:" >&2
  ls "$WORKSPACE_DIR/agents/" | grep -v "TASKS.md" >&2
  exit 1
fi

# Ensure output directories exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$FULL_OUTPUT")"

echo "=== Spawning $DEPT specialist ==="
echo "Task: $TASK"
echo "Output: $OUTPUT_FILE"
echo ""

# Build the full brief — all context injected here
FULL_BRIEF="You are a specialist in the $DEPT department.

## Your Identity and Role
$(cat "$SOUL_FILE" 2>/dev/null || echo "No SOUL.md found for $DEPT — operate as a focused $DEPT specialist.")

## Department Memory (read carefully — this is your accumulated context)
$(cat "$MEMORY_FILE" 2>/dev/null || echo "No MEMORY.md found — this may be a new department. Start fresh.")

## Active Cross-Department Tasks
$(cat "$TASKS_FILE" 2>/dev/null || echo "No cross-department task file found.")

## Your Specific Task
$TASK

## Output Requirements
- Be specific and actionable — no filler
- If you write code, include the complete, working code
- If you make a decision, state the decision AND the reasoning
- End your entire output with exactly one line starting with 'RESULT: ' summarizing what you produced
- If you cannot complete the task, write 'BLOCKED: [specific reason]' and stop

## Constraints
- Stay within your domain ($DEPT)
- Complete this task in a single pass
- Scope: narrow and deep, not broad and shallow"

echo "Spawning agent..."

# Capture output via openclaw agent --json
RAW_RESULT=$(openclaw agent \
  --message "$FULL_BRIEF" \
  --json 2>/dev/null) || RAW_RESULT=""

# Extract the reply field
REPLY=$(echo "$RAW_RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('reply', d.get('content', d.get('message', ''))))
except Exception:
    sys.exit(1)
" 2>/dev/null) || REPLY=""

if [ -z "$REPLY" ]; then
  echo "ERROR: No reply received from openclaw agent. Check that the gateway is running." >&2
  echo "Run: openclaw gateway status" >&2
  echo "Then retry this command." >&2
  exit 1
fi

# Write reply to output file with metadata header
{
  echo "# Specialist Output: $DEPT"
  echo "Task: $TASK"
  echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"
  echo "Output file: $OUTPUT_FILE"
  echo ""
  echo "---"
  echo ""
  echo "$REPLY"
} > "$FULL_OUTPUT"

echo ""
echo "=== Specialist completed ==="
echo "Output written to: $OUTPUT_FILE"
echo ""

# Show result summary
RESULT_LINE=$(grep "^RESULT:" "$FULL_OUTPUT" 2>/dev/null || echo "(No RESULT line — review full output)")
BLOCKED_LINE=$(grep "^BLOCKED:" "$FULL_OUTPUT" 2>/dev/null || true)

echo "--- Summary ---"
echo "$RESULT_LINE"

if [ -n "$BLOCKED_LINE" ]; then
  echo ""
  echo "⚠️  BLOCKED: $BLOCKED_LINE"
  echo "Update agents/$DEPT/MEMORY.md with the blocker before re-spawning."
  exit 2
fi

echo ""
echo "Run to update department memory:"
echo "  ./scripts/consolidate_outputs.sh --dept $DEPT"
```

---

### Script 3: `consolidate_outputs.sh`

Reads all department outputs, updates MEMORY.md with a structured session block, and generates a CEO digest.

```bash
#!/usr/bin/env bash
# consolidate_outputs.sh
# Usage: ./scripts/consolidate_outputs.sh [--dept <department>] [--digest-only]
#
# With no args: processes ALL departments and updates all MEMORY.md files
# With --dept: processes only that department
# With --digest-only: generates digest but does NOT write to MEMORY.md files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

DEPT_FILTER=""
DIGEST_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dept) DEPT_FILTER="$2"; shift 2 ;;
    --digest-only) DIGEST_ONLY=true; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

AGENTS_DIR="$WORKSPACE_DIR/agents"
SESSION_DATE=$(date '+%Y-%m-%d')
SESSION_TIME=$(date '+%Y-%m-%d %H:%M %Z')
DIGEST_FILE="$WORKSPACE_DIR/CEO/digest-$(date '+%Y-%m-%d-%H%M').md"

mkdir -p "$WORKSPACE_DIR/CEO"

echo "=== Consolidating outputs ==="
echo "Session: $SESSION_TIME"
[ -n "$DEPT_FILTER" ] && echo "Scope: $DEPT_FILTER only" || echo "Scope: all departments"
echo ""

{
  echo "# CEO Digest — $SESSION_TIME"
  echo ""
  echo "---"
  echo ""
} > "$DIGEST_FILE"

# Build department list
if [ -n "$DEPT_FILTER" ]; then
  DEPARTMENTS="$DEPT_FILTER"
else
  DEPARTMENTS=$(find "$AGENTS_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)
fi

TOTAL_TASKS=0
TOTAL_BLOCKED=0

for DEPT in $DEPARTMENTS; do
  OUTPUT_DIR="$AGENTS_DIR/$DEPT/output"
  MEMORY_FILE="$AGENTS_DIR/$DEPT/MEMORY.md"

  if [ ! -d "$OUTPUT_DIR" ]; then
    continue
  fi

  # Find output files from last 24 hours, fallback to all if none found
  RECENT_OUTPUTS=$(find "$OUTPUT_DIR" -name "*.md" -mtime -1 2>/dev/null | sort -r)
  if [ -z "$RECENT_OUTPUTS" ]; then
    RECENT_OUTPUTS=$(find "$OUTPUT_DIR" -name "*.md" 2>/dev/null | sort -r | head -5)
  fi

  if [ -z "$RECENT_OUTPUTS" ]; then
    echo "  [$DEPT] No outputs found — skipping"
    continue
  fi

  echo "  [$DEPT] Processing $(echo "$RECENT_OUTPUTS" | wc -l | tr -d ' ') output(s)..."

  # Collect task summaries
  COMPLETED_TASKS=""
  BLOCKED_TASKS=""
  KEY_DECISIONS=""

  while IFS= read -r OUTPUT_FILE; do
    FILENAME=$(basename "$OUTPUT_FILE")

    RESULT_LINE=$(grep "^RESULT:" "$OUTPUT_FILE" 2>/dev/null | head -1 || echo "RESULT: (no summary)")
    BLOCKED_LINE=$(grep "^BLOCKED:" "$OUTPUT_FILE" 2>/dev/null | head -1 || true)
    DECISION_LINE=$(grep -i "^DECISION\|^DECIDED\|^WE CHOSE\|^CHOOSING" "$OUTPUT_FILE" 2>/dev/null | head -1 || true)

    TASK_NAME=$(head -2 "$OUTPUT_FILE" | grep "^Task:" | sed 's/Task: //' || echo "$FILENAME")
    TASK_DATE=$(head -3 "$OUTPUT_FILE" | grep "^Date:" | sed 's/Date: //' || echo "$SESSION_DATE")

    COMPLETED_TASKS="$COMPLETED_TASKS\n- [$TASK_DATE] $TASK_NAME → $RESULT_LINE"
    TOTAL_TASKS=$((TOTAL_TASKS+1))

    if [ -n "$BLOCKED_LINE" ]; then
      BLOCKED_TASKS="$BLOCKED_TASKS\n- $TASK_NAME: $BLOCKED_LINE"
      TOTAL_BLOCKED=$((TOTAL_BLOCKED+1))
    fi

    if [ -n "$DECISION_LINE" ]; then
      KEY_DECISIONS="$KEY_DECISIONS\n- [$FILENAME] $DECISION_LINE"
    fi

  done <<< "$RECENT_OUTPUTS"

  # Write dept section to digest
  {
    echo "## Department: $DEPT"
    echo ""
    echo "### Tasks Completed"
    echo -e "$COMPLETED_TASKS"
    echo ""
    if [ -n "$KEY_DECISIONS" ]; then
      echo "### Key Decisions"
      echo -e "$KEY_DECISIONS"
      echo ""
    fi
    if [ -n "$BLOCKED_TASKS" ]; then
      echo "### ⚠️  Blocked"
      echo -e "$BLOCKED_TASKS"
      echo ""
    fi
    echo "---"
    echo ""
  } >> "$DIGEST_FILE"

  # Update department MEMORY.md with structured session block
  if [ "$DIGEST_ONLY" = false ] && [ -f "$MEMORY_FILE" ]; then
    SESSION_BLOCK="\n## Session $SESSION_DATE\n\n### Tasks Completed\n$(echo -e "$COMPLETED_TASKS")\n"

    if [ -n "$KEY_DECISIONS" ]; then
      SESSION_BLOCK="$SESSION_BLOCK\n### Decisions Made\n$(echo -e "$KEY_DECISIONS")\n"
    fi

    if [ -n "$BLOCKED_TASKS" ]; then
      SESSION_BLOCK="$SESSION_BLOCK\n### Blockers (resolve before next session)\n$(echo -e "$BLOCKED_TASKS")\n"
    fi

    SESSION_BLOCK="$SESSION_BLOCK\n### What The Next Specialist Needs To Know\nSee completed task outputs above. Review agents/$DEPT/output/ for full context.\n"

    # Append session block to MEMORY.md
    echo -e "$SESSION_BLOCK" >> "$MEMORY_FILE"
    echo "  [$DEPT] Updated MEMORY.md with session $SESSION_DATE"
  fi

done

# Write summary to digest
{
  echo "## Summary"
  echo ""
  echo "- Total tasks consolidated: $TOTAL_TASKS"
  echo "- Blocked items: $TOTAL_BLOCKED"
  [ "$DIGEST_ONLY" = true ] && echo "- MEMORY.md files: NOT updated (--digest-only mode)"
  echo ""
  echo "## CEO Action Items"
  echo ""
  echo "1. Review blocked items above and resolve or escalate"
  echo "2. Update CEO/MEMORY.md with any org-level decisions from this session"
  echo "3. Ping human (Alex) if any items need human judgment"
} >> "$DIGEST_FILE"

echo ""
echo "=== Consolidation complete ==="
echo "Digest: $DIGEST_FILE"
echo "Tasks: $TOTAL_TASKS | Blocked: $TOTAL_BLOCKED"
echo ""
cat "$DIGEST_FILE"
```

---

### Script 4: `autonomous_meeting.sh`

Runs a structured multi-agent debate. Engineering and Distribution each make their case. CEO synthesizes and outputs an actual decision — not just a transcript.

```bash
#!/usr/bin/env bash
# autonomous_meeting.sh
# Usage: ./scripts/autonomous_meeting.sh "<debate topic>" [output_file]
#
# Example:
#   ./scripts/autonomous_meeting.sh "Should we build REST or GraphQL for v2 API?" CEO/meetings/api-decision.md

set -euo pipefail

TOPIC="${1:?Usage: autonomous_meeting.sh '<debate topic>' [output_file]}"
TIMESTAMP=$(date '+%Y-%m-%d-%H%M')
OUTPUT="${2:-CEO/meetings/meeting-$TIMESTAMP.md}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
TRANSCRIPT="$WORKSPACE_DIR/$OUTPUT"

mkdir -p "$(dirname "$TRANSCRIPT")"

echo "=== Autonomous Meeting ==="
echo "Topic: $TOPIC"
echo "Transcript: $OUTPUT"
echo ""

# Initialize transcript
{
  echo "# Autonomous Meeting Transcript"
  echo "**Topic:** $TOPIC"
  echo "**Date:** $(date '+%Y-%m-%d %H:%M %Z')"
  echo ""
  echo "---"
  echo ""
} > "$TRANSCRIPT"

# --- Round 1: Engineering Position ---
echo "Round 1: Engineering position..."

ENG_MEMORY=$(cat "$WORKSPACE_DIR/agents/engineering/MEMORY.md" 2>/dev/null || echo "No engineering memory found.")
ENG_SOUL=$(cat "$WORKSPACE_DIR/agents/engineering/SOUL.md" 2>/dev/null || echo "You are the Engineering Head.")

ENG_BRIEF="$ENG_SOUL

You are participating in an executive meeting. The topic being debated is:
\"$TOPIC\"

Your engineering context:
$ENG_MEMORY

State your position as Engineering Head. Be specific — cite technical constraints, costs, timeline, and team capability. Don't hedge. 200-300 words.

Format your response EXACTLY as:
ENGINEERING POSITION:
[Your argument — cite specific technical facts from your memory]

ENGINEERING RECOMMENDATION: [One clear, specific recommendation]"

ENG_REPLY=$(openclaw agent \
  --message "$ENG_BRIEF" \
  --json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('reply', d.get('content', '')))
except:
    print('')
" 2>/dev/null) || ENG_REPLY=""

if [ -z "$ENG_REPLY" ]; then
  ENG_REPLY="ENGINEERING POSITION: Unable to get Engineering response — check gateway connection.
ENGINEERING RECOMMENDATION: Retry after running: openclaw gateway start"
fi

{
  echo "## Engineering Head"
  echo ""
  echo "$ENG_REPLY"
  echo ""
  echo "---"
  echo ""
} >> "$TRANSCRIPT"

echo "  Engineering position captured."

# --- Round 2: Distribution Position (reads engineering position) ---
echo "Round 2: Distribution position..."

DIST_MEMORY=$(cat "$WORKSPACE_DIR/agents/distribution/MEMORY.md" 2>/dev/null || echo "No distribution memory found.")
DIST_SOUL=$(cat "$WORKSPACE_DIR/agents/distribution/SOUL.md" 2>/dev/null || echo "You are the Distribution Head.")

DIST_BRIEF="$DIST_SOUL

You are participating in an executive meeting. The topic being debated is:
\"$TOPIC\"

The Engineering Head has already made their case. Here is the full transcript so far:
---
$(cat "$TRANSCRIPT")
---

Your distribution context:
$DIST_MEMORY

Now state your position as Distribution Head. Where do you agree? Where do you push back based on customer and market impact? 200-300 words.

Format your response EXACTLY as:
DISTRIBUTION POSITION:
[Your argument — cite specific channel data, customer impact, or market timing from your memory]

DISTRIBUTION RECOMMENDATION: [One clear, specific recommendation]"

DIST_REPLY=$(openclaw agent \
  --message "$DIST_BRIEF" \
  --json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('reply', d.get('content', '')))
except:
    print('')
" 2>/dev/null) || DIST_REPLY=""

if [ -z "$DIST_REPLY" ]; then
  DIST_REPLY="DISTRIBUTION POSITION: Unable to get Distribution response — check gateway connection.
DISTRIBUTION RECOMMENDATION: Retry after running: openclaw gateway start"
fi

{
  echo "## Distribution Head"
  echo ""
  echo "$DIST_REPLY"
  echo ""
  echo "---"
  echo ""
} >> "$TRANSCRIPT"

echo "  Distribution position captured."

# --- Round 3: CEO Synthesis → Decision ---
echo "Round 3: CEO synthesis and decision..."

CEO_MEMORY=$(cat "$WORKSPACE_DIR/CEO/MEMORY.md" 2>/dev/null || echo "No CEO memory found.")
CEO_SOUL=$(cat "$WORKSPACE_DIR/CEO/SOUL.md" 2>/dev/null || echo "You are the CEO.")

CEO_BRIEF="$CEO_SOUL

You just ran an executive meeting. Here is the full transcript:
---
$(cat "$TRANSCRIPT")
---

CEO org context:
$CEO_MEMORY

Your job now: synthesize the debate into a DECISION. Not a summary. A decision.

Format your response EXACTLY as:
SUMMARY:
[What was debated — 2-3 sentences max]

POINTS OF AGREEMENT:
[Bullet list of what both sides agreed on]

POINTS OF DISAGREEMENT:
[Bullet list of where they diverged and why]

DECISION:
[The actual decision you are making. Be specific. State what you're choosing AND what you're NOT choosing.]

REASONING:
[Why this decision — cite the strongest argument and what tipped the balance]

NEXT ACTION:
[The single first action to execute on this decision, with owner and timeline]

OPEN QUESTION FOR HUMAN:
[One question that needs human input before proceeding — or 'None, proceeding autonomously' if you can make the full call]"

CEO_REPLY=$(openclaw agent \
  --message "$CEO_BRIEF" \
  --json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('reply', d.get('content', '')))
except:
    print('')
" 2>/dev/null) || CEO_REPLY=""

if [ -z "$CEO_REPLY" ]; then
  CEO_REPLY="SUMMARY: CEO synthesis failed — gateway may be down.
DECISION: Unable to produce decision. Run 'openclaw gateway start' and retry.
NEXT ACTION: Fix gateway connection."
fi

{
  echo "## CEO Synthesis"
  echo ""
  echo "$CEO_REPLY"
  echo ""
} >> "$TRANSCRIPT"

echo "  CEO synthesis complete."

# --- Output decision to terminal ---
echo ""
echo "=== MEETING COMPLETE ==="
echo "Full transcript: $TRANSCRIPT"
echo ""
echo "============================================================"
echo "DECISION"
echo "============================================================"
grep -A 5 "^DECISION:" "$TRANSCRIPT" | head -6 || echo "(See full transcript)"
echo ""
echo "NEXT ACTION"
echo "============================================================"
grep -A 3 "^NEXT ACTION:" "$TRANSCRIPT" | head -4 || echo "(See full transcript)"
echo ""
echo "============================================================"

# Write decision to CEO MEMORY.md for persistence
CEO_MEM="$WORKSPACE_DIR/CEO/MEMORY.md"
if [ -f "$CEO_MEM" ]; then
  DECISION_LINE=$(grep -A 3 "^DECISION:" "$TRANSCRIPT" | head -4 | tr '\n' ' ' | sed 's/  */ /g')
  {
    echo ""
    echo "## Meeting Decision — $(date '+%Y-%m-%d')"
    echo "**Topic:** $TOPIC"
    echo "**$DECISION_LINE**"
    echo "Transcript: $OUTPUT"
  } >> "$CEO_MEM"
  echo "Decision written to CEO/MEMORY.md"
fi
```

---

## Inter-Agent Communication Pattern

The CEO delegates to a department head by constructing a brief and spawning. The key is always `openclaw agent --message "$BRIEF" --json`.

### CEO → Department Head Delegation

```bash
# Delegate an engineering task
./scripts/spawn_specialist.sh engineering \
  "Audit the authentication flow and identify security gaps.
   Check: session handling, token expiry, input validation.
   Output: ranked list of issues with severity and fix recommendation." \
  "agents/engineering/output/auth-audit-$(date +%Y%m%d).md"
```

### Direct Agent Call Pattern

When you want to call an agent inline (e.g., from a script) without the full spawn_specialist.sh wrapper:

```bash
# Call an agent and capture the reply
RESULT=$(openclaw agent \
  --message "$FULL_BRIEF" \
  --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('reply',''))" 2>/dev/null || echo "")

# Or: deliver result to a Telegram channel instead of capturing
openclaw agent \
  --message "$FULL_BRIEF" \
  --deliver \
  --reply-channel telegram \
  --reply-to "$TELEGRAM_CHAT_ID"

# Or: with higher thinking level for complex decisions
openclaw agent \
  --message "$BRIEF" \
  --thinking medium \
  --json
```

---

## Department Memory Architecture

This is the mechanism that makes the org get smarter over time.

### The Write-Through Pattern

```
Cycle 1:
  Specialist A executes → writes agents/engineering/output/task-1.md
  consolidate_outputs.sh runs → updates agents/engineering/MEMORY.md with session block
  
Cycle 2:
  Specialist B spawns → reads updated agents/engineering/MEMORY.md
  Specialist B has full context from Cycle 1 without being told
  Specialist B executes → writes agents/engineering/output/task-2.md
  consolidate_outputs.sh runs → MEMORY.md now has both sessions

Cycle N:
  Every specialist inherits everything every previous specialist learned.
  Intelligence compounds with every cycle.
```

### What Gets Written to MEMORY.md (each session block)

```markdown
## Session 2026-01-15

### Tasks Completed
- [2026-01-15] Refactor auth module → RESULT: JWT implementation complete, stateless auth working

### Decisions Made
- DECISION: Using RS256 signing (asymmetric) over HS256 for JWT — better key rotation story

### What The Next Specialist Needs To Know
Auth module now lives in src/auth/. JWT secret rotates via env var JWT_PRIVATE_KEY.
Old session-based auth still active on /api/v1 — don't touch until deprecation.
```

### Update Discipline

**Rule:** Run `./scripts/consolidate_outputs.sh` after every work block. Never let two cycles pass with stale MEMORY.md. Stale memory means specialists re-discover things that are already known.

---

## Troubleshooting

**"Department not found" error**
Run `mkdir -p agents/<dept>/output` and add SOUL.md + MEMORY.md for that department.

**Specialist output is shallow or generic**
MEMORY.md has no real context. Fill in the "What The Next Specialist Needs To Know" section manually with your actual current state before the first spawn.

**openclaw agent: command not found**
The CLI isn't on your PATH. Check installation: `which openclaw`. If missing, reinstall OpenClaw or fix PATH.

**openclaw agent returns empty reply**
Gateway isn't running. Run: `openclaw gateway start`, then retry.

**Meeting transcript shows "Unable to get response"**
Same issue — gateway down. Run `openclaw gateway status` to confirm.

**consolidate_outputs.sh skips a department**
Either no output files exist yet (run spawn_specialist.sh first) or the output directory doesn't exist (run `mkdir -p agents/<dept>/output`).

**validate_setup.sh shows "placeholder" warnings**
Open the flagged SOUL.md files and replace "Acme Software" references with your actual org name and context. The skill ships with a filled-in example — you must adapt it to your org.

---

## What This Skill Pairs With

This system is designed to plug into the rest of the ClawGear stack:

- **ClawGear Persona** — use it for the CEO agent's persona layer
- **Close-The-Loop System** — wire the ACK→Plan→ETA→Report protocol into each agent's SOUL.md
- **Agent Ops Playbook Pro** — the memory architecture principles here extend what that skill teaches; strongly recommended for enforcement
- **Sub-Agent Orchestrator** — the spawn_specialist.sh script in this skill is a higher-level wrapper; the orchestrator's scripts handle lower-level parallel monitoring

You don't need all of them. Start with this skill alone. Add the others as you need more sophistication.

---

## Reference: All Files Included

| File | Purpose |
|------|---------|
| `CEO/SOUL.md` | CEO identity, delegation rules, output format |
| `CEO/MEMORY.md` | Cross-org state, active projects, key decisions |
| `agents/engineering/SOUL.md` | Engineering head identity and domain |
| `agents/distribution/SOUL.md` | Distribution head identity and domain |
| `agents/engineering/MEMORY.md` | Engineering department context (filled example) |
| `agents/distribution/MEMORY.md` | Distribution department context (filled example) |
| `agents/TASKS.md` | Cross-department task tracker (filled example) |
| `scripts/validate_setup.sh` | Verify installation before first spawn |
| `scripts/spawn_specialist.sh` | Spawn a specialist with full context injection |
| `scripts/consolidate_outputs.sh` | Update MEMORY.md with structured session blocks |
| `scripts/autonomous_meeting.sh` | Multi-agent debate with CEO decision output |

---

## Pricing

**This skill — $44**

Gets you the full multi-agent org system: file structure, templates, all 4 scripts, the memory architecture, and the autonomous meeting pattern. Enough to run a functioning multi-agent org from day one.

**Pairs well with:**

| Skill | Price | What It Adds |
|-------|-------|-------------|
| Agent Ops Playbook Pro | $19 | Memory enforcement, validator scripts, pre-commit hooks so MEMORY.md never goes stale |
| Close-The-Loop System | $14 | ACK→Plan→ETA→Execute→Report protocol wired into every agent, so nothing goes silent |
| **Full stack** | **$77** | **Complete autonomous org: structure + memory enforcement + reporting discipline** |

The full stack is the production-grade version. Each skill works standalone, but together they close every gap.
