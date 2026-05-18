"""Tests for kg/cli/install/systemd.py — port of install.sh:cmd_systemd()."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from kg.cli.install.systemd import (
    _SERVICE_NAME,
    _GRAPHUI_PORT,
    _SYSTEMD_UNIT,
    cmd_systemd,
    generate_systemd_unit,
)


# ---------------------------------------------------------------------------
# generate_systemd_unit — unit-file content
# ---------------------------------------------------------------------------

_EXPECTED_UNIT = """\
[Unit]
Description=knowledge-graph viewer (depgraph + logigraph)
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/user/tools/knowledge-graph/graphui
Environment=PATH=/home/user/tools/knowledge-graph/graphui/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=DEPGRAPH_DATA_DIR=/data/depgraph
Environment=LOGIGRAPH_DATA_DIR=/data/logigraph
Environment=DEPGRAPH_BIN=/home/user/tools/knowledge-graph/depgraph/bin/depgraph
Environment=LOGIGRAPH_BIN=/home/user/tools/knowledge-graph/logigraph/bin/logigraph
ExecStart=/home/user/tools/knowledge-graph/graphui/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8081
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""


def test_generate_systemd_unit_content() -> None:
    """generate_systemd_unit produces the expected unit file string."""
    result = generate_systemd_unit(
        target="/home/user/tools",
        depg="/data/depgraph",
        logg="/data/logigraph",
    )
    assert result == _EXPECTED_UNIT


def test_generate_systemd_unit_custom_port() -> None:
    """Custom port propagates into ExecStart."""
    result = generate_systemd_unit(
        target="/home/user/tools",
        depg="/data/depgraph",
        logg="/data/logigraph",
        port=9090,
    )
    assert "--port 9090" in result
    assert "--port 8081" not in result


def test_generate_systemd_unit_trailing_newline() -> None:
    """Unit content ends with exactly one newline (matches bash heredoc)."""
    result = generate_systemd_unit("/t", "/d", "/l")
    assert result.endswith("\n")
    assert not result.endswith("\n\n")


# ---------------------------------------------------------------------------
# cmd_systemd dry-run (no --apply)
# ---------------------------------------------------------------------------

def _dry_run_args(
    project: str | None = None,
    depgraph_data_dir: str | None = None,
    logigraph_data_dir: str | None = None,
    target: str = "/home/user/tools",
) -> argparse.Namespace:
    return argparse.Namespace(
        target=target,
        project=project,
        depgraph_data_dir=depgraph_data_dir,
        logigraph_data_dir=logigraph_data_dir,
        apply=False,
    )


def test_dry_run_prints_header_and_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Dry-run prints a header comment and the unit file content to stdout."""
    monkeypatch.setenv("HOME", str(tmp_path))
    args = _dry_run_args(project="/some/project")
    rc = cmd_systemd(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "# Write the following to" in out
    assert _SYSTEMD_UNIT in out
    assert "systemctl --user daemon-reload" in out
    assert "[Unit]" in out
    assert "WantedBy=default.target" in out


def test_dry_run_unit_content_matches_generate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """The unit block in dry-run stdout equals generate_systemd_unit output."""
    monkeypatch.setenv("HOME", str(tmp_path))
    target = "/home/user/tools"
    depg = "/data/depgraph"
    logg = "/data/logigraph"
    args = _dry_run_args(
        depgraph_data_dir=depg,
        logigraph_data_dir=logg,
        target=target,
    )
    rc = cmd_systemd(args)
    assert rc == 0
    out = capsys.readouterr().out
    expected_unit = generate_systemd_unit(target, depg, logg)
    # The unit content must appear verbatim inside stdout.
    assert expected_unit in out


def test_dry_run_explicit_overrides_propagate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--depgraph-data-dir and --logigraph-data-dir override project layout."""
    monkeypatch.setenv("HOME", str(tmp_path))
    depg = "/explicit/depgraph"
    logg = "/explicit/logigraph"
    args = _dry_run_args(
        project="/ignored/project",
        depgraph_data_dir=depg,
        logigraph_data_dir=logg,
    )
    rc = cmd_systemd(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert f"DEPGRAPH_DATA_DIR={depg}" in out
    assert f"LOGIGRAPH_DATA_DIR={logg}" in out


def test_dry_run_sibling_hyphen_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Sibling-with-hyphen layout: passing `<project>-knowledge-graph`
    as --project resolves to that path AS the bundle (no nested
    knowledge-graph/ subdir appended). The previous auto-fallback —
    "if `<project>/knowledge-graph/` doesn't exist but `<project>-knowledge-graph/`
    does, use the sibling" — has been removed in favour of explicit
    detection via resolve_bundle_layout: the layout is determined by the
    path the user passes, not by which directories happen to exist."""
    monkeypatch.setenv("HOME", str(tmp_path))
    bundle = tmp_path / "myproject-knowledge-graph"
    depg = bundle / "depgraph"
    logg = bundle / "logigraph"
    depg.mkdir(parents=True)
    logg.mkdir(parents=True)

    args = _dry_run_args(project=str(bundle))
    rc = cmd_systemd(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert str(depg) in out
    assert str(logg) in out


def test_dry_run_no_write_to_systemd_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Dry-run must not create ~/.config/systemd/user/ or write any file."""
    monkeypatch.setenv("HOME", str(tmp_path))
    args = _dry_run_args(project="/some/project")
    cmd_systemd(args)
    systemd_dir = tmp_path / ".config" / "systemd" / "user"
    assert not systemd_dir.exists()


# ---------------------------------------------------------------------------
# cmd_systemd --apply: preflight refusal
# ---------------------------------------------------------------------------

def _apply_args(
    project: str | None = None,
    depgraph_data_dir: str | None = None,
    logigraph_data_dir: str | None = None,
    target: str = "/home/user/tools",
) -> argparse.Namespace:
    return argparse.Namespace(
        target=target,
        project=project,
        depgraph_data_dir=depgraph_data_dir,
        logigraph_data_dir=logigraph_data_dir,
        apply=True,
    )


def test_preflight_refuses_when_data_dirs_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply returns non-zero and does not write unit if data dirs absent."""
    monkeypatch.setenv("HOME", str(tmp_path))
    args = _apply_args(
        depgraph_data_dir="/nonexistent/depgraph",
        logigraph_data_dir="/nonexistent/logigraph",
        target=str(tmp_path / "tools"),
    )
    rc = cmd_systemd(args)
    assert rc != 0
    unit_path = tmp_path / ".config" / "systemd" / "user" / _SYSTEMD_UNIT
    assert not unit_path.exists()


def test_preflight_error_message_names_missing_dirs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Preflight error message names the missing dirs."""
    monkeypatch.setenv("HOME", str(tmp_path))
    args = _apply_args(
        depgraph_data_dir="/no/depgraph",
        logigraph_data_dir="/no/logigraph",
        target=str(tmp_path / "tools"),
    )
    cmd_systemd(args)
    err_out = capsys.readouterr().err
    assert "DEPGRAPH_DATA_DIR" in err_out
    assert "LOGIGRAPH_DATA_DIR" in err_out


# ---------------------------------------------------------------------------
# cmd_systemd --apply: write + systemctl mocking
# ---------------------------------------------------------------------------

def _make_apply_env(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create a minimal directory tree for --apply tests.

    Returns (project_depg, project_logg, graphui_dir).
    """
    depg_dir = tmp_path / "depgraph"
    logg_dir = tmp_path / "logigraph"
    bundle = tmp_path / "tools" / "knowledge-graph"
    graphui_dir = bundle / "graphui"
    uvicorn_bin = graphui_dir / ".venv" / "bin" / "uvicorn"
    uvicorn_bin.parent.mkdir(parents=True, exist_ok=True)
    uvicorn_bin.touch(mode=0o755)
    depg_dir.mkdir(parents=True, exist_ok=True)
    logg_dir.mkdir(parents=True, exist_ok=True)
    return depg_dir, logg_dir, graphui_dir


def _mock_subprocess(is_active: bool = False, start_succeeds: bool = True):
    """Return a mock for subprocess.run that simulates systemctl behaviour.

    is_active=True  — service already running before any action.
    start_succeeds  — if False, is-active returns 1 even after start.
    """
    call_count: list[int] = [0]

    def _run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        if cmd[:3] == ["systemctl", "--user", "is-active"]:
            call_count[0] += 1
            if is_active:
                result.returncode = 0  # already running
            elif call_count[0] == 1:
                result.returncode = 1  # not yet active before start
            else:
                # Second is-active check (after start)
                result.returncode = 0 if start_succeeds else 1
        return result

    return _run


def test_apply_writes_unit_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply writes the unit file to ~/.config/systemd/user/."""
    monkeypatch.setenv("HOME", str(tmp_path))
    depg_dir, logg_dir, _ = _make_apply_env(tmp_path)
    target = str(tmp_path / "tools")

    with patch("subprocess.run", side_effect=_mock_subprocess(is_active=False)):
        with patch("kg.cli.install.systemd._systemctl_available", return_value=True):
            rc = cmd_systemd(
                _apply_args(
                    depgraph_data_dir=str(depg_dir),
                    logigraph_data_dir=str(logg_dir),
                    target=target,
                )
            )

    assert rc == 0
    unit_path = tmp_path / ".config" / "systemd" / "user" / _SYSTEMD_UNIT
    assert unit_path.exists()
    content = unit_path.read_text()
    assert "[Unit]" in content
    assert f"DEPGRAPH_DATA_DIR={depg_dir}" in content


def test_apply_unit_content_matches_generate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The written unit file bytes-equal generate_systemd_unit output."""
    monkeypatch.setenv("HOME", str(tmp_path))
    depg_dir, logg_dir, _ = _make_apply_env(tmp_path)
    target = str(tmp_path / "tools")

    with patch("subprocess.run", side_effect=_mock_subprocess()):
        with patch("kg.cli.install.systemd._systemctl_available", return_value=True):
            cmd_systemd(
                _apply_args(
                    depgraph_data_dir=str(depg_dir),
                    logigraph_data_dir=str(logg_dir),
                    target=target,
                )
            )

    unit_path = tmp_path / ".config" / "systemd" / "user" / _SYSTEMD_UNIT
    expected = generate_systemd_unit(target, str(depg_dir), str(logg_dir))
    assert unit_path.read_text() == expected


def test_apply_systemctl_calls_daemon_reload_enable_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply calls daemon-reload, enable, and start (when not active)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    depg_dir, logg_dir, _ = _make_apply_env(tmp_path)
    target = str(tmp_path / "tools")

    calls_seen: list[list[str]] = []

    def _run(cmd, **kwargs):
        calls_seen.append(list(cmd))
        result = MagicMock()
        result.returncode = (
            0 if cmd[:3] == ["systemctl", "--user", "is-active"] and
            any(c == "start" for c in calls_seen[-2:-1] or []) else
            1 if cmd[:3] == ["systemctl", "--user", "is-active"] else 0
        )
        # Second is-active (after start) → returncode 0 (success)
        is_active_calls = [c for c in calls_seen if c[:3] == ["systemctl", "--user", "is-active"]]
        if cmd[:3] == ["systemctl", "--user", "is-active"]:
            result.returncode = 0 if len(is_active_calls) >= 2 else 1
        return result

    with patch("subprocess.run", side_effect=_run):
        with patch("kg.cli.install.systemd._systemctl_available", return_value=True):
            with patch("time.sleep"):  # skip the 1-second sleep
                rc = cmd_systemd(
                    _apply_args(
                        depgraph_data_dir=str(depg_dir),
                        logigraph_data_dir=str(logg_dir),
                        target=target,
                    )
                )

    assert rc == 0
    cmd_names = [c[2] if len(c) > 2 else "" for c in calls_seen if c[:2] == ["systemctl", "--user"]]
    assert "daemon-reload" in cmd_names
    assert "enable" in cmd_names
    assert "start" in cmd_names


def test_apply_systemctl_restart_when_changed_and_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply calls restart (not start) when unit changed and service active."""
    monkeypatch.setenv("HOME", str(tmp_path))
    depg_dir, logg_dir, _ = _make_apply_env(tmp_path)
    target = str(tmp_path / "tools")

    calls_seen: list[list[str]] = []

    def _run(cmd, **kwargs):
        calls_seen.append(list(cmd))
        result = MagicMock()
        result.returncode = 0  # is-active returns 0 → service is running
        return result

    with patch("subprocess.run", side_effect=_run):
        with patch("kg.cli.install.systemd._systemctl_available", return_value=True):
            rc = cmd_systemd(
                _apply_args(
                    depgraph_data_dir=str(depg_dir),
                    logigraph_data_dir=str(logg_dir),
                    target=target,
                )
            )

    assert rc == 0
    cmd_names = [c[2] if len(c) > 2 else "" for c in calls_seen if c[:2] == ["systemctl", "--user"]]
    assert "restart" in cmd_names
    assert "start" not in cmd_names


def test_apply_idempotent_no_daemon_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Re-applying the same unit skips daemon-reload (no change detected)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    depg_dir, logg_dir, _ = _make_apply_env(tmp_path)
    target = str(tmp_path / "tools")
    args = _apply_args(
        depgraph_data_dir=str(depg_dir),
        logigraph_data_dir=str(logg_dir),
        target=target,
    )

    # Pre-write the unit so the second call sees no change.
    unit_path = tmp_path / ".config" / "systemd" / "user" / _SYSTEMD_UNIT
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(generate_systemd_unit(target, str(depg_dir), str(logg_dir)))

    calls_seen: list[list[str]] = []

    def _run(cmd, **kwargs):
        calls_seen.append(list(cmd))
        result = MagicMock()
        result.returncode = 0  # service already active
        return result

    with patch("subprocess.run", side_effect=_run):
        with patch("kg.cli.install.systemd._systemctl_available", return_value=True):
            rc = cmd_systemd(args)

    assert rc == 0
    cmd_names = [c[2] if len(c) > 2 else "" for c in calls_seen if c[:2] == ["systemctl", "--user"]]
    assert "daemon-reload" not in cmd_names


def test_apply_no_systemctl_when_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Warns and returns 0 when systemctl not on PATH."""
    monkeypatch.setenv("HOME", str(tmp_path))
    depg_dir, logg_dir, _ = _make_apply_env(tmp_path)
    target = str(tmp_path / "tools")

    with patch("kg.cli.install.systemd._systemctl_available", return_value=False):
        rc = cmd_systemd(
            _apply_args(
                depgraph_data_dir=str(depg_dir),
                logigraph_data_dir=str(logg_dir),
                target=target,
            )
        )

    assert rc == 0
    err_out = capsys.readouterr().err
    assert "systemctl not found" in err_out


# ---------------------------------------------------------------------------
# sibling-hyphen layout auto-detect under --apply
# ---------------------------------------------------------------------------

def test_apply_sibling_hyphen_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply with a sibling-with-hyphen `--project` arg resolves the
    data dirs to that path's children (no nested knowledge-graph/
    subdir appended) and passes preflight."""
    monkeypatch.setenv("HOME", str(tmp_path))
    bundle = tmp_path / "myproject-knowledge-graph"
    depg = bundle / "depgraph"
    logg = bundle / "logigraph"
    depg.mkdir(parents=True)
    logg.mkdir(parents=True)

    # Also set up the graphui venv.
    target = str(tmp_path / "tools")
    tool_bundle = tmp_path / "tools" / "knowledge-graph"
    uvicorn_bin = tool_bundle / "graphui" / ".venv" / "bin" / "uvicorn"
    uvicorn_bin.parent.mkdir(parents=True, exist_ok=True)
    uvicorn_bin.touch(mode=0o755)

    args = argparse.Namespace(
        target=target,
        project=str(bundle),
        depgraph_data_dir=None,
        logigraph_data_dir=None,
        apply=True,
    )

    with patch("subprocess.run", side_effect=_mock_subprocess(is_active=False)):
        with patch("kg.cli.install.systemd._systemctl_available", return_value=True):
            with patch("time.sleep"):
                rc = cmd_systemd(args)

    # Should succeed (not fail with preflight error).
    unit_path = tmp_path / ".config" / "systemd" / "user" / _SYSTEMD_UNIT
    assert unit_path.exists(), "unit file should have been written"
    content = unit_path.read_text()
    assert str(depg) in content
    assert str(logg) in content
