#!/usr/bin/env python3.14
"""
Gmail Filter & Delete Tool

Search Gmail messages by subject(s), sender(s), and/or date filters; optionally delete them.

Usage examples:
  python gmail_filter_delete.py --subject "Weekly Report" --subject "Status Update"
  python gmail_filter_delete.py --from "noreply@example.com" --from "alerts@foo.com"
  python gmail_filter_delete.py --from "spam@foo.com" --older-than 6m --delete
"""

import argparse
import logging
import os
import sys
import webbrowser
from typing import List
from googleclean import googleclean_logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://mail.google.com/"]

def get_service(account: str | None = None):
    """Authenticate and return a Gmail API service instance."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            flow.redirect_uri = "http://localhost:8080/"
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                login_hint=account or None,
                prompt="consent",
            )
            print(f"Opening browser for account {account or '(default)'}...")
            webbrowser.get("open -a 'Google Chrome' %s").open(auth_url)
            creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def search_messages(service, query: str) -> List[str]:
    """Search Gmail messages matching the query and return message IDs."""
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    while "nextPageToken" in results:
        results = service.users().messages().list(
            userId="me", q=query, pageToken=results["nextPageToken"]
        ).execute()
        messages.extend(results.get("messages", []))
    return [m["id"] for m in messages]

def show_messages(service, ids: List[str]):
    """Display the subject, sender, and snippet of each message."""
    for i, msg_id in enumerate(ids, start=1):
        msg = service.users().messages().get(
            userId="me", id=msg_id, format="metadata", metadataHeaders=["Subject", "From", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "(unknown sender)")
        date = headers.get("Date", "(unknown date)")
        snippet = msg.get("snippet", "")
        print(f"{i:3d}. {date}\n     From: {sender}\n     Subject: {subject}\n     {snippet[:80]}{'...' if len(snippet) > 80 else ''}\n")

def delete_messages(service, ids: List[str]):
    """Delete the given Gmail messages permanently."""
    for msg_id in ids:
        service.users().messages().delete(userId="me", id=msg_id).execute()

def build_query(subjects: List[str] | None, senders: List[str] | None, newer: str | None, older: str | None) -> str:
    """Combine filters into a Gmail search query."""
    parts = []

    if subjects:
        subject_clauses = [f'subject:"{s}"' for s in subjects]
        parts.append(" OR ".join(subject_clauses))

    if senders:
        from_clauses = [f'from:"{s}"' for s in senders]
        parts.append(" OR ".join(from_clauses))

    if newer:
        parts.append(f'newer_than:{newer}')
    if older:
        parts.append(f'older_than:{older}')

    return " ".join(parts)

def main(argv=None):
    logging.basicConfig()
    parser = argparse.ArgumentParser(description="Filter and optionally delete Gmail messages by subject, sender, and/or date.")
    parser.add_argument("--subject", action="append", help="Match one or more subjects (use multiple --subject entries).")
    parser.add_argument("--from", dest="senders", action="append", help="Match one or more sender addresses (use multiple --from entries).")
    parser.add_argument("--newer-than", help="Filter messages newer than duration (e.g., 7d, 3m, 1y).")
    parser.add_argument("--older-than", help="Filter messages older than duration (e.g., 7d, 3m, 1y).")
    parser.add_argument("--delete", action="store_true", help="Delete matching messages after confirmation.")
    parser.add_argument("--account", help="Specify Gmail account to authenticate (login_hint).")

    parser.add_argument('-l', '--loglevel', default='WARN', help="Python logging level")
    args = parser.parse_args(argv)
    googleclean_logger.setLevel(getattr(logging,args.loglevel))

    service = get_service(account=args.account)
    query = build_query(args.subject, args.senders, args.newer_than, args.older_than)
    if not query:
        print("Please specify at least one filter: --subject, --from, --newer-than, or --older-than.")
        return
    googleclean_logger.info(f"Filter query is {query}")

    ids = search_messages(service, query)
    count = len(ids)

    if count == 0:
        print("No messages found.")
        return

    print(f"Found {count} messages matching: {query}\n")
    show_messages(service, ids)

    if args.delete:
        confirm = input(f"⚠️  Delete these {count} messages? (y/N): ").strip().lower()
        if confirm == "y":
            delete_messages(service, ids)
            print(f"✅ Deleted {count} messages.")
        else:
            print("Deletion canceled.")
    else:
        print("\nRun again with --delete to remove these messages.")

if __name__ == "__main__":
    sys.exit(main())

