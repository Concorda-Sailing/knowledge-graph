from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE event (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL
            )
        """))
