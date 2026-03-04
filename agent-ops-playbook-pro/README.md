# Agent Ops Playbook Pro — Claude Plugin

Production operations system for AI agents. Built from months of real deployment across multiple simultaneous projects, this plugin installs the workflows, memory architecture, and failure-prevention rules that separate a toy chatbot from a production operator.

## What this plugin does

- **Sets up new agents correctly** — scaffold all required files in one command
- **Audits memory drift** — detect when project state files are out of sync with what actually happened
- **Syncs project state** — update TASKS.md and MEMORY.md with a single command, with git commit
- **Reviews operational health** — full agent ops health check on demand (daily, weekly, or full)

## Commands

| Command | What it does |
|---------|-------------|
| `/setup-agent <workspace-path> [agent-name]` | Scaffold a new agent workspace with all required files |
| `/memory-audit [project-name]` | Detect drift between daily notes and project state files |
| `/sync-project <project-name> <status-update>` | Update TASKS.md + MEMORY.md and commit |
| `/ops-review [daily\|weekly\|full]` | Full agent ops health check |

## Skills (loaded into context)

| Skill | What it covers |
|-------|---------------|
| `memory-architecture` | Three-layer memory system, read order, sync rules |
| `session-discipline` | Startup protocol, ACK→Plan→ETA→Execute→Report loop |
| `multi-project-ops` | Project isolation, session routing, write-through rules |
| `failure-postmortems` | 4 real failures with root causes and prevention rules |

## Required file structure (per agent)

```
workspace/
├── AGENTS.md          ← startup protocol + rules
├── SOUL.md            ← agent persona
├── USER.md            ← human context
├── MEMORY.md          ← global long-term memory
├── memory/
│   ├── YYYY-MM-DD.md  ← daily session logs
│   └── heartbeat-state.json
└── projects/
    └── <project-name>/
        ├── PROJECT.md
        ├── TASKS.md
        └── MEMORY.md
```

## Connectors

See `CONNECTORS.md` for MCP server setup. Commands degrade gracefully if connectors aren't available — they output file contents for manual copy-paste.

## Made by

[ClawGear](https://clawgear.io) — production AI agent infrastructure.
