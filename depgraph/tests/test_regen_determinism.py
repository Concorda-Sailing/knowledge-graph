"""Regen-determinism gate: two consecutive regens of the same source must
produce byte-identical node dirs.

This is the lightweight version of the kitchen-sink determinism check.
Uses a tiny synthetic 1-file Python project so the test completes in
under a second; lets CI run it every push without paying the full
kitchen-sink cost.
"""
from __future__ import annotations

import filecmp
import os
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


@pytest.fixture
def hash_seed_sensitive_project(tmp_path):
    """A multi-file Python project that pins the broader shape inventory
    from the #45 hypothesis list — every construct that has historically
    been a leak path for set/dict iteration order into the structural
    hash:

      * set literals at module, class, method, function, and decorator-arg
        scope — multiple sizes, including ones that cross CPython's
        small-set / hash-distribution thresholds.
      * frozenset literals and frozenset(...) calls.
      * dict literals with many keys, including nested set values.
      * set comprehensions, dict comprehensions, nested dict-of-set
        comprehensions.
      * decorators with kwargs (incl. set-valued kwargs) — `@cached(...)`.
      * decorators stacked + ordered.
      * classes carrying @property / @classmethod / @staticmethod /
        async methods.
      * dataclass field default_factory returning a set / dict / nested set.
      * multi-base inheritance + ABCs.
      * multi-target `except (A, B, C) as e:` clauses.
      * pattern matching (3.10+) with set patterns when available.
      * lambda default args with set / dict literals.

    Each is a place where if any extractor code path replaced "preserve
    source order" with "iterate a set / unsorted dict," structural hash
    would drift across processes whose `PYTHONHASHSEED` differs.
    """
    src = tmp_path / "repo"
    api = src / "api"
    api.mkdir(parents=True)

    (api / "models.py").write_text(
        "from __future__ import annotations\n"
        "from typing import Optional, Union\n"
        "from dataclasses import dataclass, field\n"
        "from functools import lru_cache\n"
        "from abc import ABC, abstractmethod\n\n"
        "# Module-level set / frozenset / dict literals, multiple sizes.\n"
        "STATUSES: frozenset[str] = frozenset(('active', 'pending', 'archived', 'draft', 'sealed'))\n"
        "ROLE_PRIORITY: dict[str, int] = {'owner': 0, 'editor': 1, 'viewer': 2, 'guest': 3, 'admin': 4}\n"
        "TAG_SET = {'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'cyan', 'magenta'}\n"
        "NESTED: dict[str, set[str]] = {'a': {'x', 'y', 'z'}, 'b': {'p', 'q', 'r'}, 'c': {'l', 'm', 'n'}}\n"
        "SMALL_SET = {'one'}\n"
        "LARGE_SET = {f'item-{i}' for i in range(50)}\n\n"
        "@dataclass(frozen=True, kw_only=True)\n"
        "class Boat:\n"
        "    owner_id: int\n"
        "    crews: list = field(default_factory=list)\n"
        "    statuses: set = field(default_factory=lambda: {'a', 'b', 'c', 'd', 'e', 'f'})\n"
        "    tags: dict = field(default_factory=lambda: {'x': 1, 'y': 2, 'z': 3, 'w': 4, 'q': 5})\n"
        "    nested: dict = field(default_factory=lambda: {'k': {'a', 'b'}, 'm': {'c', 'd'}})\n\n"
        "    @property\n"
        "    def is_archived(self) -> bool: return False\n\n"
        "    @classmethod\n"
        "    def from_dict(cls, d) -> 'Boat': return cls(owner_id=d['owner_id'])\n\n"
        "    @staticmethod\n"
        "    def statuses_known() -> set[str]:\n"
        "        return {'active', 'pending', 'draft', 'sealed', 'expired', 'reopened', 'closed'}\n\n"
        "    async def update(self, **kw) -> None:\n"
        "        await self._touch()\n\n"
        "    async def _touch(self) -> None: pass\n\n"
        "class Mixin(ABC):\n"
        "    @abstractmethod\n"
        "    def foo(self): ...\n\n"
        "class CrewBoat(Boat, Mixin):\n"
        "    @lru_cache(maxsize=64)\n"
        "    def heavy_call(self, x: int, y: int = 1, *args, **kwargs) -> Union[int, str, None]:\n"
        "        try:\n"
        "            d = {k: v for k, v in {'a': 1, 'b': 2, 'c': 3, 'd': 4}.items()}\n"
        "            s = {f'item-{i}' for i in range(10)}\n"
        "            nested_comp = {k: {v*2 for v in range(3)} for k in ('a', 'b', 'c')}\n"
        "            return d['a']\n"
        "        except (KeyError, ValueError, TypeError, IndexError, AttributeError) as e:\n"
        "            return str(e)\n"
        "        except Exception:\n"
        "            return None\n\n"
        "    def foo(self): return 1\n"
    )

    (api / "auth.py").write_text(
        "from __future__ import annotations\n"
        "from .models import Boat, STATUSES, TAG_SET\n\n"
        "def cached(**kwargs): return lambda f: f\n\n"
        "# Decorator with set / dict / frozenset kwargs at the call site.\n"
        "@cached(ttl=60, maxsize=1024, key='lookup',\n"
        "         tags={'a', 'b', 'c', 'd', 'e', 'f', 'g'},\n"
        "         nested={'k': 1, 'm': 2, 'n': 3, 'p': 4, 'q': 5})\n"
        "def _is_boat_owner(user, boat: Boat) -> bool:\n"
        "    \"\"\"Mirror of #45 repro case.\"\"\"\n"
        "    if not getattr(user, 'is_authenticated', False): return False\n"
        "    if boat.is_archived: return False\n"
        "    statuses = {'active', 'pending', 'draft', 'sealed', 'expired', 'closed'}\n"
        "    if getattr(boat, 'status', None) not in statuses: return False\n"
        "    return any(c == user.id for c in boat.crews) or user.id == boat.owner_id\n\n"
        "# Lambda with dict / set defaults.\n"
        "build_index = lambda d={'a': 1, 'b': 2, 'c': 3, 'd': 4}, s={'x','y','z','w'}: (d, s)\n\n"
        "async def load_owner_boats(user_id: int) -> list[int]:\n"
        "    rows = [i for i in range(10) if i % 2 == 0]\n"
        "    by_tag = {t: i for i, t in enumerate(TAG_SET)}\n"
        "    seen = {i*2 for i in range(5)}\n"
        "    nested_comp = {k: {v*2 for v in range(3)} for k in ('a', 'b', 'c', 'd')}\n"
        "    return rows\n\n"
        "def parse(payload: dict) -> dict:\n"
        "    try:\n"
        "        return {k: v for k, v in payload.items() if k in STATUSES}\n"
        "    except (KeyError, ValueError, TypeError, IndexError, AttributeError, RuntimeError) as e:\n"
        "        return {'error': str(e)}\n"
    )
    return src


def _regen_with_env(repo_path: Path, data_dir: Path, env_extra: dict[str, str]) -> None:
    """Run regen in a subprocess with env overrides.

    Used to drive PYTHONHASHSEED apart across the two runs — the standard
    Python startup behavior already randomizes per-process, but pinning
    explicit mismatched seeds makes the failure mode deterministic if any
    set/frozenset iteration order leaks into the hash payload.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, **env_extra}
    proc = subprocess.run([
        sys.executable, "-m", "kg.cli", "depgraph", "regen",
        "--data-dir", str(data_dir),
        "--repo-key", "api", "--repo-path", str(repo_path / "api"),
    ], capture_output=True, text=True, env=env)
    assert proc.returncode == 0, (
        f"regen failed: stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


@pytest.mark.parametrize("seed_a,seed_b", [
    ("1", "2"),
    ("1", "42"),
    ("12345", "999"),
])
def test_regen_deterministic_under_mismatched_hash_seed(
    hash_seed_sensitive_project, tmp_path, seed_a, seed_b
):
    """Force PYTHONHASHSEED to differ between two regens of the same source
    and assert the on-disk corpus is still byte-identical.

    Catches the #45 hypothesis (`structural_hash` drift across regen
    runs) at its most likely root cause: a code path that builds the
    hash payload by iterating a `set` / `frozenset` / unsorted-dict
    derived from the source AST. Standard `ast.unparse` preserves source
    order for set/dict literals, so the hash *should* be stable here —
    but if any extractor or post-extraction pass introduced an iteration
    over a `set` that ends up in `signature` / `structural_payload` /
    `edges_out`, mismatched seeds would surface it.

    Parametrized across several seed pairs because Python's hash
    randomization can mask leaks on specific (seed, set-contents)
    combinations.
    """
    a = tmp_path / f"out_a_{seed_a}"
    b = tmp_path / f"out_b_{seed_b}"
    _regen_with_env(hash_seed_sensitive_project, a, {"PYTHONHASHSEED": seed_a})
    _regen_with_env(hash_seed_sensitive_project, b, {"PYTHONHASHSEED": seed_b})

    _normalize_meta_json(a / "depgraph" / "nodes")
    _normalize_meta_json(b / "depgraph" / "nodes")

    diffs = _walk_diff(a, b)
    assert not diffs, (
        f"non-deterministic regen detected under PYTHONHASHSEED={seed_a} vs "
        f"PYTHONHASHSEED={seed_b}:\n  " + "\n  ".join(diffs)
    )
