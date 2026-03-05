---
name: sub-agent-orchestrator
description: Working mechanics for spawning, monitoring, and collecting results from OpenClaw sub-agents. Includes spawn_agent.sh, monitor_agents.sh, and collect_results.sh scripts plus the 5-phase orchestration loop, parallel vs sequential spawn patterns, result file templates, and a real example of 5 parallel research agents. Use when coordinating multi-agent workflows, running parallel research tasks, or collecting outputs from background sub-agents.
---

# Sub-Agent Orchestrator

Most multi-agent skills are theory. This one ships working code.

Three scripts. One pattern. Real mechanics for spawning, monitoring, and collecting results from OpenClaw sub-agents.

## What You Get

- **`spawn_agent.sh`** — spawn a sub-agent with label, configure output path, register in `~/.openclaw/agents.json`
- **`monitor_agents.sh`** — poll active agents, show status table with age and output file presence
- **`collect_results.sh`** — read output files, report done/pending/failed, update registry
- **5-phase orchestration loop** — Plan → Spawn → Monitor → Collect → Sync
- **Parallel vs sequential patterns** with decision criteria
- **Real example**: 5 parallel research agents

---

## Quick Start

```bash
# Copy scripts
cp scripts/spawn_agent.sh your-workspace/scripts/
cp scripts/monitor_agents.sh your-workspace/scripts/
cp scripts/collect_results.sh your-workspace/scripts/
chmod +x your-workspace/scripts/*.sh

# Spawn an agent
./scripts/spawn_agent.sh research-openai \
  "Research OpenAI pricing for GPT-4o and o3-mini models" \
  ~/.openclaw/agent-results/research-openai.md

# Check status
./scripts/monitor_agents.sh

# Collect when done
./scripts/collect_results.sh
```

---

## The 5-Phase Orchestration Loop

### Phase 1: Plan

Define the task decomposition before spawning anything.

```
Parent task: Research competitor pricing

Subtasks:
  research-openai    - OpenAI model pricing table
  research-anthropic - Anthropic model pricing table
  research-google    - Google Gemini pricing table
  research-mistral   - Mistral pricing table
  research-groq      - Groq pricing table

Output format: Each agent writes Markdown to:
  ~/.openclaw/agent-results/<label>.md
```

### Phase 2: Spawn

```bash
LABELS=(research-openai research-anthropic research-google research-mistral research-groq)
TASKS=(
  "Research current OpenAI API pricing for GPT-4o, GPT-4o-mini, o1, o3-mini"
  "Research current Anthropic API pricing for Claude Sonnet, Haiku, Opus"
  "Research current Google Gemini API pricing for Gemini 1.5 Pro, Flash"
  "Research current Mistral API pricing for all production models"
  "Research current Groq API pricing and available models"
)

for i in "${!LABELS[@]}"; do
  ./scripts/spawn_agent.sh \
    "${LABELS[i]}" \
    "${TASKS[i]}" \
    "${HOME}/.openclaw/agent-results/${LABELS[i]}.md"
  echo "Spawned: ${LABELS[i]}"
done
```

### Phase 3: Monitor

```bash
# Poll until all agents finish
MAX_POLLS=30
for attempt in $(seq 1 $MAX_POLLS); do
  ./scripts/monitor_agents.sh 2>&1 | tee /tmp/monitor_out.txt
  PENDING=$(grep -c "PENDING" /tmp/monitor_out.txt 2>/dev/null || echo 0)
  if [[ "$PENDING" -eq 0 ]]; then
    echo "All agents complete."
    break
  fi
  echo "Poll $attempt/$MAX_POLLS: $PENDING pending. Waiting 60s..."
  sleep 60
done
```

### Phase 4: Collect

```bash
./scripts/collect_results.sh

# Aggregate all outputs
AGGREGATE="${HOME}/.openclaw/agent-results/AGGREGATE.md"
echo "# Competitor Pricing Research" > "$AGGREGATE"
echo "Generated: $(date -u +'%Y-%m-%d %H:%M UTC')" >> "$AGGREGATE"

for LABEL in research-openai research-anthropic research-google research-mistral research-groq; do
  FILE="${HOME}/.openclaw/agent-results/${LABEL}.md"
  if [[ -f "$FILE" ]]; then
    echo "" >> "$AGGREGATE"
    cat "$FILE" >> "$AGGREGATE"
  fi
done
echo "Aggregated to: $AGGREGATE"
```

### Phase 5: Sync

After collecting:
- Read `AGGREGATE.md` and summarize key findings
- Update project `TASKS.md`: move task to Done with date
- Update project `MEMORY.md`: store key decisions from output
- Report to operator via Telegram DM

---

## Result File Template

Every sub-agent MUST write output in this format:

```markdown
# <agent-label>

## Summary
2-3 sentence summary of findings. Most important info first.

## Findings
Detailed results here.

## Status
completed | partial | failed

## Completed At
2026-03-03T21:30:00Z
```

The `collect_results.sh` script validates the file exists and is non-empty.
The parent reads `## Summary` for the quick answer and `## Findings` for depth.

---

## Parallel vs Sequential: Decision Criteria

**Use parallel when:**
- Tasks are independent (no subtask depends on another)
- Research or gather tasks (same class of work per agent)
- Time is the constraint (5 agents = ~5x faster)
- Output files are separate (no write conflicts)

**Use sequential when:**
- Subtask N needs output of subtask N-1
- Building on prior results (code review → fix → re-review)
- Budget is tight (sequential burns fewer total tokens)

**Decision rule:**
```
if tasks_are_independent AND time_matters:  spawn_parallel
elif tasks_depend_on_each_other:            spawn_sequential
elif budget_is_tight:                       spawn_sequential
else:                                       spawn_parallel  # default
```

---

## Error Handling

**Sub-agent never writes output (timeout):**
```bash
# collect_results.sh shows PENDING for it
# Re-spawn with same label (replaces registry entry)
./scripts/spawn_agent.sh research-openai "Research OpenAI pricing (retry)"
```

**Output file empty or corrupt:**
```bash
# collect_results.sh marks it FAILED
cat ~/.openclaw/agent-results/research-openai.md
# Re-spawn if content is bad
./scripts/spawn_agent.sh research-openai "Research OpenAI pricing (re-run)"
```

**openclaw subagent spawn fails:**
```bash
openclaw gateway status
openclaw gateway start   # if stopped
./scripts/spawn_agent.sh <label> "<task>"
```

**All agents stuck in running:**
```bash
openclaw subagent list
ls ~/.openclaw/agent-results/
./scripts/collect_results.sh   # may detect completed files
```

---

## `agents.json` Schema

Registry at `~/.openclaw/agents.json`:

```json
[
  {
    "label":       "research-openai",
    "task":        "Research OpenAI API pricing...",
    "output_file": "/Users/you/.openclaw/agent-results/research-openai.md",
    "spawned_at":  "2026-03-03T21:00:00Z",
    "spawn_epoch": 1741042800,
    "status":      "collected",
    "collected":   true
  }
]
```

Status lifecycle: `running` → `done?` (file appeared) → `collected` (parent read it) | `failed`

---

## Useful Commands

```bash
# List active subagents
openclaw subagent list

# Check all result files
ls -la ~/.openclaw/agent-results/

# Watch a result as it is written
tail -f ~/.openclaw/agent-results/research-openai.md

# Clear registry (all tracking lost)
echo "[]" > ~/.openclaw/agents.json
```
