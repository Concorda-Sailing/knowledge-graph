"""Detect pytest test functions/methods.

A function is a test if:
- the file matches `test_*.py` or `*_test.py`, AND
- the function name starts with `test_`, AND
- if inside a class, the class name starts with `Test`.
"""
from __future__ import annotations

import ast
from typing import Any
from pathlib import PurePosixPath

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)


def _is_test_file(path: str) -> bool:
    name = PurePosixPath(path).name
    if not name.endswith(".py"):
        return False
    return name.startswith("test_") or name.endswith("_test.py")


class PytestDetector(Detector):
    name = "pytest"

    def detect(self, tree, primitives, ctx):
        if not _is_test_file(ctx.file_path):
            return []
        by_qualname = {
            n["id"].split(":", 2)[-1]: n
            for n in primitives if n["kind"] == "function"
        }
        muts: list[Mutation] = []

        class V(ast.NodeVisitor):
            def __init__(self):
                self.class_stack: list[str] = []

            def visit_ClassDef(self, node):
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()

            def _visit_fn(self, node):
                if self.class_stack:
                    if not all(c.startswith("Test") for c in self.class_stack):
                        return
                if not node.name.startswith("test_"):
                    return
                qual = ".".join(self.class_stack + [node.name])
                prim = by_qualname.get(qual)
                if prim:
                    muts.append(RelabelNode(
                        node_id=prim["id"], new_kind="test", metadata={},
                    ))

            visit_FunctionDef = _visit_fn
            visit_AsyncFunctionDef = _visit_fn

        V().visit(tree)
        return muts
