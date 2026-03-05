# Connectors

## How tool references work

Plugin files use `~~category` as a placeholder for MCP tool connections. These are not hardcoded to a specific server — they map to whatever MCP server you've connected for that category.

For example, `~~filesystem` means "use whatever filesystem MCP server is configured." The `.mcp.json` in this plugin ships with recommended defaults, but you can swap in any compatible server.

## Connectors for this plugin

| Category | Placeholder | Included servers | Other options |
|----------|-------------|-----------------|---------------|
| Filesystem | `~~filesystem` | filesystem (npx @modelcontextprotocol/server-filesystem) | Any local MCP filesystem server |
| Version control | `~~git` | GitHub (api.githubcopilot.com/mcp) | GitLab, Bitbucket, self-hosted Gitea |
| Chat | `~~chat` | Slack (mcp.slack.com/mcp) | Telegram, Discord, Teams |

## When connectors are optional

Every command in this plugin gracefully degrades when a connector isn't available:

- **~~filesystem not connected:** Commands output exact file contents for manual copy-paste
- **~~git not connected:** Sync commands describe the commit without executing it
- **~~chat not connected:** Ops review is printed to Claude output only (not sent to a channel)

## Enabling connectors

1. Open Claude Code settings → MCP Servers
2. Add the server from `.mcp.json` (or your preferred alternative)
3. Authorize the connection
4. Re-run the command — it will detect the connector automatically

For Slack specifically, you'll need to authenticate via the Slack MCP OAuth flow before `~~chat` commands work.
