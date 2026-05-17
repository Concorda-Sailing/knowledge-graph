"""Single-binding `var = "literal"` resolved through to text(var).

Real migrations sometimes name the DDL string for readability before
passing it to text(). The extractor must resolve the bare Name reference
back to the literal, otherwise the schema goes missing from the corpus.
"""
from sqlalchemy import text

ACCOUNTS_DDL = """
    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY,
        handle VARCHAR(64) NOT NULL UNIQUE
    )
"""


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text(ACCOUNTS_DDL))
