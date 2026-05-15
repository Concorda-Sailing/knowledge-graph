#!/usr/bin/env python3
"""One-off: regen Concorda with framework extractors into a scratch
dir and diff against current <data>/nodes/. Acceptance criteria from
the spec: node count per kind must match within ±2% (floor ±1 node).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CONCORDA_DATA = Path.home() / "concorda-knowledge-graph" / "depgraph"
ACCEPTABLE_PCT = 0.02
ACCEPTABLE_FLOOR = 1


def count_nodes(data_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    nodes_dir = data_dir / "nodes"
    if not nodes_dir.exists():
        return counts
    for sub in nodes_dir.iterdir():
        if sub.is_dir() and not sub.name.startswith("_"):
            counts[sub.name] = sum(1 for _ in sub.glob("*.json"))
    return counts


def main() -> int:
    current = count_nodes(CONCORDA_DATA)
    print("Current Concorda node counts:")
    for k, v in sorted(current.items()):
        print(f"  {k}: {v}")

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "depgraph"
        shutil.copy(CONCORDA_DATA / "project.toml", Path(tmp))
        # User must manually craft a parity project.toml at $TMP/depgraph/project.toml
        # that points at framework extractors with the right detectors list.
        # See scripts/concorda_parity_project.toml for a reference layout.
        print(f"\nScratch dir: {scratch}")
        print("To complete parity:")
        print(f"  1. Copy scripts/concorda_parity_project.toml -> {scratch}/project.toml")
        print(f"  2. DEPGRAPH_DATA_DIR={scratch} ~/tools/knowledge-graph/depgraph/bin/depgraph regen")
        print(f"  3. Re-run this script to compute the diff after regen.")

    if "--diff" in sys.argv:
        scratch = Path(sys.argv[sys.argv.index("--diff") + 1])
        new = count_nodes(scratch)
        print("\nDiff (current -> new):")
        all_kinds = set(current) | set(new)
        regressions = []
        for k in sorted(all_kinds):
            c, n = current.get(k, 0), new.get(k, 0)
            diff = n - c
            tol = max(ACCEPTABLE_FLOOR, int(c * ACCEPTABLE_PCT))
            marker = " OK" if abs(diff) <= tol else " REGRESSION"
            print(f"  {k}: {c} -> {n} ({diff:+d}, tol ±{tol}){marker}")
            if abs(diff) > tol:
                regressions.append(k)
        return 0 if not regressions else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
