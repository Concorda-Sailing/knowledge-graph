"""Detector contract for the Python language extractor.

A detector receives the AST of one parsed file plus the AST-primitive
nodes already emitted for that file, and returns a list of mutations
that re-shape those primitives into framework-specific nodes
(endpoints, models, etc.).
"""
from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


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
    repo_path: str = ""
    """Absolute path to the repo root. Empty string if running in single-file mode."""


class Detector(ABC):
    """Abstract base. Subclasses implement detect()."""

    name: str = ""

    @abstractmethod
    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        """Return mutations to apply to `primitives`."""
