"""Migration 0005 — create invites table."""
from sqlalchemy import text


def migrate(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY,
            event_id INTEGER NOT NULL REFERENCES events(id),
            email TEXT NOT NULL,
            token TEXT NOT NULL,
            accepted INTEGER NOT NULL DEFAULT 0,
            sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))
