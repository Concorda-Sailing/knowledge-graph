"""Direct tests for depgraph.lib.cli._shared helpers.

Uses the `data_dir` fixture from tests/depgraph/conftest.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from depgraph.lib.cli._shared import (
    _depgraph_commit_if_changed,
    find_nodes_for_target,
    load_dependents_index,
    mark_regen_in_progress,
)
from depgraph.lib.cli.context import Context


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(ctx: Context, node_id: str, repo: str, rel_path: str) -> Path:
    """Write a minimal node JSON file under nodes/."""
    node_file = ctx.NODES / f"{node_id.replace('::', '__')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "id": node_id,
        "kind": "model",
        "source": {"repo": repo, "path": rel_path},
        "extractor": "python",
        "structural_hash": "aabbccdd11223344",
    }
    node_file.write_text(json.dumps(data))
    return node_file


def _init_git_repo(path: Path) -> None:
    """Initialize a minimal git repo suitable for committing."""
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"],
                   check=True, capture_output=True)


# ---------------------------------------------------------------------------
# find_nodes_for_target
# ---------------------------------------------------------------------------

def test_find_nodes_for_target_by_id_returns_matching_node_file(
    data_dir: Path,
) -> None:
    """Searching by node id (contains '::') returns the file for that node."""
    ctx = Context.from_data_dir(data_dir)
    node_id = "test-api::models/foo.py::Foo"
    node_file = _make_node(ctx, node_id, "test-api", "models/foo.py")

    result = find_nodes_for_target(ctx, node_id)

    assert len(result) == 1
    assert result[0] == node_file


def test_find_nodes_for_target_by_path_resolves_through_project_repos(
    tmp_path: Path,
) -> None:
    """Searching by absolute path resolves through [repos.*] in project.toml."""
    # Set up a synthetic repo checkout directory.
    repo_dir = tmp_path / "my-api"
    repo_dir.mkdir()
    src_file = repo_dir / "models" / "foo.py"
    src_file.parent.mkdir(parents=True)
    src_file.touch()

    # Set up a data_dir with a project.toml that references the repo.
    data_dir = tmp_path / "depgraph"
    (data_dir / "nodes" / "_index").mkdir(parents=True)
    (data_dir / "telemetry").mkdir()
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n'
        f'[repos.api]\npath = "{repo_dir}"\n'
    )

    ctx = Context.from_data_dir(data_dir)
    node_file = _make_node(ctx, "api::models/foo.py::Foo", "my-api", "models/foo.py")

    result = find_nodes_for_target(ctx, str(src_file))

    assert len(result) == 1
    assert result[0] == node_file


def test_find_nodes_for_target_returns_empty_when_repo_unknown(
    tmp_path: Path,
) -> None:
    """A node referencing a repo not configured in project.toml is not matched by path."""
    repo_dir = tmp_path / "unknown-api"
    repo_dir.mkdir()
    src_file = repo_dir / "models" / "bar.py"
    src_file.parent.mkdir(parents=True)
    src_file.touch()

    # project.toml has no [repos.*] entries.
    data_dir = tmp_path / "depgraph"
    (data_dir / "nodes" / "_index").mkdir(parents=True)
    (data_dir / "telemetry").mkdir()
    (data_dir / "project.toml").write_text('[project]\nname = "test"\n')

    ctx = Context.from_data_dir(data_dir)
    # Write a node that claims unknown-api as its repo.
    _make_node(ctx, "unknown-api::models/bar.py::Bar", "unknown-api", "models/bar.py")

    result = find_nodes_for_target(ctx, str(src_file))

    assert result == []


# ---------------------------------------------------------------------------
# load_dependents_index
# ---------------------------------------------------------------------------

def test_load_dependents_index_returns_empty_when_missing(data_dir: Path) -> None:
    """No index file → empty dict (no crash)."""
    ctx = Context.from_data_dir(data_dir)
    assert not ctx.DEPENDENTS_INDEX.exists()
    result = load_dependents_index(ctx)
    assert result == {}


def test_load_dependents_index_handles_corrupt_json(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Corrupt JSON in the index file → empty dict + WARN to stderr."""
    ctx = Context.from_data_dir(data_dir)
    ctx.DEPENDENTS_INDEX.parent.mkdir(parents=True, exist_ok=True)
    ctx.DEPENDENTS_INDEX.write_text("NOT VALID JSON{{{")

    result = load_dependents_index(ctx)

    assert result == {}


def test_load_dependents_index_returns_by_target_on_valid_file(data_dir: Path) -> None:
    """Well-formed index → returns the by_target dict."""
    ctx = Context.from_data_dir(data_dir)
    ctx.DEPENDENTS_INDEX.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "by_target": {
            "api::models/foo.py::Foo": [{"id": "api::routes/x.py::view"}],
        },
    }
    ctx.DEPENDENTS_INDEX.write_text(json.dumps(payload))

    result = load_dependents_index(ctx)

    assert "api::models/foo.py::Foo" in result
    assert result["api::models/foo.py::Foo"][0]["id"] == "api::routes/x.py::view"


# ---------------------------------------------------------------------------
# mark_regen_in_progress
# ---------------------------------------------------------------------------

def test_mark_regen_in_progress_writes_meta_file(data_dir: Path) -> None:
    """mark_regen_in_progress writes a valid _meta.json with regen_status=in_progress."""
    ctx = Context.from_data_dir(data_dir)
    assert not ctx.CORPUS_META.exists()

    mark_regen_in_progress(ctx)

    assert ctx.CORPUS_META.exists()
    meta = json.loads(ctx.CORPUS_META.read_text())
    assert meta["schema_version"] == 1
    assert meta["regen_status"] == "in_progress"
    assert "started_at" in meta


def test_mark_regen_in_progress_preserves_existing_fields(data_dir: Path) -> None:
    """An existing _meta.json with extra fields has them preserved; status is overridden."""
    ctx = Context.from_data_dir(data_dir)
    ctx.NODES.mkdir(parents=True, exist_ok=True)
    existing = {
        "schema_version": 1,
        "regen_status": "complete",
        "git_commit": "abc123",
        "node_count": 42,
    }
    ctx.CORPUS_META.write_text(json.dumps(existing))

    mark_regen_in_progress(ctx)

    meta = json.loads(ctx.CORPUS_META.read_text())
    assert meta["regen_status"] == "in_progress"
    # The extra fields from the previous run should be preserved.
    assert meta.get("git_commit") == "abc123"
    assert meta.get("node_count") == 42


# ---------------------------------------------------------------------------
# _depgraph_commit_if_changed (git integration)
# ---------------------------------------------------------------------------

def test_depgraph_commit_if_changed_returns_true_when_diff_staged(
    data_dir: Path,
) -> None:
    """Returns True when there is a staged change to commit."""
    _init_git_repo(data_dir)
    # Create a node file and commit it so we have a baseline.
    ctx = Context.from_data_dir(data_dir)
    node_file = _make_node(ctx, "api::models/foo.py::Foo", "api", "models/foo.py")
    subprocess.run(["git", "-C", str(data_dir), "add", str(node_file)], check=True)
    subprocess.run(
        ["git", "-C", str(data_dir), "commit", "-m", "initial"],
        check=True, capture_output=True,
    )

    # Now modify the file so there is a new change to stage and commit.
    node_file.write_text(node_file.read_text() + "\n")

    result = _depgraph_commit_if_changed(
        ctx, [node_file], "test: update node"
    )

    assert result is True


def test_depgraph_commit_if_changed_returns_false_when_nothing_to_commit(
    data_dir: Path,
) -> None:
    """Returns False when there are no staged changes."""
    _init_git_repo(data_dir)
    ctx = Context.from_data_dir(data_dir)
    node_file = _make_node(ctx, "api::models/bar.py::Bar", "api", "models/bar.py")
    # Stage and commit the file first.
    subprocess.run(["git", "-C", str(data_dir), "add", str(node_file)], check=True)
    subprocess.run(
        ["git", "-C", str(data_dir), "commit", "-m", "initial"],
        check=True, capture_output=True,
    )

    # Call with the same file, no changes since last commit.
    result = _depgraph_commit_if_changed(
        ctx, [node_file], "test: no-op commit"
    )

    assert result is False
