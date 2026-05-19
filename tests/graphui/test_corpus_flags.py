"""Tests for graphui.app.loader corpus_flags + _extraction_ran (#63)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import loader  # type: ignore[import-not-found]
from app.loader import Project, _extraction_ran  # type: ignore[import-not-found]


def _make_project(graph_dir: Path) -> Project:
    return Project(
        id="test",
        name="test",
        description="",
        graph_dir=graph_dir,
        depgraph_dir=graph_dir / "depgraph",
        logigraph_dir=graph_dir / "logigraph",
    )


# ---------------------------------------------------------------------------
# _extraction_ran (pure)
# ---------------------------------------------------------------------------

def test_extraction_ran_both_empty_is_false() -> None:
    """Default load_meta shape when neither meta file exists."""
    assert _extraction_ran({"depgraph": {}, "logigraph": {}}) is False


def test_extraction_ran_depgraph_only_is_true() -> None:
    """Depgraph regen ran, logigraph never did → extraction has run."""
    assert _extraction_ran({"depgraph": {"node_count": 0}, "logigraph": {}}) is True


def test_extraction_ran_logigraph_only_is_true() -> None:
    """Logigraph regen ran, depgraph never did → extraction has run."""
    assert _extraction_ran({"depgraph": {}, "logigraph": {"node_count": 0}}) is True


def test_extraction_ran_missing_keys_is_false() -> None:
    """Defensive: a totally empty dict counts as no extraction."""
    assert _extraction_ran({}) is False


# ---------------------------------------------------------------------------
# corpus_flags integration
# ---------------------------------------------------------------------------

@pytest.fixture
def bound_project(project_dirs: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    """Bind a synthetic project to the active contextvar for one test."""
    proj = _make_project(project_dirs)
    token = loader.set_current_project(proj)
    monkeypatch.setattr(loader, "_META_CACHE", {})  # bypass per-project meta cache
    yield proj
    loader.reset_current_project(token)


def test_corpus_flags_no_meta_reports_extraction_not_run(bound_project: Project) -> None:
    """No _meta.json on either side → corpus_flags.extraction_ran is False (#63)."""
    flags = loader.corpus_flags()
    assert flags["extraction_ran"] is False
    assert flags["count_fresh"] == 0
    assert flags["count_tracked"] == 0


def test_corpus_flags_with_depgraph_meta_reports_extraction_ran(
    bound_project: Project,
) -> None:
    """_meta.json present on depgraph side → extraction_ran is True."""
    (bound_project.depgraph_dir / "nodes" / "_meta.json").write_text(
        json.dumps({"schema_version": 2, "regen_status": "complete", "node_count": 0})
    )
    flags = loader.corpus_flags()
    assert flags["extraction_ran"] is True
