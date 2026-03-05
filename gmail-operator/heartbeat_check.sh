#!/usr/bin/env bash
# heartbeat_check.sh -- Gmail heartbeat checker for OpenClaw agents.
#
# Checks for unread emails, triages them, and sends a Telegram alert
# if any URGENT emails are found.
#
# Required env vars:
#   GMAIL_CREDENTIALS_PATH   Path to OAuth 2.0 client credentials JSON
#   TELEGRAM_BOT_TOKEN       Telegram bot token
#   TELEGRAM_CHAT_ID         Telegram chat ID
#
# Optional env vars:
#   GMAIL_CONFIG_PATH        Path to .gmail-config.yml (default: ~/.openclaw/.gmail-config.yml)
#   GMAIL_SKILL_DIR          Path to this skill directory (auto-detected)

set -euo pipefail

SKILL_DIR="${GMAIL_SKILL_DIR:-"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"}"
CONFIG_PATH="${GMAIL_CONFIG_PATH:-"$HOME/.openclaw/.gmail-config.yml"}"
STATE_FILE="$HOME/.openclaw/gmail-heartbeat-state.json"
TRIAGE_OUTPUT="$HOME/.openclaw/gmail-triage-latest.json"

if [ -z "${GMAIL_CREDENTIALS_PATH:-}" ]; then
  echo "[gmail-heartbeat] ERROR: GMAIL_CREDENTIALS_PATH not set" >&2
  exit 1
fi

CHECK_INTERVAL_MINUTES=15
if [ -f "$CONFIG_PATH" ]; then
  CONFIGURED_INTERVAL=$(python3 -c "
import sys
try:
    import yaml
    config = yaml.safe_load(open('$CONFIG_PATH'))
    print(config.get('check_interval_minutes', 15))
except Exception:
    print(15)
" 2>/dev/null || echo 15)
  CHECK_INTERVAL_MINUTES="$CONFIGURED_INTERVAL"
fi

NOW=$(date +%s)
if [ -f "$STATE_FILE" ]; then
  LAST_CHECK=$(python3 -c "
import json
try:
    state = json.load(open('$STATE_FILE'))
    print(state.get('last_check', 0))
except Exception:
    print(0)
" 2>/dev/null || echo 0)
  ELAPSED=$(( NOW - LAST_CHECK ))
  MIN_INTERVAL=$(( CHECK_INTERVAL_MINUTES * 60 ))
  if [ "$ELAPSED" -lt "$MIN_INTERVAL" ]; then
    echo "[gmail-heartbeat] Skipping -- checked ${ELAPSED}s ago (interval: ${MIN_INTERVAL}s)"
    exit 0
  fi
fi

echo "[gmail-heartbeat] Running email triage..."

python3 "$SKILL_DIR/triage_email.py" \
  --config "$CONFIG_PATH" \
  --json > "$TRIAGE_OUTPUT" 2>&1 || {
  echo "[gmail-heartbeat] Triage failed. Check $TRIAGE_OUTPUT" >&2
  exit 1
}

URGENT_COUNT=$(python3 -c "
import json
try:
    emails = json.load(open('$TRIAGE_OUTPUT'))
    print(len([e for e in emails if e.get('priority') == 'URGENT']))
except Exception:
    print(0)
" 2>/dev/null || echo 0)

TOTAL_COUNT=$(python3 -c "
import json
try:
    print(len(json.load(open('$TRIAGE_OUTPUT'))))
except Exception:
    print(0)
" 2>/dev/null || echo 0)

echo "[gmail-heartbeat] Found ${TOTAL_COUNT} unread, ${URGENT_COUNT} urgent"

python3 - << INNER_PYEOF
import json
from pathlib import Path
p = Path("$STATE_FILE")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({"last_check": $NOW, "urgent_count": $URGENT_COUNT, "total_count": $TOTAL_COUNT}, indent=2))
INNER_PYEOF

if [ "${URGENT_COUNT}" -gt 0 ]; then
  BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
  CHAT_ID="${TELEGRAM_CHAT_ID:-}"

  if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "[gmail-heartbeat] WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping alert."
  else
    URGENT_SUMMARY=$(python3 -c "
import json
try:
    emails = json.load(open('$TRIAGE_OUTPUT'))
    urgent = [e for e in emails if e.get('priority') == 'URGENT'][:5]
    lines = []
    for e in urgent:
        sender = e.get('from', 'Unknown')[:40]
        subject = e.get('subject', '(no subject)')[:60]
        lines.append(f'  * From: {sender}\n    Subject: {subject}')
    print('\n'.join(lines))
except Exception:
    print('Could not parse triage output')
" 2>/dev/null || echo "Parse error")

    MESSAGE="Gmail Alert: ${URGENT_COUNT} URGENT email(s) found

${URGENT_SUMMARY}

Total unread: ${TOTAL_COUNT}
Run triage_email.py for full details"

    curl -s -X POST \
      "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -d "chat_id=${CHAT_ID}" \
      --data-urlencode "text=${MESSAGE}" \
      > /dev/null

    echo "[gmail-heartbeat] Telegram alert sent for ${URGENT_COUNT} urgent email(s)"
  fi
else
  echo "[gmail-heartbeat] No urgent emails. No alert sent."
fi
