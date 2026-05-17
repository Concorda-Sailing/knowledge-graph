"""Regen-determinism gate: two consecutive regens of the same source must
produce byte-identical node dirs.

This is the lightweight version of the kitchen-sink determinism check.
Uses a tiny synthetic 1-file Python project so the test completes in
under a second; lets CI run it every push without paying the full
kitchen-sink cost.
"""
from __future__ import annotations

import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tiny_project(tmp_path):
    """1-file Python project: routers.py with helper() + create_event()
    where create_event() calls helper()."""
    src = tmp_path / "repo"
    (src / "api").mkdir(parents=True)
    (src / "api/routers.py").write_text(
        "def helper(): pass\n\n"
        "def create_event():\n"
        "    helper()\n"
    )
    return src


def _regen(repo_path: Path, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([
        sys.executable, "-m", "kg.cli", "depgraph", "regen",
        "--data-dir", str(data_dir),
        "--repo-key", "api", "--repo-path", str(repo_path / "api"),
    ], capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"regen failed: stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def _normalize_meta_json(path: Path) -> None:
    """Remove the timestamp from _meta.json to allow deterministic comparison.

    The 'generated_at' field varies by execution time and has no bearing on
    the determinism of the actual extraction/classification/reconciliation.
    """
    meta_path = path / "_meta.json"
    if meta_path.exists():
        import json
        with open(meta_path) as f:
            data = json.load(f)
        # Remove the timestamp field
        data.pop("generated_at", None)
        with open(meta_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")


def _walk_diff(left: Path, right: Path) -> list[str]:
    """Recursively walk both dirs and collect any files that differ
    or exist in only one side. Returns list of human-readable diffs.
    """
    cmp = filecmp.dircmp(left, right)
    diffs: list[str] = []
    if cmp.diff_files:
        diffs.extend(f"differs: {f}" for f in cmp.diff_files)
    if cmp.left_only:
        diffs.extend(f"only in left: {f}" for f in cmp.left_only)
    if cmp.right_only:
        diffs.extend(f"only in right: {f}" for f in cmp.right_only)
    for sub in cmp.common_dirs:
        diffs.extend(_walk_diff(left / sub, right / sub))
    return diffs


def test_two_regens_produce_identical_corpus(tiny_project, tmp_path):
    """Run regen twice into separate dirs; the resulting node files must be
    byte-identical. Guards against accidental non-determinism: set iteration,
    timestamp fields, etc.

    Note: we normalize _meta.json by removing the generated_at timestamp
    since it varies by execution time and has no bearing on the determinism
    of the extraction/classification/reconciliation logic itself.
    """
    a = tmp_path / "out_a"
    b = tmp_path / "out_b"
    _regen(tiny_project, a)
    _regen(tiny_project, b)

    # Normalize timestamps so they don't affect the comparison
    _normalize_meta_json(a / "depgraph" / "nodes")
    _normalize_meta_json(b / "depgraph" / "nodes")

    diffs = _walk_diff(a, b)
    assert not diffs, "non-deterministic regen detected:\n  " + "\n  ".join(diffs)
