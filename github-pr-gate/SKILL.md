---
name: github-pr-gate
description: Automated PR review gate for OpenClaw coding agents. Fetches PR diffs via GitHub CLI, runs quality checks (TODO/FIXME count, hardcoded secrets scan, file size warnings, test coverage), posts structured review comments via GitHub API, and sends findings to Telegram. Use when you need automated PR review before merging agent-generated code, CI quality gates, or Telegram notifications for PR status.
---

# GitHub PR Gate

Agents shipping code via Coding Agent Loops have no automated review gate. PRs go unreviewed, regressions slip through, quality decays. This skill installs a three-script gate that catches issues before merge.

## What You Get

- **`pr_review.sh`** — fetches PR diff, runs 4 checks, writes `/tmp/pr_review_<PR>.txt`
- **`pr_gate.sh`** — reads the report, posts GitHub review (approve / comment / request changes)
- **`pr_report.sh`** — sends formatted Telegram alert with pass/warn/fail summary
- **`.pr-gate.yml` schema** — configure thresholds, blocked patterns, auto-approve rules
- **GitHub Actions workflow** — integrate the gate into CI

---

## Prerequisites

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Set required env vars
export GITHUB_TOKEN="ghp_your_token_here"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

Store these in `~/.zshenv` or your project's `.env` (never commit secrets).

---

## Quick Start

```bash
# Copy scripts to your project
cp scripts/pr_review.sh your-project/scripts/
cp scripts/pr_gate.sh your-project/scripts/
cp scripts/pr_report.sh your-project/scripts/
chmod +x your-project/scripts/pr_*.sh

# Review PR #42 in current repo
./scripts/pr_review.sh 42

# Run full gate (review + post GitHub comment)
./scripts/pr_gate.sh 42

# Send Telegram notification
./scripts/pr_report.sh 42

# Full pipeline — one command
./scripts/pr_review.sh 42 owner/repo && ./scripts/pr_gate.sh 42 owner/repo && ./scripts/pr_report.sh 42 owner/repo
```

---

## The 4 Checks

| # | Check | Pass | Warn | Fail |
|---|-------|------|------|------|
| 1 | TODO/FIXME | 0 new markers | 1–3 markers | — |
| 2 | Secrets scan | No patterns | — | Pattern match |
| 3 | File count | ≤20 files | >20 files | — |
| 4 | Test coverage | Tests included | Src changed, no tests | — |

Secrets patterns detected: `sk-*` (OpenAI), `AKIA*` (AWS), `ghp_*` (GitHub), `AIza*` (Google).

---

## Configuration: `.pr-gate.yml`

Place this in your repo root:

```yaml
# .pr-gate.yml — PR Gate configuration
max_files_changed: 20        # WARN if more files changed
max_lines_changed: 500       # WARN if diff larger than this
required_reviewers: 1        # Minimum human approvals before auto-approve
auto_approve_threshold: 0    # Auto-approve if FAIL=0 and WARN <= this value

blocked_patterns:
  - "sk-[a-zA-Z0-9]{20,}"   # OpenAI keys
  - "AKIA[0-9A-Z]{16}"      # AWS access keys
  - "ghp_[a-zA-Z0-9]{36}"   # GitHub tokens
  - "password\s*=\s*[\x27"][^\x27"]{6,}"  # Inline passwords

require_tests_for:
  - src/
  - lib/
  - app/
```

---

## GitHub Actions Integration

Add `.github/workflows/pr-gate.yml` to your repo:

```yaml
name: PR Gate
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install gh CLI
        run: |
          type -p gh >/dev/null 2>&1 || (
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
            sudo apt-get update && sudo apt-get install gh -y
          )

      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x scripts/pr_review.sh
          ./scripts/pr_review.sh "${{ github.event.pull_request.number }}" "${{ github.repository }}"

      - name: Post Gate Decision
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x scripts/pr_gate.sh
          ./scripts/pr_gate.sh "${{ github.event.pull_request.number }}" "${{ github.repository }}"

      - name: Notify Telegram
        if: always()
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          chmod +x scripts/pr_report.sh
          ./scripts/pr_report.sh "${{ github.event.pull_request.number }}" "${{ github.repository }}"
```

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in your repo Settings → Secrets.

---

## Pre-Merge Checklist

Before any agent-generated PR is merged, verify:

```
PR Pre-Merge Checklist
----------------------
[ ] pr_gate.sh exit code = 0 (no FAIL entries)
[ ] WARN count reviewed and accepted
[ ] No secrets in diff (Check 2 passed)
[ ] Tests present if src/ changed (Check 4 passed)
[ ] PR description explains what changed and why
[ ] Required reviewers approved (if configured)
[ ] Branch is up to date with main/master
[ ] CI/CD pipeline green
```

---

## Agent Integration Pattern

Wire into Coding Agent Loops by adding a post-merge hook:

```bash
# In your agent task completion handler:
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# After coding agent pushes a branch and opens a PR:
PR_NUM=$(gh pr list --head "$(git branch --show-current)" --json number -q '.[0].number')
if [[ -n "$PR_NUM" ]]; then
  "${SCRIPT_DIR}/scripts/pr_review.sh" "$PR_NUM"
  "${SCRIPT_DIR}/scripts/pr_gate.sh" "$PR_NUM"
  "${SCRIPT_DIR}/scripts/pr_report.sh" "$PR_NUM"
fi
```

---

## Useful `gh` Commands

```bash
# List open PRs
gh pr list --state open

# View PR details
gh pr view 42 --json title,additions,deletions,changedFiles

# Check PR status
gh pr status

# Merge after gate passes
gh pr merge 42 --squash --delete-branch

# List reviews on a PR
gh pr reviews 42

# View PR diff directly
gh pr diff 42
```

---

## Troubleshooting

**"gh: command not found"** — install with `brew install gh` and run `gh auth login`

**"GITHUB_TOKEN is not set"** — export it: `export GITHUB_TOKEN=$(gh auth token)`

**"HTTP 422 on review post"** — you cannot approve your own PR; use a different token or post as a comment instead

**"diff fetch failed"** — ensure `gh auth status` shows `repo` scope; re-auth with `gh auth login --scopes repo`
