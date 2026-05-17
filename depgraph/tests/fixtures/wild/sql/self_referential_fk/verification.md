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

Note: inline column-level `REFERENCES` syntax is silently dropped by the parser
(parsed as a `Reference` constraint kind, not `exp.ForeignKey`). Documented in
README as a known parser limitation.

## Actual (post-run)

Both tests pass (2 passed). Prediction was exact:
- 1 table `node` with columns `id`, `parent_id`, `label`
- FK `parent_id → node(id)` captured correctly via table-level FOREIGN KEY syntax
- No crash from self-referential reference_table match
- No warnings

## Verdict

✓ First-try match.
