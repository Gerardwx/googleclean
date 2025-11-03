import argparse
from googleclean.db import get_connection, init_db
from pathlib import Path

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

def read_addresses_from_file(file_path: Path):
    """Read addresses from a text file, one per line."""
    addresses = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                addresses.append(line)
    return addresses

def main():
    parser = argparse.ArgumentParser(description="Manage the list of retained senders.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all retained senders.")

    addp = sub.add_parser("add", help="Add one or more retained senders. Use command line or --file.")
    addp.add_argument("addresses", nargs="*", help="Email addresses to retain.")
    addp.add_argument("--file", type=Path, help="Path to text file containing one email address per line.")

    remp = sub.add_parser("remove", help="Remove retained senders.")
    remp.add_argument("addresses", nargs="+", help="Email addresses to remove.")

    args = parser.parse_args()
    init_db()

    if args.cmd == "list":
        list_retain()
    elif args.cmd == "add":
        addresses = list(args.addresses)
        if args.file:
            addresses.extend(read_addresses_from_file(args.file))
        if not addresses:
            print("No addresses provided. Use positional arguments or --file.")
            return
        add_retain(addresses)
    elif args.cmd == "remove":
        remove_retain(args.addresses)

if __name__ == "__main__":
    main()

