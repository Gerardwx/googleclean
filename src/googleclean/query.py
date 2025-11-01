# src/googleclean/query.py
import argparse
from googleclean.db import get_connection

def main():
    parser = argparse.ArgumentParser(description="Show summary of messages by sender.")
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT from_addr, COUNT(*) AS total, 
               SUM(has_attachment) AS with_attachment
        FROM messages
        GROUP BY from_addr
        ORDER BY total DESC
    """)

    print(f"{'Sender':50s} {'Messages':>8s} {'With Attachments':>16s}")
    print("=" * 80)
    for row in cur.fetchall():
        print(f"{row['from_addr'][:50]:50s} {row['total']:8d} {row['with_attachment'] or 0:16d}")

    conn.close()

if __name__ == "__main__":
    main()

