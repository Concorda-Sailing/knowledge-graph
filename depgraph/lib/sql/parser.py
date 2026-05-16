"""SQL DDL parser — extracts structured operations from SQL text.

Built on sqlglot for cross-dialect tolerance (sqlite, postgres, mysql).
Returns Operation dataclasses; downstream layers convert to primitives.

AST navigation notes for sqlglot 30.8 (significantly newer than the 23.x
the plan was originally written against):

- INTEGER source text → DType.INT in AST → kind.sql() == "INT".
  Use kind.sql(dialect="sqlite") for INT-family types to recover "INTEGER".
  Note: BIGINT/SMALLINT also map to "INTEGER" in SQLite dialect — we
  instead normalise DType.INT→"INTEGER", DType.BIGINT→"BIGINT" etc by
  checking the DType enum value directly.
- VARCHAR(N) source text → kind.sql() == "VARCHAR(N)" (correct).
  Do NOT use sqlite dialect here — it would render as TEXT(N).
- ALTER TABLE DROP COLUMN → exp.Drop action (kind='COLUMN'), not a
  dedicated exp.DropColumn expression.
- ALTER COLUMN SET DEFAULT → AlterColumn with args["default"] as a Literal.
- ALTER COLUMN DROP NOT NULL → AlterColumn with args["drop"]=True and
  args["allow_null"]=True. There is NO NotNullColumnConstraint on the
  action node; the plan's isinstance check is a no-op in 30.8.
- RENAME COLUMN → exp.RenameColumn; args["to"] is a Column node (not
  Identifier), so navigate via .this.name.
- CREATE INDEX → parsed.this is Index; index name at .this.name;
  table at .args["table"].name; columns via .args["params"].args["columns"]
  (list of Ordered nodes, each wrapping a Column).
- Table-level FOREIGN KEY → exp.ForeignKey; ref.this is a Schema node;
  ref.this.this is the referenced Table, ref.this.expressions are the
  referenced column Identifiers.
- RENAME TABLE action → exp.AlterRename (not exp.RenameTable which doesn't
  exist in 30.8).
- CURRENT_TIMESTAMP default → parsed as exp.CurrentTimestamp node which
  renders as "CURRENT_TIMESTAMP()" with trailing parens. Strip the parens
  to match the contract ("CURRENT_TIMESTAMP").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import sqlglot
from sqlglot import expressions as exp


@dataclass
class Operation:
    kind: str   # create_table | alter_add_column | alter_drop_column |
                # alter_column_type | alter_column_default | alter_column_nullable |
                # drop_table | create_index | create_view | rename_table |
                # rename_column
    table: str | None = None
    if_not_exists: bool = False
    columns: list[dict[str, Any]] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)
    column: dict[str, Any] | None = None
    column_name: str | None = None
    new_column_name: str | None = None  # rename_column
    new_type: str | None = None          # alter_column_type
    new_default: str | None = None       # alter_column_default
    new_nullable: bool | None = None     # alter_column_nullable
    index_name: str | None = None
    columns_indexed: list[str] = field(default_factory=list)
    new_name: str | None = None          # rename_table


def parse_operations(sql_text: str, *, dialect: str = "sqlite") -> list[Operation]:
    """Parse one or more SQL statements. Non-DDL statements are skipped."""
    ops: list[Operation] = []
    for parsed in sqlglot.parse(sql_text, dialect=dialect):
        if parsed is None:
            continue
        if isinstance(parsed, exp.Create):
            op = _handle_create(parsed)
            if op is not None:
                ops.append(op)
        elif isinstance(parsed, exp.Alter):
            ops.extend(_handle_alter(parsed))
        elif isinstance(parsed, exp.Drop):
            op = _handle_drop(parsed)
            if op is not None:
                ops.append(op)
        # SELECT / UPDATE / INSERT / DELETE handled by db_access path, not here.
    return ops


def _type_text(kind_node: exp.DataType) -> str:
    """Return a human-readable type string that preserves source-level names.

    sqlglot normalises INT/INTEGER/TINYINT all to DType.INT and renders them
    as "INT" by default. We recover the original name for the INT-family by
    using the DType enum's string value (which equals the SQL keyword as
    written in the standard).  For all other types we use the dialect-neutral
    sql() method which preserves VARCHAR(N), TEXT, TIMESTAMP, etc correctly.
    """
    dtype = kind_node.this  # a DType enum member
    # INT-family: use the enum's string value directly (e.g. "INT", "BIGINT")
    # but map DType.INT -> "INTEGER" for SQLite convention.
    int_family = {
        exp.DataType.Type.INT: "INTEGER",
        exp.DataType.Type.TINYINT: "TINYINT",
        exp.DataType.Type.SMALLINT: "SMALLINT",
        exp.DataType.Type.BIGINT: "BIGINT",
        exp.DataType.Type.MEDIUMINT: "MEDIUMINT",
    }
    if dtype in int_family:
        return int_family[dtype]
    # For all other types (VARCHAR, TEXT, TIMESTAMP, FLOAT, etc.) the default
    # sql() method preserves the source-level name correctly.
    return kind_node.sql()


def _column_dict(coldef: exp.ColumnDef) -> dict[str, Any]:
    name = coldef.name
    type_expr = coldef.args.get("kind")
    type_text = _type_text(type_expr) if type_expr else "UNKNOWN"
    constraints = coldef.args.get("constraints") or []
    nullable = True
    primary_key = False
    default = None
    for c in constraints:
        # In sqlglot 30.8 each ColumnConstraint has a .kind attribute that is
        # the actual constraint expression (NotNullColumnConstraint, etc.)
        ck = c.args.get("kind") if hasattr(c, "args") else None
        if isinstance(ck, exp.NotNullColumnConstraint):
            nullable = False
        elif isinstance(ck, exp.PrimaryKeyColumnConstraint):
            primary_key = True
        elif isinstance(ck, exp.DefaultColumnConstraint):
            # sqlglot 30.8 renders CURRENT_TIMESTAMP as CurrentTimestamp()
            # with trailing parens. Strip them to match the source keyword.
            if isinstance(ck.this, exp.CurrentTimestamp):
                default = "CURRENT_TIMESTAMP"
            else:
                default = ck.this.sql() if ck.this else None
    return {"name": name, "type": type_text, "nullable": nullable,
            "default": default, "primary_key": primary_key}


def _handle_create(node: exp.Create) -> Operation | None:
    target = (node.args.get("kind") or "").upper()
    if target == "TABLE":
        schema = node.this
        # schema.this is a Table node; .name gives the table name
        table_name = schema.this.name if hasattr(schema, "this") else ""
        columns = []
        foreign_keys = []
        for col in (schema.expressions or []):
            if isinstance(col, exp.ColumnDef):
                columns.append(_column_dict(col))
            elif isinstance(col, exp.PrimaryKey):
                # Table-level PRIMARY KEY (a, b, ...) constraint
                pk_cols = [c.name for c in col.expressions]
                for cd in columns:
                    if cd["name"] in pk_cols:
                        cd["primary_key"] = True
            elif isinstance(col, exp.ForeignKey):
                local_cols = [c.name for c in col.expressions]
                ref = col.args.get("reference")
                if ref:
                    # ref.this is a Schema: .this is Table node, .expressions are ref columns
                    ref_table_node = ref.this.this if hasattr(ref.this, "this") else None
                    ref_table = ref_table_node.name if ref_table_node else ""
                    ref_col_nodes = ref.this.expressions if hasattr(ref.this, "expressions") else []
                    ref_cols = [e.name for e in (ref_col_nodes or [])]
                    for lc, rc in zip(local_cols, ref_cols or [""]):
                        foreign_keys.append({"column": lc, "references_table": ref_table,
                                              "references_column": rc})
        return Operation(kind="create_table", table=table_name,
                          if_not_exists=bool(node.args.get("exists")),
                          columns=columns, foreign_keys=foreign_keys)

    if target == "INDEX":
        # parsed.this is an Index node
        index_node = node.this
        index_name = index_node.this.name if hasattr(index_node.this, "name") else ""
        table_node = index_node.args.get("table")
        table = table_node.name if table_node else ""
        params = index_node.args.get("params")
        cols = []
        if params:
            for ordered in (params.args.get("columns") or []):
                # Each element is an Ordered node; .this is a Column node
                col_node = ordered.this if hasattr(ordered, "this") else ordered
                cols.append(col_node.name if hasattr(col_node, "name") else "")
        return Operation(kind="create_index", index_name=index_name,
                          table=table, columns_indexed=cols)

    if target == "VIEW":
        return Operation(kind="create_view", table=node.this.name)

    return None  # unsupported CREATE variant — skip silently


def _handle_alter(node: exp.Alter) -> list[Operation]:
    table = node.this.name
    ops: list[Operation] = []
    for action in (node.args.get("actions") or []):
        if isinstance(action, exp.ColumnDef):
            # ADD COLUMN
            ops.append(Operation(kind="alter_add_column", table=table,
                                  column=_column_dict(action)))
        elif isinstance(action, exp.Drop) and (action.args.get("kind") or "").upper() == "COLUMN":
            # DROP COLUMN: action.this is a Column node
            col_node = action.this
            col_name = col_node.name if hasattr(col_node, "name") else str(col_node)
            ops.append(Operation(kind="alter_drop_column", table=table,
                                  column_name=col_name))
        elif isinstance(action, exp.AlterRename):
            # sqlglot 30.8: RENAME TABLE action is AlterRename, not RenameTable
            ops.append(Operation(kind="rename_table", table=table,
                                  new_name=action.this.name))
        elif isinstance(action, exp.RenameColumn):
            # In sqlglot 30.8, args["to"] is a Column node, not Identifier
            to_node = action.args.get("to")
            new_name = to_node.name if to_node else ""
            ops.append(Operation(
                kind="rename_column", table=table,
                column_name=action.this.name,
                new_column_name=new_name,
            ))
        elif isinstance(action, exp.AlterColumn):
            # ALTER COLUMN can change type, default, or nullability. Each
            # surfaces as a different arg on the action node.
            # In sqlglot 30.8:
            #   ALTER COLUMN x TYPE T  → dtype=DataType node
            #   ALTER COLUMN x SET DEFAULT v → default=Literal node
            #   ALTER COLUMN x DROP NOT NULL → drop=True, allow_null=True
            col = action.this.name if hasattr(action.this, "name") else str(action.this)
            new_type_node = action.args.get("dtype")
            new_default_node = action.args.get("default")
            drop = action.args.get("drop")      # True (bool) in 30.8 for DROP NOT NULL
            allow_null = action.args.get("allow_null")

            if new_type_node is not None:
                type_str = (new_type_node.sql()
                            if hasattr(new_type_node, "sql") else str(new_type_node))
                ops.append(Operation(kind="alter_column_type", table=table,
                                       column_name=col, new_type=type_str))
            if new_default_node is not None:
                default_str = (new_default_node.sql()
                               if hasattr(new_default_node, "sql") else str(new_default_node))
                ops.append(Operation(kind="alter_column_default", table=table,
                                       column_name=col, new_default=default_str))
            # DROP NOT NULL sets allow_null=True (and drop=True as a bool flag).
            # Defensive: accept either the old isinstance path or the 30.8 bool path.
            drops_not_null = (
                allow_null is True
                or drop is True
                or isinstance(drop, exp.NotNullColumnConstraint)
                or (hasattr(drop, "sql") and "NOT NULL" in drop.sql().upper())
            )
            # But only emit if no default/type change is also present (avoid double-emit)
            if drops_not_null and new_type_node is None and new_default_node is None:
                ops.append(Operation(kind="alter_column_nullable", table=table,
                                       column_name=col, new_nullable=True))
    return ops


def _handle_drop(node: exp.Drop) -> Operation | None:
    target = (node.args.get("kind") or "").upper()
    if target == "TABLE":
        return Operation(kind="drop_table", table=node.this.name)
    # INDEX, VIEW, etc. — skip for now
    return None
