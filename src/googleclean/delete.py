import argparse
import sys
from pathlib import Path
from googleclean.db import get_connection
from googleclean.gmail_api import get_service

def read_addresses_file(path):
    """Read one address per line from a text file, ignoring blank lines and comments."""
    p = Path(path)
    if not p.exists():
        print(f"⚠️  File not found: {p}", file=sys.stderr)
        sys.exit(1)
    addresses = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        addresses.append(line)
    return addresses

def query_messages(senders, subjects):
    """Query cached messages by sender and/or subject, excluding retained senders."""
    conn = get_connection()
    cur = conn.cursor()
    where = []
    params = []
    if senders:
        where.append("(" + " OR ".join(["from_addr LIKE ?" for _ in senders]) + ")")
        params.extend([f"%{s}%" for s in senders])
    if subjects:
        where.append("(" + " OR ".join(["subject LIKE ?" for _ in subjects]) + ")")
        params.extend([f"%{s}%" for s in subjects])
    clause = " AND ".join(where) if where else "1=1"

    query = f"""
        SELECT * FROM messages
        WHERE {clause}
          AND is_deleted = 0
          AND from_addr NOT IN (SELECT from_addr FROM retain)
    """
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def batch_delete_from_gmail(service, google_ids):
    """Delete Gmail messages in batches of 100."""
    total = 0
    for i in range(0, len(google_ids), 100):
        batch = google_ids[i:i+100]
        try:
            service.users().messages().batchDelete(userId="me", body={"ids": batch}).execute()
            total += len(batch)
        except Exception as e:
            print(f"⚠️ Batch {i//100+1} failed: {e}")
    return total

def main():
    parser = argparse.ArgumentParser(
        description="Query and optionally delete Gmail messages from Gmail and local DB."
    )
    parser.add_argument("--from", dest="senders", action="append", help="Filter by sender (can repeat).")
    parser.add_argument("--from-file", help="Text file containing sender addresses (one per line).")
    parser.add_argument("--subject", action="append", help="Filter by subject (can repeat).")
    parser.add_argument("--out", help="Write results to a text file.")
    parser.add_argument("--delete", action="store_true",
                        help="Actually delete matching messages from Gmail and mark deleted in DB. "
                             "Without this flag, only a dry run is performed.")
    parser.add_argument("--account", help="Specify Gmail account to authenticate (login_hint).")
    args = parser.parse_args()

    # Combine addresses from --from and --from-file
    all_senders = args.senders or []
    if args.from_file:
        file_senders = read_addresses_file(args.from_file)
        all_senders.extend(file_senders)
    if not all_senders and not args.subject:
        print("--from, --from-file, or --subject required", file=sys.stderr)
        sys.exit(1)

    rows = query_messages(all_senders, args.subject)

    output = []
    for r in rows:
        line = f"{r['from_addr']} | {r['subject']} | attachment={r['has_attachment']} | google_id={r['google_id']}"
        print(line)
        output.append(line)
    print(f"{len(rows)} messages selected (excluding retained senders)")

    if args.out:
        Path(args.out).write_text("\n".join(output))
        print(f"Results written to {args.out}")

    if args.delete:
        confirm = input(f"⚠️  Permanently delete these {len(rows)} messages from Gmail? (y/N): ").strip().lower()
        if confirm != "y":
            print("Deletion cancelled.")
            return

        # Connect to Gmail API and delete remotely
        service = get_service(account=args.account)
        google_ids = [r["google_id"] for r in rows if r["google_id"]]
        deleted = batch_delete_from_gmail(service, google_ids)
        print(f"✅ Deleted {deleted} messages from Gmail (batched).")

        # Mark as deleted in DB by google_id
        conn = get_connection()
        cur = conn.cursor()
        for r in rows:
            cur.execute("UPDATE messages SET is_deleted=1 WHERE google_id=?", (r["google_id"],))
        conn.commit()
        conn.close()
        print(f"✅ Updated {len(rows)} records in database as deleted.")
    else:
        print("\nDry run complete — no changes made.")
        print("Re-run with --delete to actually remove messages from Gmail and mark them deleted locally.")

if __name__ == "__main__":
    main()

