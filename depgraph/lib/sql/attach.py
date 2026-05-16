"""Attach migration metadata to module primitives.

Run after extraction + SQL reconciliation; mutates the matching module
primitive in place. Each migration file's `migration_order` becomes
`attributes.migration_order`; the ids of schema primitives it produced
become `attributes.up_operations`.
"""
from __future__ import annotations

from depgraph.lib.sql.migration import MigrationFile


def attach_migration_attributes(*, primitives: list[dict],
                                 migrations: list[MigrationFile]) -> None:
    # Build a map: filename -> migration_file
    by_filename = {m.path.name: m for m in migrations}

    # Build a map: table_name -> schema_primitive_id
    schema_by_name: dict[str, str] = {}
    for p in primitives:
        if p.get("kind") == "schema" and p["primitive"] == "class":
            schema_by_name[p["name"]] = p["id"]

    for p in primitives:
        if p["primitive"] != "module":
            continue
        # Path's basename is the migration filename
        path = p["source"]["path"]
        filename = path.rsplit("/", 1)[-1]
        mf = by_filename.get(filename)
        if mf is None:
            continue
        # Build up_operations: ids of schema primitives this migration
        # produced (one per CREATE TABLE / one per ALTER per column, etc.)
        up_op_ids: list[str] = []
        for mo in mf.operations:
            op = mo.operation
            if op.table and op.table in schema_by_name:
                # For CREATE/ALTER/DROP -- point at the (current-state) schema id.
                # For a DROP that removed the table from the corpus, schema
                # won't exist; record as "external::dropped::<table>".
                up_op_ids.append(schema_by_name[op.table])
            elif op.table:
                up_op_ids.append(f"external::dropped::table::{op.table}")
        p["attributes"]["migration_order"] = mf.migration_order
        p["attributes"]["up_operations"] = up_op_ids
