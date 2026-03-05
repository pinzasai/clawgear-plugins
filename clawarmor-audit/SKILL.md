---
name: clawarmor-audit
description: Run ClawArmor security audits, interpret results, manage baselines, and decide when to alert Alberto. Use when running scheduled security checks, responding to audit score changes, hardening the OpenClaw config, reviewing audit history, or rolling back a bad config change. ClawArmor binary: ~/clawarmor/bin/clawarmor.js or `clawarmor` if on PATH.
---

# ClawArmor Audit

Run security audits and act on results intelligently.

## Quick Commands

```bash
# Full audit
clawarmor audit

# Audit with JSON output (for parsing)
clawarmor audit --json

# Accept config baseline after reviewing changes
clawarmor audit --accept-changes

# View audit history and score trend
clawarmor trend

# Security status dashboard
clawarmor status

# Harden config (safe changes only — skips 🔴 Breaking)
clawarmor harden --auto

# Harden with monitor mode (advisory, no changes)
clawarmor harden --monitor

# Roll back last harden/fix
clawarmor rollback

# Scan installed skills for obfuscation/malicious patterns
clawarmor scan
```

## Interpreting Scores

| Score | Grade | Action |
|-------|-------|--------|
| 90-100 | A | No action needed |
| 75-89 | B | Review MEDIUM findings next session |
| 60-74 | C | Address HIGH findings soon |
| 50-59 | D | Alert Alberto — new HIGH finding likely |
| <50 | F | Urgent — alert immediately |

## Alert Decision Logic

**Alert Alberto when:**
- Score drops ≥5 points from previous audit
- Any new 🔴 HIGH finding appears (not present yesterday)
- `tools.elevated.allowFrom` becomes unrestricted
- Gateway stops being loopback-only
- Auth token is missing or weak

**Don't alert when:**
- Same known findings as previous run (score unchanged)
- Score improved
- Only config baseline drift (no new security issues)

## Known Baseline Findings (as of 2026-03-03)

These are accepted/tracked and do NOT require alerts:
- 🔴 `tools.exec.ask=off` — intentional, Alberto is aware
- 🔴 API key patterns in `~/.openclaw/` JSON files — credentials stored as designed
- 🟡 Comfy group open policy — intentional for Baira collaboration

**Do alert on any NEW finding not in this list.**

## Config Drift

`openclaw.json` baseline was set 2026-03-01. After reviewing config changes:
```bash
clawarmor audit --accept-changes
```
Run this after any intentional config update (adding channels, changing models, etc.).

## Delivery

Send audit alerts via Telegram DM to Alberto (chat_id: `1176440324`).
Format: score + grade, new findings only, one-line fix recommendation per finding.
Keep it under 10 lines total.

## Cron Setup

Audit runs daily at 5 AM via cron. To check/recreate:
```bash
openclaw cron list
# If missing:
openclaw cron add "daily-security-audit" --schedule "0 5 * * *" \
  --channel telegram --to "1176440324" \
  --prompt "Run clawarmor audit, interpret results, alert if score dropped or new findings. Known baseline: exec.ask=off, API keys in JSON, Comfy open policy — these are NOT alerts."
```
