import argparse
from googleclean.db import get_connection
import signal

# Prevent BrokenPipeError when piping to tools like head
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def main():
    parser = argparse.ArgumentParser(description="Show summary of messages by sender.")
    parser.add_argument(
        "--include-deleted",
        action="store_true",
        help="Include messages marked as deleted (default: excluded).",
    )
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT from_addr, COUNT(*) AS total, 
               SUM(has_attachment) AS with_attachment
        FROM messages
        WHERE from_addr NOT IN (SELECT from_addr FROM retain)
    """
    if not args.include_deleted:
        query += " AND is_deleted = 0"
    query += """
        GROUP BY from_addr
        ORDER BY total DESC
    """

    cur.execute(query)

    print(f"{'Sender':50s} {'Messages':>8s} {'With Attachments':>16s}")
    print("=" * 80)
    for row in cur.fetchall():
        print(f"{row['from_addr'][:50]:50s} {row['total']:8d} {row['with_attachment'] or 0:16d}")

    conn.close()

if __name__ == "__main__":
    main()

