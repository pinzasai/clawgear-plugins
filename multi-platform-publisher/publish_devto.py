#!/usr/bin/env python3
"""
publish_devto.py -- Publish a markdown file to Dev.to.

Required env var:
  DEVTO_API_KEY   Your Dev.to API key

Usage:
  python3 publish_devto.py content.md [--dry-run] [--published]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown."""
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


def publish_devto(
    markdown_path: Path,
    dry_run: bool = False,
    published: bool = False,
) -> dict:
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("Error: DEVTO_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    text = markdown_path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)

    title = fm.get("title", markdown_path.stem.replace("-", " ").title())
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    canonical_url = fm.get("canonical_url", "")

    # Dev.to accepts max 4 tags, each max 30 chars, lowercase
    tags = [str(t).lower()[:30] for t in tags[:4]]

    article = {
        "title": title,
        "body_markdown": body,
        "published": published,
        "tags": tags,
    }
    if canonical_url:
        article["canonical_url"] = canonical_url

    # Load optional config defaults
    config_path = Path.home() / ".openclaw" / "publisher-config.yml"
    if config_path.exists() and HAS_YAML:
        try:
            config = yaml.safe_load(config_path.read_text()) or {}
            devto_config = config.get("devto", {})
            if "published" in devto_config and not published:
                article["published"] = devto_config["published"]
            if "series" in devto_config:
                article["series"] = devto_config["series"]
        except Exception:
            pass

    payload = json.dumps({"article": article}).encode("utf-8")

    if dry_run:
        print("[dry-run] Would POST to Dev.to:")
        print(f"  Title: {title}")
        print(f"  Tags: {tags}")
        print(f"  Published: {article.get('published', False)}")
        if canonical_url:
            print(f"  Canonical URL: {canonical_url}")
        print(f"  Body length: {len(body)} chars")
        return {"status": "dry_run", "platform": "devto", "title": title}

    req = urllib.request.Request(
        "https://dev.to/api/articles",
        data=payload,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {
                "status": "published" if result.get("published") else "draft_created",
                "platform": "devto",
                "id": result.get("id"),
                "url": result.get("url"),
                "title": result.get("title"),
            }
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8")
        print(f"Error from Dev.to API: HTTP {e.code}: {body_err}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Publish markdown to Dev.to")
    parser.add_argument("file", type=Path, help="Markdown file to publish")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    parser.add_argument(
        "--published", action="store_true", help="Publish immediately (default: draft)"
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = publish_devto(args.file, dry_run=args.dry_run, published=args.published)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
