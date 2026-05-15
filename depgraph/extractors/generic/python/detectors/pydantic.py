"""Detect Pydantic schema classes.

A class is a schema if it (visibly) inherits from `BaseModel`. We
extract annotated field names from the class body.
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)

_SCHEMA_BASES = {"BaseModel"}


def _is_schema_path(path: str) -> bool:
    from pathlib import PurePosixPath
    return any(p == "schemas" for p in PurePosixPath(path).parts)


def _field_names(cls: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for stmt in cls.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            names.append(stmt.target.id)
    return names


class PydanticDetector(Detector):
    name = "pydantic"

    def detect(self, tree, primitives, ctx):
        if not _is_schema_path(ctx.file_path):
            return []
        muts: list[Mutation] = []
        by_qualname = {
            n["id"].split(":", 2)[-1]: n
            for n in primitives if n["kind"] == "class"
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if any(
                    (isinstance(b, ast.Name) and b.id in _SCHEMA_BASES)
                    or (isinstance(b, ast.Attribute) and b.attr in _SCHEMA_BASES)
                    for b in node.bases
                ):
                    prim = by_qualname.get(node.name)
                    if prim:
                        muts.append(RelabelNode(
                            node_id=prim["id"],
                            new_kind="schema",
                            metadata={"fields": _field_names(node)},
                        ))
        return muts
