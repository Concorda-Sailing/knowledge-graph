"""Tests for logigraph.lib.cli.self_check.cmd_self_check."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.self_check import cmd_self_check


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _write_project_toml_with_repos(data_dir: Path, repo_path: Path) -> None:
    """Add a [repos.test] section to the project.toml fixture."""
    existing = (data_dir / "project.toml").read_text()
    depgraph_dir = data_dir / "fake-depgraph"
    (data_dir / "project.toml").write_text(
        existing + f'\n[repos.test]\npath = "{repo_path}"\nbasename = "test-repo"\n'
    )


def test_self_check_no_repos_returns_1(ctx: Context) -> None:
    """When no repos are configured, self-check exits 1."""
    # data_dir fixture only has project + depgraph config, no [repos.*]
    args = argparse.Namespace()
    rc = cmd_self_check(args, ctx)
    assert rc == 1


def test_self_check_hook_returns_0_with_empty_index(
    ctx: Context, tmp_path: Path
) -> None:
    """With repos configured but empty index, uses synthetic path; hook rc=0 → returns 0."""
    repo_path = tmp_path / "fake-repo"
    repo_path.mkdir()
    _write_project_toml_with_repos(ctx.LOGIGRAPH, repo_path)

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = ""
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        args = argparse.Namespace()
        rc = cmd_self_check(args, ctx)
    assert rc == 0


def test_self_check_hook_nonzero_rc_returns_1(
    ctx: Context, tmp_path: Path
) -> None:
    """When the hook subprocess returns non-zero, self-check returns 1."""
    repo_path = tmp_path / "fake-repo"
    repo_path.mkdir()
    _write_project_toml_with_repos(ctx.LOGIGRAPH, repo_path)

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = ""
    mock_proc.stderr = "error"

    with patch("subprocess.run", return_value=mock_proc):
        args = argparse.Namespace()
        rc = cmd_self_check(args, ctx)
    assert rc == 1
