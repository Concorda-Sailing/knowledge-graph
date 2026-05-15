"""TEMPLATE: copy to detectors/<your_name>.py and fill in.

A detector recognizes a specific framework or pattern in Python source.
It receives the AST plus the primitives already emitted for one file,
and returns mutations that re-label primitives or add new nodes/edges.
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation,
    RelabelNode, AddEdge, AddNode,
)


class MyDetector(Detector):
    name = "my_detector"  # TODO: rename. Matches the filename without .py.

    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        mutations: list[Mutation] = []

        # TODO: walk `tree` looking for the construct you care about.
        # TODO: for each match, look up the corresponding primitive in
        #       `primitives` by node_id, and emit a RelabelNode mutation
        #       to change its kind + add metadata.

        # Example:
        # for node in ast.walk(tree):
        #     if isinstance(node, ast.FunctionDef) and is_my_pattern(node):
        #         node_id = f"{ctx.repo_key}:{ctx.file_path}:{node.name}"
        #         mutations.append(RelabelNode(
        #             node_id=node_id,
        #             new_kind="my_kind",
        #             metadata={"extra": "info"},
        #         ))

        return mutations
