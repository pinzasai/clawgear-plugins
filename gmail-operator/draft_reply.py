#!/usr/bin/env python3
"""
draft_reply.py — Create a Gmail draft reply to an existing thread.

This script NEVER sends email. It only creates drafts.

Requires env var:
  GMAIL_CREDENTIALS_PATH  Path to OAuth 2.0 client credentials JSON

Usage:
  python3 draft_reply.py --thread-id THREAD_ID --body "Your reply text"
  python3 draft_reply.py --thread-id THREAD_ID --body-file reply.txt
"""

import argparse
import base64
import email.mime.text
import json
import os
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_PATH = Path.home() / ".openclaw" / "gmail_token.json"


def _get_credentials():
    credentials_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
    if not credentials_path:
        print("Error: GMAIL_CREDENTIALS_PATH env var not set", file=sys.stderr)
        sys.exit(1)

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "Error: Missing dependencies. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client",
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


def _get_thread_info(service, thread_id: str) -> dict:
    """Fetch thread metadata to build a proper reply."""
    thread = service.users().threads().get(
        userId="me", id=thread_id, format="metadata"
    ).execute()

    messages = thread.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    headers = {
        h["name"].lower(): h["value"]
        for h in last_msg.get("payload", {}).get("headers", [])
    }
    return {
        "message_id": last_msg["id"],
        "from": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "message_id_header": headers.get("message-id", ""),
        "references": headers.get("references", ""),
    }


def create_draft(thread_id: str, body: str) -> dict:
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("Error: googleapiclient not installed", file=sys.stderr)
        sys.exit(1)

    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    thread_info = _get_thread_info(service, thread_id)

    # Build reply subject
    subject = thread_info.get("subject", "")
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Build MIME message
    msg = email.mime.text.MIMEText(body, "plain", "utf-8")
    msg["To"] = thread_info.get("from", "")
    msg["Subject"] = subject

    # Set threading headers
    if thread_info.get("message_id_header"):
        msg["In-Reply-To"] = thread_info["message_id_header"]
        existing_refs = thread_info.get("references", "")
        if existing_refs:
            msg["References"] = f"{existing_refs} {thread_info['message_id_header']}"
        else:
            msg["References"] = thread_info["message_id_header"]

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    draft_body = {
        "message": {
            "raw": raw,
            "threadId": thread_id,
        }
    }

    draft = service.users().drafts().create(userId="me", body=draft_body).execute()

    return {
        "status": "draft_created",
        "draft_id": draft["id"],
        "thread_id": thread_id,
        "to": msg["To"],
        "subject": subject,
        "body_preview": body[:200],
        "note": "Draft created. NOT sent. Review in Gmail before sending.",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create a Gmail draft reply (does NOT send)"
    )
    parser.add_argument(
        "--thread-id", required=True, help="Gmail thread ID to reply to"
    )

    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Reply text (inline)")
    body_group.add_argument(
        "--body-file", type=Path, help="Path to file containing reply text"
    )

    args = parser.parse_args()

    if not os.environ.get("GMAIL_CREDENTIALS_PATH"):
        print("Error: GMAIL_CREDENTIALS_PATH env var not set", file=sys.stderr)
        sys.exit(1)

    if args.body_file:
        if not args.body_file.exists():
            print(f"Error: Body file not found: {args.body_file}", file=sys.stderr)
            sys.exit(1)
        body = args.body_file.read_text(encoding="utf-8").strip()
    else:
        body = args.body

    result = create_draft(args.thread_id, body)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
