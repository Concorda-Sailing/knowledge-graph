"""End-to-end integration test for kg install bootstrap.

Exercises the whole bootstrap pipeline (init → hooks → kg add →
systemd → path) end-to-end against tmp_path dirs.  cmd_tools is
mocked (its internals are covered by unit tests); systemctl and pip
subprocess calls are intercepted so the test doesn't touch real
package managers or systemd.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from kg.cli.install import bootstrap as bootstrap_mod


TOOL_ROOT = Path(__file__).resolve().parents[4]
KG_BIN = TOOL_ROOT / "bin" / "kg"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def hermetic_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Redirect HOME, KG_REGISTRY_PATH, and the install --target to tmp_path.

    Also pre-creates a stub graphui directory tree (with a fake uvicorn binary)
    so that cmd_systemd's preflight check passes without needing a real venv.

    Returns a dict with keys:
      home      — the fake $HOME dir
      registry  — path where kg-graphs.toml will be written
      project   — path to use as the project root (does not exist yet)
    """
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("KG_REGISTRY_PATH", str(fake_home / "kg-graphs.toml"))
    monkeypatch.delenv("KG_PROJECT", raising=False)

    # cmd_systemd resolves its graphui dir as:
    #   {target}/knowledge-graph/graphui
    # where target defaults to $HOME/tools.  Pre-seed a stub so the
    # preflight check passes without running pip/venv.
    stub_graphui = fake_home / "tools" / "knowledge-graph" / "graphui"
    fake_uvicorn = stub_graphui / ".venv" / "bin" / "uvicorn"
    fake_uvicorn.parent.mkdir(parents=True, exist_ok=True)
    fake_uvicorn.write_text("#!/bin/sh\n")  # non-empty stub

    return {
        "home": fake_home,
        "registry": fake_home / "kg-graphs.toml",
        "project": tmp_path / "myproject",
    }


def _make_subprocess_shim(real_run, captured: list) -> object:
    """Return a ``subprocess.run`` replacement.

    Passes through git and kg invocations; short-circuits systemctl and any
    pip invocations (returns returncode=0 without executing them).  Every call
    is appended to *captured* as a list of strings.
    """
    class _FakeProc:
        returncode = 0

    def _shim(cmd, *a, **k):
        cmd_list = list(cmd) if not isinstance(cmd, str) else [cmd]
        captured.append(cmd_list)
        head = cmd_list[0] if cmd_list else ""
        # Intercept systemctl and pip; let everything else through.
        if head == "systemctl" or "/pip" in str(head) or head.endswith("pip"):
            return _FakeProc()
        return real_run(cmd, *a, **k)

    return _shim


# ---------------------------------------------------------------------------
# Test 1: full bootstrap creates the expected layout and side-effects
# ---------------------------------------------------------------------------


def test_bootstrap_creates_full_layout_and_registers(
    hermetic_env: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full bootstrap: init creates the layout, hooks writes settings.json,
    kg add registers the project, systemd writes the unit file, path writes
    ~/.profile.
    """
    # cmd_tools is unit-tested in isolation; mock it here to avoid pip/venv calls.
    monkeypatch.setattr(bootstrap_mod, "cmd_tools", lambda args: 0)

    captured: list = []
    monkeypatch.setattr(subprocess, "run", _make_subprocess_shim(subprocess.run, captured))

    # systemd's --apply path does a preflight check that the data dirs exist.
    # The project won't have been created yet when systemd runs (bootstrap runs
    # init first, so by the time systemd runs the dirs ARE there).  We also
    # need to stub _systemctl_available so we exercise the systemctl path.
    from kg.cli.install import systemd as systemd_mod
    monkeypatch.setattr(systemd_mod, "_systemctl_available", lambda: True)

    args = argparse.Namespace(project=str(hermetic_env["project"]), data=[])
    rc = bootstrap_mod.cmd_bootstrap(args)
    assert rc == 0, f"bootstrap returned non-zero ({rc})"

    # 1. Init scaffold
    bundle = hermetic_env["project"] / "knowledge-graph"
    assert (bundle / "depgraph" / "project.toml").exists(), "depgraph/project.toml missing"
    assert (bundle / "logigraph" / "project.toml").exists(), "logigraph/project.toml missing"
    assert (bundle / "project.toml").exists(), "root project.toml missing"

    # 2. Hooks written to settings.json inside the fake HOME
    settings = hermetic_env["home"] / ".claude" / "settings.json"
    assert settings.exists(), "settings.json not created"
    data = json.loads(settings.read_text())
    assert "hooks" in data, "settings.json has no 'hooks' key"
    # Must contain at least one hook entry
    hook_section = data["hooks"]
    assert any(isinstance(v, list) and v for v in hook_section.values()), (
        "hooks section appears empty"
    )

    # 3. kg project add registered the project in the hermetic registry
    registry = hermetic_env["registry"]
    assert registry.exists(), "kg-graphs.toml not created"
    reg_text = registry.read_text()
    assert "myproject" in reg_text, f"myproject not in registry:\n{reg_text}"

    # 4. systemctl was attempted
    systemctl_calls = [c for c in captured if c and c[0] == "systemctl"]
    assert systemctl_calls, "no systemctl calls were made"
    flat = [tok for c in systemctl_calls for tok in c]
    assert "daemon-reload" in flat, (
        f"systemctl daemon-reload not called; all systemctl calls: {systemctl_calls}"
    )

    # 5. PATH block written to ~/.profile (relative to fake HOME)
    profile = hermetic_env["home"] / ".profile"
    assert profile.exists(), "~/.profile not created"
    assert "knowledge-graph" in profile.read_text(), (
        f"~/.profile doesn't mention 'knowledge-graph':\n{profile.read_text()}"
    )


# ---------------------------------------------------------------------------
# Test 2: existing layout skips init
# ---------------------------------------------------------------------------


def test_bootstrap_skips_init_for_existing_layout(
    hermetic_env: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If <project>/knowledge-graph/{depgraph,logigraph} already exist,
    bootstrap skips the init step and leaves cmd_init uncalled.
    """
    # Pre-seed the layout that init would normally create.
    bundle = hermetic_env["project"] / "knowledge-graph"
    (bundle / "depgraph").mkdir(parents=True)
    (bundle / "logigraph").mkdir(parents=True)
    (bundle / "project.toml").write_text(
        '[project]\nname = "myproject"\nsubsystems = ["depgraph", "logigraph"]\n'
    )
    # Minimal project.toml files so that cmd_hooks and kg add don't blow up.
    (bundle / "depgraph" / "project.toml").write_text(
        '[project]\nname = "myproject"\n'
    )
    (bundle / "logigraph" / "project.toml").write_text(
        '[project]\nname = "myproject"\n'
    )

    monkeypatch.setattr(bootstrap_mod, "cmd_tools", lambda args: 0)

    init_called: list = []
    real_init = bootstrap_mod.cmd_init

    def spy_init(a: argparse.Namespace) -> int:
        init_called.append(a)
        return real_init(a)

    monkeypatch.setattr(bootstrap_mod, "cmd_init", spy_init)

    captured: list = []
    monkeypatch.setattr(subprocess, "run", _make_subprocess_shim(subprocess.run, captured))

    from kg.cli.install import systemd as systemd_mod
    monkeypatch.setattr(systemd_mod, "_systemctl_available", lambda: True)

    args = argparse.Namespace(project=str(hermetic_env["project"]), data=[])
    rc = bootstrap_mod.cmd_bootstrap(args)

    assert rc == 0, f"bootstrap returned non-zero ({rc})"
    assert init_called == [], (
        f"cmd_init was called despite existing layout: {init_called}"
    )

    # Other steps still ran: registry should be populated, profile should exist.
    registry = hermetic_env["registry"]
    assert registry.exists(), "registry not created"
    profile = hermetic_env["home"] / ".profile"
    assert profile.exists(), "~/.profile not created"
