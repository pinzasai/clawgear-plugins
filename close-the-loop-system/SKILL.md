---
name: close-the-loop-system
description: Mandatory close-the-loop reporting protocol for OpenClaw agents. Installs the ACK-Plan-ETA-Execute-Report discipline, a Telegram reporting script, status templates, escalation rules, and daily-note integration so agents never go silent after completing a task.
metadata:
  version: 1.0.0
  author: ClawGear
  category: Ops
  tags: [reporting, telegram, close-the-loop, sub-agent, communication]
  price: 14
---

# Close-The-Loop System

**Type:** Ops  
**Version:** 1.0.0  
**Price:** $14

The most common failure mode for AI agents: task acknowledged, work done, silence. The operator has no idea what happened, what's next, or what's blocked. The feedback loop is broken, trust erodes, and the human has to chase the agent down.

This skill installs a mandatory reporting protocol that closes the loop every time — with a real script that sends reports to Telegram, templates for every status type, and rules for when to DM vs post to the group.

---

## What You Get

- **`report_task.sh`** — formats and sends task completion reports to Telegram via Bot API
- **ACK → Plan → ETA → Execute → Report** protocol (wired into SOUL.md / AGENTS.md)
- **Status templates** for: completed / blocked / in-progress / needs-input
- **Escalation rules** — when to DM vs group channel
- **Daily note integration** — every report auto-appended to `memory/YYYY-MM-DD.md`
- **Sub-agent close-loop checklist** — runs after every sub-agent completes
- **Good vs bad report examples** — know the difference at a glance

---

## Quick Start

```bash
# 1. Copy the script
cp scripts/report_task.sh ~/your-workspace/scripts/
chmod +x ~/your-workspace/scripts/report_task.sh

# 2. Set your Telegram credentials as environment variables
export TELEGRAM_BOT_TOKEN="your-bot-token-here"
export TELEGRAM_CHAT_ID="your-chat-id-here"

# 3. Send a test report
./scripts/report_task.sh \
  --status completed \
  --task "Set up project scaffolding" \
  --result "Created 3 project folders, updated index.json" \
  --next "Fill in PROJECT.md goals" \
  --project my-saas
```

The script sends to Telegram and appends to today's daily note automatically.

---

## The Protocol: ACK → Plan → ETA → Execute → Report

Every task the agent handles follows this sequence. No shortcuts.

### Step 1: ACK
Confirm receipt in the same channel the task came from.

```
Got it. Working on: [task summary]
```

Never say "on it" and go silent. That's the anti-pattern this skill fixes.

### Step 2: Plan
State what you'll do, in what order, before doing it.

```
Plan:
1. [First thing]
2. [Second thing]
3. [Third thing]
```

Short tasks (under 2 minutes): you can skip a formal plan, but the ACK still happens.

### Step 3: ETA
Give an honest time estimate. If you can't estimate, say why.

```
ETA: executing now in this turn
ETA: ~5 minutes (need to read 3 files first)
ETA: blocked — need your input before I can proceed (see below)
```

Never give a fake ETA to sound confident. If it requires multiple turns or external input, say so explicitly.

### Step 4: Execute
Do the actual work in the same turn. Not in the background, not later, not "I'll start on that."

If the work genuinely requires multiple turns (sub-agent, long process), break it into visible checkpoints:
```
Checkpoint 1 complete: [what was done]
Starting checkpoint 2...
```

### Step 5: Report
Send a structured completion report. Use `report_task.sh` or the templates below.

The report goes to the right channel (see Escalation Rules), gets appended to today's daily note, and is done. The loop is closed.

---

## Status Templates

Use these verbatim or as a base. The structure matters — don't freeform.

### COMPLETED

```
DONE: [task name]
Project: [project name or "general"]
Result: [what was actually done — 1-2 sentences, concrete]
Next: [specific next step agent can start immediately]
Blockers: none
```

### BLOCKED

```
BLOCKED: [task name]
Project: [project name]
Done so far: [what was completed before hitting the block]
Blocked on: [exactly what is needed — be specific]
Options:
  A) [option A]
  B) [option B]
Waiting for your call.
```

### IN PROGRESS (checkpoint update)

```
UPDATE: [task name]
Project: [project name]
Status: [X of Y steps complete]
Completed: [what's done]
Doing now: [current step]
ETA for next update: [honest estimate]
```

### NEEDS INPUT

```
NEEDS INPUT: [task name]
Project: [project name]
Context: [brief context so they can answer without reading anything]
Question: [single clear question — one at a time]
Options:
  A) [option A — recommended if applicable]
  B) [option B]
Default if no response in [timeframe]: [what agent will do]
```

---

## Escalation Rules

**Post to the project's group channel when:**
- The task was assigned in that group
- The result affects other people in the group (not just the operator)
- It's a project milestone or completion

**DM the operator when:**
- The task was assigned in DM
- It's sensitive (credentials, personal info, private decisions)
- It's urgent and the group channel is noisy
- You're blocked and need a fast decision
- Something went wrong and you don't want to alarm the group

**Never post to the wrong channel:**
- Don't announce Project A work in Project B's group
- Don't DM project updates when the group expects them
- Don't cross-post the same update to both DM and group (pick one)

---

## Scripts

### `scripts/report_task.sh`

```bash
#!/usr/bin/env bash
# report_task.sh — format and send a task completion report to Telegram
# Also appends to today's daily note
#
# Usage:
#   ./scripts/report_task.sh --status <status> --task <name> --result <text> [options]
#
# Required env vars:
#   TELEGRAM_BOT_TOKEN — your bot token from @BotFather
#   TELEGRAM_CHAT_ID   — the chat ID to send to (DM or group)
#
# Options:
#   --status    completed|blocked|in-progress|needs-input  (required)
#   --task      task name                                   (required)
#   --result    what was done or current state              (required)
#   --next      next step                                   (optional)
#   --blocked   what is blocking                            (optional)
#   --project   project name                                (optional)
#   --no-notes  skip appending to daily notes               (optional)
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STATUS=""
TASK=""
RESULT=""
NEXT=""
BLOCKED_ON=""
PROJECT=""
SKIP_NOTES=0
DATE="$(date +%Y-%m-%d)"
TIME="$(date +%H:%M)"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --status)   STATUS="$2";     shift 2 ;;
    --task)     TASK="$2";       shift 2 ;;
    --result)   RESULT="$2";     shift 2 ;;
    --next)     NEXT="$2";       shift 2 ;;
    --blocked)  BLOCKED_ON="$2"; shift 2 ;;
    --project)  PROJECT="$2";    shift 2 ;;
    --no-notes) SKIP_NOTES=1;    shift   ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Validate required
if [[ -z "$STATUS" || -z "$TASK" || -z "$RESULT" ]]; then
  echo "Usage: $0 --status <status> --task <name> --result <text> [--next <text>] [--blocked <text>] [--project <name>]" >&2
  echo "Required env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID" >&2
  exit 1
fi

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "Error: TELEGRAM_BOT_TOKEN not set" >&2
  exit 1
fi

if [[ -z "${TELEGRAM_CHAT_ID:-}" ]]; then
  echo "Error: TELEGRAM_CHAT_ID not set" >&2
  exit 1
fi

# Build message based on status
case "$STATUS" in
  completed)
    EMOJI="DONE"
    MSG="${EMOJI}: ${TASK}"
    [[ -n "$PROJECT" ]] && MSG="${MSG}
Project: ${PROJECT}"
    MSG="${MSG}
Result: ${RESULT}"
    [[ -n "$NEXT" ]] && MSG="${MSG}
Next: ${NEXT}"
    MSG="${MSG}
Blockers: none"
    ;;

  blocked)
    EMOJI="BLOCKED"
    MSG="${EMOJI}: ${TASK}"
    [[ -n "$PROJECT" ]] && MSG="${MSG}
Project: ${PROJECT}"
    MSG="${MSG}
Done so far: ${RESULT}
Blocked on: ${BLOCKED_ON:-[not specified]}"
    [[ -n "$NEXT" ]] && MSG="${MSG}
Options: ${NEXT}"
    MSG="${MSG}
Waiting for your call."
    ;;

  in-progress)
    EMOJI="UPDATE"
    MSG="${EMOJI}: ${TASK}"
    [[ -n "$PROJECT" ]] && MSG="${MSG}
Project: ${PROJECT}"
    MSG="${MSG}
Status: ${RESULT}"
    [[ -n "$NEXT" ]] && MSG="${MSG}
Doing next: ${NEXT}"
    ;;

  needs-input)
    EMOJI="NEEDS INPUT"
    MSG="${EMOJI}: ${TASK}"
    [[ -n "$PROJECT" ]] && MSG="${MSG}
Project: ${PROJECT}"
    MSG="${MSG}
Context: ${RESULT}
Question: ${NEXT:-[see above]}"
    ;;

  *)
    echo "Error: unknown status '$STATUS'. Use: completed, blocked, in-progress, needs-input" >&2
    exit 1
    ;;
esac

# Send to Telegram
send_response=$(curl -s -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"${TELEGRAM_CHAT_ID}\", \"text\": $(echo "$MSG" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")

# Check response
if echo "$send_response" | python3 -c "import json,sys; r=json.load(sys.stdin); sys.exit(0 if r.get('ok') else 1)" 2>/dev/null; then
  echo "Report sent to Telegram (chat: ${TELEGRAM_CHAT_ID})"
else
  echo "Warning: Telegram send may have failed. Response: $send_response" >&2
fi

# Append to daily notes
if [[ $SKIP_NOTES -eq 0 ]]; then
  NOTES_DIR="$WORKSPACE_DIR/memory"
  NOTES_FILE="$NOTES_DIR/$DATE.md"
  mkdir -p "$NOTES_DIR"

  NOTE_ENTRY="
## Task Report — $TIME

**Status:** $STATUS
**Task:** $TASK"

  [[ -n "$PROJECT" ]] && NOTE_ENTRY="${NOTE_ENTRY}
**Project:** $PROJECT"

  NOTE_ENTRY="${NOTE_ENTRY}
**Result:** $RESULT"

  [[ -n "$NEXT" ]] && NOTE_ENTRY="${NOTE_ENTRY}
**Next:** $NEXT"

  [[ -n "$BLOCKED_ON" ]] && NOTE_ENTRY="${NOTE_ENTRY}
**Blocked on:** $BLOCKED_ON"

  echo "$NOTE_ENTRY" >> "$NOTES_FILE"
  echo "Appended to $NOTES_FILE"
fi
```

### `scripts/subagent_checklist.sh`

Run this after every sub-agent completes. Prompts you through the close-loop checklist.

```bash
#!/usr/bin/env bash
# subagent_checklist.sh — close-loop checklist after sub-agent completion
# Usage: ./scripts/subagent_checklist.sh <agent-label> <project>
set -euo pipefail

AGENT_LABEL="${1:-unknown-agent}"
PROJECT="${2:-}"

echo ""
echo "Sub-Agent Close-Loop Checklist: $AGENT_LABEL"
echo "---"
echo ""
echo "1. Read the sub-agent output? (yes/no)"
read -r step1
if [[ "$step1" != "yes" ]]; then
  echo "   -> Do that first. The checklist doesn't work without it."
  exit 1
fi

echo "2. Did the agent complete the task? (yes/no/partial)"
read -r step2

echo "3. Update TASKS.md with what was done? (yes/skip)"
read -r step3
if [[ "$step3" == "yes" ]]; then
  if [[ -n "$PROJECT" ]]; then
    echo "   -> Open: projects/$PROJECT/TASKS.md"
  fi
fi

echo "4. Update MEMORY.md with key decisions/findings? (yes/skip)"
read -r step4
if [[ "$step4" == "yes" ]]; then
  if [[ -n "$PROJECT" ]]; then
    echo "   -> Open: projects/$PROJECT/MEMORY.md"
  fi
fi

echo "5. Send completion report to operator? (yes/skip)"
read -r step5
if [[ "$step5" == "yes" ]]; then
  echo "   -> Use: ./scripts/report_task.sh --status completed --task \"$AGENT_LABEL\" --result \"...\" --next \"...\""
fi

echo ""
echo "Checklist complete for: $AGENT_LABEL"
echo "Status: $step2"
```

---

## Daily Note Integration

Every call to `report_task.sh` automatically appends a structured entry to `memory/YYYY-MM-DD.md`. No extra setup needed.

The entry looks like:

```markdown
## Task Report — 21:15

**Status:** completed
**Task:** Set up project scaffolding
**Project:** my-saas
**Result:** Created PROJECT.md, TASKS.md, MEMORY.md for my-saas. Updated index.json with Telegram group mapping.
**Next:** Fill in PROJECT.md with goals and stack details
```

To skip daily note appending (for automated/test runs):
```bash
./scripts/report_task.sh --status completed --task "test" --result "ok" --no-notes
```

---

## Sub-Agent Checklist

After every sub-agent completes, run through this before reporting to the operator:

```
Sub-Agent Close-Loop Checklist
-------------------------------
[ ] Read the full sub-agent output
[ ] Did it complete the task? (yes / partial / no)
[ ] Update TASKS.md — move completed items to Done with date
[ ] Update MEMORY.md — log key decisions, findings, tokens received
[ ] Update daily notes if significant
[ ] Send completion report via report_task.sh or Telegram
[ ] Clear from heartbeat-state.json taskQueue if it was queued there
```

This is not optional. The parent session is responsible for syncing project files after a sub-agent runs — the sub-agent cannot do this itself.

---

## Examples: Good vs Bad Reports

### Bad report (do not do this)

```
Done with the task. Let me know if you need anything else.
```

Problems:
- No mention of what was actually done
- No next steps proposed
- No project context
- No structured format
- Forces the operator to ask "so what happened?"

---

### Bad report (also wrong)

```
I've been working on the scaffolding and I think it went well overall. I ran the script and created some files and things look pretty good from what I can see. You might want to check the TASKS.md file. I wasn't sure if I should also update the MEMORY.md so I left that for you.
```

Problems:
- Vague ("some files", "pretty good")
- No structure — hard to scan
- Deferred a decision that should have been made
- Walls of hedged text instead of facts

---

### Good report (completed)

```
DONE: Project scaffolding for my-saas
Project: my-saas
Result: Created projects/my-saas/ with PROJECT.md, TASKS.md, MEMORY.md. Registered group -5195996657 in index.json.
Next: Fill in PROJECT.md with goals and stack — takes 5 min, I can do it now
Blockers: none
```

Why it works: structured, scannable, concrete result, clear next step, closes the loop.

---

### Good report (blocked)

```
BLOCKED: OAuth token setup for Telegram bot
Project: clawarmor
Done so far: Created bot via @BotFather, got token, hit 409 Conflict error when registering webhook
Blocked on: Existing webhook URL registered to a different server. Need to delete it first or get the current URL.
Options:
  A) Delete existing webhook and re-register (recommended if you own the other server)
  B) Use polling mode instead of webhook (simpler, slightly less efficient)
Waiting for your call.
```

Why it works: tells exactly where it got stuck, gives concrete options, doesn't just say "I can't do this."

---

## Configuration

### Environment variables

```bash
# Required for report_task.sh
export TELEGRAM_BOT_TOKEN="1234567890:ABCdef..."
export TELEGRAM_CHAT_ID="-5195996657"   # group ID (negative) or user ID (positive)
```

Store these in your shell profile or in a `.env` file (not committed to git).

To get your bot token: message @BotFather on Telegram, create a bot, copy the token.
To get a group chat ID: add your bot to the group, send a message, call `https://api.telegram.org/bot<TOKEN>/getUpdates` and look for `chat.id`.

### Wiring into SOUL.md

Add this block to your agent's SOUL.md under behavioral rules:

```markdown
## Close the Loop — Always

After completing any meaningful task:
1. Do it — don't ask permission for things already in scope
2. Report back in the same channel — use the DONE/BLOCKED/UPDATE/NEEDS INPUT format
3. Keep it tight — structured, concrete, scannable
4. Propose next steps — don't wait for the operator to ask "what's next?"

Never say "on it" and go silent. If you ACK, you deliver in the same turn or
you immediately report why you cannot and what you need.
```

### Wiring into AGENTS.md

Add this to the end of your agent session protocol:

```markdown
## After Every Significant Task

Run the sync checklist:
- Did I change project state? Update TASKS.md
- Did I make a decision worth remembering? Update MEMORY.md
- Was this a sub-agent result? Read output, sync to project files
- Send a structured report to the right channel
```

---

## Troubleshooting

**Telegram reports not sending**
Check that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are exported. Test with:
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```
If that fails, the token is wrong. If it succeeds but messages don't arrive, the chat ID is wrong or the bot is not a member of the group.

**Daily note not getting appended**
The `memory/` directory must exist under your workspace root. The script creates it automatically, but if your workspace layout is different, pass the full path via `WORKSPACE_DIR`:
```bash
WORKSPACE_DIR=/your/workspace ./scripts/report_task.sh ...
```

**report_task.sh exits with "python3 not found"**
The script uses python3 to JSON-encode the message. Install python3 or replace the encoding with `jq`:
```bash
# Replace the python3 line with:
-d "{\"chat_id\": \"${TELEGRAM_CHAT_ID}\", \"text\": $(echo "$MSG" | jq -Rs .)}")
```
