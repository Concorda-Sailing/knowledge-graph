"""Tests for kg/cli/install/cascade.py — port of install.sh:cmd_cascade()."""
from __future__ import annotations

import argparse
import os
import stat
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from kg.cli.install.cascade import (
    generate_hook_script,
    cmd_cascade,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_git_repo(path: Path) -> None:
    """Create a minimal git repo at *path*."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", str(path)],
        capture_output=True,
        check=True,
    )


def _make_args(
    *,
    target_repo: str,
    depgraph: str = "",
    logigraph: str = "",
    apply: bool = False,
    force: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        target_repo=target_repo,
        depgraph=depgraph,
        logigraph=logigraph,
        apply=apply,
        force=force,
    )


# ---------------------------------------------------------------------------
# generate_hook_script — content
# ---------------------------------------------------------------------------


def test_generate_hook_script_shebang() -> None:
    """Generated hook starts with #!/bin/bash."""
    script = generate_hook_script(
        depgraph="/data/depgraph",
        logigraph="/data/logigraph",
        script_path="/tools/bin/kg-prepush-cascade",
    )
    assert script.startswith("#!/bin/bash\n")


def test_generate_hook_script_sets_depgraph_env() -> None:
    """KG_DEPGRAPH_DIR is exported with the supplied depgraph path."""
    script = generate_hook_script(
        depgraph="/data/depgraph",
        logigraph="",
        script_path="/tools/bin/kg-prepush-cascade",
    )
    assert 'export KG_DEPGRAPH_DIR="/data/depgraph"' in script


def test_generate_hook_script_sets_logigraph_env() -> None:
    """KG_LOGIGRAPH_DIR is exported with the supplied logigraph path."""
    script = generate_hook_script(
        depgraph="",
        logigraph="/data/logigraph",
        script_path="/tools/bin/kg-prepush-cascade",
    )
    assert 'export KG_LOGIGRAPH_DIR="/data/logigraph"' in script


def test_generate_hook_script_exec_line() -> None:
    """Hook ends with exec pointing at kg-prepush-cascade."""
    sp = "/tools/bin/kg-prepush-cascade"
    script = generate_hook_script(
        depgraph="/d",
        logigraph="/l",
        script_path=sp,
    )
    assert f'exec "{sp}" "$@"' in script


def test_generate_hook_script_trailing_newline() -> None:
    """Hook content ends with exactly one newline (matches bash printf + newline)."""
    script = generate_hook_script("/d", "/l", "/sp")
    assert script.endswith("\n")
    assert not script.endswith("\n\n")


# ---------------------------------------------------------------------------
# dry-run (no --apply)
# ---------------------------------------------------------------------------


def test_dry_run_prints_hook_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Dry-run prints the full hook script to stdout."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    depg = tmp_path / "depgraph"
    depg.mkdir()
    logg = tmp_path / "logigraph"
    logg.mkdir()

    # Patch script_path existence check so the test isn't coupled to disk layout.
    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        rc = cmd_cascade(_make_args(
            target_repo=str(repo),
            depgraph=str(depg),
            logigraph=str(logg),
        ))
    assert rc == 0
    out = capsys.readouterr().out
    assert "#!/bin/bash" in out
    assert "KG_DEPGRAPH_DIR" in out
    assert "kg-prepush-cascade" in out


def test_dry_run_not_written_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Dry-run prints 'not written' notice."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    depg = tmp_path / "depgraph"
    depg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        cmd_cascade(_make_args(target_repo=str(repo), depgraph=str(depg)))
    out = capsys.readouterr().out
    assert "not written" in out
    assert "pre-push" in out


def test_dry_run_does_not_write_hook(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dry-run must not create .git/hooks/pre-push."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    depg = tmp_path / "depgraph"
    depg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        cmd_cascade(_make_args(target_repo=str(repo), depgraph=str(depg)))
    hook = repo / ".git" / "hooks" / "pre-push"
    assert not hook.exists()


# ---------------------------------------------------------------------------
# --apply: write hook to a git repo
# ---------------------------------------------------------------------------


def test_apply_writes_hook_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply writes .git/hooks/pre-push."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    depg = tmp_path / "depgraph"
    depg.mkdir()
    logg = tmp_path / "logigraph"
    logg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        rc = cmd_cascade(_make_args(
            target_repo=str(repo),
            depgraph=str(depg),
            logigraph=str(logg),
            apply=True,
        ))
    assert rc == 0
    hook = repo / ".git" / "hooks" / "pre-push"
    assert hook.exists()
    content = hook.read_text()
    assert "#!/bin/bash" in content
    assert str(depg) in content


def test_apply_hook_is_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply sets executable bit on the hook."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    depg = tmp_path / "depgraph"
    depg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        cmd_cascade(_make_args(
            target_repo=str(repo),
            depgraph=str(depg),
            apply=True,
        ))
    hook = repo / ".git" / "hooks" / "pre-push"
    mode = hook.stat().st_mode
    assert mode & stat.S_IXUSR, "hook must have owner execute bit"


def test_apply_hook_content_matches_generate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Written hook bytes-equal generate_hook_script output."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    depg = tmp_path / "depgraph"
    depg.mkdir()
    logg = tmp_path / "logigraph"
    logg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()
    script_path_str = str(fake_script)

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=script_path_str):
        cmd_cascade(_make_args(
            target_repo=str(repo),
            depgraph=str(depg),
            logigraph=str(logg),
            apply=True,
        ))
    hook = repo / ".git" / "hooks" / "pre-push"
    expected = generate_hook_script(str(depg), str(logg), script_path_str)
    assert hook.read_text() == expected


# ---------------------------------------------------------------------------
# --apply: idempotent — same content → no-op
# ---------------------------------------------------------------------------


def test_apply_same_content_is_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply when hook already exists with same content → no-op."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    depg = tmp_path / "depgraph"
    depg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        # First apply.
        cmd_cascade(_make_args(target_repo=str(repo), depgraph=str(depg), apply=True))
        hook = repo / ".git" / "hooks" / "pre-push"
        first_content = hook.read_text()
        first_mtime = hook.stat().st_mtime_ns

        # Second apply — should be no-op.
        rc = cmd_cascade(_make_args(target_repo=str(repo), depgraph=str(depg), apply=True))

    assert rc == 0
    assert hook.read_text() == first_content
    assert hook.stat().st_mtime_ns == first_mtime
    out = capsys.readouterr().out
    assert "already in place" in out or "no-op" in out.lower()


# ---------------------------------------------------------------------------
# --apply: different content → backup before overwrite
# ---------------------------------------------------------------------------


def test_apply_different_content_creates_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply when hook exists with different content → backup before overwrite."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    old_hook = hooks_dir / "pre-push"
    old_hook.write_text("#!/bin/bash\n# old hook\n")

    depg = tmp_path / "depgraph"
    depg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        rc = cmd_cascade(_make_args(
            target_repo=str(repo),
            depgraph=str(depg),
            apply=True,
        ))
    assert rc == 0
    # A backup should exist.
    backups = list(hooks_dir.glob("pre-push.bak.*"))
    assert len(backups) >= 1
    # And the hook should now contain the new content.
    assert "#!/bin/bash" in old_hook.read_text()
    assert "KG_DEPGRAPH_DIR" in old_hook.read_text()


def test_apply_different_content_warns_about_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply with existing different hook emits a warning about backup."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (hooks_dir / "pre-push").write_text("#!/bin/bash\n# old hook\n")

    depg = tmp_path / "depgraph"
    depg.mkdir()

    fake_script = tmp_path / "kg-prepush-cascade"
    fake_script.touch()

    with patch("kg.cli.install.cascade._resolve_script_path", return_value=str(fake_script)):
        cmd_cascade(_make_args(
            target_repo=str(repo),
            depgraph=str(depg),
            apply=True,
        ))
    err_out = capsys.readouterr().err
    assert "backed up" in err_out or "backup" in err_out.lower()


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_refuse_if_not_git_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SystemExit if target_repo is not a git repository."""
    monkeypatch.setenv("HOME", str(tmp_path))
    not_a_repo = tmp_path / "notrepo"
    not_a_repo.mkdir()
    depg = tmp_path / "depgraph"
    depg.mkdir()

    with pytest.raises(SystemExit):
        cmd_cascade(_make_args(target_repo=str(not_a_repo), depgraph=str(depg)))


def test_refuse_if_no_depgraph_or_logigraph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SystemExit if neither --depgraph nor --logigraph is supplied."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)

    with pytest.raises(SystemExit):
        cmd_cascade(_make_args(target_repo=str(repo)))


def test_refuse_if_depgraph_dir_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SystemExit if --depgraph path doesn't exist."""
    monkeypatch.setenv("HOME", str(tmp_path))
    repo = tmp_path / "myrepo"
    _init_git_repo(repo)

    with pytest.raises(SystemExit):
        cmd_cascade(_make_args(
            target_repo=str(repo),
            depgraph=str(tmp_path / "nonexistent"),
        ))
