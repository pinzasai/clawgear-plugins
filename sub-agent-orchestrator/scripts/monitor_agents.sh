#!/usr/bin/env bash
# monitor_agents.sh - show status of tracked sub-agents
# Usage: ./scripts/monitor_agents.sh
set -euo pipefail
AGENTS_FILE="${AGENTS_FILE:-${HOME}/.openclaw/agents.json}"
if [[ ! -f "$AGENTS_FILE" ]]; then
  echo "No agents registry. Spawn agents first with spawn_agent.sh"
  exit 0
fi
echo "=== Sub-Agent Status ==="
echo "Time: $(date -u +%Y-%m-%d\ %H:%M\ UTC)"
python3 - "$AGENTS_FILE" << PYSCRIPT
import sys,json,os
from datetime import datetime,timezone
f=sys.argv[1]
try: agents=json.load(open(f))
except: agents=[]
if not agents: print("No agents registered."); exit()
now=datetime.now(timezone.utc).timestamp()
w=max(len(a.get("label","")) for a in agents)+2
print(f" {chr(76):<{w}} {chr(83):<12} {chr(65):>8}  Output")
print(" "+"-"*70)
for a in agents:
    lbl=a.get("label","?"); st=a.get("status","?"); out=a.get("output_file","")
    ep=a.get("spawn_epoch",0); age=int(now-ep) if ep else 0
    ag=f"{age//3600}h{(age%3600)//60}m" if age>3600 else f"{age//60}m{age%60}s"
    m="+" if os.path.exists(out) else "."
    if os.path.exists(out) and st=="running": st="done?"
    print(f" {lbl:<{w}} {st:<12} {ag:>8}  {m} {out}")
r=sum(1 for a in agents if a.get("status")=="running")
print(f"Total:{len(agents)}  Running:{r}")
PYSCRIPT
if command -v openclaw >/dev/null 2>&1; then
  echo ""
  openclaw subagent list 2>/dev/null || echo "(openclaw subagent list unavailable)"
fi
