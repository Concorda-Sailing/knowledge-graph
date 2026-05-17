from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE comment (
                id INTEGER PRIMARY KEY,
                post_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES post(id)
            )
        """))
