from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        # Two DDL statements in one text() call — both are parsed.
        conn.execute(text("""
            CREATE TABLE archive (
                id INTEGER PRIMARY KEY,
                event_id INTEGER,
                snapshot TEXT NOT NULL
            );
            ALTER TABLE archive ADD COLUMN archived_at TEXT
        """))
