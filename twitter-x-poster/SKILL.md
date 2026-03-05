---
name: twitter-x-poster
description: Post tweets, threads, and replies to Twitter/X as @PinzasAi using the xurl CLI or Twitter API v2. Use when posting content for the security-copywriter project, engaging with other accounts, checking recent posts, scheduling content, or running the daily content strategy. Account: @PinzasAi. Credentials in ~/.openclaw/agent-accounts.json → accounts.twitter.
---

# Twitter/X Poster

Post and manage content on @PinzasAi via Twitter API v2.

## Setup

Credentials are in `~/.openclaw/agent-accounts.json → accounts.twitter`.

The `xurl` CLI handles auth. Check if configured:
```bash
xurl get /2/users/me
```

If not configured, credentials needed: bearer_token, api_key, api_secret, access_token, access_token_secret from agent-accounts.json.

## Posting

### Single tweet
```bash
xurl post /2/tweets -d '{"text": "Your tweet text here"}'
```

### Thread (multiple tweets)
Post first tweet, capture ID, reply to it:
```bash
# Post first tweet
TWEET1=$(xurl post /2/tweets -d '{"text": "1/ First tweet in thread"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")

# Reply to create thread
xurl post /2/tweets -d "{\"text\": \"2/ Second tweet\", \"reply\": {\"in_reply_to_tweet_id\": \"$TWEET1\"}}"
```

### Reply to another tweet
```bash
xurl post /2/tweets -d '{"text": "@user Great point!", "reply": {"in_reply_to_tweet_id": "TWEET_ID"}}'
```

### Quote tweet
```bash
xurl post /2/tweets -d '{"text": "My take on this:", "quote_tweet_id": "TWEET_ID"}'
```

## Reading

### Get recent tweets from @PinzasAi
```bash
# Get own user ID first
USER_ID=$(xurl get /2/users/me | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")
xurl get "/2/users/$USER_ID/tweets?max_results=10&tweet.fields=created_at,public_metrics"
```

### Search tweets
```bash
xurl get "/2/tweets/search/recent?query=clawarmor&max_results=10"
```

## Content Strategy (Security Copywriter Project)

**Account purpose:** Build Alberto's personal brand in AI/security space, document building in public.

**Post types:**
- 🔨 **Build updates** — what shipped, what broke, what we learned (Mon/Wed)
- 🧵 **Threads** — deep dives on OpenClaw, ClawArmor, agent ops (Tue)
- 💬 **Engagement** — reply to relevant accounts in AI/security space (daily, 80/20 rule)
- 📊 **Weekly recap** — numbers, lessons, what's next (Fri/Sat)

**Hard rules:**
- No engagement bait ("Agree? Comment YES")
- No generic motivational content
- Always specific — name the tool, the number, the failure
- Run output through De-AI-ify skill before posting if AI-generated

**Voice:** Direct, builder mindset, shows the work, occasional dry humor.

## Engagement Workflow

The 80/20 rule: 80% of growth from engaging others, 20% from own posts.

```bash
# Find relevant accounts to engage
xurl get "/2/tweets/search/recent?query=openclaw OR clawarmor OR \"agent security\"&max_results=20"
```

Reply with genuine insight, not just "great point." Add your own experience or a counterpoint.

## Tracking

Check metrics weekly:
```bash
USER_ID=$(xurl get /2/users/me | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")
xurl get "/2/users/$USER_ID?user.fields=public_metrics"
```

Log follower count weekly in `projects/security-copywriter/MEMORY.md`.
