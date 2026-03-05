#!/usr/bin/env python3
"""
publish_twitter.py -- Post a Twitter/X thread from a markdown file.

Content is split into tweets at `---` delimiters.
Each tweet is truncated to 280 chars at the last word boundary.

Required env vars:
  TWITTER_AUTH_TOKEN   Value of auth_token cookie from twitter.com
  TWITTER_CT0          Value of ct0 cookie from twitter.com

Usage:
  python3 publish_twitter.py content.md [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

MAX_TWEET_LENGTH = 280
TWITTER_API_URL = "https://api.twitter.com/2/tweets"
TWITTER_GRAPHQL_URL = "https://api.twitter.com/graphql/oB-5XsHNAbjvARJEc8CZFw/CreateTweet"


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


def _truncate_tweet(text: str, max_len: int = MAX_TWEET_LENGTH) -> str:
    """Truncate text to max_len chars at the last word boundary."""
    text = text.strip()
    if len(text) <= max_len:
        return text
    # Find last space within limit
    truncated = text[:max_len - 1]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space] + "\u2026"
    return truncated[:max_len - 1] + "\u2026"


def _split_into_tweets(body: str) -> list:
    """Split markdown body into tweets at --- delimiters."""
    segments = re.split(r"\n---\n", body)
    tweets = []
    for segment in segments:
        text = segment.strip()
        if not text:
            continue
        # Remove markdown headers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Remove markdown links, keep text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # Remove code fences
        text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
        text = text.strip()
        if text:
            tweets.append(_truncate_tweet(text))
    return tweets


def _post_tweet_session(tweet_text: str, auth_token: str, ct0: str, reply_to_id: str = None) -> dict:
    """Post a single tweet using session-based auth (cookie method)."""
    payload = {
        "variables": {
            "tweet_text": tweet_text,
            "dark_request": False,
            "media": {"media_entities": [], "possibly_sensitive": False},
            "semantic_annotation_ids": [],
        },
        "features": {
            "interactive_text_enabled": True,
            "longform_notetweets_inline_media_enabled": False,
            "responsive_web_text_conversations_enabled": False,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
            "vibe_api_enabled": False,
            "rweb_lists_timeline_redesign_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_media_interstitial_enabled": False,
            "responsive_web_enhance_cards_enabled": False,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_image_original_aspect_ratio_enabled": True,
        },
        "queryId": "oB-5XsHNAbjvARJEc8CZFw",
    }

    if reply_to_id:
        payload["variables"]["reply"] = {
            "in_reply_to_tweet_id": reply_to_id,
            "exclude_reply_user_ids": [],
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TWITTER_GRAPHQL_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "Cookie": f"auth_token={auth_token}; ct0={ct0}",
            "x-csrf-token": ct0,
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "x-twitter-active-user": "yes",
            "Referer": "https://twitter.com/",
            "Origin": "https://twitter.com",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            tweet_data = (
                result.get("data", {})
                .get("create_tweet", {})
                .get("tweet_results", {})
                .get("result", {})
            )
            tweet_id = tweet_data.get("rest_id", "")
            return {"id": tweet_id, "text": tweet_text}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"Twitter API error HTTP {e.code}: {err_body}")


def publish_twitter(markdown_path: Path, dry_run: bool = False) -> dict:
    auth_token = os.environ.get("TWITTER_AUTH_TOKEN")
    ct0 = os.environ.get("TWITTER_CT0")

    if not auth_token or not ct0:
        print("Error: TWITTER_AUTH_TOKEN and TWITTER_CT0 env vars must be set", file=sys.stderr)
        sys.exit(1)

    text = markdown_path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)

    tweets = _split_into_tweets(body)
    if not tweets:
        print("Error: No tweet content found in file", file=sys.stderr)
        sys.exit(1)

    title = fm.get("title", "")
    if title and not tweets[0].startswith(title[:20]):
        tweets[0] = _truncate_tweet(f"{title}\n\n{tweets[0]}")

    if dry_run:
        print(f"[dry-run] Would post {len(tweets)} tweet(s) to Twitter/X:\n")
        for i, tweet in enumerate(tweets, 1):
            print(f"  Tweet {i}/{len(tweets)} ({len(tweet)} chars):")
            print(f"  {tweet[:200]}")
            print()
        return {"status": "dry_run", "platform": "twitter", "tweet_count": len(tweets)}

    posted = []
    reply_to_id = None
    for i, tweet_text in enumerate(tweets):
        try:
            result = _post_tweet_session(tweet_text, auth_token, ct0, reply_to_id)
            posted.append(result)
            reply_to_id = result.get("id")
            print(f"  Posted tweet {i+1}/{len(tweets)}: {reply_to_id}")
            if i < len(tweets) - 1:
                time.sleep(2)
        except RuntimeError as e:
            print(f"Error posting tweet {i+1}: {e}", file=sys.stderr)
            sys.exit(1)

    first_id = posted[0]["id"] if posted else ""
    return {
        "status": "published",
        "platform": "twitter",
        "tweet_count": len(posted),
        "first_tweet_id": first_id,
        "thread_url": f"https://twitter.com/i/web/status/{first_id}" if first_id else "",
        "tweets": posted,
    }


def main():
    parser = argparse.ArgumentParser(description="Post Twitter/X thread from markdown")
    parser.add_argument("file", type=Path, help="Markdown file to publish")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = publish_twitter(args.file, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
