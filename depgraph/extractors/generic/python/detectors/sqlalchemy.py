"""Detect SQLAlchemy model classes.

A class is a model if it (transitively) inherits from `DeclarativeBase`
or any class named `Base`. We don't follow imports across files; the
heuristic is: any class with `__tablename__` assigned at class body
scope, OR any class whose base list contains a name from a configured
set of base names ("Base", "DeclarativeBase").
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)


_BASE_NAMES = {"Base", "DeclarativeBase", "BaseModel"}


def _is_model_path(path: str) -> bool:
    from pathlib import PurePosixPath
    return any(p == "models" for p in PurePosixPath(path).parts)


def _tablename(cls: ast.ClassDef) -> str | None:
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        return stmt.value.value
    return None


def _has_model_base(cls: ast.ClassDef, model_classes: set[str]) -> bool:
    for base in cls.bases:
        if isinstance(base, ast.Name) and (base.id in _BASE_NAMES or base.id in model_classes):
            return True
        if isinstance(base, ast.Attribute) and base.attr in _BASE_NAMES:
            return True
    return False


class SQLAlchemyDetector(Detector):
    name = "sqlalchemy"

    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        muts: list[Mutation] = []
        by_qualname = {
            n["id"].split(":", 2)[-1]: n
            for n in primitives if n["kind"] == "class"
        }
        model_classes: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                tn = _tablename(node)
                in_models_dir = _is_model_path(ctx.file_path)
                inherits_known_base = _has_model_base(node, model_classes)
                inherits_modelish_base = in_models_dir and any(
                    (isinstance(b, ast.Name) and b.id.endswith("Model"))
                    or (isinstance(b, ast.Attribute) and b.attr.endswith("Model"))
                    for b in node.bases
                )
                if tn or inherits_known_base or inherits_modelish_base:
                    model_classes.add(node.name)
                    prim = by_qualname.get(node.name)
                    if prim:
                        meta: dict[str, Any] = {}
                        if tn:
                            meta["tablename"] = tn
                        muts.append(RelabelNode(
                            node_id=prim["id"],
                            new_kind="model",
                            metadata=meta,
                        ))
        return muts
