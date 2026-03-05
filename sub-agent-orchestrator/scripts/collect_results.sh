#!/usr/bin/env bash
# collect_results.sh - read sub-agent output files and report done/pending/failed
# Usage: ./scripts/collect_results.sh [LABEL]
set -euo pipefail
AGENTS_FILE="${AGENTS_FILE:-${HOME}/.openclaw/agents.json}"
TARGET="${1:-}"
if [[ ! -f "$AGENTS_FILE" ]]; then echo "No agents registry found."; exit 1; fi
echo "=== Collecting Results ==="
echo "Time: $(date -u +%Y-%m-%d\ %H:%M\ UTC)"
python3 - "$AGENTS_FILE" "$TARGET" << PYSCRIPT
import sys,json,os
af,target=sys.argv[1],sys.argv[2]
try: agents=json.load(open(af))
except Exception as e: print(f"ERROR: {e}"); sys.exit(1)
subset=[a for a in agents if a.get("label")==target] if target else agents
if target and not subset: print(f"ERROR: No agent: {target}"); sys.exit(1)
done,pending,failed=[],[],[]
for a in subset:
    lbl=a.get("label","?"); out=a.get("output_file","")
    if not out: print(f"[FAILED]  {lbl}: no output_file"); failed.append(lbl); continue
    if os.path.exists(out):
        sz=os.path.getsize(out)
        if sz<10: print(f"[FAILED]  {lbl}: empty ({sz}b) {out}"); failed.append(lbl)
        else:
            print(f"[DONE]    {lbl}: {sz}b {out}")
            lines=open(out).readlines()[:3]
            for l in lines:
                if l.strip(): print(f"          > {l.rstrip()}")
            done.append(lbl); a["status"]="collected"; a["collected"]=True
    else: print(f"[PENDING] {lbl}: waiting for {out}"); pending.append(lbl)
seen={a.get("label") for a in subset}
merged=[a for a in agents if a.get("label") not in seen]+subset
open(af,"w").write(json.dumps(merged,indent=2))
print(f"Summary: {len(done)} done, {len(pending)} pending, {len(failed)} failed")
if failed: sys.exit(1)
PYSCRIPT
