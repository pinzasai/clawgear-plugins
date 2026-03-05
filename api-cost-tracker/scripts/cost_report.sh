#!/usr/bin/env bash
# cost_report.sh - format daily cost summary and send to Telegram
# Usage: ./scripts/cost_report.sh
# Required env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TRACKER="${SCRIPT_DIR}/track_cost.py"

for VAR in TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  if [[ -z "${!VAR:-}" ]]; then
    echo "ERROR: ${VAR} is not set. Export it before running."
    exit 1
  fi
done

# Get daily breakdown
DAILY_OUTPUT=$(python3 "${TRACKER}" daily 2>&1) || {
  echo "ERROR: track_cost.py failed"
  exit 1
}

# Get dashboard for projected monthly
DASHBOARD=$(python3 "${TRACKER}" dashboard 2>&1) || true
PROJECTED=$(echo "$DASHBOARD" | grep "Projected monthly" | awk -F'\$' '{print $2}' || echo "?")
DAILY_AVG=$(echo "$DASHBOARD" | grep "Daily avg" | awk -F'\$' '{print $2}' || echo "?")

TODAY=$(date -u +'%Y-%m-%d')
MSG="📊 API Cost Report — ${TODAY}
${DAILY_OUTPUT}
Daily avg: \$${DAILY_AVG}
Projected month: \$${PROJECTED}
Data: ~/.openclaw/costs.json"

ENCODED=$(python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" <<< "$MSG")
HTTP_STATUS=$(curl -s -o /tmp/tg_cost_response.json -w "%{http_code}" \
  -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{"chat_id": "${TELEGRAM_CHAT_ID}", "text": ${ENCODED}}")

if [[ "$HTTP_STATUS" == "200" ]]; then
  echo "Cost report sent to Telegram"
else
  echo "WARN: Telegram returned HTTP $HTTP_STATUS"
  cat /tmp/tg_cost_response.json 2>/dev/null || true
fi
