"""Tests for depgraph.lib.cli.self_check.

cmd_self_check shells out to hooks/pre_edit_inject.py, so full end-to-end
testing is an integration concern (covered by P2T15 smoke test).  We cover
the one branch that returns early without shelling out: no repos configured.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from lib.cli.context import Context
from lib.cli.self_check import cmd_self_check


def test_self_check_no_repos_exits_1(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """project.toml with no [repos.*] tables → exit 1 before shelling out."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace()
    rc = cmd_self_check(args, ctx)
    assert rc == 1
    err = capsys.readouterr().err
    assert "no [repos.*]" in err


def test_self_check_returns_int(
    data_dir: Path,
) -> None:
    """Verify the handler always returns an int (not None)."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace()
    rc = cmd_self_check(args, ctx)
    assert isinstance(rc, int)
