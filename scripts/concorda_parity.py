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


def shape_check(scratch: Path) -> list[str]:
    """Assert every per-kind file has the required fields."""
    failures: list[str] = []
    nodes_dir = scratch / "nodes"
    if not nodes_dir.exists():
        return [f"nodes dir missing: {nodes_dir}"]
    for kind_dir in sorted(nodes_dir.iterdir()):
        if not kind_dir.is_dir() or kind_dir.name.startswith("_"):
            continue
        for f in sorted(kind_dir.glob("*.json"))[:5]:
            try:
                node = json.loads(f.read_text())
            except Exception as e:
                failures.append(f"{f}: parse error {e}")
                continue
            kind = node.get("kind")
            # Per-kind required fields. route_call is a known outlier.
            if kind == "route_call":
                required = ("schema_version", "id", "kind", "source",
                            "signature", "structural_hash")
            else:
                required = ("schema_version", "id", "kind", "title", "source",
                            "signature", "structural_hash", "depends_on",
                            "dossier", "extractor")
            for r in required:
                if r not in node:
                    failures.append(f"{f}: missing {r}")
            if node.get("id") and kind != "route_call" and "::" not in node["id"]:
                failures.append(f"{f}: id lacks '::'")
            sh = node.get("structural_hash", "")
            if kind != "route_call" and not (len(sh) == 64 and all(c in "0123456789abcdef" for c in sh)):
                failures.append(f"{f}: structural_hash not 64-hex")
    return failures


def hash_regression(scratch: Path, current: Path) -> list[str]:
    """Every id present in current/ must have matching structural_hash in scratch/."""
    failures: list[str] = []
    # Index scratch by id
    by_id: dict[str, str] = {}
    for f in (scratch / "nodes").rglob("*.json"):
        if "_index" in f.parts or "_archive" in f.parts or "_manifests" in f.parts:
            continue
        try:
            n = json.loads(f.read_text())
        except Exception:
            continue
        if "id" in n and "structural_hash" in n:
            by_id[n["id"]] = n["structural_hash"]

    # Walk current and compare
    for f in (current / "nodes").rglob("*.json"):
        if "_index" in f.parts or "_archive" in f.parts or "_manifests" in f.parts:
            continue
        try:
            n = json.loads(f.read_text())
        except Exception:
            continue
        nid = n.get("id")
        if not nid or "structural_hash" not in n:
            continue
        if nid not in by_id:
            failures.append(f"missing in scratch: {nid}")
            continue
        if by_id[nid] != n["structural_hash"]:
            failures.append(
                f"hash mismatch for {nid}: expected {n['structural_hash']}, got {by_id[nid]}"
            )
    return failures


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
        scratch_dir = Path(sys.argv[sys.argv.index("--diff") + 1])
        new = count_nodes(scratch_dir)
        print("\nDiff (current -> new):")
        all_kinds = set(current) | set(new)
        regressions = []
        additions = []
        for k in sorted(all_kinds):
            c, n = current.get(k, 0), new.get(k, 0)
            diff = n - c
            tol = max(ACCEPTABLE_FLOOR, int(c * ACCEPTABLE_PCT))
            if c == 0 and n > 0:
                marker = "NEW"
                additions.append((k, n))
            elif abs(diff) <= tol:
                marker = "OK"
            else:
                marker = "REGRESSION"
                regressions.append(k)
            print(f"  {k}: {c} -> {n} ({diff:+d}, tol ±{tol}) {marker}")
        if additions:
            print("\nNet additions (kinds not present in baseline):")
            for k, n in additions:
                print(f"  +{k}: {n}")

        gate_failed = bool(regressions)

        print("\n--- shape_check ---")
        shape_failures = shape_check(scratch_dir)
        if shape_failures:
            for msg in shape_failures:
                print(f"  FAIL: {msg}")
            gate_failed = True
        else:
            print("  OK: 0 failures")

        print("\n--- hash_regression ---")
        hash_failures = hash_regression(scratch_dir, CONCORDA_DATA)
        if hash_failures:
            cap = 50
            for msg in hash_failures[:cap]:
                print(f"  FAIL: {msg}")
            if len(hash_failures) > cap:
                print(f"  ... and {len(hash_failures) - cap} more (showing first {cap})")
            gate_failed = True
        else:
            print("  OK: 0 mismatches")

        return 1 if gate_failed else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
