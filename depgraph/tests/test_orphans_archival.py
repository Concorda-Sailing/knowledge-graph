"""Tests for the orphans archival fix (#43): repeat archival of a node with
the same source name must not raise OSError, and archived files carry
`_archived_at` / `_archive_reason` metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.orphans import archive_node_file, cmd_orphans


def _write_node(node_path: Path, *, node_id: str, repo: str, rel: str) -> None:
    node_path.parent.mkdir(parents=True, exist_ok=True)
    node_path.write_text(json.dumps({
        "id": node_id,
        "primitive": "function",
        "name": rel.split("/")[-1],
        "source": {"repo": repo, "path": rel, "language": "python"},
    }))


def _make_ctx(depgraph: Path) -> Context:
    (depgraph / "nodes").mkdir(parents=True, exist_ok=True)
    return Context.from_data_dir(depgraph)


def test_archive_node_file_writes_metadata(tmp_path):
    node = tmp_path / "nodes" / "fn.json"
    _write_node(node, node_id="r::a.py::f", repo="r", rel="a.py")
    archive = tmp_path / "nodes" / "_archive"

    dest = archive_node_file(node, archive, reason="source_path_missing")

    assert dest.exists()
    assert not node.exists(), "original should have been moved"
    body = json.loads(dest.read_text())
    assert body["_archived_at"], "archived file should carry _archived_at"
    assert body["_archive_reason"] == "source_path_missing"


def test_archive_node_file_handles_name_collision(tmp_path):
    """Repeat archival of same-named node must not raise — earlier copy stays
    put (with its own stamp), newer copy gets a timestamp-suffixed name."""
    archive = tmp_path / "nodes" / "_archive"

    first = tmp_path / "nodes" / "fn.json"
    _write_node(first, node_id="r::a.py::f", repo="r", rel="a.py")
    dest1 = archive_node_file(first, archive, reason="source_path_missing")

    second = tmp_path / "nodes" / "fn.json"
    _write_node(second, node_id="r::a.py::f", repo="r", rel="a.py")
    dest2 = archive_node_file(second, archive, reason="source_path_missing")

    assert dest1.exists() and dest2.exists()
    assert dest1 != dest2
    # The collision-resolved name encodes the archival timestamp.
    assert "archived-" in dest2.name


def test_cmd_orphans_purge_rerun_no_oserror(tmp_path):
    """Whole-loop guard: --purge twice in a row over a recurring node must
    not abort with OSError: File exists."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)

    # project.toml so basename_path_map resolves "r" → an existing-but-empty repo.
    repo_root = tmp_path / "r"
    repo_root.mkdir()
    (depgraph / "project.toml").write_text(
        f'[repos.r]\npath = "{repo_root}"\nlanguages = ["python"]\n'
    )

    args = argparse.Namespace(purge=True)

    # Round 1: create node pointing at non-existent source, purge it.
    node = depgraph / "nodes" / "fn.json"
    _write_node(node, node_id="r::a.py::f", repo="r", rel="a.py")
    rc = cmd_orphans(args, ctx)
    assert rc == 0
    assert not node.exists()

    # Round 2: same-named node reappears (re-extraction), purge again.
    _write_node(node, node_id="r::a.py::f", repo="r", rel="a.py")
    rc = cmd_orphans(args, ctx)
    assert rc == 0
    archived = list((depgraph / "nodes" / "_archive").glob("*.json"))
    assert len(archived) == 2, f"expected two archived files, got {archived}"
