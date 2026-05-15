"""Detect service-layer functions.

A function is labeled kind=service if it lives under a directory named
`services` or `utils` (case-sensitive, at any depth) and is:
- module-level (no enclosing class),
- public (does not start with `_`),
- not already labeled by another detector running after this one.

This is a path-convention detector, not framework-detected. Lifted
from Concorda's extract_api.py extract_service_nodes().
"""
from __future__ import annotations

import ast
from typing import Any
from pathlib import PurePosixPath

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)


_SERVICE_DIRS = {"services", "utils"}


def _is_service_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return any(p in _SERVICE_DIRS for p in parts)


class ServiceDetector(Detector):
    name = "service"

    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        if not _is_service_path(ctx.file_path):
            return []
        muts: list[Mutation] = []
        for n in primitives:
            if n["kind"] != "function":
                continue
            if n.get("parent_id") is not None:
                # method, skip
                continue
            if n["name"].startswith("_"):
                continue
            muts.append(RelabelNode(
                node_id=n["id"],
                new_kind="service",
                metadata={},
            ))
        return muts
