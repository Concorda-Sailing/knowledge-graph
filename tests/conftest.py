"""Root test conftest — coordinates the shared `lib` namespace.

Both tests/depgraph/ and tests/logigraph/ rely on bare `from lib.cli.*`
imports, but each resolves `lib` to a different directory. The key
constraint: depgraph tests use `is` identity checks on function objects
imported at module level — those objects must not be evicted and
re-imported between collection and test execution.

Strategy:
- _PatchedModule ensures each test module is imported with the right
  sys.path. It evicts only the lib modules that OVERLAP between both
  graphs (lib, lib.cli, lib.config, lib.cli.context, lib.cli._shared)
  when switching. Depgraph-only modules (lib.cli.memory_sync etc.) are
  left intact because they don't exist in logigraph's lib and evicting
  them would create new objects at test-run time.
- __init__.py in both test packages solves the basename collision between
  tests/depgraph/test_context.py and tests/logigraph/test_context.py.
- pytest_collection_finish resets sys.path to depgraph after collection
  (since depgraph runs first alphabetically), evicting only overlapping
  modules.
- The logigraph autouse fixture evicts overlapping modules before each
  logigraph test so `from lib.cli.context import Context` returns the
  logigraph version.
"""
from __future__ import annotations

import sys
from pathlib import Path

from _pytest.python import Module

_TOOL_ROOT = Path(__file__).resolve().parent.parent
_DEPGRAPH_ROOT = str(_TOOL_ROOT / "depgraph")
_LOGIGRAPH_ROOT = str(_TOOL_ROOT / "logigraph")

_DEPGRAPH_TESTS = str(_TOOL_ROOT / "tests" / "depgraph")
_LOGIGRAPH_TESTS = str(_TOOL_ROOT / "tests" / "logigraph")

# Modules that exist in BOTH depgraph/lib and logigraph/lib.
# These must be evicted when switching between the two graphs.
# Depgraph-only modules (memory_sync, regen, etc.) are NOT in this list
# so that module-level imports and `is` identity checks survive.
_SHARED_LIB_MODULES = frozenset([
    "lib",
    "lib.cli",
    "lib.config",
    "lib.cli.context",
    "lib.cli._shared",
    "lib.cli.regen",
])


def _evict_shared() -> None:
    """Evict lib modules that exist in both graphs."""
    for k in _SHARED_LIB_MODULES:
        sys.modules.pop(k, None)


def _set_lib_root(graph_root: str) -> None:
    """Switch to a graph root: evict shared modules and set path."""
    _evict_shared()
    if graph_root in sys.path:
        sys.path.remove(graph_root)
    sys.path.insert(0, graph_root)


def _make_patched_module(parent, module_path: Path, graph_root: str) -> Module:
    """Return a Module subclass that sets up the correct sys.path before importing."""

    class _PatchedModule(Module):
        def _importtestmodule(self):  # type: ignore[override]
            _set_lib_root(graph_root)
            return super()._importtestmodule()

    return _PatchedModule.from_parent(parent, path=module_path)


def pytest_pycollect_makemodule(module_path, path, parent):  # noqa: ANN001
    """Return a patched Module that fixes sys.path just before import."""
    path_str = str(module_path)
    if path_str.startswith(_DEPGRAPH_TESTS) and module_path.suffix == ".py":
        return _make_patched_module(parent, module_path, _DEPGRAPH_ROOT)
    if path_str.startswith(_LOGIGRAPH_TESTS) and module_path.suffix == ".py":
        return _make_patched_module(parent, module_path, _LOGIGRAPH_ROOT)
    return None  # default collection for everything else


def pytest_collection_finish(session) -> None:  # noqa: ANN001
    """After all modules are collected, reset lib to depgraph for test execution.

    Depgraph tests run first (alphabetical). Resetting to depgraph here
    ensures in-function `from lib.cli.*` imports in depgraph test functions
    find the depgraph version without creating new module objects (the
    depgraph submodules are already in sys.modules from collection time).
    """
    paths = {str(item.fspath) for item in session.items}
    has_depgraph = any(p.startswith(_DEPGRAPH_TESTS) for p in paths)
    has_logigraph = any(p.startswith(_LOGIGRAPH_TESTS) for p in paths)
    if has_depgraph and has_logigraph:
        if _DEPGRAPH_ROOT in sys.path:
            sys.path.remove(_DEPGRAPH_ROOT)
        sys.path.insert(0, _DEPGRAPH_ROOT)
        _evict_shared()
