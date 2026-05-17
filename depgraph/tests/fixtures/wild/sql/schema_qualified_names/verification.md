# Verification log: schema_qualified_names

## Pre-read prediction

Without the fix: both `CREATE TABLE`s collapse to key `users`. The second
CREATE either overwrites the first or is dropped depending on
`reconcile_schema`'s replay semantics; the `ALTER` applies to whichever
survives. Result: one `users` table, columns either `[id, name, email]` or
`[id, event, email]`. Both possibilities fail the expected.json check.

With the fix: `_qualified_table_name` returns `public.users` for the first
CREATE and `analytics.users` for the second. The ALTER scoped to
`public.users` adds the `email` column to that one only. Two schema
primitives, distinct columns, no warnings.

## Prediction vs expected.json

Matches.

## Notes

The wild-SQL test asserts both table-set equality and column-set equality
per table; the column-set check picks up an accidental cross-schema merge
because the merged table would have either an extra or a missing column.
