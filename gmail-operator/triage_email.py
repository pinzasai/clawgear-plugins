#!/usr/bin/env python3
"""
triage_email.py — Classify Gmail messages as URGENT, NORMAL, or LOW priority.

Requires env var:
  GMAIL_CREDENTIALS_PATH  Path to OAuth 2.0 client credentials JSON

Usage:
  python3 triage_email.py [--config PATH] [--max-results N] [--json]
"""

import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".openclaw" / ".gmail-config.yml"

DEFAULT_URGENT_KEYWORDS = [
    "urgent",
    "asap",
    "critical",
    "action required",
    "deadline",
    "payment",
    "invoice",
    "emergency",
    "immediate",
    "time-sensitive",
]


def _load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(config_path.read_text()) or {}
    except ImportError:
        # Minimal fallback: parse simple key: value YAML
        config = {}
        lines = config_path.read_text().splitlines()
        current_key = None
        in_list = False
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- ") and in_list and current_key:
                if current_key not in config:
                    config[current_key] = []
                config[current_key].append(stripped[2:].strip())
            elif ":" in stripped and not stripped.startswith("-"):
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip()
                current_key = key
                if value:
                    config[key] = int(value) if value.isdigit() else value
                    in_list = False
                else:
                    config[key] = []
                    in_list = True
        return config


def _classify(email: dict, sender_whitelist: list, urgent_keywords: list) -> str:
    sender = email.get("from", "").lower()
    subject = email.get("subject", "").lower()
    snippet = email.get("snippet", "").lower()
    body = email.get("body_preview", "").lower()

    combined_text = f"{subject} {snippet} {body}"

    # Whitelist senders are always URGENT
    for whitelisted in sender_whitelist:
        if whitelisted.lower() in sender:
            return "URGENT"

    # Keyword match
    for keyword in urgent_keywords:
        if keyword.lower() in combined_text:
            return "URGENT"

    # Heuristics for LOW priority
    low_indicators = [
        "unsubscribe",
        "newsletter",
        "no-reply",
        "noreply",
        "notification",
        "automated",
        "do not reply",
    ]
    for indicator in low_indicators:
        if indicator in sender or indicator in combined_text:
            return "LOW"

    return "NORMAL"


def triage_emails(config_path: Path, max_results: int = 20) -> list:
    # Import here to avoid circular issues with the check_inbox module pattern
    sys.path.insert(0, str(Path(__file__).parent))
    from check_inbox import check_inbox

    config = _load_config(config_path)
    sender_whitelist = config.get("sender_whitelist", [])
    urgent_keywords = config.get("urgent_keywords", DEFAULT_URGENT_KEYWORDS)
    max_results = config.get("max_results", max_results)

    emails = check_inbox(max_results=max_results)

    triaged = []
    for email in emails:
        priority = _classify(email, sender_whitelist, urgent_keywords)
        triaged.append(
            {
                "priority": priority,
                "id": email["id"],
                "thread_id": email["thread_id"],
                "from": email["from"],
                "subject": email["subject"],
                "date": email["date"],
                "snippet": email["snippet"],
            }
        )

    # Sort: URGENT first, then NORMAL, then LOW
    priority_order = {"URGENT": 0, "NORMAL": 1, "LOW": 2}
    triaged.sort(key=lambda x: priority_order.get(x["priority"], 9))
    return triaged


def _print_report(triaged: list):
    urgent = [e for e in triaged if e["priority"] == "URGENT"]
    normal = [e for e in triaged if e["priority"] == "NORMAL"]
    low = [e for e in triaged if e["priority"] == "LOW"]

    print(f"\n=== EMAIL TRIAGE REPORT ({len(triaged)} unread) ===\n")

    if urgent:
        print(f"🔴 URGENT ({len(urgent)})")
        for e in urgent:
            print(f"  From: {e['from']}")
            print(f"  Subject: {e['subject']}")
            print(f"  Thread: {e['thread_id']}")
            print(f"  Preview: {e['snippet'][:100]}")
            print()

    if normal:
        print(f"🟡 NORMAL ({len(normal)})")
        for e in normal:
            print(f"  From: {e['from']}")
            print(f"  Subject: {e['subject']}")
            print()

    if low:
        print(f"🟢 LOW ({len(low)})")
        for e in low:
            print(f"  From: {e['from']}")
            print(f"  Subject: {e['subject']}")
            print()

    print(
        f"Summary: {len(urgent)} urgent, {len(normal)} normal, {len(low)} low"
    )


def main():
    parser = argparse.ArgumentParser(description="Triage Gmail by priority")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Config file path (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--max-results", type=int, default=20, help="Max emails to fetch"
    )
    parser.add_argument(
        "--json", action="store_true", dest="output_json", help="Output JSON instead of report"
    )
    args = parser.parse_args()

    if not os.environ.get("GMAIL_CREDENTIALS_PATH"):
        print("Error: GMAIL_CREDENTIALS_PATH env var not set", file=sys.stderr)
        sys.exit(1)

    triaged = triage_emails(args.config, args.max_results)

    if args.output_json:
        print(json.dumps(triaged, indent=2, ensure_ascii=False))
    else:
        _print_report(triaged)


if __name__ == "__main__":
    main()
