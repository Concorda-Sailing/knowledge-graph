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


@pytest.fixture
def realistic_python_project(tmp_path):
    """A multi-file Python project that exercises constructs the tiny
    fixture skips: classes with @property / @classmethod / @staticmethod,
    async methods, type-annotated signatures, decorator-with-args, set /
    dict / frozenset literals in function bodies, multi-target except
    clauses, comprehensions, inheritance, module-level constants.

    Each of these is a place set-iteration or hash-randomized ordering
    has historically leaked into `ast.unparse`-derived `body_text` or
    into the signature payload. The kitchen-sink covers most of these,
    but this fixture is small enough to run every push without paying
    the full kitchen-sink cost.
    """
    src = tmp_path / "repo"
    api = src / "api"
    api.mkdir(parents=True)

    (api / "models.py").write_text(
        "from __future__ import annotations\n"
        "from typing import Optional\n\n"
        "STATUSES: frozenset[str] = frozenset(('active', 'pending', 'archived'))\n"
        "ROLE_PRIORITY: dict[str, int] = {'owner': 0, 'editor': 1, 'viewer': 2}\n\n"
        "class Boat:\n"
        "    archived_at: Optional[str] = None\n"
        "    def __init__(self, owner_id: int, crews: list[int]) -> None:\n"
        "        self.owner_id = owner_id\n"
        "        self.crews = crews\n"
        "    @property\n"
        "    def is_archived(self) -> bool:\n"
        "        return self.archived_at is not None\n"
        "    @classmethod\n"
        "    def from_dict(cls, d: dict) -> 'Boat':\n"
        "        return cls(d['owner_id'], d.get('crews', []))\n"
        "    @staticmethod\n"
        "    def known_statuses() -> set[str]:\n"
        "        return {'active', 'pending', 'archived', 'draft'}\n\n"
        "class CrewBoat(Boat):\n"
        "    def __init__(self, owner_id: int, crews: list[int], captain: int) -> None:\n"
        "        super().__init__(owner_id, crews)\n"
        "        self.captain = captain\n"
    )

    (api / "auth.py").write_text(
        "from __future__ import annotations\n"
        "from .models import Boat, STATUSES\n\n"
        "def _is_boat_owner(user, boat: Boat) -> bool:\n"
        "    \"\"\"Check if user owns boat. Mirrors the #45 repro case.\"\"\"\n"
        "    if not getattr(user, 'is_authenticated', False):\n"
        "        return False\n"
        "    if boat.is_archived:\n"
        "        return False\n"
        "    statuses = {'active', 'pending'}\n"
        "    if getattr(boat, 'status', None) not in statuses:\n"
        "        return False\n"
        "    return any(c == user.id for c in boat.crews) or user.id == boat.owner_id\n\n"
        "async def load_owner_boats(user_id: int) -> list[int]:\n"
        "    rows = [i for i in range(10) if i % 2 == 0]\n"
        "    return rows\n\n"
        "def parse(payload: dict) -> dict:\n"
        "    try:\n"
        "        return {k: v for k, v in payload.items() if k in STATUSES}\n"
        "    except (KeyError, ValueError, TypeError) as e:\n"
        "        return {'error': str(e)}\n"
    )
    return src


def _regen_generic(repo_path: Path, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([
        sys.executable, "-m", "kg.cli", "depgraph", "regen",
        "--data-dir", str(data_dir),
        "--repo-key", "api", "--repo-path", str(repo_path / "api"),
    ], capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"regen failed: stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_realistic_python_two_regens_produce_identical_corpus(
    realistic_python_project, tmp_path
):
    """Pin determinism against the realistic Python patterns from #45.

    The tiny fixture (two top-level functions, no classes / decorators /
    annotations / comprehensions / set or dict literals) doesn't exercise
    most of the surfaces where `ast.unparse`-derived `body_text` can drift
    across processes. This fixture does, and runs each regen in a fresh
    subprocess so PYTHONHASHSEED varies per the standard CPython startup
    behavior — surfacing any set-iteration-order leakage into the hash
    payload.
    """
    a = tmp_path / "out_a"
    b = tmp_path / "out_b"
    _regen_generic(realistic_python_project, a)
    _regen_generic(realistic_python_project, b)

    _normalize_meta_json(a / "depgraph" / "nodes")
    _normalize_meta_json(b / "depgraph" / "nodes")

    diffs = _walk_diff(a, b)
    assert not diffs, "non-deterministic regen detected:\n  " + "\n  ".join(diffs)
