"""db_access edge recognition — targets schema-sourced primitives.

The pipeline:
  1. Recognize `session.query(X)`, `db.add(x)`, `cursor.execute(text("..."))`
     and similar SDK patterns inside Python function bodies.
  2. Resolve the argument to a Python class primitive (via local symbol
     index + import resolution).
  3. Follow the Python class's `references -> schema` edge to find the
     schema primitive.
  4. Emit db_access edge from the calling function to the schema primitive
     with confidence=exact.

Fallbacks:
- If the argument doesn't resolve to a known class, emit confidence=unresolved
  with the function name as `via` and no target (or `external::unresolved::<symbol>` if a
  target field is required).
- If the argument resolves to a Python class with no schema reference, emit
  confidence=unresolved targeting the Python class.
- For `cursor.execute(text("SELECT ... FROM users ..."))` (raw SQL outside
  migrations), parse the SQL with sqlglot, identify each referenced table,
  emit one db_access edge per table.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import sqlglot
from sqlglot import expressions as exp


_SESSION_METHODS = {"query", "add", "commit", "execute", "scalars",
                    "scalar", "delete", "merge", "flush", "rollback"}
_CURSOR_METHODS = {"execute", "executemany", "fetchone", "fetchall", "fetchmany"}

# All db_access fallback edges target `external::unresolved::db_target` /
# `external::unresolved::table::<name>`, so the prefix-based mapping pins
# them to the typed-receiver bucket. Issue #53 Option A.
_UNRESOLVED_DB_TARGET_CONFIDENCE = "unresolved_receiver"


def attach_db_access_edges(primitives: list[dict], *, repo_path: Path) -> list[dict]:
    schema_by_name = {
        p["name"]: p["id"] for p in primitives
        if p.get("kind") == "schema" and p["primitive"] == "class"
    }
    # Python class id -> schema id (via references edges)
    schema_ids = set(schema_by_name.values())
    py_class_to_schema: dict[str, str] = {}
    py_classes_by_id: dict[str, dict] = {}
    for p in primitives:
        if p["primitive"] == "class" and p["source"]["language"] == "python":
            py_classes_by_id[p["id"]] = p
            for e in p["edges_out"]:
                if e["kind"] == "references" and e["target"] in schema_ids:
                    py_class_to_schema[p["id"]] = e["target"]

    # Build a per-file local-name -> python-class-id index
    by_path: dict[str, list[dict]] = {}
    for p in primitives:
        if p["source"]["language"] != "python":
            continue
        by_path.setdefault(p["source"]["path"], []).append(p)

    for path, prims_in_file in by_path.items():
        local_names: dict[str, str] = {}
        for p in prims_in_file:
            if p["primitive"] == "class" and p.get("owner") is None:
                local_names[p["name"]] = p["id"]

        # Imported names: scan import edges on the module primitive.
        # Per the import-edge convention (Phase 3.3), each import edge
        # carries `local_binding` = the name as bound in the importing
        # file. For `from X import User as TheUser`, local_binding =
        # "TheUser"; for unaliased imports, it equals the target symbol.
        module = next((p for p in prims_in_file if p["primitive"] == "module"), None)
        if module:
            for e in module["edges_out"]:
                if e["kind"] != "imports":
                    continue
                if e["target"] not in py_classes_by_id:
                    continue
                imported_cls = py_classes_by_id[e["target"]]
                local_binding = e.get("local_binding") or imported_cls["name"]
                local_names[local_binding] = e["target"]

        full_path = repo_path / path
        if not full_path.is_file():
            continue
        source_text = full_path.read_text()
        try:
            tree = ast.parse(source_text)
        except SyntaxError:
            continue
        fn_by_line = {p["source"]["line"]: p
                      for p in prims_in_file if p["primitive"] == "function"}

        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fn_prim = fn_by_line.get(fn_node.lineno)
            if not fn_prim:
                continue
            # Track local variable types from parameter annotations
            param_types: dict[str, str] = {}
            for arg in fn_node.args.args:
                if arg.annotation is not None:
                    ann = ast.unparse(arg.annotation)
                    param_types[arg.arg] = ann.split("[")[0].strip()

            for sub in ast.walk(fn_node):
                if not isinstance(sub, ast.Call):
                    continue
                if isinstance(sub.func, ast.Attribute):
                    method = sub.func.attr
                    receiver = ast.unparse(sub.func.value)
                    # Pattern A: session.<method>(...)
                    if method in _SESSION_METHODS:
                        _emit_session_edge(fn_prim, sub, method, receiver, path,
                                           local_names, py_class_to_schema, param_types)
                    # Pattern B: cursor.execute(text("..."))
                    if method in _CURSOR_METHODS:
                        _emit_cursor_edge(fn_prim, sub, method, receiver, path,
                                          schema_by_name)
    return primitives


def _emit_session_edge(fn_prim, call, method, receiver, path,
                       local_names, py_class_to_schema, param_types):
    """Resolve session.<method>(<arg>) target and emit edge."""
    arg = call.args[0] if call.args else None
    # Sentinel target used when the resolver can't pin a schema primitive;
    # confidence falls into the `unresolved_receiver` bucket (the typed-
    # receiver gap, since `session`/`db` here is itself a method-receiver
    # whose target table couldn't be inferred). See edges.confidence_for_external_target.
    target_id, confidence = None, _UNRESOLVED_DB_TARGET_CONFIDENCE

    if isinstance(arg, ast.Name):
        # session.query(User) -- resolve `User` via local names
        class_id = local_names.get(arg.id)
        if class_id and class_id in py_class_to_schema:
            target_id, confidence = py_class_to_schema[class_id], "exact"
        elif arg.id in param_types:
            # session.add(user) where user: User
            class_id = local_names.get(param_types[arg.id])
            if class_id and class_id in py_class_to_schema:
                target_id, confidence = py_class_to_schema[class_id], "exact"
    # else: text() call, attribute access, dynamic -- unresolved

    fn_prim["edges_out"].append({
        "target": target_id or "external::unresolved::db_target",
        "kind": "db_access",
        "via": f"{receiver}.{method}",
        "where": f"{path}:{call.lineno}",
        "confidence": confidence,
    })


def _emit_cursor_edge(fn_prim, call, method, receiver, path, schema_by_name):
    """For cursor.execute(text("SELECT ... FROM <table>")), parse SQL and
    emit one edge per referenced table that resolves to a schema primitive."""
    arg = call.args[0] if call.args else None
    sql_text = None
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "text":
        if arg.args and isinstance(arg.args[0], ast.Constant) and isinstance(arg.args[0].value, str):
            sql_text = arg.args[0].value
    elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        sql_text = arg.value

    if not sql_text:
        fn_prim["edges_out"].append({
            "target": "external::unresolved::db_target", "kind": "db_access",
            "via": f"{receiver}.{method}", "where": f"{path}:{call.lineno}",
            "confidence": _UNRESOLVED_DB_TARGET_CONFIDENCE,
        })
        return

    tables = _tables_referenced_by_sql(sql_text)
    if not tables:
        fn_prim["edges_out"].append({
            "target": "external::unresolved::db_target", "kind": "db_access",
            "via": f"{receiver}.{method}", "where": f"{path}:{call.lineno}",
            "confidence": _UNRESOLVED_DB_TARGET_CONFIDENCE,
        })
        return

    for table_name in tables:
        target_id = schema_by_name.get(table_name)
        if target_id:
            fn_prim["edges_out"].append({
                "target": target_id, "kind": "db_access",
                "via": f"{receiver}.{method}(SQL)",
                "where": f"{path}:{call.lineno}",
                "confidence": "exact",
            })
        else:
            fn_prim["edges_out"].append({
                "target": f"external::unresolved::table::{table_name}",
                "kind": "db_access", "via": f"{receiver}.{method}(SQL)",
                "where": f"{path}:{call.lineno}",
                "confidence": _UNRESOLVED_DB_TARGET_CONFIDENCE,
            })


def _tables_referenced_by_sql(sql_text: str) -> list[str]:
    """Return the list of table names that the SQL reads from or writes to."""
    try:
        parsed = sqlglot.parse(sql_text, dialect="sqlite")
    except sqlglot.errors.ParseError:
        return []
    names: list[str] = []
    for stmt in parsed:
        if stmt is None:
            continue
        for tbl in stmt.find_all(exp.Table):
            names.append(tbl.name)
    # Deduplicate while preserving order
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n); out.append(n)
    return out
