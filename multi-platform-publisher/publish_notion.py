#!/usr/bin/env python3
"""
publish_notion.py -- Create a Notion page from a markdown file.

Required env vars:
  NOTION_API_KEY       Notion integration token
  NOTION_DATABASE_ID   Target database UUID

Usage:
  python3 publish_notion.py content.md [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

NOTION_API_VERSION = "2022-06-28"
NOTION_PAGES_URL = "https://api.notion.com/v1/pages"


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


def _text_block(text: str) -> dict:
    """Create a Notion paragraph block."""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _heading_block(text: str, level: int = 2) -> dict:
    """Create a Notion heading block."""
    h_type = f"heading_{min(max(level, 1), 3)}"
    return {
        "object": "block",
        "type": h_type,
        h_type: {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _code_block(text: str, language: str = "plain text") -> dict:
    """Create a Notion code block."""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "language": language,
        },
    }


def _bullet_block(text: str) -> dict:
    """Create a Notion bulleted list item."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _markdown_to_blocks(markdown: str) -> list:
    """Convert markdown to Notion blocks (simplified)."""
    blocks = []
    lines = markdown.splitlines()
    i = 0
    in_code_block = False
    code_lines = []
    code_lang = "plain text"

    while i < len(lines):
        line = lines[i]

        # Code fences
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip() or "plain text"
                code_lines = []
            else:
                in_code_block = False
                if code_lines:
                    blocks.append(_code_block("\n".join(code_lines), code_lang))
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Headings
        h_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if h_match:
            level = len(h_match.group(1))
            text = h_match.group(2).strip()
            blocks.append(_heading_block(text, level))
            i += 1
            continue

        # Bullet lists
        if re.match(r"^[-*]\s+", line):
            text = re.sub(r"^[-*]\s+", "", line).strip()
            # Strip inline formatting
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            if text:
                blocks.append(_bullet_block(text))
            i += 1
            continue

        # Horizontal rule -- skip
        if re.match(r"^-{3,}$", line.strip()):
            i += 1
            continue

        # Paragraph text
        text = line.strip()
        if text:
            # Strip inline markdown formatting for clean Notion text
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            text = re.sub(r"`(.+?)`", r"\1", text)
            text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
            blocks.append(_text_block(text))

        i += 1

    return blocks


def _build_page_payload(
    title: str,
    database_id: str,
    blocks: list,
    tags: list,
    canonical_url: str = "",
) -> dict:
    properties = {
        "title": {
            "title": [{"type": "text", "text": {"content": title}}]
        }
    }

    # Add tags as multi-select if database has a Tags property
    if tags:
        properties["Tags"] = {
            "multi_select": [{"name": str(t)[:100]} for t in tags[:10]]
        }

    if canonical_url:
        properties["URL"] = {"url": canonical_url}

    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
        "children": blocks[:100],  # Notion API limit: 100 blocks per request
    }
    return payload


def publish_notion(markdown_path: Path, dry_run: bool = False) -> dict:
    api_key = os.environ.get("NOTION_API_KEY")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    # Also check config file for database_id
    if not database_id:
        config_path = Path.home() / ".openclaw" / "publisher-config.yml"
        if config_path.exists() and HAS_YAML:
            try:
                config = yaml.safe_load(config_path.read_text()) or {}
                database_id = config.get("notion", {}).get("database_id", "")
            except Exception:
                pass

    if not api_key:
        print("Error: NOTION_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)
    if not database_id:
        print("Error: NOTION_DATABASE_ID env var not set (or notion.database_id in config)", file=sys.stderr)
        sys.exit(1)

    text = markdown_path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)

    title = fm.get("title", markdown_path.stem.replace("-", " ").title())
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    canonical_url = fm.get("canonical_url", "")

    blocks = _markdown_to_blocks(body)

    if dry_run:
        print(f"[dry-run] Would create Notion page in database {database_id}:")
        print(f"  Title: {title}")
        print(f"  Tags: {tags}")
        if canonical_url:
            print(f"  URL: {canonical_url}")
        print(f"  Blocks: {len(blocks)}")
        return {"status": "dry_run", "platform": "notion", "title": title, "block_count": len(blocks)}

    payload = _build_page_payload(title, database_id, blocks, tags, canonical_url)
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        NOTION_PAGES_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_API_VERSION,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            page_url = result.get("url", "")
            page_id = result.get("id", "")
            return {
                "status": "published",
                "platform": "notion",
                "page_id": page_id,
                "url": page_url,
                "title": title,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"Error from Notion API: HTTP {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create Notion page from markdown")
    parser.add_argument("file", type=Path, help="Markdown file to publish")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = publish_notion(args.file, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
