"""Tests for depgraph.lib.cli.orphans."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.orphans import cmd_orphans


def _make_node(ctx: Context, node_id: str, repo: str, rel_path: str) -> Path:
    """Write a minimal node JSON file under nodes/."""
    node_file = ctx.NODES / f"{node_id.replace('::', '_')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    node_file.write_text(json.dumps({
        "id": node_id,
        "source": {"repo": repo, "path": rel_path},
    }))
    return node_file


def _make_project_toml(data_dir: Path, repo_path: Path) -> None:
    """Write a project.toml pointing at repo_path.

    The [repos.<key>] table key must equal the directory basename so that
    basename_path_map() returns {basename: path} and matches the `source.repo`
    field stored in node JSON files.
    """
    key = repo_path.name  # basename == key, matching real-world concorda layout
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n'
        f'[repos.{key}]\npath = "{repo_path}"\n'
    )


def test_orphans_no_orphans_when_source_exists(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose source file exists is NOT flagged as an orphan."""
    fake_repo = tmp_path / "fake-repo"
    fake_repo.mkdir()
    src_file = fake_repo / "models" / "foo.py"
    src_file.parent.mkdir(parents=True)
    src_file.touch()

    _make_project_toml(data_dir, fake_repo)
    ctx = Context.from_data_dir(data_dir)
    _make_node(ctx, "fake-repo::models/foo.py::Foo", "fake-repo", "models/foo.py")

    args = argparse.Namespace(purge=False)
    rc = cmd_orphans(args, ctx)

    assert rc == 0
    out = capsys.readouterr().out
    assert "no orphans" in out


def test_orphans_detects_missing_source(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose source file is missing IS flagged as an orphan."""
    fake_repo = tmp_path / "fake-repo"
    fake_repo.mkdir()
    # Do NOT create the source file — it's intentionally absent.

    _make_project_toml(data_dir, fake_repo)
    ctx = Context.from_data_dir(data_dir)
    _make_node(ctx, "fake-repo::models/gone.py::Gone", "fake-repo", "models/gone.py")

    args = argparse.Namespace(purge=False)
    rc = cmd_orphans(args, ctx)

    assert rc == 0
    out = capsys.readouterr().out
    assert "orphan:" in out
    assert "fake-repo::models/gone.py::Gone" in out


def test_orphans_purge_archives_orphan_file(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With --purge, the orphan node file is moved to nodes/_archive/."""
    fake_repo = tmp_path / "fake-repo"
    fake_repo.mkdir()

    _make_project_toml(data_dir, fake_repo)
    ctx = Context.from_data_dir(data_dir)
    node_file = _make_node(ctx, "fake-repo::models/deleted.py::Deleted", "fake-repo", "models/deleted.py")

    assert node_file.exists()

    args = argparse.Namespace(purge=True)
    rc = cmd_orphans(args, ctx)

    assert rc == 0
    # Original file must be gone.
    assert not node_file.exists()
    # Archive directory must contain the file.
    archive = ctx.NODES / "_archive"
    assert (archive / node_file.name).exists()
    out = capsys.readouterr().out
    assert "archived" in out
