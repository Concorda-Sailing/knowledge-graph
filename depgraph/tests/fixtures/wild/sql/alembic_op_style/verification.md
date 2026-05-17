# Verification: alembic_op_style

sqlglot version: 30.8.0

## Pre-read prediction

The migration file uses `op.create_table(...)` with no `text()` call.
`is_migration_file()` checks for a `text()` AST node — finds none — returns False.
The file is filtered out before `extract_migration` is called.
Result: 0 migrations, 0 tables, 0 warnings.

Test skips via `skip_reason` in expected.json.

## Actual (post-run)

Test skipped as expected. Confirmed: `is_migration_file` returns False for
Alembic-style files (no `text()` call in AST).

## Verdict

✓ Skip fires correctly. Alembic support remains deferred.
