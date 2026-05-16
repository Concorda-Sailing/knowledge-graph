"""Shared fixtures for depgraph.lib.cli tests."""
from __future__ import annotations

from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Build a minimal depgraph data dir with nodes/ + telemetry/."""
    (tmp_path / "nodes" / "_index").mkdir(parents=True)
    (tmp_path / "telemetry").mkdir()
    (tmp_path / "project.toml").write_text(
        '[project]\nname = "test"\n'
    )
    return tmp_path
