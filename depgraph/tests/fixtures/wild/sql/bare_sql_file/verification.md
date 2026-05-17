# Verification: bare_sql_file

sqlglot version: 30.8.0

## Pre-read prediction

`src.rglob("*.py")` finds no Python files (only `schema.sql` is present).
`is_migration_file` is never called. 0 migrations → 0 tables → 0 warnings.

Test skips via `skip_reason` in expected.json.

When the standalone SQL extractor is implemented, this fixture should become
active and assert tables: `author`, `book`, `review` with the foreign key chain
author ← book ← review.

## Actual (post-run)

Test skipped as expected. `rglob("*.py")` yields nothing for a `.sql`-only src.

## Verdict

✓ Skip fires correctly. Standalone SQL extractor remains deferred.
