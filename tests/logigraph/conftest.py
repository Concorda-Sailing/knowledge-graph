"""Shared fixtures for logigraph.lib.cli tests."""
from __future__ import annotations

from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]


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
