"""Shared fixtures for logigraph.lib.cli tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
LOGIGRAPH_ROOT = TOOL_ROOT / "logigraph"

sys.path.insert(0, str(LOGIGRAPH_ROOT))


@pytest.fixture(autouse=True)
def _logigraph_lib_on_path() -> None:
    """Ensure logigraph/lib is active before every test in this package.

    Evicts only modules that exist in BOTH depgraph/lib and logigraph/lib
    (lib, lib.cli, lib.config, lib.cli.context, lib.cli._shared). Depgraph-
    only modules (lib.cli.memory_sync, etc.) are left intact so identity
    checks in depgraph tests aren't broken if execution order ever changes.
    """
    _root = str(LOGIGRAPH_ROOT)
    _shared = ("lib", "lib.cli", "lib.config", "lib.cli.context", "lib.cli._shared", "lib.cli.flag")
    current_lib = sys.modules.get("lib")
    if current_lib is not None:
        lib_file = getattr(current_lib, "__file__", "") or ""
        if not lib_file.startswith(_root):
            for k in _shared:
                sys.modules.pop(k, None)
    if _root in sys.path:
        sys.path.remove(_root)
    sys.path.insert(0, _root)


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Build a minimal logigraph data dir.

    Creates the subdirs Context.from_data_dir references so tests can
    construct a Context cleanly. Also writes a project.toml with a
    [depgraph] section pointing at a sibling fake-depgraph dir.
    """
    (tmp_path / "nodes" / "_index").mkdir(parents=True)
    (tmp_path / "dossiers").mkdir()
    (tmp_path / "calibration").mkdir()
    (tmp_path / "telemetry").mkdir()
    # Logigraph project.toml; the [depgraph] section points at a sibling
    # depgraph data dir which the test creates (empty).
    depgraph_dir = tmp_path / "fake-depgraph"
    (depgraph_dir / "nodes").mkdir(parents=True)
    (depgraph_dir / "project.toml").write_text('[project]\nname = "fake"\n')
    (tmp_path / "project.toml").write_text(
        f'[project]\nname = "test"\n\n[depgraph]\ndata_dir = "{depgraph_dir}"\n'
    )
    return tmp_path
