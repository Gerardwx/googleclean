import argparse
from googleclean.db import get_connection, init_db

def list_retain():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT from_addr FROM retain ORDER BY from_addr")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No retained senders.")
    else:
        print("Retained senders:")
        for r in rows:
            print(f"  {r['from_addr']}")

def add_retain(addresses):
    conn = get_connection()
    cur = conn.cursor()
    for addr in addresses:
        cur.execute("INSERT OR IGNORE INTO retain (from_addr) VALUES (?)", (addr,))
        print(f"✅ Added {addr}")
    conn.commit()
    conn.close()

def remove_retain(addresses):
    conn = get_connection()
    cur = conn.cursor()
    for addr in addresses:
        cur.execute("DELETE FROM retain WHERE from_addr=?", (addr,))
        print(f"🗑️  Removed {addr}")
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Manage the list of retained senders.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all retained senders.")

    addp = sub.add_parser("add", help="Add one or more retained senders.")
    addp.add_argument("addresses", nargs="+", help="Email addresses to retain.")

    remp = sub.add_parser("remove", help="Remove retained senders.")
    remp.add_argument("addresses", nargs="+", help="Email addresses to remove.")

    args = parser.parse_args()
    init_db()

    if args.cmd == "list":
        list_retain()
    elif args.cmd == "add":
        add_retain(args.addresses)
    elif args.cmd == "remove":
        remove_retain(args.addresses)

if __name__ == "__main__":
    main()

