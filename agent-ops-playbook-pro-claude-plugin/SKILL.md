---
name: agent-ops-playbook-pro-claude-plugin
description: Claude Code plugin — production ops system for AI agents. Commands for setup, memory audit, project sync, and ops review. Includes skills for memory architecture, session discipline, multi-project isolation, and failure post-mortems. Price 29 USD. By ClawGear (clawgear.io). Version 1.0.0. Category Ops.
---

# Agent Ops Playbook Pro — Claude Plugin

The Claude Code / Claude Cowork compatible version of the Agent Ops Playbook Pro. Installs as a native Claude plugin with slash commands, knowledge skills, and MCP connector support.

Built from months of production deployment across multiple simultaneous agent projects. These aren't best guesses — they're the rules that came from real failures.

## Install

```bash
claude plugins add agent-ops-playbook-pro
```

Or in Claude Code, open the command palette and search "Add Plugin".

## What's included

### 4 Commands

| Command | What it does |
|---------|-------------|
| `/setup-agent <workspace-path> [agent-name]` | Scaffold a new agent workspace — AGENTS.md, SOUL.md, USER.md, memory directory, MEMORY.md, heartbeat-state.json |
| `/memory-audit [project-name]` | Detect drift between daily notes and project state files. Produces exact copy-paste patches. |
| `/sync-project <project-name> <status-update>` | Update TASKS.md + MEMORY.md from a free-text status update, then git commit |
| `/ops-review [daily\|weekly\|full]` | Full agent ops health check — memory sync, task queue, sub-agent results, security posture, next actions |

### 4 Skills (loaded into context)

**memory-architecture** — The three-layer memory system (project files / global MEMORY.md / daily notes), read order, when to write to each layer, project isolation rules, and the 6 memory sync rules that prevent state loss.

**session-discipline** — Startup protocol, context window management, sub-agent decision criteria, the ACK-Plan-ETA-Execute-Report loop, phantom ETA rule, heartbeat discipline, and close-the-loop requirement.

**multi-project-ops** — Project file structure (PROJECT.md/TASKS.md/MEMORY.md), session routing by channel/group ID, context isolation rules, the write-through rule for every state change, sync checkpoint checklist, and project transition handling.

**failure-postmortems** — Four real production failures with specific root causes and prevention rules: credential loss (token received but not written), memory drift (sub-agent results not synced), exec lockout (wrong host config), and Google account lockout cascading to GitHub and NPM.

## MCP Connectors

The plugin ships with `.mcp.json` configured for:
- **filesystem** — for file read/write in commands
- **github** — for git operations in `/sync-project`
- **slack** — for sending ops review summaries via `/ops-review full`

All commands degrade gracefully without connectors — they output exact file contents for manual copy-paste when filesystem MCP is not available.

See `CONNECTORS.md` for swapping in alternative MCP servers.

## Made by

ClawGear — production AI agent infrastructure. https://clawgear.io
