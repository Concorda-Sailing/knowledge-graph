"""Detector contract for the Rust language extractor.

Detectors receive a tree-sitter `Tree` plus the primitives already
emitted, and return mutations. Tree-sitter nodes are accessed via
`tree.root_node`; use `tree_sitter` Node API to walk.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tree_sitter import Tree


@dataclass(frozen=True)
class RelabelNode:
    node_id: str
    new_kind: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AddEdge:
    from_id: str
    to_id: str
    kind: str


@dataclass(frozen=True)
class AddNode:
    kind: str
    payload: dict[str, Any]


Mutation = RelabelNode | AddEdge | AddNode


@dataclass(frozen=True)
class DetectorContext:
    repo_key: str
    file_path: str
    project_config: dict[str, Any]


class Detector(ABC):
    name: str = ""

    @abstractmethod
    def detect(
        self,
        tree: Tree,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        ...
