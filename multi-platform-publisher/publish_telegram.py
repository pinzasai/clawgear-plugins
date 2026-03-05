#!/usr/bin/env python3
"""
publish_telegram.py -- Post a markdown file to a Telegram channel or group.

Required env vars:
  TELEGRAM_BOT_TOKEN   Telegram bot token
  TELEGRAM_CHAT_ID     Target chat/channel/group ID

Usage:
  python3 publish_telegram.py content.md [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

TELEGRAM_MAX_LENGTH = 4096


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm_text = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    if HAS_YAML:
        fm = yaml.safe_load(fm_text) or {}
    else:
        fm = {}
        for line in fm_text.splitlines():
            if ":" in line and not line.startswith(" "):
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def _markdown_to_telegram(text: str) -> str:
    """
    Convert markdown to Telegram-compatible Markdown.
    Telegram supports: *bold*, _italic_, `code`, ```pre```, [text](url)
    """
    # Convert ## headings to bold
    text = re.sub(r"^#{1,6}\s+(.+)$", r"*\1*", text, flags=re.MULTILINE)

    # Convert **bold** to *bold* (Telegram uses single asterisk)
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)

    # Convert __bold__ to *bold*
    text = re.sub(r"__(.+?)__", r"*\1*", text)

    # Keep _italic_ and `code` as-is (Telegram supports these)
    # Remove HTML-style tags if any slipped through
    text = re.sub(r"<[^>]+>", "", text)

    # Convert horizontal rules to decorative line
    text = re.sub(r"^\s*---\s*$", "\u2015\u2015\u2015\u2015\u2015", text, flags=re.MULTILINE)

    return text.strip()


def _split_message(text: str, max_len: int = TELEGRAM_MAX_LENGTH) -> list:
    """Split long messages at paragraph boundaries."""
    if len(text) <= max_len:
        return [text]

    parts = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                parts.append(current.strip())
            if len(paragraph) <= max_len:
                current = paragraph
            else:
                # Hard split at max_len
                for i in range(0, len(paragraph), max_len):
                    parts.append(paragraph[i:i + max_len])
                current = ""

    if current:
        parts.append(current.strip())

    return [p for p in parts if p.strip()]


def _send_telegram_message(bot_token: str, chat_id: str, text: str, parse_mode: str = "Markdown") -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"Telegram API error HTTP {e.code}: {err_body}")


def publish_telegram(markdown_path: Path, dry_run: bool = False) -> dict:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars must be set", file=sys.stderr)
        sys.exit(1)

    # Load optional config
    parse_mode = "Markdown"
    config_path = Path.home() / ".openclaw" / "publisher-config.yml"
    if config_path.exists() and HAS_YAML:
        try:
            config = yaml.safe_load(config_path.read_text()) or {}
            tg_config = config.get("telegram", {})
            parse_mode = tg_config.get("parse_mode", "Markdown")
        except Exception:
            pass

    text = markdown_path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)

    title = fm.get("title", "")
    formatted_body = _markdown_to_telegram(body)

    if title:
        message = f"*{title}*\n\n{formatted_body}"
    else:
        message = formatted_body

    parts = _split_message(message)

    if dry_run:
        print(f"[dry-run] Would send {len(parts)} message(s) to Telegram chat {chat_id}:\n")
        for i, part in enumerate(parts, 1):
            print(f"  Message {i}/{len(parts)} ({len(part)} chars):")
            print(f"  {part[:300]}")
            print()
        return {"status": "dry_run", "platform": "telegram", "message_count": len(parts)}

    sent_ids = []
    for part in parts:
        result = _send_telegram_message(bot_token, chat_id, part, parse_mode)
        msg_id = result.get("result", {}).get("message_id")
        sent_ids.append(msg_id)

    return {
        "status": "published",
        "platform": "telegram",
        "message_count": len(sent_ids),
        "message_ids": sent_ids,
        "chat_id": chat_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Publish markdown to Telegram")
    parser.add_argument("file", type=Path, help="Markdown file to publish")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = publish_telegram(args.file, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
