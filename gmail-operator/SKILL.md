---
name: gmail-operator
description: Monitor Gmail inbox, triage emails by priority, create draft replies, and surface urgent items in heartbeat via Telegram. Includes OAuth 2.0 setup, inbox checker, triage classifier, draft creator, and heartbeat integration.
---

# Gmail Operator

Give your OpenClaw agent full Gmail access — monitor inbox, triage by priority, draft replies, and fire Telegram alerts for urgent email — all without the agent ever sending a message you didn't approve.

## What You Get

| Script | Purpose |
|---|---|
| `check_inbox.py` | List unread emails as JSON |
| `triage_email.py` | Classify emails URGENT / NORMAL / LOW |
| `draft_reply.py` | Create a Gmail draft (never sends) |
| `heartbeat_check.sh` | Cron/heartbeat wrapper with Telegram alert |
| `.gmail-config.yml` | Your whitelist, keywords, intervals |

---

## Step 1 — Create a Google Cloud OAuth 2.0 Client

You need a **Desktop app** OAuth client. Takes ~5 minutes.

### Option A: Google Cloud Console (browser)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project (or pick an existing one)
3. Enable the Gmail API:
   ```
   APIs & Services → Enable APIs → search "Gmail API" → Enable
   ```
4. Create credentials:
   ```
   APIs & Services → Credentials → Create Credentials → OAuth client ID
   Application type: Desktop app
   Name: openclaw-gmail (or anything)
   ```
5. Click **Download JSON** → save as your credentials file
6. Set the env var:
   ```bash
   export GMAIL_CREDENTIALS_PATH="$HOME/.openclaw/gmail_credentials.json"
   mv ~/Downloads/client_secret_*.json "$GMAIL_CREDENTIALS_PATH"
   ```

### Option B: gcloud CLI

```bash
# Install gcloud if needed: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud projects create openclaw-gmail-$(date +%s) --name="OpenClaw Gmail"
gcloud config set project <YOUR_PROJECT_ID>

# Enable Gmail API
gcloud services enable gmail.googleapis.com

# Create OAuth client (Desktop)
gcloud alpha iap oauth-clients create \
  projects/<YOUR_PROJECT_ID>/brands/<YOUR_BRAND> \
  --display_name="openclaw-gmail"
```

> **Note:** For most operators, Option A (browser) is faster. The Console UI gives you a ready-to-download JSON.

### Configure OAuth Consent Screen

Before your first token, set up the consent screen:
```
APIs & Services → OAuth consent screen
User Type: External (fine for personal use)
App name: OpenClaw Gmail
Developer email: your@email.com
Scopes: add "https://www.googleapis.com/auth/gmail.modify"
Test users: add your Gmail address
```

---

## Step 2 — Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pyyaml
```

---

## Step 3 — First-Time Token Auth

Run `check_inbox.py` once interactively. It will open a browser for OAuth consent and save your token:

```bash
export GMAIL_CREDENTIALS_PATH="$HOME/.openclaw/gmail_credentials.json"
python3 check_inbox.py
```

Token is saved at `~/.openclaw/gmail_token.json`. After this, all scripts run non-interactively.

---

## Step 4 — Configure `.gmail-config.yml`

Copy the example:

```bash
cp .gmail-config.yml.example ~/.openclaw/.gmail-config.yml
```

Edit to match your setup. See schema below.

---

## Step 5 — Wire Up Heartbeat

Add to your `HEARTBEAT.md`:

```
- Run: bash ~/.openclaw/workspace/skills/gmail-operator/heartbeat_check.sh
```

Or as a cron job:
```bash
# Every 15 minutes
*/15 * * * * GMAIL_CREDENTIALS_PATH=$HOME/.openclaw/gmail_credentials.json \
  TELEGRAM_BOT_TOKEN=your_token \
  bash ~/.openclaw/workspace/skills/gmail-operator/heartbeat_check.sh
```

---

## Config Schema — `.gmail-config.yml`

```yaml
# ~/.openclaw/.gmail-config.yml

sender_whitelist:
  - boss@company.com
  - alerts@pagerduty.com

urgent_keywords:
  - urgent
  - ASAP
  - critical
  - action required
  - deadline
  - payment
  - invoice
  - emergency

check_interval_minutes: 15
max_results: 20

telegram_bot_token_env: TELEGRAM_BOT_TOKEN
telegram_chat_id: "123456789"
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `sender_whitelist` | list | Senders that are always URGENT |
| `urgent_keywords` | list | Subject/body keywords that trigger URGENT |
| `check_interval_minutes` | int | Minimum minutes between heartbeat checks |
| `max_results` | int | Max emails to fetch per check (default 20) |
| `telegram_bot_token_env` | string | Name of env var holding the bot token |
| `telegram_chat_id` | string | Telegram chat ID for alerts |

---

## Usage Examples

### Check Inbox
```bash
export GMAIL_CREDENTIALS_PATH="$HOME/.openclaw/gmail_credentials.json"
python3 check_inbox.py
# Outputs JSON array of unread emails to stdout
```

### Triage
```bash
python3 triage_email.py --config ~/.openclaw/.gmail-config.yml
# Outputs triage report: each email with URGENT/NORMAL/LOW label
```

### Draft a Reply
```bash
python3 draft_reply.py \
  --thread-id "18abc123def456" \
  --body "Thanks for reaching out, I'll review and get back to you by Friday."
# Creates a draft -- does NOT send
```

### Heartbeat Check
```bash
export GMAIL_CREDENTIALS_PATH="$HOME/.openclaw/gmail_credentials.json"
export TELEGRAM_BOT_TOKEN="bot12345:AAAA..."
bash heartbeat_check.sh
```

---

## Security Notes

- **Draft only, never send** -- `draft_reply.py` uses `drafts.create`, not `messages.send`
- **Token scope** -- `gmail.modify` (read + draft). Not `gmail.send`.
- **Token file** -- `~/.openclaw/gmail_token.json` is created on first auth. Keep it out of git.
- **Credentials file** -- Set via `GMAIL_CREDENTIALS_PATH` env var, never hardcoded.

---

## Files in This Skill

```
gmail-operator/
  SKILL.md               <- this file
  check_inbox.py         <- list unread emails as JSON
  triage_email.py        <- classify emails by priority
  draft_reply.py         <- create draft reply
  heartbeat_check.sh     <- heartbeat/cron wrapper
  .gmail-config.yml.example  <- config schema example
```
