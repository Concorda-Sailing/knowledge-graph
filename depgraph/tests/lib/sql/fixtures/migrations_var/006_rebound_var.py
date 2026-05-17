"""When a name is bound more than once at module scope we can't tell
which value is live at the text() call, so the binding is dropped and
the call falls through to the dynamic-SQL warning."""
from sqlalchemy import text

DDL = "CREATE TABLE first (id INTEGER PRIMARY KEY)"
DDL = "CREATE TABLE second (id INTEGER PRIMARY KEY)"


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text(DDL))
