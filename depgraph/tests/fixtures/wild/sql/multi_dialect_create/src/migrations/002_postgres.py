from sqlalchemy import text


def migrate(engine):
    # Postgres-style CREATE TABLE IF NOT EXISTS — idempotent re-apply of schema.
    # sqlglot (sqlite dialect) can tokenise SERIAL and NUMERIC even in sqlite mode.
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price NUMERIC(10,2) NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        """))
