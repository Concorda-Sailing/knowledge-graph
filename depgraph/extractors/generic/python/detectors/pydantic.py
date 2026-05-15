"""Detect Pydantic schema classes.

Pre-flip extract_api.py:631-680 emits one schema node per top-level
class in `schemas/**/*.py` whose name does NOT start with `_`. No
inheritance check — schemas commonly extend other schemas (not
BaseModel directly). We mirror that exactly.

Field names come from `ast.AnnAssign` statements whose target is
`ast.Name`. The name is `target.id`; otherwise the literal "?" is
used (reproduces extract_api.py:659-663). The list is then sorted.
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)


def _is_schema_path(path: str) -> bool:
    from pathlib import PurePosixPath
    return any(p == "schemas" for p in PurePosixPath(path).parts)


def _field_names(cls: ast.ClassDef) -> list[str]:
    """Reproduce extract_api.py:659-663: AnnAssign target names, sorted.
    Non-Name targets emit '?'."""
    names: list[str] = []
    for stmt in cls.body:
        if isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name):
                names.append(stmt.target.id)
    return sorted(names)


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
        # Pre-flip selects only top-level classes (tree.body), not nested.
        if not isinstance(tree, ast.Module):
            return muts
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name.startswith("_"):
                continue
            prim = by_qualname.get(node.name)
            if not prim:
                continue
            muts.append(RelabelNode(
                node_id=prim["id"],
                new_kind="schema",
                metadata={"fields": _field_names(node)},
            ))
        return muts
