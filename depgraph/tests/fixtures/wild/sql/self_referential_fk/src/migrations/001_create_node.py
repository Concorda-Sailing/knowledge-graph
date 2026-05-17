from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE node (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER,
                label TEXT NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES node(id)
            )
        """))
