from sqlalchemy import text


def migrate(engine):
    # MySQL-style CREATE TABLE IF NOT EXISTS — idempotent re-apply of schema.
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL DEFAULT 0
            )
        """))
