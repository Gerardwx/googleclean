from pathlib import Path
import sqlite3

DB_PATH = "googleclean.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the database schema if not exists."""
    conn = get_connection()
    cur = conn.cursor()

    # Messages table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        google_id TEXT PRIMARY KEY,
        rfc822_id TEXT,
        to_addr TEXT,
        from_addr TEXT,
        subject TEXT,
        has_attachment INTEGER,
        is_deleted INTEGER DEFAULT 0
    );
    """)

    # ⚡ Add index to optimize lookups by sender
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_from_addr ON messages(from_addr);")

    # Retain table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS retain (
        from_addr TEXT PRIMARY KEY
    );
    """)

    conn.commit()
    conn.close()

