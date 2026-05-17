"""Migration with ONLY f-string interpolated SQL.

The table name is runtime-dynamic — static extraction is impossible.
extract_migration records a warning and produces zero operations.
"""
from sqlalchemy import text


def migrate(engine, table_name):
    with engine.connect() as conn:
        conn.execute(text(f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY, val TEXT)"))
