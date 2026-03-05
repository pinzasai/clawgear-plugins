---
name: api-cost-tracker
description: Track LLM API costs across multiple providers and agents. Records per-session token usage, calculates daily/weekly/monthly totals, renders ASCII dashboard, and sends Telegram alerts when spending exceeds thresholds. Use when you need visibility into Anthropic and OpenAI API costs, projected monthly billing, per-model cost breakdowns, or automated spend alerts in your agent workflow.
---

# API Cost Tracker

Operators running multiple agents have no visibility into costs. Bills are surprises. This skill installs a zero-dependency cost tracking system with a live ASCII dashboard, Telegram reporting, and spend alerts.

## What You Get

- **`track_cost.py`** — record entries, view dashboard, compute totals (Python 3.9+, no pip required)
- **`cost_report.sh`** — daily Telegram summary with per-provider breakdown + projected monthly
- **`cost_alert.sh`** — threshold alert: fires when daily spend exceeds limit
- **`costs.json` schema** — structured storage at `~/.openclaw/costs.json`

---

## Quick Start

```bash
# Copy scripts to your workspace
cp scripts/track_cost.py your-workspace/scripts/
cp scripts/cost_report.sh your-workspace/scripts/
cp scripts/cost_alert.sh your-workspace/scripts/
chmod +x your-workspace/scripts/cost_*.sh

# Set Telegram credentials
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Record a cost entry manually
python3 scripts/track_cost.py record \
  --provider anthropic \
  --model claude-sonnet-4-6 \
  --tokens-in 1500 \
  --tokens-out 800 \
  --session-id "session-abc123"

# View dashboard
python3 scripts/track_cost.py dashboard

# Send daily report to Telegram
./scripts/cost_report.sh

# Alert if over $2.00 today
./scripts/cost_alert.sh 2.00
```

---

## `costs.json` Schema

Each entry in `~/.openclaw/costs.json`:

```json
{
  "provider":   "anthropic",
  "model":      "claude-sonnet-4-6",
  "tokens_in":  1500,
  "tokens_out": 800,
  "cost_usd":   0.016500,
  "timestamp":  "2026-03-03T21:30:00+00:00",
  "session_id": "session-abc123"
}
```

The file is a JSON array. All writes are atomic (full file rewrite). Never edit manually while track_cost.py is running.

---

## Pricing Table

Run to see current rates:

```bash
python3 scripts/track_cost.py pricing
```

| Provider  | Model              | Input/1M | Output/1M |
|-----------|--------------------|----------|-----------|
| anthropic | claude-opus-4-5    | $15.00   | $75.00    |
| anthropic | claude-sonnet-4-6  | $3.00    | $15.00    |
| anthropic | claude-haiku-3-5   | $0.80    | $4.00     |
| openai    | gpt-4o             | $5.00    | $15.00    |
| openai    | gpt-4o-mini        | $0.15    | $0.60     |
| openai    | o1                 | $15.00   | $60.00    |

Update `PRICING` in `track_cost.py` when providers change rates.

---

## Dashboard Output

```
=============================================================
  API Cost Dashboard — 2026-03-03 21:30 UTC
=============================================================
  Model                      Today     This Week   This Month
  -------------------------- ---------- ------------ ------------
  anthropic/claude-haiku-3-5  $0.0120  $    0.0840  $    0.3200
  anthropic/claude-sonnet-4-6 $0.1650  $    1.1550  $    4.9500
  openai/gpt-4o-mini          $0.0045  $    0.0315  $    0.1200
  -------------------------- ---------- ------------ ------------
  TOTAL                       $0.1815  $    1.2705  $    5.3900

  Daily avg this month: $0.1797
  Projected monthly:    $5.39
  Entries recorded:     42
  Data file:            /Users/you/.openclaw/costs.json
=============================================================
```

---

## Heartbeat Integration

Add to your `HEARTBEAT.md` or heartbeat script:

```bash
# Show cost summary in every heartbeat
COST_SUMMARY=$(python3 scripts/track_cost.py daily 2>/dev/null || echo "No cost data")
echo "Costs: ${COST_SUMMARY}"

# Alert if over threshold
./scripts/cost_alert.sh 1.00 || echo "ALERT: cost threshold exceeded"
```

---

## Recording Costs Automatically

If your agent logs token usage, parse and record automatically:

```bash
# After any OpenClaw session, extract usage from session output
# and pipe into track_cost.py

record_session_cost() {
  local provider="$1"
  local model="$2"
  local tokens_in="$3"
  local tokens_out="$4"
  local session_id="$5"
  python3 scripts/track_cost.py record \
    --provider "$provider" \
    --model "$model" \
    --tokens-in "$tokens_in" \
    --tokens-out "$tokens_out" \
    --session-id "$session_id"
}

# Example call from agent wrapper
record_session_cost "anthropic" "claude-sonnet-4-6" 2100 950 "session-xyz"
```

---

## Setting Up Alerts via Cron

```bash
# Check costs every day at 8pm and alert if over $2.00
# Add to crontab: crontab -e
0 20 * * * export TELEGRAM_BOT_TOKEN=your_token; export TELEGRAM_CHAT_ID=your_chat_id; /path/to/scripts/cost_alert.sh 2.00

# Daily report at 9pm
0 21 * * * export TELEGRAM_BOT_TOKEN=your_token; export TELEGRAM_CHAT_ID=your_chat_id; /path/to/scripts/cost_report.sh
```

Or use OpenClaw cron (recommended — tokens set via env, not embedded in crontab):

```bash
openclaw cron add "cost-check" "0 20 * * *" \
  --command "python3 /path/to/scripts/cost_alert.sh 2.00" \
  --channel telegram --to "YOUR_CHAT_ID"
```

---

## Troubleshooting

**"No cost data found"** — record your first entry with `track_cost.py record`

**Dashboard shows $0 for today** — check your system timezone; the script uses UTC; entries before midnight UTC won't show in today

**"track_cost.py record" unknown model** — script will use a default rate of $3/$15 per 1M; update `PRICING` in the script to add your model

**costs.json corrupted** — the file is plain JSON; inspect with `python3 -m json.tool ~/.openclaw/costs.json`
