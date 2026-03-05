#!/usr/bin/env bash
# publish.sh -- Master content publisher for multi-platform-publisher skill.
#
# Reads frontmatter from a markdown file and publishes to configured platforms.
#
# Usage:
#   bash publish.sh [--dry-run] content.md
#
# Platforms are determined by the `platforms:` field in frontmatter.
# Supported: devto, twitter, telegram, notion
#
# Required env vars depend on platform (see SKILL.md):
#   DEVTO_API_KEY, TWITTER_AUTH_TOKEN, TWITTER_CT0,
#   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NOTION_API_KEY, NOTION_DATABASE_ID

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false
CONTENT_FILE=""

# Parse arguments
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      ;;
    *)
      CONTENT_FILE="$arg"
      ;;
  esac
done

if [ -z "$CONTENT_FILE" ]; then
  echo "Usage: bash publish.sh [--dry-run] <content.md>" >&2
  exit 1
fi

if [ ! -f "$CONTENT_FILE" ]; then
  echo "Error: File not found: $CONTENT_FILE" >&2
  exit 1
fi

# Extract platforms from frontmatter using python
PLATFORMS=$(python3 - << INNER_PYEOF
import sys
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

with open("$CONTENT_FILE", "r") as f:
    text = f.read()

lines = text.splitlines()
if not lines or lines[0].strip() != "---":
    print("")
    sys.exit(0)

end = None
for i in range(1, len(lines)):
    if lines[i].strip() == "---":
        end = i
        break

if end is None:
    print("")
    sys.exit(0)

fm_text = "\n".join(lines[1:end])

if HAS_YAML:
    fm = yaml.safe_load(fm_text) or {}
else:
    fm = {}

platforms = fm.get("platforms", [])
if isinstance(platforms, list):
    print(" ".join(str(p) for p in platforms))
elif isinstance(platforms, str):
    print(platforms)
INNER_PYEOF
)

if [ -z "$PLATFORMS" ]; then
  echo "Error: No 'platforms:' field found in frontmatter" >&2
  echo "Add 'platforms: [devto, twitter, telegram, notion]' to your markdown frontmatter" >&2
  exit 1
fi

TITLE=$(python3 - << INNER_PYEOF
try:
    import yaml
    with open("$CONTENT_FILE") as f:
        text = f.read()
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end:
        fm = yaml.safe_load("\n".join(lines[1:end])) or {}
        print(fm.get("title", "$CONTENT_FILE"))
    else:
        print("$CONTENT_FILE")
except Exception:
    print("$CONTENT_FILE")
INNER_PYEOF
)

DRY_FLAG=""
if [ "$DRY_RUN" = "true" ]; then
  DRY_FLAG="--dry-run"
  echo "[publisher] DRY RUN mode -- nothing will be posted"
fi

echo "[publisher] Publishing: $TITLE"
echo "[publisher] Platforms: $PLATFORMS"
echo "[publisher] File: $CONTENT_FILE"
echo ""

RESULTS=()
ERRORS=()

for platform in $PLATFORMS; do
  echo "[publisher] --- $platform ---"
  case "$platform" in
    devto)
      if python3 "$SKILL_DIR/publish_devto.py" $DRY_FLAG "$CONTENT_FILE"; then
        RESULTS+=("devto:ok")
      else
        ERRORS+=("devto")
        echo "[publisher] WARNING: devto publish failed" >&2
      fi
      ;;
    twitter)
      if python3 "$SKILL_DIR/publish_twitter.py" $DRY_FLAG "$CONTENT_FILE"; then
        RESULTS+=("twitter:ok")
      else
        ERRORS+=("twitter")
        echo "[publisher] WARNING: twitter publish failed" >&2
      fi
      ;;
    telegram)
      if python3 "$SKILL_DIR/publish_telegram.py" $DRY_FLAG "$CONTENT_FILE"; then
        RESULTS+=("telegram:ok")
      else
        ERRORS+=("telegram")
        echo "[publisher] WARNING: telegram publish failed" >&2
      fi
      ;;
    notion)
      if python3 "$SKILL_DIR/publish_notion.py" $DRY_FLAG "$CONTENT_FILE"; then
        RESULTS+=("notion:ok")
      else
        ERRORS+=("notion")
        echo "[publisher] WARNING: notion publish failed" >&2
      fi
      ;;
    *)
      echo "[publisher] WARNING: Unknown platform '$platform' -- skipping" >&2
      ERRORS+=("$platform:unknown")
      ;;
  esac
  echo ""
done

echo "[publisher] === SUMMARY ==="
echo "[publisher] Succeeded: ${RESULTS[*]:-none}"
if [ ${#ERRORS[@]} -gt 0 ]; then
  echo "[publisher] Failed: ${ERRORS[*]}"
  exit 1
else
  echo "[publisher] All platforms succeeded."
fi
