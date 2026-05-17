# Verification: self_referential_fk

sqlglot version: 30.8.0

## Pre-read prediction

Single migration creates `node(id, parent_id, label)` with a table-level
`FOREIGN KEY (parent_id) REFERENCES node(id)`.

Parser probe confirmed:
- `_handle_create` walks `exp.ForeignKey` nodes → finds the table-level FK
- Produces `foreign_keys: [{column: "parent_id", references_table: "node", references_column: "id"}]`
- Reconciler does not crash on self-referential FK (references_table == table name is just a string match)

Expected schema:
- 1 table: `node`
- Columns: `id`, `parent_id`, `label`
- FK: parent_id → node(id)
- No warnings

## Actual (post-run)

Both tests pass (2 passed). Prediction was exact:
- 1 table `node` with columns `id`, `parent_id`, `label`
- FK `parent_id → node(id)` captured correctly via table-level FOREIGN KEY syntax
- No crash from self-referential reference_table match
- No warnings

## Verdict

✓ First-try match.

## Parser gap — now closed (2026-05-17)

Inline column-level `REFERENCES` syntax (`col TYPE REFERENCES other(col)`) was
previously silently dropped by the parser. It is now handled by `_inline_fk()`
in `parser.py`, which walks `exp.Reference` constraints on `ColumnDef` nodes and
appends matching entries to `foreign_keys`. This fixture was not affected (it uses
table-level syntax), but the gap closure is noted here for completeness. See
`test_inline_column_fk_recorded_on_table` and `test_mixed_inline_and_table_level_fk`
in `test_parser.py` for the regression tests.
