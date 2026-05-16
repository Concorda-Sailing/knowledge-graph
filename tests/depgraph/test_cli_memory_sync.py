"""Tests for depgraph.lib.cli.memory_sync."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.memory_sync import cmd_memory_sync


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args() -> argparse.Namespace:
    return argparse.Namespace()


# ---------------------------------------------------------------------------
# Tests: missing [memory] mirror config
# ---------------------------------------------------------------------------

def test_memory_sync_missing_config_returns_1(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When project.toml has no [memory] section, exits with rc=1 and a message."""
    # data_dir fixture writes a project.toml without [memory]
    ctx = Context.from_data_dir(data_dir)
    rc = cmd_memory_sync(_args(), ctx)
    assert rc == 1
    err = capsys.readouterr().err
    assert "memory-sync" in err
    assert "nothing to do" in err


def test_memory_sync_empty_memory_section_returns_1(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """[memory] section without mirror key also exits with rc=1."""
    (data_dir / "project.toml").write_text(
        '[project]\nname = "test"\n\n[memory]\n'
    )
    ctx = Context.from_data_dir(data_dir)
    rc = cmd_memory_sync(_args(), ctx)
    assert rc == 1
    err = capsys.readouterr().err
    assert "nothing to do" in err


# ---------------------------------------------------------------------------
# Tests: canonical dir missing
# ---------------------------------------------------------------------------

def test_memory_sync_canonical_missing_returns_1(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When canonical dir doesn't exist, exits with rc=1 and an error message."""
    mirror_dir = tmp_path / "mirror"
    # Write project.toml with [memory] mirror pointing to a temp relative path.
    # We need to patch Path.home() so the mirror resolves under tmp_path.
    rel_mirror = "nonexistent-canonical-test-mirror"
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n[memory]\nmirror = "{rel_mirror}"\n'
    )
    ctx = Context.from_data_dir(data_dir)

    # Patch Path.home() to return a tmp dir so canonical path won't exist.
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    # canonical = fake_home / ".claude" / "projects" / <encoded> / "memory"
    # It won't exist since we haven't created it.
    with patch("depgraph.lib.cli.memory_sync.Path") as MockPath:
        # Restore Path behaviour but redirect home()
        import pathlib
        MockPath.side_effect = pathlib.Path
        MockPath.home.return_value = fake_home

        rc = cmd_memory_sync(_args(), ctx)

    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err or "canonical" in err


# ---------------------------------------------------------------------------
# Tests: happy path — files are mirrored
# ---------------------------------------------------------------------------

def test_memory_sync_copies_files(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With a valid canonical dir and mirror config, files are copied and rc=0."""
    # Build fake canonical dir
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    home_encoded = str(fake_home).replace("/", "-")
    canonical = fake_home / ".claude" / "projects" / home_encoded / "memory"
    canonical.mkdir(parents=True)
    (canonical / "foo.md").write_text("# Hello\nNo secrets here.\n")
    (canonical / "bar.md").write_text("Just a note.\n")

    # Mirror will be created under fake_home/<rel>
    mirror_rel = "my-project/memory"
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n[memory]\nmirror = "{mirror_rel}"\n'
    )
    ctx = Context.from_data_dir(data_dir)

    import pathlib
    with patch("depgraph.lib.cli.memory_sync.Path") as MockPath:
        MockPath.side_effect = pathlib.Path
        MockPath.home.return_value = fake_home

        rc = cmd_memory_sync(_args(), ctx)

    assert rc == 0
    out = capsys.readouterr().out
    assert "2 file(s)" in out

    mirror_path = fake_home / mirror_rel
    assert (mirror_path / "foo.md").exists()
    assert (mirror_path / "bar.md").exists()
    assert (mirror_path / "foo.md").read_text() == "# Hello\nNo secrets here.\n"


# ---------------------------------------------------------------------------
# Tests: credential redaction
# ---------------------------------------------------------------------------

def test_memory_sync_redacts_password_line(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Lines matching credential patterns are replaced with REDACTED placeholders."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    home_encoded = str(fake_home).replace("/", "-")
    canonical = fake_home / ".claude" / "projects" / home_encoded / "memory"
    canonical.mkdir(parents=True)
    secret_content = "# Server\npassword: supersecret123\nother: stuff\n"
    (canonical / "secrets.md").write_text(secret_content)

    mirror_rel = "my-project/memory"
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n[memory]\nmirror = "{mirror_rel}"\n'
    )
    ctx = Context.from_data_dir(data_dir)

    import pathlib
    with patch("depgraph.lib.cli.memory_sync.Path") as MockPath:
        MockPath.side_effect = pathlib.Path
        MockPath.home.return_value = fake_home

        rc = cmd_memory_sync(_args(), ctx)

    assert rc == 0
    mirror_path = fake_home / mirror_rel
    mirrored = (mirror_path / "secrets.md").read_text()
    # The password line must be redacted; the rest should survive.
    assert "supersecret123" not in mirrored
    assert "REDACTED" in mirrored
    assert "other: stuff" in mirrored

    # Stats output should mention redaction.
    out = capsys.readouterr().out
    assert "redacted" in out


# ---------------------------------------------------------------------------
# Tests: stale file removal
# ---------------------------------------------------------------------------

def test_memory_sync_removes_stale_files(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Files present in mirror but absent from canonical (except README.md) are removed."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    home_encoded = str(fake_home).replace("/", "-")
    canonical = fake_home / ".claude" / "projects" / home_encoded / "memory"
    canonical.mkdir(parents=True)
    (canonical / "current.md").write_text("current content\n")

    mirror_rel = "my-project/memory"
    mirror_path = fake_home / mirror_rel
    mirror_path.mkdir(parents=True)
    # Pre-populate stale file in mirror
    (mirror_path / "stale.md").write_text("old stuff\n")
    # README.md must NOT be removed
    (mirror_path / "README.md").write_text("readme\n")

    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n[memory]\nmirror = "{mirror_rel}"\n'
    )
    ctx = Context.from_data_dir(data_dir)

    import pathlib
    with patch("depgraph.lib.cli.memory_sync.Path") as MockPath:
        MockPath.side_effect = pathlib.Path
        MockPath.home.return_value = fake_home

        rc = cmd_memory_sync(_args(), ctx)

    assert rc == 0
    assert not (mirror_path / "stale.md").exists()
    assert (mirror_path / "README.md").exists()
    out = capsys.readouterr().out
    assert "stale" in out or "removed" in out


# ---------------------------------------------------------------------------
# Tests: register()
# ---------------------------------------------------------------------------

def test_register_adds_memory_sync_subparser() -> None:
    """register() attaches a 'memory-sync' subparser with the correct default func."""
    import argparse as ap
    from depgraph.lib.cli.memory_sync import register

    parser = ap.ArgumentParser()
    sub = parser.add_subparsers()
    register(sub)

    args = parser.parse_args(["memory-sync"])
    assert hasattr(args, "func")
    assert args.func is cmd_memory_sync
