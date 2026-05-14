"""Tests for kg.project — parse a graph repo's root project.toml."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOL_ROOT))

from kg import project  # noqa: E402


def _write_root(graph: Path, body: str) -> None:
    graph.mkdir(parents=True, exist_ok=True)
    (graph / "project.toml").write_text(body)


def _write_depgraph(graph: Path, body: str) -> None:
    sub = graph / "depgraph"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "project.toml").write_text(body)


def test_load_reads_name_and_subsystems(tmp_path: Path) -> None:
    g = tmp_path / "g"
    _write_root(
        g,
        """
[project]
name = "test-graph"
subsystems = ["depgraph", "logigraph"]
source_roots = ["~/code/foo"]
""",
    )
    proj = project.load(g)
    assert proj.name == "test-graph"
    assert proj.subsystems == ["depgraph", "logigraph"]
    assert proj.path == g.resolve()


def test_load_resolves_explicit_source_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    src = tmp_path / "code" / "foo"
    src.mkdir(parents=True)
    g = tmp_path / "g"
    _write_root(
        g,
        """
[project]
name = "g"
subsystems = ["depgraph"]
source_roots = ["~/code/foo", "/abs/path/missing"]
""",
    )
    proj = project.load(g)
    # ~ expansion, absolute, but no existence check (existence is a soft thing).
    assert src.resolve() in proj.source_roots
    assert Path("/abs/path/missing") in proj.source_roots


def test_load_derives_source_roots_from_depgraph_repos(tmp_path: Path) -> None:
    """If root project.toml omits source_roots, derive them from
    depgraph/project.toml's [repos.*] tables."""
    g = tmp_path / "g"
    _write_root(
        g,
        """
[project]
name = "g"
subsystems = ["depgraph", "logigraph"]
""",
    )
    _write_depgraph(
        g,
        f"""
[project]
name = "g"

[repos.api]
path = "{tmp_path}/code/api"

[repos.web]
path = "{tmp_path}/code/web"
""",
    )
    proj = project.load(g)
    assert (tmp_path / "code" / "api").resolve() in proj.source_roots
    assert (tmp_path / "code" / "web").resolve() in proj.source_roots


def test_load_missing_project_toml_raises(tmp_path: Path) -> None:
    g = tmp_path / "no-config"
    g.mkdir()
    with pytest.raises(FileNotFoundError):
        project.load(g)


def test_load_missing_name_raises(tmp_path: Path) -> None:
    g = tmp_path / "g"
    _write_root(g, '[project]\nsubsystems = ["depgraph"]\nsource_roots = ["/a"]\n')
    with pytest.raises(ValueError, match="name"):
        project.load(g)


def test_load_missing_subsystems_raises(tmp_path: Path) -> None:
    g = tmp_path / "g"
    _write_root(g, '[project]\nname = "g"\nsource_roots = ["/a"]\n')
    with pytest.raises(ValueError, match="subsystems"):
        project.load(g)


def test_load_no_source_roots_anywhere_raises(tmp_path: Path) -> None:
    g = tmp_path / "g"
    _write_root(g, '[project]\nname = "g"\nsubsystems = ["depgraph"]\n')
    # No depgraph/project.toml either.
    with pytest.raises(ValueError, match="source_roots"):
        project.load(g)


def test_load_tooling_version_optional(tmp_path: Path) -> None:
    g = tmp_path / "g"
    _write_root(
        g,
        """
[project]
name = "g"
subsystems = ["depgraph"]
source_roots = ["/a"]
tooling_version = "1.2.3"
""",
    )
    assert project.load(g).tooling_version == "1.2.3"


def test_owns_path_matches_under_source_root(tmp_path: Path) -> None:
    g = tmp_path / "g"
    _write_root(
        g,
        f"""
[project]
name = "g"
subsystems = ["depgraph"]
source_roots = ["{tmp_path}/code/foo"]
""",
    )
    proj = project.load(g)
    assert proj.owns(tmp_path / "code" / "foo" / "file.py") is True
    assert proj.owns(tmp_path / "code" / "foo" / "nested" / "x.py") is True
    assert proj.owns(tmp_path / "code" / "bar" / "x.py") is False


def test_owns_path_handles_tilde_in_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    src = tmp_path / "code"
    src.mkdir()
    g = tmp_path / "g"
    _write_root(
        g,
        """
[project]
name = "g"
subsystems = ["depgraph"]
source_roots = ["~/code"]
""",
    )
    proj = project.load(g)
    assert proj.owns(Path("~/code/x.py")) is True
