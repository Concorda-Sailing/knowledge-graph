"""Tests for kg install dispatch: routing, error handling, and init integration."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = {**os.environ, "KG_REGISTRY_PATH": "/tmp/kg-test-install-dispatch.toml"}
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(KG_BIN), *args],
        capture_output=True, text=True, env=full_env,
    )


# ---------------------------------------------------------------------------
# Help / usage
# ---------------------------------------------------------------------------

def test_kg_install_help_prints_usage() -> None:
    """kg install --help exits 0 and prints the Subcommands: section."""
    res = _run("install", "--help")
    assert res.returncode == 0
    assert "Subcommands:" in res.stdout


def test_kg_install_help_lists_known_subcommands() -> None:
    """The help output enumerates the known subcommands."""
    res = _run("install", "--help")
    assert res.returncode == 0
    for cmd in ("tools", "init", "hooks", "systemd", "path", "cascade", "bootstrap"):
        assert cmd in res.stdout


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_kg_install_unknown_subcommand_errors() -> None:
    """kg install <bogus> exits non-zero and mentions 'unknown subcommand'."""
    res = _run("install", "bogus")
    assert res.returncode != 0
    assert "unknown subcommand" in res.stderr


def test_kg_install_no_subcommand_errors() -> None:
    """kg install with no subcommand exits non-zero."""
    res = _run("install")
    assert res.returncode != 0


# ---------------------------------------------------------------------------
# init routing — proves the Python handler runs, not install.sh
# ---------------------------------------------------------------------------

def test_kg_install_init_routes_to_native_handler(tmp_path: Path) -> None:
    """kg install init <path> creates the bundle structure via the Python handler.

    We verify both exit 0 AND the presence of specific files that the Python
    handler (init.py) creates. This confirms routing reached the native handler
    rather than a shell subprocess (which would behave differently or error in
    test environments).
    """
    project_dir = tmp_path / "myproject"
    res = _run("install", "init", str(project_dir))

    assert res.returncode == 0, f"stderr: {res.stderr}"

    bundle = project_dir / "knowledge-graph"
    # Root layout
    assert (bundle / "project.toml").exists()
    # Depgraph structure
    assert (bundle / "depgraph" / "nodes").is_dir()
    assert (bundle / "depgraph" / "project.toml").exists()
    assert (bundle / "depgraph" / "extractors" / "README.md").exists()
    # Logigraph structure
    assert (bundle / "logigraph" / "nodes" / "rules").is_dir()
    assert (bundle / "logigraph" / "nodes" / "domain").is_dir()
    assert (bundle / "logigraph" / "project.toml").exists()
    assert (bundle / "logigraph" / "CANDIDATES.md").exists()


def test_kg_install_init_project_name_comes_from_path(tmp_path: Path) -> None:
    """The project name in project.toml is derived from the directory name."""
    project_dir = tmp_path / "acme-sailing"
    res = _run("install", "init", str(project_dir))

    assert res.returncode == 0
    toml_text = (project_dir / "knowledge-graph" / "project.toml").read_text()
    assert 'name = "acme-sailing"' in toml_text


def test_kg_install_init_refuses_to_overwrite_existing_depgraph(tmp_path: Path) -> None:
    """kg install init exits non-zero if depgraph already exists."""
    project_dir = tmp_path / "existing"
    bundle = project_dir / "knowledge-graph"
    (bundle / "depgraph").mkdir(parents=True)

    res = _run("install", "init", str(project_dir))

    assert res.returncode != 0
