"""Migration whose DDL string is named at module scope before being
handed to text(). The extractor must resolve the bare Name through the
module-level binding instead of dropping the schema."""
from sqlalchemy import text

ACCOUNTS_DDL = """
    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY,
        handle VARCHAR(64) NOT NULL UNIQUE
    )
"""

INVITES_DDL: str = """
    CREATE TABLE invites (
        id INTEGER PRIMARY KEY,
        account_id INTEGER REFERENCES accounts(id),
        token VARCHAR(64) NOT NULL
    )
"""


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text(ACCOUNTS_DDL))
        conn.execute(text(INVITES_DDL))
