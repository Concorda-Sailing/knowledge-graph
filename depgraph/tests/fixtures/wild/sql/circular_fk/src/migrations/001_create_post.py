from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE post (
                id INTEGER PRIMARY KEY,
                body TEXT NOT NULL,
                featured_comment_id INTEGER,
                FOREIGN KEY (featured_comment_id) REFERENCES comment(id)
            )
        """))
