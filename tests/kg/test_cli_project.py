"""Tests for kg project subcommand group."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


@pytest.fixture
def two_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Register two projects with full data-dir layouts."""
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
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
        return root

    a = make("alpha")
    b = make("beta")
    subprocess.run([sys.executable, str(KG_BIN), "project", "add", str(a)], check=True,
                   env={**os.environ, "KG_REGISTRY_PATH": str(reg)})
    subprocess.run([sys.executable, str(KG_BIN), "project", "add", str(b)], check=True,
                   env={**os.environ, "KG_REGISTRY_PATH": str(reg)})
    return {"alpha": a, "beta": b, "registry": reg, "tmp_path": tmp_path}


def _run(env_reg: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "KG_REGISTRY_PATH": str(env_reg)}
    return subprocess.run(
        [sys.executable, str(KG_BIN), *args],
        capture_output=True, text=True, env=env, cwd=cwd,
    )


def test_list_shows_two_projects(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "list")
    assert res.returncode == 0
    assert "alpha" in res.stdout
    assert "beta" in res.stdout


def test_use_then_list_marks_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "list")
    assert "* alpha" in res.stdout
    assert "  beta" in res.stdout  # 2-space prefix = not default


def test_use_clear_unsets_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "use", "--clear")
    assert res.returncode == 0
    res = _run(two_projects["registry"], "project", "list")
    assert "* alpha" not in res.stdout


def test_use_unknown_project_errors(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "use", "ghost")
    assert res.returncode != 0
    assert "not registered" in res.stderr


def test_current_reports_source(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "beta")
    res = _run(two_projects["registry"], "project", "current")
    assert "beta" in res.stdout
    assert "kg-graphs.toml default" in res.stdout


def test_show_prints_resolved_project(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "show")
    assert res.returncode == 0
    assert "alpha" in res.stdout
    assert str(two_projects["alpha"]) in res.stdout


def test_show_named_project_overrides_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "show", "beta")
    assert "beta" in res.stdout
    assert str(two_projects["beta"]) in res.stdout


def test_remove_unregisters(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "remove", "alpha")
    assert res.returncode == 0
    list_res = _run(two_projects["registry"], "project", "list")
    assert "alpha" not in list_res.stdout


def test_init_scaffolds_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    project_root = tmp_path / "fresh"
    res = _run(reg, "project", "init", str(project_root))
    assert res.returncode == 0
    assert (project_root / "knowledge-graph" / "depgraph" / "project.toml").exists()
    assert (project_root / "knowledge-graph" / "logigraph" / "project.toml").exists()


def test_add_repo_via_kg_project_writes_subtable(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    cfg_text = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert "[repos.api]" in cfg_text
    assert "path = " in cfg_text


def test_list_repos_via_kg_project(two_projects: dict) -> None:
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    res = _run(two_projects["registry"], "project", "--project", "alpha", "list-repos")
    assert res.returncode == 0
    assert "api" in res.stdout


def test_remove_repo_via_kg_project(two_projects: dict) -> None:
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    res = _run(two_projects["registry"], "project", "--project", "alpha", "remove-repo", "api")
    assert res.returncode == 0
    cfg_text = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert "[repos.api]" not in cfg_text


def test_set_primary_repo(two_projects: dict) -> None:
    # Add a repo first so primary_repo has a valid target.
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake"),
    )
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "primary_repo", "api",
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    cfg = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert 'primary_repo = "api"' in cfg


def test_set_rejects_non_whitelist_field(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "wild_field", "value",
    )
    assert res.returncode != 0
    assert "not in whitelist" in res.stderr.lower()


def test_set_primary_repo_rejects_unknown_key(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "primary_repo", "missing-key",
    )
    assert res.returncode != 0
