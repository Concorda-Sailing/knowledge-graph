"""Tests for logigraph.lib.cli.regen.cmd_regen."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.cli.context import Context
from lib.cli.regen import cmd_regen


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def test_regen_calls_reconcile_rc0(ctx: Context) -> None:
    """cmd_regen returns 0 when reconcile.py exits cleanly."""
    with patch("subprocess.call", return_value=0) as mock_call:
        args = argparse.Namespace()
        rc = cmd_regen(args, ctx)
    assert rc == 0
    assert mock_call.called
    # The call should include the reconcile.py path
    called_cmd = mock_call.call_args[0][0]
    assert "reconcile.py" in " ".join(str(a) for a in called_cmd)


def test_regen_calls_reconcile_rc1(ctx: Context) -> None:
    """cmd_regen returns 1 when reconcile.py exits with non-zero."""
    with patch("subprocess.call", return_value=1):
        args = argparse.Namespace()
        rc = cmd_regen(args, ctx)
    assert rc == 1


def test_regen_injects_logigraph_data_dir_in_env(ctx: Context) -> None:
    """cmd_regen passes LOGIGRAPH_DATA_DIR in the subprocess env."""
    captured_kwargs: list[dict] = []

    def _mock_call(cmd, **kwargs):  # noqa: ANN001
        captured_kwargs.append(kwargs)
        return 0

    with patch("subprocess.call", side_effect=_mock_call):
        args = argparse.Namespace()
        cmd_regen(args, ctx)

    assert captured_kwargs
    env = captured_kwargs[0].get("env", {})
    assert "LOGIGRAPH_DATA_DIR" in env
    assert env["LOGIGRAPH_DATA_DIR"] == str(ctx.LOGIGRAPH)
