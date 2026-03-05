---
name: multi-platform-publisher
description: Publish a single markdown file to multiple platforms simultaneously -- Dev.to, Twitter/X, Telegram, and Notion. Supports dry-run mode, frontmatter-driven platform selection, and thread splitting for Twitter.
---

# Multi-Platform Publisher

Write once, publish everywhere. Feed the skill a markdown file with frontmatter, and it distributes your content to the platforms you choose -- Dev.to, Twitter/X, Telegram, and Notion.

## What You Get

| Script | Purpose |
|---|---|
| `publish.sh` | Master orchestrator -- runs selected publishers |
| `publish_devto.py` | Post article to Dev.to |
| `publish_twitter.py` | Post thread to Twitter/X |
| `publish_telegram.py` | Post to Telegram channel/group |
| `publish_notion.py` | Create page in Notion database |

---

## Content Frontmatter Schema

Your markdown file must have a YAML frontmatter block:

```yaml
---
title: "My Skill Release: Gmail Operator"
platforms:
  - devto
  - twitter
  - telegram
  - notion
tags:
  - openclaw
  - automation
  - gmail
canonical_url: "https://yourblog.com/gmail-operator"
---

Your content here...
```

**Fields:**

| Field | Required | Description |
|---|---|---|
| `title` | Yes | Post/article title |
| `platforms` | Yes | List: devto, twitter, telegram, notion |
| `tags` | No | Tags (used by Dev.to and Notion) |
| `canonical_url` | No | Canonical URL for Dev.to SEO |

---

## Environment Variables

Set these before publishing:

```bash
# Dev.to
export DEVTO_API_KEY="your_devto_api_key"

# Twitter/X (session-based auth)
export TWITTER_AUTH_TOKEN="your_auth_token_cookie"
export TWITTER_CT0="your_ct0_cookie"

# Telegram
export TELEGRAM_BOT_TOKEN="bot12345:AAAA..."
export TELEGRAM_CHAT_ID="-1001234567890"

# Notion
export NOTION_API_KEY="secret_abc123..."
export NOTION_DATABASE_ID="your-database-uuid"
```

Store these in your shell profile or `~/.openclaw/publisher-config.yml` (see Config section).

---

## Config File (Optional)

`~/.openclaw/publisher-config.yml` can store non-secret defaults:

```yaml
# ~/.openclaw/publisher-config.yml

devto:
  published: false        # true = publish immediately, false = save as draft
  series: "OpenClaw Skills"

twitter:
  max_tweet_length: 280

telegram:
  parse_mode: Markdown    # Markdown or HTML

notion:
  database_id: "your-database-uuid"   # can also use env var
  cover_emoji: "book"
```

---

## Usage

### Publish to all configured platforms
```bash
export DEVTO_API_KEY="..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python3 publish_devto.py my-post.md
python3 publish_telegram.py my-post.md
```

### Use the master script
```bash
bash publish.sh my-post.md
```

### Dry run (preview without posting)
```bash
bash publish.sh --dry-run my-post.md
python3 publish_devto.py --dry-run my-post.md
python3 publish_twitter.py --dry-run my-post.md
```

### Twitter thread format
Split your content into tweets using `---` delimiters:

```markdown
---
title: "My Thread"
platforms:
  - twitter
---

First tweet content here. Keep it under 280 chars.

---

Second tweet continues the thread.

---

Third tweet wraps it up.
```

---

## Getting API Keys

### Dev.to
1. Go to [dev.to/settings/extensions](https://dev.to/settings/extensions)
2. Scroll to "DEV API Keys"
3. Generate a new key
4. Set: `export DEVTO_API_KEY="your_key"`

### Twitter/X (Session Auth)
1. Log into Twitter in Chrome
2. Open DevTools → Application → Cookies → twitter.com
3. Copy `auth_token` cookie value
4. Copy `ct0` cookie value
5. Set both env vars

### Telegram Bot
1. Message `@BotFather` on Telegram
2. Run `/newbot` and follow prompts
3. Copy the bot token
4. Add your bot to the target channel/group as admin
5. Get chat ID: forward a message to `@getidsbot`

### Notion
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create integration with "Insert content" permission
3. Copy the API key
4. Share your target database with the integration

---

## Files in This Skill

```
multi-platform-publisher/
  SKILL.md               <- this file
  publish.sh             <- master orchestrator
  publish_devto.py       <- Dev.to publisher
  publish_twitter.py     <- Twitter/X thread publisher
  publish_telegram.py    <- Telegram publisher
  publish_notion.py      <- Notion page creator
```
