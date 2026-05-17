# Verification: variable_sql_binding

sqlglot version: 30.8.0

## Pre-read prediction

Single migration with two `text(<Name>)` calls.

- `_collect_string_bindings` walks the module body; sees one Assign
  binding `ACCOUNTS_DDL` and one AnnAssign binding `INVITES_DDL`. Both
  have RHSs that reduce to string literals via `_extract_string` with
  empty `var_map`, so both go into the returned map.
- `extract_migration`'s walk finds two `text()` Calls. Each arg is an
  `ast.Name`, looked up in `var_map`. Both resolve to literal CREATE
  TABLE strings, parsed by sqlglot.
- 2 schema primitives emitted: `accounts`, `invites`.
- 0 warnings.

Expected after probe: tables match exactly; `expect_warnings=false`
implies `has_warnings=False`.

## Actual (post-run)

Both wild tests pass on first run.
- `test_wild_schema_matches_expected[variable_sql_binding]`: tables
  match `{accounts, invites}`; columns match the expected lists.
- `test_wild_warnings_match_expected[variable_sql_binding]`: no
  warnings emitted, matching `expect_warnings=false`.

## Verdict

✓ First-try match.
