#!/usr/bin/env python3
"""
track_cost.py — record LLM API costs and compute daily/weekly/monthly totals

Usage:
  # Record a cost entry
  python3 scripts/track_cost.py record \
    --provider anthropic \
    --model claude-sonnet-4-6 \
    --tokens-in 1500 \
    --tokens-out 800 \
    --session-id "session-abc123"

  # Show dashboard
  python3 scripts/track_cost.py dashboard

  # Export daily total (for heartbeat integration)
  python3 scripts/track_cost.py daily

Required: Python 3.9+ (no external dependencies)
Costs stored at: ~/.openclaw/costs.json
"""

import sys
import json
import argparse
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Cost per 1M tokens (input / output) — update as pricing changes
PRICING: dict[str, dict[str, tuple[float, float]]] = {
    "anthropic": {
        "claude-opus-4-5":       (15.00, 75.00),
        "claude-sonnet-4-6":     (3.00,  15.00),
        "claude-sonnet-3-7":     (3.00,  15.00),
        "claude-haiku-3-5":      (0.80,  4.00),
        "claude-haiku-3":        (0.25,  1.25),
    },
    "openai": {
        "gpt-4o":                (5.00,  15.00),
        "gpt-4o-mini":           (0.15,  0.60),
        "gpt-4-turbo":           (10.00, 30.00),
        "gpt-3.5-turbo":         (0.50,  1.50),
        "o1":                    (15.00, 60.00),
        "o1-mini":               (3.00,  12.00),
        "o3-mini":               (1.10,  4.40),
    },
}

COSTS_FILE = Path.home() / ".openclaw" / "costs.json"


def load_costs() -> list[dict]:
    if not COSTS_FILE.exists():
        return []
    try:
        return json.loads(COSTS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def save_costs(entries: list[dict]) -> None:
    COSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    COSTS_FILE.write_text(json.dumps(entries, indent=2))


def calc_cost(provider: str, model: str, tokens_in: int, tokens_out: int) -> float:
    p = PRICING.get(provider.lower(), {})
    if model in p:
        in_rate, out_rate = p[model]
    else:
        # Fall back to a conservative default
        in_rate, out_rate = 3.00, 15.00
    return round((tokens_in * in_rate + tokens_out * out_rate) / 1_000_000, 6)


def cmd_record(args: argparse.Namespace) -> None:
    entries = load_costs()
    cost_usd = calc_cost(args.provider, args.model, args.tokens_in, args.tokens_out)
    entry = {
        "provider":    args.provider.lower(),
        "model":       args.model,
        "tokens_in":   args.tokens_in,
        "tokens_out":  args.tokens_out,
        "cost_usd":    cost_usd,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "session_id":  args.session_id or "",
    }
    entries.append(entry)
    save_costs(entries)
    print(f"Recorded: {args.provider}/{args.model} in={args.tokens_in} out={args.tokens_out} cost=${cost_usd:.6f}")


def totals_for_window(entries: list[dict], since: datetime) -> dict[str, float]:
    totals: dict[str, float] = {}
    for e in entries:
        ts = datetime.fromisoformat(e["timestamp"])
        if ts >= since:
            key = f"{e['provider']}/{e['model']}"
            totals[key] = round(totals.get(key, 0.0) + e["cost_usd"], 6)
    return totals


def cmd_daily(args: argparse.Namespace) -> None:
    entries = load_costs()
    now = datetime.now(timezone.utc)
    since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    totals = totals_for_window(entries, since)
    daily_total = round(sum(totals.values()), 6)
    print(f"Today: ${daily_total:.4f}")
    for model, cost in sorted(totals.items(), key=lambda x: -x[1]):
        print(f"  {model}: ${cost:.4f}")


def cmd_dashboard(args: argparse.Namespace) -> None:
    entries = load_costs()
    if not entries:
        print("No cost data found. Record some entries first.")
        print(f"Data file: {COSTS_FILE}")
        return

    now = datetime.now(timezone.utc)
    day_start   = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = day_start - timedelta(days=now.weekday())
    month_start = day_start.replace(day=1)

    day_totals   = totals_for_window(entries, day_start)
    week_totals  = totals_for_window(entries, week_start)
    month_totals = totals_for_window(entries, month_start)

    day_sum   = round(sum(day_totals.values()), 4)
    week_sum  = round(sum(week_totals.values()), 4)
    month_sum = round(sum(month_totals.values()), 4)

    # Projected monthly based on daily average
    days_in_month = 30
    daily_avg = month_sum / max(now.day, 1)
    projected = round(daily_avg * days_in_month, 2)

    # Collect all models seen
    all_models: set[str] = set()
    for e in entries:
        all_models.add(f"{e['provider']}/{e['model']}")

    col_w = max((len(m) for m in all_models), default=20) + 2

    print("=" * (col_w + 42))
    print(f"  API Cost Dashboard — {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * (col_w + 42))
    print(f"  {'Model':<{col_w}} {'Today':>10} {'This Week':>12} {'This Month':>12}")
    print(f"  {'-'*col_w} {'----------':>10} {'------------':>12} {'------------':>12}")

    for model in sorted(all_models):
        d = day_totals.get(model, 0.0)
        w = week_totals.get(model, 0.0)
        m = month_totals.get(model, 0.0)
        if d + w + m > 0:
            print(f"  {model:<{col_w}} ${d:>9.4f} ${w:>11.4f} ${m:>11.4f}")

    print(f"  {'-'*col_w} {'----------':>10} {'------------':>12} {'------------':>12}")
    print(f"  {'TOTAL':<{col_w}} ${day_sum:>9.4f} ${week_sum:>11.4f} ${month_sum:>11.4f}")
    print()
    print(f"  Daily avg this month: ${daily_avg:.4f}")
    print(f"  Projected monthly:    ${projected:.2f}")
    print(f"  Entries recorded:     {len(entries)}")
    print(f"  Data file:            {COSTS_FILE}")
    print("=" * (col_w + 42))


def cmd_pricing(args: argparse.Namespace) -> None:
    print(f"{'Provider':<12} {'Model':<25} {'Input/1M':>12} {'Output/1M':>12}")
    print(f"{'-'*12} {'-'*25} {'----------':>12} {'----------':>12}")
    for provider, models in sorted(PRICING.items()):
        for model, (inp, out) in sorted(models.items()):
            print(f"{provider:<12} {model:<25} ${inp:>11.2f} ${out:>11.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Track LLM API costs")
    sub = parser.add_subparsers(dest="command")

    rec = sub.add_parser("record", help="Record a cost entry")
    rec.add_argument("--provider",   required=True, help="anthropic | openai")
    rec.add_argument("--model",      required=True, help="Model name")
    rec.add_argument("--tokens-in",  type=int, required=True, dest="tokens_in")
    rec.add_argument("--tokens-out", type=int, required=True, dest="tokens_out")
    rec.add_argument("--session-id", default="", dest="session_id")

    sub.add_parser("daily",     help="Show today's cost total")
    sub.add_parser("dashboard", help="Show full cost dashboard (ASCII table)")
    sub.add_parser("pricing",   help="Print pricing table")

    args = parser.parse_args()

    if args.command == "record":
        cmd_record(args)
    elif args.command == "daily":
        cmd_daily(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "pricing":
        cmd_pricing(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
