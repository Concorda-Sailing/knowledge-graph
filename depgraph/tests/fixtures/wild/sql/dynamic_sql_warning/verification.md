# Verification: dynamic_sql_warning

sqlglot version: 30.8.0

## Pre-read prediction

Single migration with one f-string `text()` call.

- `is_migration_file` → True (text() node present in AST)
- `extract_migration` finds the text() call
- Arg is `ast.JoinedStr` (f-string) with `{table_name}` interpolation
- `_extract_string` returns `("", "f-string interpolation")`
- Warning appended: `"line N: dynamic SQL skipped (f-string interpolation)"`
- 0 operations produced → 0 tables after reconcile

Expected: 0 tables, `expect_warnings=true` fires, `has_warnings=True`.

Probe confirmed this exact behaviour before writing the fixture.

## Actual (post-run)

Both tests pass. Prediction was exact:
- 0 tables (no parseable SQL)
- Warning present: "line 10: dynamic SQL skipped (f-string interpolation)"
- test_wild_warnings_match_expected asserts has_warnings=True correctly

## Verdict

✓ First-try match.
