#!/usr/bin/env bash
# pr_review.sh - fetch a PR diff and run automated quality checks
# Usage: ./scripts/pr_review.sh <PR_NUMBER> [owner/repo]
# Required env vars: GITHUB_TOKEN
# Outputs a structured report to stdout and writes to /tmp/pr_review_<PR>.txt
set -euo pipefail

PR_NUMBER="${1:-}"
REPO="${2:-}"

if [[ -z "$PR_NUMBER" ]]; then
  echo "Usage: $0 <PR_NUMBER> [owner/repo]"
  exit 1
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "ERROR: GITHUB_TOKEN is not set. Export it before running."
  exit 1
fi

if [[ -z "$REPO" ]]; then
  REPO=$(git remote get-url origin 2>/dev/null | sed -E "s|.*github\.com[:/]||;s|\.git$||") || true
fi
if [[ -z "$REPO" ]]; then
  echo "ERROR: Could not detect repo. Pass owner/repo as second arg."
  exit 1
fi

REPORT_FILE="/tmp/pr_review_${PR_NUMBER}.txt"
echo "=== PR Review Report ===" | tee "$REPORT_FILE"
echo "PR:   #${PR_NUMBER}" | tee -a "$REPORT_FILE"
echo "Repo: ${REPO}" | tee -a "$REPORT_FILE"
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "--- PR Metadata ---" | tee -a "$REPORT_FILE"
PR_JSON=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json title,author,state,additions,deletions,changedFiles 2>&1) || {
  echo "ERROR: gh pr view failed. Verify GITHUB_TOKEN and repo."
  exit 1
}
TITLE=$(echo "$PR_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get("title","?"))")
AUTHOR=$(echo "$PR_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get("author",{}).get("login","?"))")
STATE=$(echo "$PR_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get("state","?"))")
ADDITIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get("additions",0))")
DELETIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get("deletions",0))")
CHANGED_FILES=$(echo "$PR_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get("changedFiles",0))")
echo "Title:         $TITLE" | tee -a "$REPORT_FILE"
echo "Author:        $AUTHOR" | tee -a "$REPORT_FILE"
echo "State:         $STATE" | tee -a "$REPORT_FILE"
echo "Additions:     +$ADDITIONS" | tee -a "$REPORT_FILE"
echo "Deletions:     -$DELETIONS" | tee -a "$REPORT_FILE"
echo "Files changed: $CHANGED_FILES" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

DIFF_FILE="/tmp/pr_diff_${PR_NUMBER}.patch"
gh pr diff "$PR_NUMBER" --repo "$REPO" > "$DIFF_FILE" 2>&1 || echo "WARN: diff fetch failed" | tee -a "$REPORT_FILE"

echo "--- Check 1: TODO/FIXME ---" | tee -a "$REPORT_FILE"
if [[ -f "$DIFF_FILE" ]]; then
  TODO_COUNT=$(grep -cE "^\+.*(TODO|FIXME|HACK|XXX)" "$DIFF_FILE" 2>/dev/null || echo 0)
  if [[ "$TODO_COUNT" -gt 0 ]]; then
    echo "WARN: $TODO_COUNT new TODO/FIXME markers in diff" | tee -a "$REPORT_FILE"
  else
    echo "PASS: No new TODO/FIXME markers" | tee -a "$REPORT_FILE"
  fi
else
  echo "SKIP: No diff available" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

echo "--- Check 2: Hardcoded Secrets ---" | tee -a "$REPORT_FILE"
SECRETS_FOUND=0
if [[ -f "$DIFF_FILE" ]]; then
  for PATTERN in "sk-[a-zA-Z0-9]{20,}" "AKIA[0-9A-Z]{16}" "ghp_[a-zA-Z0-9]{36}" "AIza[0-9A-Za-z_-]{35}"; do
    if grep -qiE "^\+.*${PATTERN}" "$DIFF_FILE" 2>/dev/null; then
      echo "FAIL: Possible secret detected" | tee -a "$REPORT_FILE"
      SECRETS_FOUND=$((SECRETS_FOUND + 1))
    fi
  done
  if [[ "$SECRETS_FOUND" -eq 0 ]]; then
    echo "PASS: No hardcoded secrets detected" | tee -a "$REPORT_FILE"
  fi
else
  echo "SKIP: No diff available" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

echo "--- Check 3: File Size ---" | tee -a "$REPORT_FILE"
if [[ "$CHANGED_FILES" -gt 20 ]]; then
  echo "WARN: $CHANGED_FILES files changed (threshold: 20)" | tee -a "$REPORT_FILE"
else
  echo "PASS: $CHANGED_FILES files changed (ok)" | tee -a "$REPORT_FILE"
fi
TOTAL_LINES=$((ADDITIONS + DELETIONS))
if [[ "$TOTAL_LINES" -gt 500 ]]; then
  echo "WARN: Large diff ($TOTAL_LINES lines)" | tee -a "$REPORT_FILE"
else
  echo "PASS: Diff size OK ($TOTAL_LINES lines)" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

echo "--- Check 4: Test Coverage ---" | tee -a "$REPORT_FILE"
if [[ -f "$DIFF_FILE" ]]; then
  TEST_FILES=$(grep -cE "^\+\+\+ b/.*(test|spec)\." "$DIFF_FILE" 2>/dev/null || echo 0)
  SRC_FILES=$(grep -cE "^\+\+\+ b/(src|lib|app)/" "$DIFF_FILE" 2>/dev/null || echo 0)
  if [[ "$SRC_FILES" -gt 0 && "$TEST_FILES" -eq 0 ]]; then
    echo "WARN: $SRC_FILES source files changed, no tests detected" | tee -a "$REPORT_FILE"
  elif [[ "$TEST_FILES" -gt 0 ]]; then
    echo "PASS: $TEST_FILES test file(s) included" | tee -a "$REPORT_FILE"
  else
    echo "INFO: No src/ changes — test check skipped" | tee -a "$REPORT_FILE"
  fi
else
  echo "SKIP: No diff available" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

echo "--- Summary ---" | tee -a "$REPORT_FILE"
FAIL_COUNT=$(grep -c "^FAIL:" "$REPORT_FILE" 2>/dev/null || echo 0)
WARN_COUNT=$(grep -c "^WARN:" "$REPORT_FILE" 2>/dev/null || echo 0)
PASS_COUNT=$(grep -c "^PASS:" "$REPORT_FILE" 2>/dev/null || echo 0)
echo "PASS: $PASS_COUNT  WARN: $WARN_COUNT  FAIL: $FAIL_COUNT" | tee -a "$REPORT_FILE"
echo "Report written to: $REPORT_FILE"
if [[ -f "$DIFF_FILE" ]]; then unlink "$DIFF_FILE"; fi
if [[ "$FAIL_COUNT" -gt 0 ]]; then exit 2; fi
