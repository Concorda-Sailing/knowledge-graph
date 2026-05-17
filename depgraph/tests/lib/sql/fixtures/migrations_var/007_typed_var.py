"""AnnAssign (`var: str = "..."`) is also recognized."""
from sqlalchemy import text

INVITES_DDL: str = """
    CREATE TABLE invites (
        id INTEGER PRIMARY KEY,
        token VARCHAR(64) NOT NULL
    )
"""


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text(INVITES_DDL))
