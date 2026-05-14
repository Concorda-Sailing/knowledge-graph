"""End-to-end CLI tests: invoke `bin/kg` as a subprocess."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


def _make_graph(parent: Path, name: str, *source_roots: str) -> Path:
    """Build a minimal graph repo with a valid project.toml."""
    g = parent / f"{name}-knowledge-graph"
    g.mkdir(parents=True)
    sr_lines = ", ".join(f'"{s}"' for s in source_roots)
    (g / "project.toml").write_text(
        f"""
[project]
name = "{name}"
subsystems = ["depgraph"]
source_roots = [{sr_lines}]
"""
    )
    return g


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [str(KG_BIN), *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


@pytest.fixture
def registry_env(tmp_path: Path) -> dict[str, str]:
    return {"KG_REGISTRY_PATH": str(tmp_path / "kg-graphs.toml")}


def test_list_when_empty_says_so(tmp_path: Path, registry_env: dict[str, str]) -> None:
    result = _run("list", env=registry_env)
    assert result.returncode == 0
    assert "no graphs" in result.stdout.lower() or "0" in result.stdout


def test_add_then_list_shows_graph(tmp_path: Path, registry_env: dict[str, str]) -> None:
    g = _make_graph(tmp_path, "alpha", "/some/source/root")

    add = _run("add", str(g), env=registry_env)
    assert add.returncode == 0, add.stderr
    assert "alpha" in add.stdout

    lst = _run("list", env=registry_env)
    assert lst.returncode == 0
    assert "alpha" in lst.stdout
    assert str(g) in lst.stdout


def test_add_missing_path_fails(tmp_path: Path, registry_env: dict[str, str]) -> None:
    result = _run("add", str(tmp_path / "nope"), env=registry_env)
    assert result.returncode != 0
    assert "not exist" in result.stderr.lower() or "missing" in result.stderr.lower()


def test_add_path_without_project_toml_fails(
    tmp_path: Path, registry_env: dict[str, str]
) -> None:
    bare = tmp_path / "bare-dir"
    bare.mkdir()
    result = _run("add", str(bare), env=registry_env)
    assert result.returncode != 0
    assert "project.toml" in result.stderr.lower()


def test_add_duplicate_name_fails(
    tmp_path: Path, registry_env: dict[str, str]
) -> None:
    g1 = _make_graph(tmp_path / "a", "dup", "/x")
    g2 = _make_graph(tmp_path / "b", "dup", "/y")
    assert _run("add", str(g1), env=registry_env).returncode == 0
    second = _run("add", str(g2), env=registry_env)
    assert second.returncode != 0
    assert "already" in second.stderr.lower()


def test_remove_existing(tmp_path: Path, registry_env: dict[str, str]) -> None:
    g = _make_graph(tmp_path, "beta", "/x")
    _run("add", str(g), env=registry_env)

    result = _run("remove", "beta", env=registry_env)
    assert result.returncode == 0

    lst = _run("list", env=registry_env)
    assert "beta" not in lst.stdout


def test_remove_missing_exits_nonzero(
    tmp_path: Path, registry_env: dict[str, str]
) -> None:
    result = _run("remove", "ghost", env=registry_env)
    assert result.returncode != 0
    assert "not registered" in result.stderr.lower() or "not found" in result.stderr.lower()


def test_help_includes_known_subcommands(registry_env: dict[str, str]) -> None:
    result = _run("--help", env=registry_env)
    assert result.returncode == 0
    for cmd in ("list", "add", "remove"):
        assert cmd in result.stdout
