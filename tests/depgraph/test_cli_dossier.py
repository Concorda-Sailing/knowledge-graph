"""Tests for depgraph.lib.cli.dossier — all 4 lifecycle handlers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.dossier import (
    cmd_dossier_rank,
    cmd_dossier_draft,
    cmd_dossier_finalize,
    cmd_dossier_bump,
)


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
    structural_hash: str = "aabbccdd11223344",
    dossier: str | None = None,
) -> Path:
    node_file = ctx.NODES / f"{node_id.replace('::', '_').replace('/', '_')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "schema_version": 1,
        "id": node_id,
        "kind": kind,
        "source": {"repo": repo, "path": path, "line": 1},
        "extractor": "python",
        "structural_hash": structural_hash,
    }
    if dossier is not None:
        data["dossier"] = dossier
    node_file.write_text(json.dumps(data))
    return node_file


def _make_dossier(
    ctx: Context,
    rel: str,
    *,
    structural_hash: str = "aabbccdd11223344",
    status: str = "llm_drafted",
) -> Path:
    p = ctx.DEPGRAPH / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\nnode_id: test-api::models/foo.py::Foo\n"
        f"last_reviewed_against_hash: {structural_hash}\n"
        f"status: {status}\n---\n\n# Foo\n\nBody text.\n"
    )
    return p


# ---------------------------------------------------------------------------
# dossier-rank
# ---------------------------------------------------------------------------

def test_dossier_rank_outputs_header(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: with no nodes, rank still prints the table header."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(
        only_stale=False,
        only_unreviewed=True,
        tier=None,
        limit=50,
        include_tests=False,
    )
    rc = cmd_dossier_rank(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "fan" in out
    assert "total:" in out


def test_dossier_rank_lists_unreviewed_node(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose dossier has status: unreviewed shows up in rank output."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/foo.py/Foo.md"
    _make_node(ctx, "test-api::models/foo.py::Foo", dossier=dossier_rel)
    # Write a dossier with status: unreviewed (no last_reviewed_against_hash)
    p = ctx.DEPGRAPH / dossier_rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\nstatus: unreviewed\n---\n\n# Foo\n\nBody.\n")
    args = argparse.Namespace(
        only_stale=False,
        only_unreviewed=True,
        tier=None,
        limit=50,
        include_tests=False,
    )
    rc = cmd_dossier_rank(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-api::models/foo.py::Foo" in out


# ---------------------------------------------------------------------------
# dossier-draft
# ---------------------------------------------------------------------------

def test_dossier_draft_outputs_prompt(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: draft emits an LLM prompt referencing the node id."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        dossier="dossiers/test-api/models/foo.py/Foo.md",
    )
    (data_dir / "project.toml").write_text(
        '[project]\nname = "test"\n\n'
        '[repos.test-api]\npath = "/nonexistent/test-api"\n'
    )
    args = argparse.Namespace(target="test-api::models/foo.py::Foo")
    rc = cmd_dossier_draft(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-api::models/foo.py::Foo" in out
    assert "dossier-finalize" in out


def test_dossier_draft_missing_node_returns_1(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """draft with an unknown id returns exit code 1."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(target="no-such::node")
    rc = cmd_dossier_draft(args, ctx)
    assert rc == 1


# ---------------------------------------------------------------------------
# dossier-finalize
# ---------------------------------------------------------------------------

def test_dossier_finalize_writes_body(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: finalize writes the dossier file with frontmatter."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/foo.py/Foo.md"
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        dossier=dossier_rel,
    )

    body_file = tmp_path / "body.md"
    body_file.write_text("## Purpose\nDoes things.\n")

    args = argparse.Namespace(
        node_id="test-api::models/foo.py::Foo",
        body_file=str(body_file),
        authored_by=[],
    )
    rc = cmd_dossier_finalize(args, ctx)
    assert rc == 0

    dossier_path = ctx.DEPGRAPH / dossier_rel
    assert dossier_path.exists()
    text = dossier_path.read_text()
    assert "status: llm_drafted" in text
    assert "## Purpose" in text


def test_dossier_finalize_missing_node_returns_1(
    data_dir: Path, tmp_path: Path
) -> None:
    """finalize with unknown node_id returns exit code 1."""
    ctx = Context.from_data_dir(data_dir)
    body_file = tmp_path / "body.md"
    body_file.write_text("## Purpose\nDoes things.\n")
    args = argparse.Namespace(
        node_id="no-such::node",
        body_file=str(body_file),
        authored_by=[],
    )
    rc = cmd_dossier_finalize(args, ctx)
    assert rc == 1


# ---------------------------------------------------------------------------
# dossier-bump
# ---------------------------------------------------------------------------

def test_dossier_bump_updates_status(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: bump updates status from llm_drafted to current."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/foo.py/Foo.md"
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        dossier=dossier_rel,
    )
    _make_dossier(ctx, dossier_rel, status="llm_drafted")

    args = argparse.Namespace(
        node_id="test-api::models/foo.py::Foo",
        status="current",
    )
    rc = cmd_dossier_bump(args, ctx)
    assert rc == 0

    text = (ctx.DEPGRAPH / dossier_rel).read_text()
    assert "status: current" in text


def test_dossier_bump_missing_node_returns_1(
    data_dir: Path,
) -> None:
    """bump with unknown node_id returns exit code 1."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(node_id="no-such::node", status="current")
    rc = cmd_dossier_bump(args, ctx)
    assert rc == 1
