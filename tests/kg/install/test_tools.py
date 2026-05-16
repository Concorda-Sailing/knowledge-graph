"""Tests for kg.cli.install.tools.cmd_tools."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from kg.cli.install.tools import cmd_tools


def test_tools_errors_when_subsystem_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If target/knowledge-graph/depgraph doesn't exist, refuse."""
    bundle = tmp_path / "knowledge-graph"
    bundle.mkdir()
    # Don't create depgraph/logigraph/graphui sub-dirs
    args = argparse.Namespace(target=str(tmp_path), data=[])
    rc = cmd_tools(args)
    assert rc != 0


def test_tools_succeeds_when_subsystems_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the framework dirs are present, the tools step works.
    Mocks the venv pip-install call so the test doesn't actually run pip.
    """
    bundle = tmp_path / "knowledge-graph"
    (bundle / "depgraph").mkdir(parents=True)
    (bundle / "logigraph").mkdir()
    g = bundle / "graphui"
    g.mkdir()
    (g / "requirements.txt").write_text("# stub\n")
    args = argparse.Namespace(target=str(tmp_path), data=[])
    # Mock the pip subprocess; ensure venv create runs (it's lightweight)
    # plus mock the install step that pulls fastembed.
    real_run = subprocess.run
    def fake_run(cmd, *a, **k):
        if isinstance(cmd, list) and len(cmd) > 1 and "pip" in cmd[0]:
            # Skip pip install
            class _R:
                returncode = 0
            return _R()
        return real_run(cmd, *a, **k)
    with patch.object(subprocess, "run", side_effect=fake_run):
        rc = cmd_tools(args)
    assert rc == 0
    assert (g / ".venv").exists()  # venv directory should be created
