# mixed_text_and_op

## Pattern

A migration file that uses BOTH `text("SQL...")` AND `op.add_column(...)` —
the kind of file a developer might write when mixing SQLAlchemy's text()-based
convention with Alembic helpers.

```python
from sqlalchemy import text
from alembic import op
import sqlalchemy as sa

def upgrade(conn):
    # text() portion — extracted and parsed
    conn.execute(text("CREATE TABLE log (id INTEGER PRIMARY KEY, msg TEXT)"))
    # op.* portion — silently ignored (no text() call)
    op.add_column("log", sa.Column("level", sa.String(50)))
```

## Key behaviour under test

- `is_migration_file` returns True because there IS a `text()` call.
- `extract_migration` finds and parses only the `text(...)` argument.
- The `op.add_column(...)` call has no `text()` call → invisible to the
  extractor → silently ignored.
- Result: table `log` has only the columns from the CREATE TABLE statement
  (`id`, `msg`). The `level` column added by `op.add_column` is absent.

This is the correct and documented behaviour for Phase 4: Alembic op.* calls
are out of scope.

## sqlglot version

Tested against sqlglot 30.8.0.
