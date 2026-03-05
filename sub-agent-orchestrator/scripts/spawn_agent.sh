#!/usr/bin/env bash
# spawn_agent.sh - spawn an OpenClaw sub-agent and log it to ~/.openclaw/agents.json
# Usage: ./scripts/spawn_agent.sh <LABEL> "<TASK>" [OUTPUT_FILE]
# Required: openclaw CLI in PATH
set -euo pipefail

LABEL="${1:-}"
TASK="${2:-}"
OUTPUT_FILE="${3:-}"
AGENTS_FILE="${AGENTS_FILE:-${HOME}/.openclaw/agents.json}"

if [[ -z "$LABEL" || -z "$TASK" ]]; then
  echo "Usage: $0 <LABEL> <TASK> [OUTPUT_FILE]"
  exit 1
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
OUTPUT_FILE="${OUTPUT_FILE:-${HOME}/.openclaw/agent-results/${LABEL}.md}"
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "Spawning agent: $LABEL"
echo "Output: $OUTPUT_FILE"

FULL_TASK="${TASK}. Write your complete output to: ${OUTPUT_FILE} (Markdown format, start with # ${LABEL})."

openclaw subagent spawn \
  --label "$LABEL" \
  --prompt "$FULL_TASK" 2>&1 || {
  echo "WARN: openclaw subagent spawn returned non-zero"
}

SPAWN_TIME="$(date -u +%s)"

python3 -c "
import json, os
af = "\"
try: agents = json.load(open(af))
except: agents = []
agents = [a for a in agents if a.get("label") != "\"]
agents.append({"label": "\", "output_file": "\", "spawned_at": "\", "spawn_epoch": \, "status": "running", "collected": False})
os.makedirs(os.path.dirname(af), exist_ok=True)
open(af, "w").write(json.dumps(agents, indent=2))
print(f"Registered {len(agents)} agents in {af}")
"

echo "Done. Monitor: ./scripts/monitor_agents.sh"
