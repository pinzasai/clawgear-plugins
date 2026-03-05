# HEARTBEAT.md

## 1. Memory Sync Check (EVERY heartbeat — mandatory)
Run: `bash scripts/memory-sync.sh`
- Exit 0 → continue
- Exit 1 → DRIFT DETECTED. Fix stale project files NOW before doing anything else.

## 2. Task Queue (every heartbeat)
Read TASKS.md. Execute any non-blocked items autonomously. Update file when done.
Hold 🔐 items until human is active or it's been >24h.

## 3. Periodic Checks (rotate, 2-4x per day)
- Email — any urgent unread messages?
- Calendar — upcoming events in next 2 hours?
- Project status — anything blocked or stalled?

Check `memory/heartbeat-state.json` before running — skip if checked < 30 min ago.
Update timestamps after each check.

## 4. Nightly Memory Audit (after 9pm, once per day)
1. Read all today's `memory/YYYY-MM-DD*.md` files
2. For each project mentioned: verify TASKS.md and MEMORY.md are current
3. Update global MEMORY.md with cross-project insights
4. Commit workspace changes

Skip if already ran today (check heartbeat-state.json).

## Gateway Health
If gateway errors appear: `openclaw gateway restart`
