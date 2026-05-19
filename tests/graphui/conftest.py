"""Shared fixtures for graphui tests.

graphui resolves its active project from a contextvar and falls back to
env-var-derived defaults. Tests don't go through the FastAPI middleware,
so they wire a Project explicitly via `set_current_project`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
# graphui/app/loader.py uses `from .` relative imports, so the package needs
# to be importable as `app.*`. graphui/ isn't a package itself — its `app/`
# subdir is the package — so we add `graphui/` to sys.path.
sys.path.insert(0, str(TOOL_ROOT / "graphui"))


@pytest.fixture
def project_dirs(tmp_path: Path) -> Path:
    """Build a minimal multi-project layout: graph_dir / {depgraph, logigraph}
    each with their own nodes/ tree. Returns the graph_dir."""
    graph_dir = tmp_path / "test-knowledge-graph"
    (graph_dir / "depgraph" / "nodes").mkdir(parents=True)
    (graph_dir / "logigraph" / "nodes").mkdir(parents=True)
    (graph_dir / "project.toml").write_text(
        '[project]\nname = "test"\ndescription = "test"\n'
    )
    return graph_dir
