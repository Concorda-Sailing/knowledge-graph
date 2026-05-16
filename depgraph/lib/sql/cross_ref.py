"""Cross-reference ORM mapper classes to their schema-sourced counterparts.

For each Python class that has a class-scoped variable `__tablename__`
bound to a string literal AND extends a known ORM base class, emit a
`references` edge to the schema primitive whose name matches.

The variable primitive for `__tablename__` is produced by Phase 2;
its RHS expression is recorded in `signature.value_text` (the canonical
field for raw initializer text, set by Task 2.3's `_variable_primitives`).
"""
from __future__ import annotations

import ast
from pathlib import Path


def attach_model_schema_references(primitives: list[dict]) -> list[dict]:
    """In-place: append `references` edges from each ORM model class to
    the schema-sourced class with matching name."""
    schema_by_name: dict[str, str] = {
        p["id"].split("::schema::", 1)[-1]: p["id"]
        for p in primitives
        if p.get("kind") == "schema" and "::schema::" in p["id"]
        and p["primitive"] == "class"
    }
    if not schema_by_name:
        return primitives

    # Index Python class primitives by their id and find their __tablename__
    classes_by_id = {
        p["id"]: p for p in primitives
        if p["primitive"] == "class" and p["source"]["language"] == "python"
    }
    tablename_by_class: dict[str, str] = {}
    for p in primitives:
        if (p["primitive"] == "variable"
                and p.get("owner") in classes_by_id
                and p["name"].endswith(".__tablename__")):
            # Task 2.3 records the RHS as signature.value_text. For
            # `__tablename__ = "users"`, value_text is `'"users"'` (the
            # string with quotes preserved by ast.unparse).
            tablename_value = _string_literal(p["signature"].get("value_text"))
            if tablename_value:
                tablename_by_class[p["owner"]] = tablename_value

    for class_id, tablename in tablename_by_class.items():
        schema_id = schema_by_name.get(tablename)
        if not schema_id:
            continue
        cls = classes_by_id[class_id]
        cls["edges_out"].append({
            "target": schema_id, "kind": "references",
            "via": "__tablename__",
            "where": f"{cls['source']['path']}:{cls['source']['line']}",
            "confidence": "exact",
        })
    return primitives


def _string_literal(value_text: str | None) -> str | None:
    """Unwrap a Python string literal expression to its content. Inputs come
    from `ast.unparse(node.value)`, so `"users"` -> `users`. Non-literal
    expressions (concatenations, format strings) return None -- we don't
    evaluate dynamic table names."""
    if not value_text:
        return None
    text = value_text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return None
