# Setup Guide — 30 Minutes to a Clawsome Agent

## Before You Start

You need:
- OpenClaw installed and running
- A workspace directory (default: `~/.openclaw/workspace`)
- Telegram bot configured (optional — skip if using webchat only)

---

## Step 1: Install Core Files (5 min)

Copy the five persona files into your workspace root:

```
~/.openclaw/workspace/
├── SOUL.md           ← identity + behavioral rules
├── AGENTS.md         ← session protocol + memory system
├── USER.md           ← fill this in (see below)
├── HEARTBEAT.md      ← proactive check schedule
└── scripts/
    └── memory-sync.sh
```

Make the script executable:
```bash
chmod +x ~/.openclaw/workspace/scripts/memory-sync.sh
```

---

## Step 2: Fill In USER.md (5 min)

Open `USER.md` and fill in:
- Your name
- Your timezone
- Your Telegram chat ID (find it by messaging @userinfobot on Telegram)
- Which channels you use and what each is for

Example:
```markdown
## About
- Name: Alex
- Timezone: America/New_York
- Telegram DM chat_id: 123456789

## Channels
| Channel | Purpose |
|---------|---------|
| Webchat | Everything personal and cross-project |
| Telegram DM | Urgent alerts and close-the-loop updates |
```

---

## Step 3: Set Up Memory Structure (5 min)

Create the directories:
```bash
mkdir -p ~/.openclaw/workspace/memory
mkdir -p ~/.openclaw/workspace/projects
```

Create heartbeat state file:
```bash
echo '{"lastChecks": {"email": null, "calendar": null, "nightlyAudit": null}}' \
  > ~/.openclaw/workspace/memory/heartbeat-state.json
```

Create today's daily notes file:
```bash
echo "# $(date +%Y-%m-%d)" > ~/.openclaw/workspace/memory/$(date +%Y-%m-%d).md
```

Run the validator to confirm clean state:
```bash
bash ~/.openclaw/workspace/scripts/memory-sync.sh
# Should print: ✅ Memory sync OK
```

---

## Step 4: Set Up Git (5 min)

The memory system uses git commits as checkpoints:
```bash
cd ~/.openclaw/workspace
git init
git add -A
git commit -m "Initial Clawsome persona install"
```

Install the pre-commit hook (blocks commits with stale project files):
```bash
cp scripts/memory-sync.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## Step 5: Set Up Heartbeat (5 min)

In OpenClaw, configure a heartbeat:
```bash
openclaw config set heartbeat.enabled true
openclaw config set heartbeat.intervalMinutes 10
```

Or via cron for exact timing:
```bash
openclaw cron add "heartbeat" --schedule "*/10 * * * *" \
  --channel telegram --to "YOUR_CHAT_ID" \
  --prompt "Read HEARTBEAT.md if it exists. Follow it strictly. If nothing needs attention, reply HEARTBEAT_OK."
```

---

## Step 6: Configure Exec on Host (5 min)

Clawsome needs exec to run on the host (not sandboxed) for memory-sync.sh and file operations:

```bash
openclaw config set tools.exec.host sandbox
openclaw config set tools.exec.security full
openclaw config set agents.defaults.sandbox.mode all
```

Restart gateway:
```bash
openclaw gateway restart
```

---

## Step 7: First Session Test (5 min)

Start a new webchat session. Your agent should:
1. Read SOUL.md, USER.md, and today's daily notes automatically
2. Greet you in a direct, non-sycophantic way
3. Ask what you want to work on

If it's listing files or asking what to read — it didn't load the startup protocol. Check that AGENTS.md is in the workspace root and the workspace path is configured correctly in OpenClaw.

---

## Multi-Project Setup (Optional, +10 min)

If you're running multiple projects across Telegram groups, see [multi-project-guide.md](multi-project-guide.md).

---

## Troubleshooting

**Agent is generic / not following the persona**
→ Check SOUL.md is in workspace root. Restart gateway. Start a new session (not a resumed one).

**Memory sync failing**
→ Run `bash scripts/memory-sync.sh` manually. It prints what's out of sync. Fix those files first.

**Heartbeat not triggering**
→ Check `openclaw cron list`. If empty, re-add the heartbeat cron. Cron jobs don't persist across gateway restarts.

**Agent responding to every group message**
→ Check `AGENTS.md` has the "Know When to Speak" section. Make sure the group session is loading the right project context via index.json.
