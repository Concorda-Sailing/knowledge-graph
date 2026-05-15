"""Tests for kg.cli.resolve — the 7-step project resolver."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOL_ROOT))

from kg import registry  # noqa: E402
from kg.cli import resolve  # noqa: E402


@pytest.fixture
def two_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Set up two registered projects with full data-dir layouts."""
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / "kg-graphs.toml"))
    monkeypatch.delenv("KG_PROJECT", raising=False)
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.delenv("LOGIGRAPH_DATA_DIR", raising=False)

    def make(name: str) -> Path:
        root = tmp_path / f"{name}-knowledge-graph"
        (root / "depgraph" / "nodes").mkdir(parents=True)
        (root / "logigraph" / "nodes").mkdir(parents=True)
        (root / "project.toml").write_text(
            f'[project]\nname = "{name}"\nsubsystems = ["depgraph", "logigraph"]\n'
        )
        (root / "depgraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        (root / "logigraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        registry.add(name=name, path=root)
        return root

    return {
        "concorda": make("concorda"),
        "demo": make("demo"),
        "tmp_path": tmp_path,
    }


def test_rule_1_data_dir_flag_wins(two_projects: dict) -> None:
    proj = resolve.resolve_project(data_dir=two_projects["concorda"] / "depgraph")
    assert proj.name == "concorda"
    assert proj.source == "--data-dir flag"


def test_rule_1_project_flag(two_projects: dict) -> None:
    proj = resolve.resolve_project(project_name="demo")
    assert proj.name == "demo"
    assert proj.source == "--project flag"


def test_rule_1_project_flag_unknown_errors(two_projects: dict) -> None:
    with pytest.raises(resolve.UnknownProject):
        resolve.resolve_project(project_name="ghost")


def test_rule_2_KG_PROJECT_env(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_PROJECT", "demo")
    proj = resolve.resolve_project()
    assert proj.name == "demo"
    assert proj.source == "$KG_PROJECT"


def test_rule_3_DEPGRAPH_DATA_DIR_env(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPGRAPH_DATA_DIR", str(two_projects["concorda"] / "depgraph"))
    proj = resolve.resolve_project()
    assert proj.name == "concorda"
    assert proj.source == "$DEPGRAPH_DATA_DIR"


def test_rule_4_cwd_ancestor_walk(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(two_projects["concorda"] / "depgraph")
    proj = resolve.resolve_project()
    assert proj.name == "concorda"
    assert proj.source == "cwd ancestor walk"


def test_rule_5_default_in_registry(two_projects: dict) -> None:
    registry.save_default("demo")
    proj = resolve.resolve_project()
    assert proj.name == "demo"
    assert proj.source == "kg-graphs.toml default"


def test_rule_6_single_registered_used_implicitly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_REGISTRY_PATH", str(tmp_path / "kg-graphs.toml"))
    monkeypatch.delenv("KG_PROJECT", raising=False)
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.delenv("LOGIGRAPH_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    root = tmp_path / "solo-knowledge-graph"
    (root / "depgraph" / "nodes").mkdir(parents=True)
    (root / "logigraph" / "nodes").mkdir(parents=True)
    (root / "project.toml").write_text(
        '[project]\nname = "solo"\nsubsystems = ["depgraph", "logigraph"]\n'
    )
    registry.add(name="solo", path=root)

    proj = resolve.resolve_project()
    assert proj.name == "solo"
    assert proj.source == "only registered project"


def test_rule_7_ambiguous_errors_with_list(two_projects: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(two_projects["tmp_path"])
    with pytest.raises(resolve.AmbiguousProject) as exc:
        resolve.resolve_project()
    msg = str(exc.value)
    assert "concorda" in msg
    assert "demo" in msg
    assert "--project" in msg


def test_project_dataclass_paths(two_projects: dict) -> None:
    proj = resolve.resolve_project(project_name="concorda")
    assert proj.data_dir == (two_projects["concorda"]).resolve()
    assert proj.depgraph_dir == (two_projects["concorda"] / "depgraph").resolve()
    assert proj.logigraph_dir == (two_projects["concorda"] / "logigraph").resolve()
