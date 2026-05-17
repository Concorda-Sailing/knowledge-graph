# alembic_op_style

## Pattern

A migration written in Alembic's `op.create_table(...)` style, using SQLAlchemy
Column objects rather than raw SQL strings inside `text()`.

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
```

## Why this is out of scope

The extractor (`extract_migration`) works by finding `text("SQL string")` calls
in migration Python files and parsing the embedded SQL with sqlglot. Alembic's
`op.*` API passes Column objects, not SQL strings — there is no `text()` call to
find, so `is_migration_file` returns False and the file is not processed.

Supporting `op.*` would require:
1. Recognising the Alembic `op.create_table` / `op.add_column` / `op.drop_column`
   call patterns in the AST.
2. Mapping SQLAlchemy Column type objects to SQL type strings.
3. Building the equivalent schema Operation without going through sqlglot.

This is deferred. The fixture documents the expected skip behaviour.

## Expected behaviour

- `is_migration_file` → False (no `text()` call)
- No migration extracted
- 0 schema primitives
- Test skipped via `skip_reason` in expected.json

## sqlglot version

Tested against sqlglot 30.8.0.
