# bare_sql_file

## Pattern

A standalone `.sql` file containing three `CREATE TABLE` statements — no Python
wrapper, no `text()` call:

```sql
CREATE TABLE author (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE book (id INTEGER PRIMARY KEY, author_id INTEGER, title TEXT NOT NULL);
CREATE TABLE review (id INTEGER PRIMARY KEY, book_id INTEGER, rating INTEGER);
```

## Why this is out of scope (for now)

The migration pipeline is Python-first: `is_migration_file` accepts `.py` files
containing `text(...)` calls. Bare `.sql` files would need a separate extractor
that reads the file directly as SQL — there is no Python AST to walk.

The language registry (`languages.toml`) lists SQL as a recognised language, but
the standalone SQL file extractor is deferred per the plan's "Out of scope" note:
"schema-language extractors other than via migration are deferred."

When the SQL file extractor ships, this fixture should become non-skipped and
assert 3 tables: `author`, `book`, `review`.

## Expected behaviour

- `src.rglob("*.py")` finds no files (only a `.sql` file exists)
- 0 migrations → 0 tables
- Test skipped via `skip_reason` in expected.json

## sqlglot version

Tested against sqlglot 30.8.0.
