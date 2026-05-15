"""Smoke tests for kg's subprocess shims to depgraph / logigraph / install.sh."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


@pytest.fixture
def single_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    root = tmp_path / "solo-knowledge-graph"
    (root / "depgraph" / "nodes").mkdir(parents=True)
    (root / "logigraph" / "nodes").mkdir(parents=True)
    (root / "project.toml").write_text(
        '[project]\nname = "solo"\nsubsystems = ["depgraph", "logigraph"]\n'
    )
    (root / "depgraph" / "project.toml").write_text('[project]\nname = "solo"\n')
    (root / "logigraph" / "project.toml").write_text('[project]\nname = "solo"\n')
    subprocess.run(
        [sys.executable, str(KG_BIN), "project", "add", str(root)],
        check=True, env={**os.environ, "KG_REGISTRY_PATH": str(reg)},
    )
    return {"root": root, "registry": reg}


def _run(env_reg: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KG_BIN), *args],
        capture_output=True, text=True,
        env={**os.environ, "KG_REGISTRY_PATH": str(env_reg)},
    )


def test_kg_depgraph_help_reaches_depgraph(single_project: dict) -> None:
    res = _run(single_project["registry"], "depgraph", "--help")
    assert res.returncode == 0
    # depgraph's --help mentions a subcommand we know exists.
    assert "regen" in res.stdout


def test_kg_depgraph_validate_runs_against_resolved_project(single_project: dict) -> None:
    res = _run(single_project["registry"], "depgraph", "validate")
    # Validate on an empty graph should succeed with no errors.
    assert res.returncode == 0, f"stderr: {res.stderr}"


def test_kg_logigraph_help_reaches_logigraph(single_project: dict) -> None:
    res = _run(single_project["registry"], "logigraph", "--help")
    assert res.returncode == 0
    assert "regen" in res.stdout


def test_kg_install_help_reaches_install_sh(single_project: dict) -> None:
    res = _run(single_project["registry"], "install", "--help")
    assert res.returncode == 0
    # install.sh --help mentions a known subcommand.
    assert "bootstrap" in res.stdout or "systemd" in res.stdout
