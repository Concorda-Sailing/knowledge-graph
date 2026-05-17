# Verification: multi_dialect_create

sqlglot version: 30.8.0

## Pre-read prediction

Three migration files create the same `product` table with `IF NOT EXISTS`.
The reconciler applies them in numeric order (001 → 002 → 003).

- 001 (order=1): actual CREATE succeeds → product table exists with SQLite types.
  id=INTEGER, name=TEXT, price=FLOAT (sqlglot renders REAL as FLOAT), stock=INTEGER.
- 002 (order=2): IF NOT EXISTS + table already present → `defined_by` appended, no column change.
- 003 (order=3): same as 002 — silently skipped.

Final schema:
- 1 table: `product`
- Columns: `id`, `name`, `price`, `stock`
- No warnings

Column types in expected.json are not asserted by the harness (only names), so
the FLOAT-vs-REAL rendering difference does not affect pass/fail.

## Actual (post-run)

Both tests pass (2 passed, 0 failed). Prediction was exact:
- 1 table `product` with columns `id`, `name`, `price`, `stock`
- No warnings
- 002 and 003 silently skipped via `if_not_exists` branch as predicted

## Verdict

✓ First-try match. No surprises.
