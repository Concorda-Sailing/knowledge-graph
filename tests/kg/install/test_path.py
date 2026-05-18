"""Tests for kg/cli/install/path.py — port of install.sh:cmd_path()."""
from __future__ import annotations

import argparse
import stat
from pathlib import Path

import pytest

from kg.cli.install.path import (
    PATH_BLOCK_MARKER,
    generate_path_snippet,
    cmd_path,
)

_DEFAULT_TARGET = str(Path.home() / "tools")
_BUNDLE_DIR = "knowledge-graph"


# ---------------------------------------------------------------------------
# generate_path_snippet — snippet content
# ---------------------------------------------------------------------------


def test_generate_path_snippet_contains_marker() -> None:
    """Snippet starts with the sentinel comment."""
    snippet = generate_path_snippet("/home/user/tools")
    assert snippet.startswith(PATH_BLOCK_MARKER)


def test_generate_path_snippet_contains_both_bins() -> None:
    """Snippet adds both depgraph/bin and logigraph/bin to PATH."""
    snippet = generate_path_snippet("/home/user/tools")
    assert "depgraph/bin" in snippet
    assert "logigraph/bin" in snippet
    assert "export PATH" in snippet


def test_generate_path_snippet_target_embedded() -> None:
    """Snippet uses the supplied target path."""
    snippet = generate_path_snippet("/custom/target")
    assert "/custom/target/knowledge-graph/depgraph/bin" in snippet
    assert "/custom/target/knowledge-graph/logigraph/bin" in snippet


def test_generate_path_snippet_trailing_newline() -> None:
    """Snippet ends with exactly one newline (matches bash heredoc)."""
    snippet = generate_path_snippet("/t")
    assert snippet.endswith("\n")
    assert not snippet.endswith("\n\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_args(
    *,
    target: str = _DEFAULT_TARGET,
    rcfile: str | None = None,
    apply: bool = False,
    force: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        target=target,
        rcfile=rcfile,
        apply=apply,
        force=force,
    )


# ---------------------------------------------------------------------------
# dry-run (no --apply)
# ---------------------------------------------------------------------------


def test_dry_run_prints_snippet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Dry-run prints the header comment and snippet to stdout."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rc = cmd_path(_make_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "# Append the following to" in out
    assert PATH_BLOCK_MARKER in out
    assert "depgraph/bin" in out
    assert "logigraph/bin" in out
    assert "export PATH" in out


def test_dry_run_names_rcfile_in_header(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Dry-run header includes the rcfile path."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rcfile = str(tmp_path / "custom.rc")
    rc = cmd_path(_make_args(rcfile=rcfile))
    assert rc == 0
    out = capsys.readouterr().out
    assert rcfile in out


def test_dry_run_default_rcfile_is_dot_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Without --rcfile, default is ~/.profile (uses $HOME)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rc = cmd_path(_make_args())
    assert rc == 0
    out = capsys.readouterr().out
    expected = str(tmp_path / ".profile")
    assert expected in out


def test_dry_run_does_not_write_rcfile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dry-run must not create or modify the rcfile."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rc = cmd_path(_make_args())
    assert rc == 0
    profile = tmp_path / ".profile"
    assert not profile.exists()


# ---------------------------------------------------------------------------
# --apply: case 1 — no block present, append
# ---------------------------------------------------------------------------


def test_apply_empty_rcfile_writes_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply to an empty rcfile appends the PATH block."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rcfile = tmp_path / ".profile"
    rcfile.touch()

    rc = cmd_path(_make_args(rcfile=str(rcfile), apply=True))
    assert rc == 0
    content = rcfile.read_text()
    assert PATH_BLOCK_MARKER in content
    assert "depgraph/bin" in content
    assert "export PATH" in content


def test_apply_writes_expected_snippet_verbatim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The written block equals generate_path_snippet output."""
    monkeypatch.setenv("HOME", str(tmp_path))
    target = str(tmp_path / "tools")
    rcfile = tmp_path / ".profile"
    rcfile.touch()

    rc = cmd_path(_make_args(target=target, rcfile=str(rcfile), apply=True))
    assert rc == 0
    content = rcfile.read_text()
    expected = generate_path_snippet(target)
    # Block must appear verbatim inside the file.
    assert expected.rstrip() in content


def test_apply_creates_rcfile_parent_dirs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply creates missing parent directories for rcfile."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rcfile = tmp_path / "subdir" / ".profile"
    # Parent doesn't exist yet.

    rc = cmd_path(_make_args(rcfile=str(rcfile), apply=True))
    assert rc == 0
    assert rcfile.exists()
    assert PATH_BLOCK_MARKER in rcfile.read_text()


# ---------------------------------------------------------------------------
# --apply: case 2 — block present, same target → no-op
# ---------------------------------------------------------------------------


def test_apply_same_target_is_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply with same target is a no-op (file unchanged)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    target = str(tmp_path / "tools")
    rcfile = tmp_path / ".profile"
    rcfile.touch()

    # First apply writes the block.
    cmd_path(_make_args(target=target, rcfile=str(rcfile), apply=True))
    first_content = rcfile.read_text()
    first_mtime = rcfile.stat().st_mtime_ns

    # Second apply should be a no-op.
    rc = cmd_path(_make_args(target=target, rcfile=str(rcfile), apply=True))
    assert rc == 0
    second_content = rcfile.read_text()
    assert first_content == second_content
    assert rcfile.stat().st_mtime_ns == first_mtime  # file not touched

    out = capsys.readouterr().out
    assert "no-op" in out or "already current" in out


# ---------------------------------------------------------------------------
# --apply: case 3 — different target, no --force → refuse
# ---------------------------------------------------------------------------


def test_apply_different_target_without_force_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply with different target but no --force returns non-zero and stderr."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rcfile = tmp_path / ".profile"
    rcfile.touch()

    # Write a block for original target.
    old_target = str(tmp_path / "old-tools")
    cmd_path(_make_args(target=old_target, rcfile=str(rcfile), apply=True))

    # Attempt to update to new target without --force.
    new_target = str(tmp_path / "new-tools")
    rc = cmd_path(_make_args(target=new_target, rcfile=str(rcfile), apply=True))
    assert rc != 0
    err_out = capsys.readouterr().err
    assert "--apply --force" in err_out or "force" in err_out.lower()


def test_apply_different_target_without_force_does_not_modify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without --force, the rcfile is not modified when target differs."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rcfile = tmp_path / ".profile"
    rcfile.touch()

    old_target = str(tmp_path / "old-tools")
    cmd_path(_make_args(target=old_target, rcfile=str(rcfile), apply=True))
    content_after_first = rcfile.read_text()

    new_target = str(tmp_path / "new-tools")
    cmd_path(_make_args(target=new_target, rcfile=str(rcfile), apply=True))
    assert rcfile.read_text() == content_after_first


# ---------------------------------------------------------------------------
# --apply: case 4 — different target, --force → backup + replace
# ---------------------------------------------------------------------------


def test_apply_force_replaces_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """--apply --force replaces a stale block with the new target."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rcfile = tmp_path / ".profile"
    rcfile.touch()

    old_target = str(tmp_path / "old-tools")
    cmd_path(_make_args(target=old_target, rcfile=str(rcfile), apply=True))

    new_target = str(tmp_path / "new-tools")
    rc = cmd_path(_make_args(target=new_target, rcfile=str(rcfile), apply=True, force=True))
    assert rc == 0
    content = rcfile.read_text()
    assert f"{new_target}/knowledge-graph/depgraph/bin" in content
    assert f"{old_target}/knowledge-graph/depgraph/bin" not in content


def test_apply_force_creates_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--apply --force creates a backup file before overwriting."""
    monkeypatch.setenv("HOME", str(tmp_path))
    rcfile = tmp_path / ".profile"
    rcfile.touch()

    old_target = str(tmp_path / "old-tools")
    cmd_path(_make_args(target=old_target, rcfile=str(rcfile), apply=True))

    new_target = str(tmp_path / "new-tools")
    cmd_path(_make_args(target=new_target, rcfile=str(rcfile), apply=True, force=True))

    # Single-suffix backup of the prior ~/.profile should exist.
    assert (tmp_path / ".profile.bak").exists()
    # And no legacy timestamped backups accumulated across the two apply runs.
    assert list(tmp_path.glob(".profile.bak.*")) == []
