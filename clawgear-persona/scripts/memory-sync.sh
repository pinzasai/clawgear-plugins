#!/bin/bash
# memory-sync.sh — Validate project memory is in sync with daily notes
# Run: bash scripts/memory-sync.sh [--fix]
# Exit codes: 0 = all synced, 1 = drift detected
#
# This script checks if today's daily notes mention projects whose
# TASKS.md/MEMORY.md haven't been updated today. It's the machine
# enforcement layer for the Memory Sync System.

set -euo pipefail

# Determine workspace root:
# 1. If WORKSPACE_ROOT is set, use it
# 2. If git is available, use repo root
# 3. Fall back to script's parent's parent dir
# 4. Last resort: ~/.openclaw/workspace
if [[ -n "${WORKSPACE_ROOT:-}" ]]; then
  WORKSPACE="$WORKSPACE_ROOT"
elif command -v git &>/dev/null && git rev-parse --show-toplevel &>/dev/null; then
  WORKSPACE="$(git rev-parse --show-toplevel)"
elif [[ -f "$(dirname "$0")/../projects/index.json" ]]; then
  WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
else
  WORKSPACE="${HOME}/.openclaw/workspace"
fi
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d 2>/dev/null || echo "")
DAILY_TODAY="${WORKSPACE}/memory/${TODAY}.md"
DAILY_YESTERDAY="${WORKSPACE}/memory/${YESTERDAY}.md"
INDEX="${WORKSPACE}/projects/index.json"
DRIFT_FOUND=0
FIX_MODE=0

if [[ "${1:-}" == "--fix" ]]; then
  FIX_MODE=1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧠 Memory Sync Validator"
echo "========================"
echo "Date: ${TODAY}"
echo ""

# Get list of project names from index.json
PROJECTS=$(cat "$INDEX" | grep '"project"' | sed 's/.*"project": *"//;s/".*//')

for PROJECT in $PROJECTS; do
  FOLDER=$(cat "$INDEX" | grep -A3 "\"project\": \"${PROJECT}\"" | grep '"folder"' | sed 's/.*"folder": *"//;s/".*//')
  TASKS_FILE="${WORKSPACE}/${FOLDER}/TASKS.md"
  MEMORY_FILE="${WORKSPACE}/${FOLDER}/MEMORY.md"
  
  # Check if today's daily notes mention this project
  MENTIONED_TODAY=0
  MENTIONED_YESTERDAY=0
  
  if [[ -f "$DAILY_TODAY" ]]; then
    # Case-insensitive search, excluding "no activity" / "no updates" lines
    MATCH=$(grep -i "${PROJECT}\|${FOLDER}" "$DAILY_TODAY" 2>/dev/null | grep -iv "no activity\|no updates\|nothing new\|skipped\|waiting for briefing" || true)
    if [[ -n "$MATCH" ]]; then
      MENTIONED_TODAY=1
    fi
  fi
  
  if [[ -n "$YESTERDAY" && -f "$DAILY_YESTERDAY" ]]; then
    MATCH=$(grep -i "${PROJECT}\|${FOLDER}" "$DAILY_YESTERDAY" 2>/dev/null | grep -iv "no activity\|no updates\|nothing new\|skipped\|waiting for briefing" || true)
    if [[ -n "$MATCH" ]]; then
      MENTIONED_YESTERDAY=1
    fi
  fi
  
  # Also check memory/*.md files from today (sub-agent outputs)
  for EXTRA in "${WORKSPACE}"/memory/${TODAY}-*.md; do
    if [[ -f "$EXTRA" ]]; then
      if grep -qi "${PROJECT}\|${FOLDER}" "$EXTRA" 2>/dev/null; then
        MENTIONED_TODAY=1
      fi
    fi
  done
  
  if [[ $MENTIONED_TODAY -eq 0 && $MENTIONED_YESTERDAY -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} ${PROJECT}: no recent activity — skipping"
    continue
  fi
  
  # Project was mentioned in daily notes — check if files are fresh
  TASKS_FRESH=0
  MEMORY_FRESH=0
  
  if [[ -f "$TASKS_FILE" ]]; then
    # Get mtime as YYYY-MM-DD (portable across macOS and Linux)
    TASKS_MTIME=$(stat -f %Sm -t %Y-%m-%d "$TASKS_FILE" 2>/dev/null || stat -c %y "$TASKS_FILE" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
    TASKS_MTIME=$(echo "$TASKS_MTIME" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
    [[ -z "$TASKS_MTIME" ]] && TASKS_MTIME="unknown"
    
    # Fresh = modified today OR yesterday (timezone tolerance between UTC sandbox and local host)
    if [[ "$TASKS_MTIME" == "$TODAY" || "$TASKS_MTIME" == "$YESTERDAY" ]]; then
      TASKS_FRESH=1
    fi
    # Also check if the file contains today's or yesterday's date as a content marker
    if grep -q "$TODAY" "$TASKS_FILE" 2>/dev/null; then
      TASKS_FRESH=1
    fi
    if [[ -n "$YESTERDAY" ]] && grep -q "$YESTERDAY" "$TASKS_FILE" 2>/dev/null; then
      TASKS_FRESH=1
    fi
  fi
  
  if [[ -f "$MEMORY_FILE" ]]; then
    MEMORY_MTIME=$(stat -f %Sm -t %Y-%m-%d "$MEMORY_FILE" 2>/dev/null || stat -c %y "$MEMORY_FILE" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
    MEMORY_MTIME=$(echo "$MEMORY_MTIME" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
    [[ -z "$MEMORY_MTIME" ]] && MEMORY_MTIME="unknown"
    
    if [[ "$MEMORY_MTIME" == "$TODAY" || "$MEMORY_MTIME" == "$YESTERDAY" ]]; then
      MEMORY_FRESH=1
    fi
    if grep -q "$TODAY" "$MEMORY_FILE" 2>/dev/null; then
      MEMORY_FRESH=1
    fi
    if [[ -n "$YESTERDAY" ]] && grep -q "$YESTERDAY" "$MEMORY_FILE" 2>/dev/null; then
      MEMORY_FRESH=1
    fi
  fi
  
  if [[ $TASKS_FRESH -eq 1 && $MEMORY_FRESH -eq 1 ]]; then
    echo -e "${GREEN}✓${NC} ${PROJECT}: mentioned in daily notes, files are fresh"
  else
    DRIFT_FOUND=1
    echo -e "${RED}✗${NC} ${PROJECT}: DRIFT DETECTED"
    if [[ $MENTIONED_TODAY -eq 1 ]]; then
      echo "  → Mentioned in today's daily notes (${TODAY})"
    fi
    if [[ $MENTIONED_YESTERDAY -eq 1 ]]; then
      echo "  → Mentioned in yesterday's daily notes (${YESTERDAY})"
    fi
    if [[ $TASKS_FRESH -eq 0 ]]; then
      echo -e "  → ${YELLOW}TASKS.md not updated today${NC} (mtime: ${TASKS_MTIME:-unknown})"
    fi
    if [[ $MEMORY_FRESH -eq 0 ]]; then
      echo -e "  → ${YELLOW}MEMORY.md not updated today${NC} (mtime: ${MEMORY_MTIME:-unknown})"
    fi
  fi
done

echo ""
if [[ $DRIFT_FOUND -eq 0 ]]; then
  echo -e "${GREEN}All project files are in sync.${NC}"
  exit 0
else
  echo -e "${RED}⚠️  MEMORY DRIFT DETECTED — project files are stale.${NC}"
  echo ""
  echo "Action required: update the stale TASKS.md and MEMORY.md files"
  echo "to reflect what's in the daily notes."
  echo ""
  echo "This means a write-through was missed during an active session."
  exit 1
fi
