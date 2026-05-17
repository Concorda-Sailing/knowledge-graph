# Verification: mixed_text_and_op

sqlglot version: 30.8.0

## Pre-read prediction

Single migration with both `text()` and `op.add_column()`.

- `is_migration_file` → True (text() call present)
- `extract_migration` walks AST for `text()` nodes only
- Finds: `text("CREATE TABLE log (id INTEGER PRIMARY KEY, msg TEXT)")`
- Parses: 1 operation, create_table, columns=[id, msg]
- `op.add_column("log", ...)` — no `text()` call → invisible → silently ignored
- Result: 1 table `log` with columns `id`, `msg` only. `level` column absent.
- No warnings (the text() arg is a plain string literal, not dynamic)

## Actual (post-run)

Both tests pass. Prediction was exact:
- 1 table `log` with columns `id`, `msg` only
- `level` column from op.add_column() absent (invisible to extractor)
- No warnings

## Verdict

✓ First-try match.
