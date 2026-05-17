# self_referential_fk

## Pattern

A table with a foreign key that references itself — the classic tree/adjacency-list
pattern where `parent_id` references `node(id)`.

```sql
CREATE TABLE node (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER,
    label TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES node(id)
);
```

## Key behaviour under test

- The parser must not crash on a self-referencing FK.
- `foreign_keys` on the resulting `SchemaPrimitive` must include:
  `{column: "parent_id", references_table: "node", references_column: "id"}`
- The reconciler must not loop or choke when the FK's `references_table`
  matches the table's own name.

## Implementation note: table-level vs inline FK syntax

sqlglot 30.8 parses an inline column-level `REFERENCES` clause as a `Reference`
constraint kind on the `ColumnDef`, not as a top-level `exp.ForeignKey` node.
The parser handles both forms: `_handle_create` walks `exp.ForeignKey` nodes for
table-level declarations and calls `_inline_fk()` for inline `Reference`
constraints. Both styles produce the same `foreign_keys` output shape.

This fixture uses the explicit `FOREIGN KEY (...) REFERENCES ...` table-level
syntax to exercise the self-referential FK path specifically. Inline FK handling
is covered by `test_inline_column_fk_recorded_on_table` and
`test_mixed_inline_and_table_level_fk` in `test_parser.py`.

## sqlglot version

Tested against sqlglot 30.8.0.
