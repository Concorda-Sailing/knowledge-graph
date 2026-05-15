"""Detect FastAPI endpoint definitions.

A function is an endpoint if its decorator list contains
`<obj>.<http_method>(...)` where http_method is one of
get/post/put/patch/delete/options/head, and <obj> is plausibly a
FastAPI / APIRouter instance (we don't try to type-resolve; the
decorator shape is enough in practice).
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)

_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _endpoint_decorator(dec: ast.expr) -> tuple[str, str] | None:
    """If `dec` is a FastAPI route decorator, return (METHOD, route).
    Otherwise None."""
    if not isinstance(dec, ast.Call):
        return None
    func = dec.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in _METHODS:
        return None
    if not dec.args:
        return None
    first = dec.args[0]
    if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
        return None
    return func.attr.upper(), first.value


class FastAPIDetector(Detector):
    name = "fastapi"

    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        muts: list[Mutation] = []
        by_qualname: dict[str, dict] = {}
        for n in primitives:
            if n["kind"] == "function":
                qual = n["id"].split(":", 2)[-1]
                by_qualname[qual] = n

        class V(ast.NodeVisitor):
            def __init__(self):
                self.class_stack: list[str] = []

            def visit_ClassDef(self, node: ast.ClassDef):
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()

            def _visit_fn(self, node):
                qual = ".".join(self.class_stack + [node.name])
                prim = by_qualname.get(qual)
                if not prim:
                    return
                for dec in node.decorator_list:
                    result = _endpoint_decorator(dec)
                    if result:
                        method, route = result
                        muts.append(RelabelNode(
                            node_id=prim["id"],
                            new_kind="endpoint",
                            metadata={"route": route, "method": method},
                        ))
                        break
                self.generic_visit(node)

            visit_FunctionDef = _visit_fn
            visit_AsyncFunctionDef = _visit_fn

        V().visit(tree)
        return muts
