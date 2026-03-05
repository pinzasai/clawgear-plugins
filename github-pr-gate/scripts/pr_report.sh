#!/usr/bin/env bash
# pr_report.sh - format PR gate findings and send to Telegram
# Usage: ./scripts/pr_report.sh <PR_NUMBER> [owner/repo]
# Required env vars: GITHUB_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
set -euo pipefail

PR_NUMBER="${1:-}"
REPO="${2:-}"

if [[ -z "$PR_NUMBER" ]]; then
  echo "Usage: $0 <PR_NUMBER> [owner/repo]"
  exit 1
fi

for VAR in GITHUB_TOKEN TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  if [[ -z "${!VAR:-}" ]]; then
    echo "ERROR: ${VAR} is not set. Export it before running."
    exit 1
  fi
done

if [[ -z "$REPO" ]]; then
  REPO=$(git remote get-url origin 2>/dev/null | sed -E "s|.*github\.com[:/]||;s|\.git$||") || true
fi

REPORT_FILE="/tmp/pr_review_${PR_NUMBER}.txt"
if [[ ! -f "$REPORT_FILE" ]]; then
  echo "ERROR: No report found. Run pr_review.sh first."
  exit 1
fi

FAIL_COUNT=$(grep -c "^FAIL:" "$REPORT_FILE" 2>/dev/null || echo 0)
WARN_COUNT=$(grep -c "^WARN:" "$REPORT_FILE" 2>/dev/null || echo 0)
PASS_COUNT=$(grep -c "^PASS:" "$REPORT_FILE" 2>/dev/null || echo 0)

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  STATUS_ICON="❌"
  STATUS_TEXT="BLOCKED"
elif [[ "$WARN_COUNT" -gt 0 ]]; then
  STATUS_ICON="⚠️"
  STATUS_TEXT="WARNINGS"
else
  STATUS_ICON="✅"
  STATUS_TEXT="PASSED"
fi

MSG="${STATUS_ICON} PR Gate: ${STATUS_TEXT}
PR: #${PR_NUMBER} (${REPO})
Checks: ${PASS_COUNT} pass | ${WARN_COUNT} warn | ${FAIL_COUNT} fail
Time: $(date -u +"%Y-%m-%d %H:%M UTC")"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  FAILS=$(grep "^FAIL:" "$REPORT_FILE" | head -5 | sed "s/^/  /")
  MSG="${MSG}
Failures:
${FAILS}"
fi

if [[ "$WARN_COUNT" -gt 0 ]]; then
  WARNS=$(grep "^WARN:" "$REPORT_FILE" | head -3 | sed "s/^/  /")
  MSG="${MSG}
Warnings:
${WARNS}"
fi

MSG="${MSG}
Report: /tmp/pr_review_${PR_NUMBER}.txt"

ENCODED=$(python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" <<< "$MSG")
HTTP_STATUS=$(curl -s -o /tmp/tg_pr_response.json -w "%{http_code}" \
  -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{"chat_id": "${TELEGRAM_CHAT_ID}", "text": ${ENCODED}}")

if [[ "$HTTP_STATUS" == "200" ]]; then
  echo "Telegram report sent (HTTP $HTTP_STATUS)"
else
  echo "WARN: Telegram returned HTTP $HTTP_STATUS"
  cat /tmp/tg_pr_response.json 2>/dev/null || true
fi
