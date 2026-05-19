"""Dispatch tests for `depgraph regen` --repo-key / --repo-path combinations.

Regression coverage for the crash where `--repo-key` alone (no `--repo-path`)
dropped into Mode B and hit `Path(None)`. The OOM-mitigation hint in
`_run_v2_pipeline` recommends `regen --repo-key <key>` as the way to regen
one repo at a time; that path is exercised here.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _make_project(tmp_path: Path) -> tuple[Path, Path]:
    """Build an umbrella data-dir + a tiny single-file api repo.

    Returns (data_dir, api_repo_path).
    """
    api = tmp_path / "api"
    (api / "src").mkdir(parents=True)
    (api / "src" / "main.py").write_text(
        "def helper(): pass\n\n"
        "def create_event():\n"
        "    helper()\n"
    )

    data_dir = tmp_path / "project"
    data_dir.mkdir()
    (data_dir / "project.toml").write_text(
        f'[repos.api]\npath = "{api}"\nlanguages = ["python"]\n'
    )
    return data_dir, api


def _run_regen(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "kg.cli", "depgraph", "regen", *args],
        capture_output=True, text=True, timeout=120,
    )


def test_repo_key_alone_uses_project_toml(tmp_path):
    """`regen --repo-key api` (no --repo-path) should look up the repo from
    project.toml's [repos.api] table and run a single-repo regen."""
    data_dir, _api = _make_project(tmp_path)
    r = _run_regen("--data-dir", str(data_dir), "--repo-key", "api")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    # Real corpus was written.
    assert (data_dir / "depgraph" / "nodes").is_dir()


def test_repo_key_alone_unknown_key_errors_clearly(tmp_path):
    """An unknown --repo-key should print a clear error listing known keys,
    not crash."""
    data_dir, _api = _make_project(tmp_path)
    r = _run_regen("--data-dir", str(data_dir), "--repo-key", "missing")
    assert r.returncode != 0
    assert "missing" in r.stderr
    assert "api" in r.stderr  # known keys listed


def test_repo_path_alone_errors_with_hint(tmp_path):
    """`--repo-path` without `--repo-key` is ambiguous; the CLI should reject
    it rather than silently regen all repos and ignore the path."""
    data_dir, api = _make_project(tmp_path)
    r = _run_regen("--data-dir", str(data_dir), "--repo-path", str(api))
    assert r.returncode != 0
    assert "--repo-key" in r.stderr


def test_repo_key_with_repo_path_still_mode_b(tmp_path):
    """Both flags together — Mode B — must keep working without project.toml."""
    api = tmp_path / "api"
    (api / "src").mkdir(parents=True)
    (api / "src" / "main.py").write_text("def f(): pass\n")
    data_dir = tmp_path / "project"
    data_dir.mkdir()  # no project.toml

    r = _run_regen(
        "--data-dir", str(data_dir),
        "--repo-key", "api", "--repo-path", str(api),
        "--languages", "python",
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert (data_dir / "depgraph" / "nodes").is_dir()
