"""Tests for depgraph.lib.cli.health."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.health import cmd_health


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(ctx: Context, node_id: str, *, kind: str = "model",
               structural_hash: str = "aabbccdd11223344",
               dossier: str | None = None) -> Path:
    """Write a minimal valid node JSON under nodes/."""
    node_file = ctx.NODES / f"{node_id.replace('::', '_')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "schema_version": 1,
        "id": node_id,
        "kind": kind,
        "source": {"repo": "test-api", "path": "models/foo.py"},
        "extractor": "python",
        "structural_hash": structural_hash,
    }
    if dossier is not None:
        data["dossier"] = dossier
    node_file.write_text(json.dumps(data))
    return node_file


def _make_dossier(ctx: Context, rel_path: str, *,
                  last_reviewed_against_hash: str,
                  status: str = "current") -> Path:
    """Write a minimal dossier YAML front-matter file at ctx.DEPGRAPH/rel_path."""
    full = ctx.DEPGRAPH / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(
        f"---\n"
        f"status: {status}\n"
        f"last_reviewed_against_hash: {last_reviewed_against_hash}\n"
        f"---\n"
        f"## The rule\nsome content\n"
    )
    return full


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health_empty_graph_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty nodes/ → no problems → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Depgraph health" in out
    assert "clean" in out


def test_health_single_node_no_dossier_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node with no dossier and few dependents is not a tier-A concern → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(ctx, "test-api::models/foo.py::Foo")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0


def test_health_stale_dossier_exits_nonzero(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose dossier was reviewed against a different hash → stale → exit 1."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/foo.md"
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        structural_hash="currenthash0000001",
        dossier=dossier_rel,
    )
    _make_dossier(ctx, dossier_rel, last_reviewed_against_hash="oldhash99999999")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "stale" in out


def test_health_current_dossier_exits_0(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose dossier hash matches structural_hash → current → exit 0."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/bar.md"
    _make_node(
        ctx,
        "test-api::models/bar.py::Bar",
        structural_hash="matchinghash12345",
        dossier=dossier_rel,
    )
    _make_dossier(ctx, dossier_rel, last_reviewed_against_hash="matchinghash12345")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "clean" in out


def test_health_skips_underscore_files(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Files starting with _ (e.g. _meta.json, _index/) are skipped."""
    ctx = Context.from_data_dir(data_dir)
    # Write a broken JSON file under an underscore name — should be ignored.
    (ctx.NODES / "_broken.json").write_text("NOT VALID JSON")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0
