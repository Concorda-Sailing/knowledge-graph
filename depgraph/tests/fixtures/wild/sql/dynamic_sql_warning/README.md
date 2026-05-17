# dynamic_sql_warning

## Pattern

A migration whose ONLY SQL is inside an f-string — the table name (or some
other structural part) is interpolated at runtime, making static extraction
impossible.

```python
from sqlalchemy import text

def migrate(engine, table_name):
    with engine.connect() as conn:
        conn.execute(text(f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY, val TEXT)"))
```

## Key behaviour under test

- `is_migration_file` returns True: there IS a `text()` call present.
- `extract_migration` finds the `text()` call and inspects its argument.
- The argument is a `JoinedStr` (f-string) with at least one non-literal
  expression (`{table_name}`). `_extract_string` returns
  `dynamic_reason="f-string interpolation"`.
- A warning entry is appended: `"line N: dynamic SQL skipped (f-string interpolation)"`.
- No `Operation` objects are produced → 0 schema primitives.

## sqlglot version

Tested against sqlglot 30.8.0.
