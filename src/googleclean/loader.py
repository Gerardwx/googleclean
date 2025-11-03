import argparse
from googleclean.db import get_connection, init_db
from googleclean.gmail_api import get_service

def has_attachments(payload) -> bool:
    if not payload:
        return False
    if payload.get("filename") and "attachmentId" in payload.get("body", {}):
        return True
    for part in payload.get("parts", []):
        if has_attachments(part):
            return True
    return False

def load_year(service, year: int):
    """Load all Gmail messages for the given year into SQLite."""
    query = f"after:{year}-01-01 before:{year+1}-01-01"
    conn = get_connection()
    cur = conn.cursor()
    total = 0

    print(f"🔍 Fetching all messages for {year}...")
    next_token = None

    while True:
        response = service.users().messages().list(
            userId="me", q=query, maxResults=500, pageToken=next_token
        ).execute()

        messages = response.get("messages", [])
        if not messages:
            break

        for msg_meta in messages:
            msg_id = msg_meta["id"]
            msg = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full",
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            rfc822_id = headers.get("Message-ID")
            subj = headers.get("Subject", "(no subject)")
            from_addr = headers.get("From", "")
            to_addr = headers.get("To", "")
            has_attachment = int(has_attachments(msg.get("payload")))

            cur.execute(
                """
                INSERT OR REPLACE INTO messages
                (google_id, rfc822_id, to_addr, from_addr, subject, has_attachment, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, COALESCE(
                    (SELECT is_deleted FROM messages WHERE google_id = ?), 0
                ))
                """,
                (msg_id, rfc822_id, to_addr, from_addr, subj, has_attachment, msg_id),
            )
            total += 1

        conn.commit()
        next_token = response.get("nextPageToken")
        if not next_token:
            break

    conn.close()
    print(f"✅ Loaded {total} messages for {year}.")

def main():
    parser = argparse.ArgumentParser(description="Load Gmail messages for a given year into SQLite database.")
    parser.add_argument("year", type=int, help="Year to load messages for.")
    args = parser.parse_args()

    init_db()
    service = get_service()
    load_year(service, args.year)

if __name__ == "__main__":
    main()

