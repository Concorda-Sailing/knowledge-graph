"""Migration 0003 — create rsvps table."""
from sqlalchemy import text


def migrate(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS rsvps (
            id INTEGER PRIMARY KEY,
            event_id INTEGER NOT NULL REFERENCES events(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            status TEXT NOT NULL DEFAULT 'attending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))
