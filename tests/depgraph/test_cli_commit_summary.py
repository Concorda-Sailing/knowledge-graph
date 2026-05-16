"""Tests for depgraph.lib.cli.commit_summary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.commit_summary import cmd_commit_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(
    ctx: Context,
    node_id: str,
    *,
    kind: str = "model",
    repo: str = "test-api",
    path: str = "models/foo.py",
) -> Path:
    """Write a minimal valid node JSON under nodes/."""
    node_file = ctx.NODES / f"{node_id.replace('::', '_').replace('/', '_')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "schema_version": 1,
        "id": node_id,
        "kind": kind,
        "source": {"repo": repo, "path": path},
        "extractor": "python",
        "structural_hash": "aabbccdd11223344",
    }
    node_file.write_text(json.dumps(data))
    return node_file


# ---------------------------------------------------------------------------
# Tests: explicit files arg
# ---------------------------------------------------------------------------

def test_commit_summary_explicit_files_no_nodes(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Explicit files with no tracked nodes → reports 'no tracked changes' style output."""
    ctx = Context.from_data_dir(data_dir)
    # No nodes in the graph, so no matches.
    args = argparse.Namespace(files=["models/foo.py"])
    rc = cmd_commit_summary(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    # Must emit the Depgraph: trailer header regardless.
    assert "Depgraph:" in out


def test_commit_summary_explicit_files_with_matching_node(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Explicit file that matches a tracked node → output mentions the node."""
    ctx = Context.from_data_dir(data_dir)
    # We need a project.toml that registers a repo so _repo_relative can resolve it.
    (data_dir / "project.toml").write_text(
        '[project]\nname = "test"\n\n'
        '[repos.test-api]\npath = "/nonexistent/test-api"\n'
    )
    _make_node(ctx, "test-api::models/foo.py::Foo", kind="model",
               repo="test-api", path="models/foo.py")
    # Pass a relative path matching the registered repo basename.
    args = argparse.Namespace(files=["test-api/models/foo.py"])
    rc = cmd_commit_summary(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Depgraph:" in out
    # The output should mention the file or the node count.
    assert "tracked node" in out


def test_commit_summary_explicit_no_files_empty_list(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty files list with no git repo → falls back to git diff, which may
    fail gracefully since we're not in a git repo or prints no-changes line."""
    ctx = Context.from_data_dir(data_dir)
    # Provide an empty explicit files list (falsy) → triggers git path.
    # In the test environment git may or may not be available, but it must
    # not crash with an unhandled exception.
    args = argparse.Namespace(files=[])
    try:
        rc = cmd_commit_summary(args, ctx)
        # If git is available, we expect a clean exit (0 or 1 depending on diff).
        assert rc in (0, 1)
        out, err = capsys.readouterr()
        # Either the Depgraph: header (no diff) or an error message.
        assert "Depgraph:" in out or "git" in err or rc == 1
    except SystemExit as exc:
        # argparse may call sys.exit in some edge cases; just verify the code.
        assert exc.code in (0, 1, None)


def test_commit_summary_no_files_arg_none(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """args.files = None (no CLI args given) → attempts git diff gracefully."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(files=None)
    try:
        rc = cmd_commit_summary(args, ctx)
        assert rc in (0, 1)
    except SystemExit as exc:
        assert exc.code in (0, 1, None)


# ---------------------------------------------------------------------------
# Tests: output shape
# ---------------------------------------------------------------------------

def test_commit_summary_untracked_files_reported(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Files with no tracked nodes → appear in the untracked section."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(files=["some/random/file.py", "another.ts"])
    rc = cmd_commit_summary(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Depgraph:" in out
    # Both files are untracked; the trailer must mention them.
    assert "untracked" in out


def test_commit_summary_returns_int(
    data_dir: Path,
) -> None:
    """cmd_commit_summary always returns an integer exit code."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(files=["x.py"])
    rc = cmd_commit_summary(args, ctx)
    assert isinstance(rc, int)
