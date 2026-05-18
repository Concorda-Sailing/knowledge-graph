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


def test_tools_provisions_depgraph_venv_when_requirements_present(
    tmp_path: Path,
) -> None:
    """With depgraph/requirements.txt present, cmd_tools creates depgraph/.venv
    and pip-installs into it (#13)."""
    bundle = tmp_path / "knowledge-graph"
    (bundle / "depgraph").mkdir(parents=True)
    (bundle / "depgraph" / "requirements.txt").write_text("# stub\n")
    (bundle / "logigraph").mkdir()
    (bundle / "graphui").mkdir()
    (bundle / "graphui" / "requirements.txt").write_text("# stub\n")

    pip_calls: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(cmd, *a, **k):
        if isinstance(cmd, list) and any("pip" in c for c in cmd):
            pip_calls.append(list(cmd))
            class _R:
                returncode = 0
                stdout = ""
                stderr = ""
            return _R()
        return real_run(cmd, *a, **k)

    args = argparse.Namespace(target=str(tmp_path), data=[])
    with patch.object(subprocess, "run", side_effect=fake_run):
        rc = cmd_tools(args)
    assert rc == 0
    # depgraph venv created on disk.
    assert (bundle / "depgraph" / ".venv").exists()
    # At least one pip call targeted the depgraph requirements.
    assert any(
        any("depgraph/requirements.txt" in str(part) for part in call)
        for call in pip_calls
    ), f"no pip call referenced depgraph/requirements.txt; saw: {pip_calls}"


def test_tools_warns_when_npm_missing_but_ts_extractor_present(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """If the TS extractor's package.json exists but npm is not on PATH,
    cmd_tools warns loudly rather than silently skipping (#13)."""
    bundle = tmp_path / "knowledge-graph"
    (bundle / "depgraph").mkdir(parents=True)
    (bundle / "logigraph").mkdir()
    (bundle / "graphui").mkdir()
    (bundle / "graphui" / "requirements.txt").write_text("# stub\n")
    ts = bundle / "depgraph" / "extractors" / "typescript"
    ts.mkdir(parents=True)
    (ts / "package.json").write_text('{"name": "stub"}')

    real_run = subprocess.run
    def fake_run(cmd, *a, **k):
        if isinstance(cmd, list) and any("pip" in c for c in cmd):
            class _R:
                returncode = 0
                stdout = ""
                stderr = ""
            return _R()
        return real_run(cmd, *a, **k)

    args = argparse.Namespace(target=str(tmp_path), data=[])
    import shutil as _shutil
    real_which = _shutil.which

    def fake_which(cmd):
        if cmd == "npm":
            return None
        return real_which(cmd)

    with patch.object(_shutil, "which", side_effect=fake_which), \
         patch.object(subprocess, "run", side_effect=fake_run):
        rc = cmd_tools(args)
    assert rc == 0
    captured = capsys.readouterr()
    # Warning text goes through the framework's `warn` helper to stderr.
    assert "npm" in (captured.err + captured.out).lower()
