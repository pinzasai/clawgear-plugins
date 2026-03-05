#!/usr/bin/env python3
"""
check_inbox.py — List unread Gmail messages as JSON.

Requires env var:
  GMAIL_CREDENTIALS_PATH  Path to OAuth 2.0 client credentials JSON

Token is stored at: ~/.openclaw/gmail_token.json

Usage:
  python3 check_inbox.py [--max-results N] [--label LABEL]
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_PATH = Path.home() / ".openclaw" / "gmail_token.json"


def _get_credentials():
    credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
    if not credentials_path:
        print(
            json.dumps({"error": "GMAIL_CREDENTIALS_PATH env var not set"}),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            json.dumps(
                {
                    "error": "Missing dependencies. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def _parse_headers(headers: list) -> dict:
    result = {}
    for h in headers:
        name = h.get("name", "").lower()
        if name in ("from", "to", "subject", "date"):
            result[name] = h.get("value", "")
    return result


def check_inbox(max_results: int = 20, label: str = "UNREAD") -> list:
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print(
            json.dumps({"error": "googleapiclient not installed"}), file=sys.stderr
        )
        sys.exit(1)

    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=[label], maxResults=max_results)
        .execute()
    )

    messages = results.get("messages", [])
    emails = []

    for msg_ref in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="full")
            .execute()
        )

        payload = msg.get("payload", {})
        headers = _parse_headers(payload.get("headers", []))

        snippet = msg.get("snippet", "")

        body_text = ""
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        else:
            for part in payload.get("parts", []):
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode(
                            "utf-8", errors="replace"
                        )
                    break

        emails.append(
            {
                "id": msg["id"],
                "thread_id": msg.get("threadId", ""),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "subject": headers.get("subject", "(no subject)"),
                "date": headers.get("date", ""),
                "snippet": snippet,
                "body_preview": body_text[:500] if body_text else snippet[:500],
                "labels": msg.get("labelIds", []),
            }
        )

    return emails


def main():
    parser = argparse.ArgumentParser(description="Check Gmail inbox")
    parser.add_argument(
        "--max-results", type=int, default=20, help="Max emails to fetch (default: 20)"
    )
    parser.add_argument(
        "--label", default="UNREAD", help="Gmail label filter (default: UNREAD)"
    )
    args = parser.parse_args()

    emails = check_inbox(max_results=args.max_results, label=args.label)
    print(json.dumps(emails, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
