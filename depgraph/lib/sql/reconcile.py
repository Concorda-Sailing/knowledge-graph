"""Replay ordered migration operations to produce final-state schema primitives.

Input: list of MigrationFile (each with operations[] + migration_order).
Output: list of SchemaPrimitive (one per surviving table).

Ordering rules:
- Migrations with `migration_order != None` run first, sorted by that int.
- Migrations with `migration_order == None` run after, sorted by filename.
- Tables touched by later `ALTER TABLE` accumulate the column changes.
- Tables dropped by `DROP TABLE` are removed from the output set.
- `CREATE INDEX` emits a references edge from the table primitive to the
  indexed column (stored on the table's `attributes.indexes[]`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from depgraph.lib.sql.migration import MigrationFile


@dataclass
class SchemaPrimitive:
    """A reconciled table after replaying all migrations."""
    id: str
    name: str
    kind: str = "schema"
    primitive: str = "class"
    columns: list[dict[str, Any]] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)
    indexes: list[dict[str, Any]] = field(default_factory=list)
    source: dict[str, Any] = field(default_factory=dict)
    defined_by: list[str] = field(default_factory=list)  # migration paths
    schema_version: int = 2


def _ordered(migrations: list[MigrationFile]) -> list[MigrationFile]:
    numbered = sorted(
        [m for m in migrations if m.migration_order is not None],
        key=lambda m: m.migration_order,
    )
    unnumbered = sorted(
        [m for m in migrations if m.migration_order is None],
        key=lambda m: m.path.name,
    )
    return numbered + unnumbered


def reconcile_schema(migrations: list[MigrationFile], *, repo_key: str) -> list[SchemaPrimitive]:
    tables: dict[str, SchemaPrimitive] = {}

    for migration in _ordered(migrations):
        mig_path = str(migration.path)
        for mo in migration.operations:
            op = mo.operation
            if op.kind == "create_table":
                if op.table in tables:
                    # IF NOT EXISTS — silently skip duplicate CREATE
                    if op.if_not_exists:
                        tables[op.table].defined_by.append(mig_path)
                        continue
                tables[op.table] = SchemaPrimitive(
                    id=f"{repo_key}::schema::{op.table}",
                    name=op.table,
                    columns=list(op.columns),
                    foreign_keys=list(op.foreign_keys),
                    source={
                        "repo": repo_key,
                        "path": str(migration.path),
                        "language": "sql",
                        "line": mo.source_line,
                        "end_line": mo.source_line,
                    },
                    defined_by=[mig_path],
                )
            elif op.kind == "alter_add_column":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                tbl.columns.append(op.column)
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_drop_column":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                tbl.columns = [c for c in tbl.columns if c["name"] != op.column_name]
                # GC: drop any index that referenced this column
                tbl.indexes = [idx for idx in tbl.indexes
                               if op.column_name not in idx.get("columns", [])]
                # GC: drop any FK originating from this column
                tbl.foreign_keys = [fk for fk in tbl.foreign_keys
                                    if fk.get("column") != op.column_name]
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_column_type":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["type"] = op.new_type
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_column_default":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["default"] = op.new_default
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_column_nullable":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["nullable"] = bool(op.new_nullable)
                tbl.defined_by.append(mig_path)
            elif op.kind == "rename_column":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["name"] = op.new_column_name
                # Rewrite references to old column name in indexes / FKs
                for idx in tbl.indexes:
                    idx["columns"] = [op.new_column_name if n == op.column_name else n
                                       for n in idx.get("columns", [])]
                for fk in tbl.foreign_keys:
                    if fk.get("column") == op.column_name:
                        fk["column"] = op.new_column_name
                tbl.defined_by.append(mig_path)
            elif op.kind == "drop_table":
                tables.pop(op.table, None)
                # GC: any other table's FK pointing at the dropped table is dangling
                for other in tables.values():
                    other.foreign_keys = [fk for fk in other.foreign_keys
                                           if fk.get("references_table") != op.table]
            elif op.kind == "rename_table":
                tbl = tables.pop(op.table, None)
                if tbl is None:
                    continue
                # Rewrite incoming FKs from any other table that referenced the old name
                for other in tables.values():
                    for fk in other.foreign_keys:
                        if fk.get("references_table") == op.table:
                            fk["references_table"] = op.new_name
                tbl.name = op.new_name
                tbl.id = f"{repo_key}::schema::{op.new_name}"
                tbl.defined_by.append(mig_path)
                tables[op.new_name] = tbl
            elif op.kind == "create_index":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                tbl.indexes.append({"name": op.index_name, "columns": op.columns_indexed})
                tbl.defined_by.append(mig_path)

    return list(tables.values())


# ── Task 4.4: emit schema primitives as wire-format dicts ──────────────────

from depgraph.lib.primitives import compute_hash, structural_hash_payload

EXTRACTOR_TAG = "depgraph/lib/sql/reconcile.py@2026-05-16"


def schema_to_primitives(tables: list[SchemaPrimitive]) -> list[dict]:
    """Convert SchemaPrimitive dataclasses into wire-format primitive dicts.
    One class primitive per table; one variable primitive per column.

    Hash payloads use the spec-aligned shape (primitive / name / signature
    / body_text) via `structural_hash_payload` — same as Python and TS
    extractors. A schema-sourced `users` class and a Python `users` class
    hash differently because their `signature` differs, but the *payload
    shape* is identical across languages.
    """
    prims: list[dict] = []
    for t in tables:
        table_id = t.id
        table_signature = {
            "decorators": [],
            "primary_key": [c["name"] for c in t.columns if c.get("primary_key")],
            "foreign_keys": list(t.foreign_keys),
            "indexes": list(t.indexes),
        }
        table_body = repr([
            {"name": c["name"], "type": c["type"], "nullable": c["nullable"],
             "default": c.get("default")}
            for c in t.columns
        ])
        table_prim = {
            "schema_version": 2,
            "id": table_id,
            "primitive": "class",
            "name": t.name,
            "owner": None,
            "source": dict(t.source),
            "signature": table_signature,
            "attributes": {
                "abstract": False, "generated": False, "external": False,
                "template_parameters": [], "macro": False, "mutable": False,
                "instantiable": True, "inheritable": False,
                "defined_by": list(t.defined_by),
            },
            "edges_out": [],
            "structural_hash": compute_hash(structural_hash_payload(
                primitive="class", name=t.name,
                signature=table_signature, body_text=table_body,
            )),
            "kind": "schema",
            "extractor": EXTRACTOR_TAG,
        }
        prims.append(table_prim)

        for c in t.columns:
            col_id = f"{table_id}.{c['name']}"
            col_signature = {
                "type_annotation": c["type"],
                "value_text": c.get("default"),
            }
            col_body = c.get("default") or ""
            prims.append({
                "schema_version": 2,
                "id": col_id,
                "primitive": "variable",
                "name": f"{t.name}.{c['name']}",
                "owner": table_id,
                "source": dict(t.source),
                "signature": col_signature,
                "attributes": {
                    "abstract": False, "generated": False, "external": False,
                    "template_parameters": [], "macro": False,
                    "mutable": True, "instantiable": False, "inheritable": False,
                    "nullable": c["nullable"], "primary_key": c.get("primary_key", False),
                    "default": c.get("default"),
                },
                "edges_out": [],
                "structural_hash": compute_hash(structural_hash_payload(
                    primitive="variable", name=f"{t.name}.{c['name']}",
                    signature=col_signature, body_text=col_body,
                )),
                "kind": None,
                "extractor": EXTRACTOR_TAG,
            })
    return prims
