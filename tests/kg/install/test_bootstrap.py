"""Tests for kg/cli/install/bootstrap.py — port of install.sh:cmd_bootstrap()."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from kg.cli.install import bootstrap as bootstrap_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mk(name: str, calls: list[str]):
    """Return a no-op replacement for a cmd_* function that records its name."""
    def fn(*a, **k):
        calls.append(name)
        return 0
    return fn


class _FakeProc:
    returncode = 0


def _make_args(project: str, data: list[str] | None = None) -> argparse.Namespace:
    return argparse.Namespace(project=project, data=data or [])


# ---------------------------------------------------------------------------
# Orchestration order — new project (no existing layout)
# ---------------------------------------------------------------------------


def test_bootstrap_orchestrates_all_steps_in_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All 6 steps run in the correct order for a fresh project."""
    calls: list[str] = []

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", _mk("tools", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_init", _mk("init", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", _mk("hooks", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", _mk("systemd", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_path", _mk("path", calls))

    proc_calls: list[list[str]] = []

    def fake_run(cmd, *a, **k):
        proc_calls.append(list(cmd))
        return _FakeProc()

    monkeypatch.setattr(subprocess, "run", fake_run)

    args = _make_args(str(tmp_path / "newproj"))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 0
    assert calls == ["tools", "init", "hooks", "systemd", "path"]
    # kg add is called via subprocess once
    assert len(proc_calls) == 1
    assert "add" in proc_calls[0]


def test_bootstrap_passes_data_to_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--data specs are forwarded to cmd_tools."""
    captured_tools_args: list[argparse.Namespace] = []

    def fake_tools(a: argparse.Namespace) -> int:
        captured_tools_args.append(a)
        return 0

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", fake_tools)
    monkeypatch.setattr(bootstrap_mod, "cmd_init", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_path", lambda *a, **k: 0)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    args = _make_args(str(tmp_path / "proj"), data=["myorg/myrepo=~/data"])
    bootstrap_mod.cmd_bootstrap(args)

    assert captured_tools_args[0].data == ["myorg/myrepo=~/data"]


# ---------------------------------------------------------------------------
# init branch: skip when layout already exists
# ---------------------------------------------------------------------------


def test_bootstrap_skips_init_when_layout_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """init is NOT called when both depgraph/ and logigraph/ already exist."""
    calls: list[str] = []

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", _mk("tools", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_init", _mk("init", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", _mk("hooks", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", _mk("systemd", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_path", _mk("path", calls))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    project = tmp_path / "existing"
    (project / "knowledge-graph" / "depgraph").mkdir(parents=True)
    (project / "knowledge-graph" / "logigraph").mkdir(parents=True)

    args = _make_args(str(project))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 0
    assert "init" not in calls
    assert "tools" in calls
    assert "hooks" in calls
    assert "systemd" in calls
    assert "path" in calls


def test_bootstrap_skips_init_when_only_depgraph_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """init IS called when depgraph/ is absent even if logigraph/ exists."""
    calls: list[str] = []

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", _mk("tools", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_init", _mk("init", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", _mk("hooks", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", _mk("systemd", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_path", _mk("path", calls))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    project = tmp_path / "partial"
    # Only logigraph present — depgraph absent → must scaffold.
    (project / "knowledge-graph" / "logigraph").mkdir(parents=True)

    args = _make_args(str(project))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 0
    assert "init" in calls


def test_bootstrap_skips_init_when_only_logigraph_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """init IS called when logigraph/ is absent even if depgraph/ exists."""
    calls: list[str] = []

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", _mk("tools", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_init", _mk("init", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", _mk("hooks", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", _mk("systemd", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_path", _mk("path", calls))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    project = tmp_path / "partial2"
    # Only depgraph present — logigraph absent → must scaffold.
    (project / "knowledge-graph" / "depgraph").mkdir(parents=True)

    args = _make_args(str(project))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 0
    assert "init" in calls


def test_bootstrap_runs_init_when_no_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """init IS called for a completely new project directory."""
    calls: list[str] = []

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", _mk("tools", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_init", _mk("init", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", _mk("hooks", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", _mk("systemd", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_path", _mk("path", calls))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    args = _make_args(str(tmp_path / "brandnew"))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 0
    assert "init" in calls


# ---------------------------------------------------------------------------
# kg add subprocess call
# ---------------------------------------------------------------------------


def test_bootstrap_calls_kg_add_with_bundle_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The subprocess kg add call receives the <project>/knowledge-graph path."""
    monkeypatch.setattr(bootstrap_mod, "cmd_tools", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_init", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_path", lambda *a, **k: 0)

    proc_calls: list[list[str]] = []

    def fake_run(cmd, *a, **k):
        proc_calls.append(list(cmd))
        return _FakeProc()

    monkeypatch.setattr(subprocess, "run", fake_run)

    project = tmp_path / "myproject"
    args = _make_args(str(project))
    bootstrap_mod.cmd_bootstrap(args)

    assert len(proc_calls) == 1
    cmd = proc_calls[0]
    # Command: [<kg_bin>, "add", "<project>/knowledge-graph"]
    assert cmd[-2] == "add"
    assert cmd[-1].endswith("knowledge-graph")
    assert str(project) in cmd[-1]


def test_bootstrap_warns_but_continues_if_kg_add_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """A non-zero kg add exit code emits a warning but bootstrap still returns 0."""
    monkeypatch.setattr(bootstrap_mod, "cmd_tools", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_init", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_path", lambda *a, **k: 0)

    class _Failed:
        returncode = 1

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Failed())

    args = _make_args(str(tmp_path / "proj"))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 0
    err_out = capsys.readouterr().err
    assert "kg add" in err_out or "manually" in err_out


# ---------------------------------------------------------------------------
# Step args: hooks and path always receive --force
# ---------------------------------------------------------------------------


def test_bootstrap_passes_force_to_hooks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cmd_hooks is called with apply=True, force=True."""
    captured: list[argparse.Namespace] = []

    def fake_hooks(a: argparse.Namespace) -> int:
        captured.append(a)
        return 0

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_init", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", fake_hooks)
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_path", lambda *a, **k: 0)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    args = _make_args(str(tmp_path / "proj"))
    bootstrap_mod.cmd_bootstrap(args)

    assert captured[0].apply is True
    assert captured[0].force is True


def test_bootstrap_passes_force_to_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cmd_path is called with apply=True, force=True."""
    captured: list[argparse.Namespace] = []

    def fake_path(a: argparse.Namespace) -> int:
        captured.append(a)
        return 0

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_init", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", lambda *a, **k: 0)
    monkeypatch.setattr(bootstrap_mod, "cmd_path", fake_path)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    args = _make_args(str(tmp_path / "proj"))
    bootstrap_mod.cmd_bootstrap(args)

    assert captured[0].apply is True
    assert captured[0].force is True


# ---------------------------------------------------------------------------
# Short-circuit: tools failure aborts bootstrap
# ---------------------------------------------------------------------------


def test_bootstrap_aborts_if_tools_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If cmd_tools returns non-zero, bootstrap returns that code immediately."""
    calls: list[str] = []

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", lambda *a, **k: 1)
    monkeypatch.setattr(bootstrap_mod, "cmd_init", _mk("init", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", _mk("hooks", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", _mk("systemd", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_path", _mk("path", calls))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    args = _make_args(str(tmp_path / "proj"))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 1
    assert calls == []  # nothing after tools


def test_bootstrap_aborts_if_hooks_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If cmd_hooks returns non-zero, bootstrap returns that code immediately."""
    calls: list[str] = []

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", _mk("tools", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_init", _mk("init", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_hooks", lambda *a, **k: 2)
    monkeypatch.setattr(bootstrap_mod, "cmd_systemd", _mk("systemd", calls))
    monkeypatch.setattr(bootstrap_mod, "cmd_path", _mk("path", calls))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeProc())

    args = _make_args(str(tmp_path / "proj"))
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 2
    assert "systemd" not in calls
    assert "path" not in calls
