"""Migration mixing text() and op.add_column().

Only the text() portion is extracted. The op.add_column() call is silently
ignored because it has no text() argument — it is invisible to the extractor.
"""
from sqlalchemy import text

# Alembic import present but op.* is out of scope
try:
    from alembic import op
    import sqlalchemy as sa
except ImportError:
    op = None
    sa = None


def upgrade(conn):
    # This text() call IS extracted and parsed.
    conn.execute(text("CREATE TABLE log (id INTEGER PRIMARY KEY, msg TEXT)"))
    # This op.add_column() call is NOT extracted — no text() wrapper.
    if op is not None:
        op.add_column("log", sa.Column("level", sa.String(50)))
