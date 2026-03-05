#!/usr/bin/env bash
# cost_alert.sh - check if daily spend exceeds threshold, send Telegram alert
# Usage: ./scripts/cost_alert.sh [THRESHOLD_USD]
# Required env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
# Default threshold: $1.00/day (override with first argument or COST_ALERT_THRESHOLD env var)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TRACKER="${SCRIPT_DIR}/track_cost.py"
THRESHOLD="${1:-${COST_ALERT_THRESHOLD:-1.00}}"

for VAR in TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  if [[ -z "${!VAR:-}" ]]; then
    echo "ERROR: ${VAR} is not set. Export it before running."
    exit 1
  fi
done

# Get today's total (first line of daily output is "Today: $X.XXXX")
DAILY_LINE=$(python3 "${TRACKER}" daily 2>&1 | head -1) || {
  echo "ERROR: track_cost.py failed"
  exit 1
}

DAILY_COST=$(echo "$DAILY_LINE" | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo "0")

# Compare using python3 (awk float comparison is unreliable)
EXCEEDED=$(python3 -c "print('yes' if float('${DAILY_COST}') > float('${THRESHOLD}') else 'no')")

if [[ "$EXCEEDED" == "yes" ]]; then
  MSG="🚨 API Cost Alert!
Today: \$${DAILY_COST} (threshold: \$${THRESHOLD})
Action: Review active agents and session counts.
Details: run track_cost.py dashboard"

  ENCODED=$(python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" <<< "$MSG")
  curl -s -o /dev/null \
    -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{"chat_id": "${TELEGRAM_CHAT_ID}", "text": ${ENCODED}}"
  echo "ALERT: Daily spend \$${DAILY_COST} exceeds threshold \$${THRESHOLD}. Telegram alert sent."
  exit 1
else
  echo "OK: Daily spend \$${DAILY_COST} is under threshold \$${THRESHOLD}"
fi
