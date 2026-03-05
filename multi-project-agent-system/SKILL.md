---
name: multi-project-agent-system
description: Full multi-project orchestration system for OpenClaw agents. Isolates context per project, prevents memory drift, and routes Telegram/Discord sessions to the right project automatically. Includes scaffolding scripts, memory sync validator, and git pre-commit hooks.
metadata:
  version: 1.0.0
  author: ClawGear
  category: Ops
  tags: [multi-project, memory, orchestration, telegram, heartbeat]
  price: 29
---

# Multi-Project Agent System

**Type:** Ops  
**Version:** 1.0.0  
**Price:** $29

Operators running multiple projects suffer from the same failure pattern: context bleeds between projects, tasks get lost mid-session, and memory drifts until no one knows what state anything is in. This skill fixes that with a complete, enforced multi-project system built from production use running 4 simultaneous projects.

The scripts are the product. Install this and you get a system that enforces isolation, catches drift, and routes the right agent context to the right channel — automatically.

---

## What You Get

- **`init_project.sh`** — Scaffold a new project in 1 command (PROJECT.md, TASKS.md, MEMORY.md + channel registration)
- **`memory_sync.sh`** — Validate project file freshness against daily notes; catch drift before it compounds
- **`pre-commit`** — Git hook that blocks commits when project files are stale
- **`route_session.sh`** — Map a Telegram/Discord group ID to its project context files
- **Context isolation rules** — What goes where, enforced by convention and validator
- **Heartbeat integration** — heartbeat-state.json task queue pattern for autonomous project work

---

## Quick Start

```bash
# 1. Copy scripts to your workspace
cp scripts/init_project.sh ~/your-workspace/scripts/
cp scripts/memory_sync.sh ~/your-workspace/scripts/
cp scripts/route_session.sh ~/your-workspace/scripts/
chmod +x ~/your-workspace/scripts/*.sh

# 2. Install the git pre-commit hook
cp scripts/pre-commit ~/your-workspace/.git/hooks/pre-commit
chmod +x ~/your-workspace/.git/hooks/pre-commit

# 3. Scaffold your first project
cd ~/your-workspace
./scripts/init_project.sh my-saas -5195996657

# 4. Run the memory sync validator
./scripts/memory_sync.sh

# 5. Route a session to a project
./scripts/route_session.sh -5195996657
```

That's it. Your project is isolated, tracked, and ready.

---

## Architecture

### Directory Layout

```
workspace/
  projects/
    index.json                     <- group ID to project folder mapping
    my-saas/
      PROJECT.md                   <- what the project is, goals, current status
      TASKS.md                     <- active / in-progress / done tasks
      MEMORY.md                    <- project-specific decisions and context
    another-project/
      PROJECT.md
      TASKS.md
      MEMORY.md
  memory/
    2026-03-01.md                  <- daily raw session logs
    heartbeat-state.json           <- task queue + last-check timestamps
  scripts/
    init_project.sh
    memory_sync.sh
    route_session.sh
  MEMORY.md                        <- global agent memory (main session only)
  AGENTS.md                        <- session startup protocol
```

### Context Isolation Rules

| What | Where | Who reads it |
|------|-------|--------------|
| Project goals, status, phase | `projects/<name>/PROJECT.md` | Group session for that project |
| Active/done tasks | `projects/<name>/TASKS.md` | Group session + heartbeat |
| Project decisions, credentials, key facts | `projects/<name>/MEMORY.md` | Group session for that project |
| Global agent persona, cross-project lessons | `MEMORY.md` (root) | Main session ONLY |
| Raw session logs, running commentary | `memory/YYYY-MM-DD.md` | Supplementary only |
| Task queue for autonomous work | `memory/heartbeat-state.json` | Heartbeat only |

**Hard rules:**
1. A group session for Project A NEVER reads Project B's files
2. Global `MEMORY.md` is NEVER loaded in group sessions — it may contain private context
3. Daily notes are a raw log, not the source of truth. Project files are authoritative.
4. Every state change writes through immediately — not at the next heartbeat

---

## Feature: Project Scaffolding

Run `init_project.sh <name> [group_id]` to create a complete project skeleton.

**What it creates:**
- `projects/<name>/PROJECT.md` — filled with template sections
- `projects/<name>/TASKS.md` — empty task list with correct structure
- `projects/<name>/MEMORY.md` — empty memory file with header
- Updates `projects/index.json` with the group ID to project mapping

---

## Feature: Memory Sync Validator

`memory_sync.sh` scans daily notes for project mentions and cross-checks against project file modification times. If daily notes reference work that happened after the project files were last updated, drift is detected and the script exits 1.

**Exit codes:**
- `0` — All project files are in sync
- `1` — Drift detected (one or more projects have stale files)

---

## Feature: Git Pre-Commit Hook

`pre-commit` runs `memory_sync.sh` before every commit. If drift is detected, the commit is blocked with an explanation. Forces the agent to sync project files before the codebase can be committed.

```
Error: Memory sync failed — stale project files detected.
Run ./scripts/memory_sync.sh to see what's out of date, then update TASKS.md / MEMORY.md.
```

---

## Feature: Session Routing

`route_session.sh` takes a channel group ID and outputs shell variables pointing to that project's files. Source the output at session startup to load the right context.

```bash
$ ./scripts/route_session.sh -5195996657
PROJECT=my-saas
PROJECT_MD=projects/my-saas/PROJECT.md
TASKS_MD=projects/my-saas/TASKS.md
MEMORY_MD=projects/my-saas/MEMORY.md
PROJECT_DIR=/workspace/projects/my-saas

# In session startup:
eval "$(./scripts/route_session.sh "$GROUP_ID")"
# Now $PROJECT, $PROJECT_MD, $TASKS_MD, $MEMORY_MD are set
```

---

## Feature: Heartbeat Task Queue

`memory/heartbeat-state.json` tracks when each periodic check last ran and holds a task queue for work to pick up next heartbeat.

```json
{
  "lastChecks": {
    "email": 1709500000,
    "calendar": 1709500000,
    "weather": null,
    "my-saas": 1709500000
  },
  "taskQueue": [
    {
      "project": "my-saas",
      "task": "Run the build and report status",
      "priority": "high",
      "addedAt": 1709500000,
      "addedBy": "group-session"
    }
  ]
}
```

When a group session identifies async work: append a task to `taskQueue`. At next heartbeat the main agent executes it, posts results to the right channel, and clears the completed item.

---

## Scripts

### `scripts/init_project.sh`

```bash
#!/usr/bin/env bash
# init_project.sh — scaffold a new project
# Usage: ./scripts/init_project.sh <name> [telegram_group_id]
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:-}"
GROUP_ID="${2:-}"
DATE="$(date +%Y-%m-%d)"

if [[ -z "$NAME" ]]; then
  echo "Usage: $0 <project-name> [telegram_group_id]" >&2
  exit 1
fi

if ! echo "$NAME" | grep -qE '^[a-z0-9][a-z0-9-]*[a-z0-9]$'; then
  echo "Error: project name must be lowercase with hyphens (e.g. my-saas)" >&2
  exit 1
fi

PROJECT_DIR="$WORKSPACE_DIR/projects/$NAME"
INDEX_FILE="$WORKSPACE_DIR/projects/index.json"

if [[ -d "$PROJECT_DIR" ]]; then
  echo "Project '$NAME' already exists at $PROJECT_DIR" >&2
  exit 1
fi

echo "Creating project: $NAME"
mkdir -p "$PROJECT_DIR"

cat > "$PROJECT_DIR/PROJECT.md" << EOF
# $NAME

Created: $DATE
Status: Active
Phase: Setup

## What This Is

[Describe the project in 2-3 sentences]

## Goals

- [ ] [Primary goal]
- [ ] [Secondary goal]

## Key Context

- **Stack:** [tech stack]
- **Audience:** [who this serves]

## Channel

Telegram group: ${GROUP_ID:-[add group ID]}

## Current Status

[What is happening right now]
EOF

cat > "$PROJECT_DIR/TASKS.md" << EOF
# $NAME Tasks

Last updated: $DATE

## Active

- [ ] [First task]

## In Progress

## Blocked

## Done

EOF

cat > "$PROJECT_DIR/MEMORY.md" << EOF
# $NAME Memory

Last updated: $DATE

## Key Decisions

## Credentials and Config

(Store references here, not raw values)

## Lessons Learned

EOF

echo "Created $PROJECT_DIR/"

mkdir -p "$WORKSPACE_DIR/projects"
if [[ ! -f "$INDEX_FILE" ]]; then
  echo '{}' > "$INDEX_FILE"
fi

if command -v python3 &>/dev/null; then
  python3 - "$INDEX_FILE" "$NAME" "$GROUP_ID" << 'PYEOF'
import json, sys
index_file, name, group_id = sys.argv[1], sys.argv[2], sys.argv[3]
with open(index_file) as f:
    index = json.load(f)
index[name] = {"folder": f"projects/{name}", "groupId": group_id if group_id else None}
if group_id:
    index[f"group:{group_id}"] = name
with open(index_file, "w") as f:
    json.dump(index, f, indent=2)
    f.write("\n")
print(f"Updated {index_file}")
PYEOF
else
  echo "Warning: python3 not found. Update projects/index.json manually." >&2
fi

echo ""
echo "Project '$NAME' is ready."
if [[ -n "$GROUP_ID" ]]; then
  echo "Telegram group $GROUP_ID maps to projects/$NAME"
fi
```

### `scripts/memory_sync.sh`

```bash
#!/usr/bin/env bash
# memory_sync.sh — validate project file freshness against daily notes
# Usage: ./scripts/memory_sync.sh [project-name]
# Exit 0 = synced, Exit 1 = drift detected
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECTS_DIR="$WORKSPACE_DIR/projects"
MEMORY_DIR="$WORKSPACE_DIR/memory"
FILTER_PROJECT="${1:-}"
DRIFT_FOUND=0
TODAY="$(date +%Y-%m-%d)"

# Cross-platform yesterday
if date -v-1d +%Y-%m-%d &>/dev/null 2>&1; then
  YESTERDAY="$(date -v-1d +%Y-%m-%d)"
else
  YESTERDAY="$(date -d 'yesterday' +%Y-%m-%d 2>/dev/null || echo '')"
fi

get_mtime() {
  local file="$1"
  if stat -f "%m" "$file" &>/dev/null 2>&1; then
    stat -f "%m" "$file"
  else
    stat -c "%Y" "$file" 2>/dev/null || echo 0
  fi
}

date_to_epoch() {
  local d="$1"
  if date -j -f "%Y-%m-%d" "$d" "+%s" &>/dev/null 2>&1; then
    date -j -f "%Y-%m-%d" "$d" "+%s"
  elif date -d "$d" "+%s" &>/dev/null 2>&1; then
    date -d "$d" "+%s"
  else
    echo 0
  fi
}

check_project() {
  local project_name="$1"
  local project_dir="$PROJECTS_DIR/$project_name"

  [[ ! -d "$project_dir" ]] && return 0

  local latest_mention_date=""
  for note_date in "$TODAY" "$YESTERDAY"; do
    [[ -z "$note_date" ]] && continue
    local note_file="$MEMORY_DIR/$note_date.md"
    if [[ -f "$note_file" ]] && grep -qi "$project_name" "$note_file" 2>/dev/null; then
      latest_mention_date="$note_date"
      break
    fi
  done

  if [[ -z "$latest_mention_date" ]]; then
    echo "  $project_name — no recent daily note mention, skipping"
    return 0
  fi

  local note_epoch
  note_epoch="$(date_to_epoch "$latest_mention_date")"

  local stale_files=()

  for fname in TASKS.md MEMORY.md; do
    local fpath="$project_dir/$fname"
    if [[ -f "$fpath" ]]; then
      local fmtime
      fmtime="$(get_mtime "$fpath")"
      if [[ "$fmtime" -lt "$note_epoch" ]]; then
        stale_files+=("$fname")
      fi
    else
      stale_files+=("$fname (missing)")
    fi
  done

  if [[ ${#stale_files[@]} -gt 0 ]]; then
    echo "DRIFT: $project_name — mentioned on $latest_mention_date but stale: ${stale_files[*]}"
    DRIFT_FOUND=1
  else
    echo "OK: $project_name — in sync (last mention: $latest_mention_date)"
  fi
}

if [[ ! -d "$PROJECTS_DIR" ]]; then
  echo "No projects directory at $PROJECTS_DIR"
  exit 0
fi

echo "Memory Sync Check — $(date '+%Y-%m-%d %H:%M')"
echo "---"

if [[ -n "$FILTER_PROJECT" ]]; then
  check_project "$FILTER_PROJECT"
else
  found_any=0
  for project_dir in "$PROJECTS_DIR"/*/; do
    [[ -d "$project_dir" ]] || continue
    project_name="$(basename "$project_dir")"
    check_project "$project_name"
    found_any=1
  done
  if [[ $found_any -eq 0 ]]; then
    echo "No projects found. Run init_project.sh to create one."
  fi
fi

echo "---"
if [[ $DRIFT_FOUND -eq 1 ]]; then
  echo "FAIL: Drift detected. Update project files before committing."
  exit 1
else
  echo "PASS: All project files are in sync."
  exit 0
fi
```

### `scripts/pre-commit`

```bash
#!/usr/bin/env bash
# Git pre-commit hook — block commits when project files are stale
# Install: cp scripts/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_SYNC="$SCRIPT_DIR/../../scripts/memory_sync.sh"

if [[ ! -f "$MEMORY_SYNC" ]]; then
  # Try relative to repo root
  MEMORY_SYNC="$(git rev-parse --show-toplevel 2>/dev/null)/scripts/memory_sync.sh"
fi

if [[ -f "$MEMORY_SYNC" ]]; then
  if ! bash "$MEMORY_SYNC" > /tmp/memory_sync_output.txt 2>&1; then
    echo ""
    echo "ERROR: Memory sync failed — stale project files detected."
    echo ""
    cat /tmp/memory_sync_output.txt
    echo ""
    echo "Update TASKS.md / MEMORY.md for the projects listed above, then commit again."
    echo "To bypass (not recommended): add --no-verify flag to git commit"
    [ -f /tmp/memory_sync_output.txt ] && unlink /tmp/memory_sync_output.txt
    exit 1
  fi
  [ -f /tmp/memory_sync_output.txt ] && unlink /tmp/memory_sync_output.txt
fi

exit 0
```

### `scripts/route_session.sh`

```bash
#!/usr/bin/env bash
# route_session.sh — map a group ID to its project context files
# Usage: ./scripts/route_session.sh <group_id>
# Outputs shell variables — eval the output to load project paths
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INDEX_FILE="$WORKSPACE_DIR/projects/index.json"
GROUP_ID="${1:-}"

if [[ -z "$GROUP_ID" ]]; then
  echo "Usage: $0 <group_id>" >&2
  exit 1
fi

if [[ ! -f "$INDEX_FILE" ]]; then
  echo "# No projects/index.json found. Run init_project.sh first." >&2
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "# python3 required" >&2
  exit 1
fi

python3 - "$INDEX_FILE" "$GROUP_ID" "$WORKSPACE_DIR" << 'PYEOF'
import json, sys

index_file, group_id, workspace = sys.argv[1], sys.argv[2], sys.argv[3]

with open(index_file) as f:
    index = json.load(f)

key = f"group:{group_id}"
if key not in index:
    print(f"# No project mapped to group ID: {group_id}", file=sys.stderr)
    print(f"# Add it: ./scripts/init_project.sh <name> {group_id}", file=sys.stderr)
    sys.exit(1)

project_name = index[key]
project_info = index.get(project_name, {})
folder = project_info.get("folder", f"projects/{project_name}")

print(f"PROJECT={project_name}")
print(f"PROJECT_MD={folder}/PROJECT.md")
print(f"TASKS_MD={folder}/TASKS.md")
print(f"MEMORY_MD={folder}/MEMORY.md")
print(f"PROJECT_DIR={workspace}/{folder}")
PYEOF
```

---

## Configuration

### `projects/index.json` format

```json
{
  "my-saas": {
    "folder": "projects/my-saas",
    "groupId": "-5195996657"
  },
  "group:-5195996657": "my-saas",
  "another-project": {
    "folder": "projects/another-project",
    "groupId": "-5267334417"
  },
  "group:-5267334417": "another-project"
}
```

### AGENTS.md addition for group sessions

```markdown
## Group Session Startup

1. Get the group ID from the channel context
2. Run: eval "$(./scripts/route_session.sh GROUP_ID_HERE)"
3. Read $PROJECT_MD for goals and phase
4. Read $TASKS_MD for what is active and done
5. Read $MEMORY_MD for project-specific decisions
6. Do NOT read global MEMORY.md in group sessions
```

---

## Examples

### Scaffold a project

```bash
$ ./scripts/init_project.sh clawarmor -5066079193
Creating project: clawarmor
Created /workspace/projects/clawarmor/
Updated /workspace/projects/index.json

Project 'clawarmor' is ready.
Telegram group -5066079193 maps to projects/clawarmor
```

### Sync validator output

```bash
$ ./scripts/memory_sync.sh
Memory Sync Check — 2026-03-03 21:00
---
OK: clawarmor — in sync (last mention: 2026-03-03)
DRIFT: my-saas — mentioned on 2026-03-03 but stale: TASKS.md
---
FAIL: Drift detected. Update project files before committing.
```

### Session routing

```bash
$ eval "$(./scripts/route_session.sh -5066079193)"
$ echo $PROJECT
clawarmor
$ echo $TASKS_MD
projects/clawarmor/TASKS.md
```

---

## Troubleshooting

**route_session.sh says no project mapped**
The group ID is not in index.json. Run `init_project.sh <name> <group_id>` to register it.

**Memory sync always passes but files are clearly stale**
The daily note does not mention the project name. Check your daily note for that date contains the project folder name (case-insensitive). If you abbreviated it, memory_sync.sh won't find it.

**Pre-commit hook not running**
Run `chmod +x .git/hooks/pre-commit` and verify the hook file exists.

**date command errors on Linux**
The script uses `date -v-1d` for macOS and falls back to `date -d yesterday` for Linux. If neither works, set `YESTERDAY` manually before calling the script.
