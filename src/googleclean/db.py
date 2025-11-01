# src/googleclean/db.py
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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        rfc822_id TEXT PRIMARY KEY,
        google_id TEXT,
        to_addr TEXT,
        from_addr TEXT,
        subject TEXT,
        has_attachment INTEGER,
        is_deleted INTEGER DEFAULT 0
    );
    """)
    conn.commit()
    conn.close()

