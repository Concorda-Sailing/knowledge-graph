"""TEMPLATE: copy to detectors/<your_name>.py for Rust framework recognition."""
from __future__ import annotations
from typing import Any
from tree_sitter import Tree
from extractors.generic.rust.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode, AddEdge, AddNode,
)


class MyDetector(Detector):
    name = "my_detector"

    def detect(self, tree: Tree, primitives: list[dict[str, Any]],
               ctx: DetectorContext) -> list[Mutation]:
        muts: list[Mutation] = []
        # TODO: walk tree.root_node looking for the construct you care about.
        return muts
