"""Tests for logigraph.lib.cli.rollup_cmd.cmd_rollup."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.rollup_cmd import cmd_rollup


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _write_domain_node(ctx: Context, node_id: str, node: dict) -> None:
    domain_dir = ctx.NODES / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    parts = node_id.split("::")
    p = domain_dir / f"{parts[0]}__{parts[1]}__{parts[2]}.json"
    p.write_text(json.dumps(node) + "\n")


def _write_dependents_index(depgraph_dir: Path, index: dict) -> None:
    """Plant the dependents.json index that load_rollup_inputs requires."""
    idx_dir = depgraph_dir / "nodes" / "_index"
    idx_dir.mkdir(parents=True, exist_ok=True)
    (idx_dir / "dependents.json").write_text(json.dumps(index) + "\n")


# ---------------------------------------------------------------------------
# Missing entity_id → stderr + exit 1
# ---------------------------------------------------------------------------

def test_rollup_missing_entity_exits_1(ctx: Context, capsys) -> None:
    """An entity_id not in logigraph nodes emits stderr and exits 1."""
    # Need dependents.json so load_rollup_inputs doesn't raise first.
    _write_dependents_index(ctx.depgraph_dir, {"by_target": {}})
    args = argparse.Namespace(
        entity_id="resource::test::nonexistent",
        kind=None, depth=3, format="text",
    )
    rc = cmd_rollup(args, ctx)
    assert rc == 1
    err = capsys.readouterr().err
    assert "no logigraph node" in err
    assert "resource::test::nonexistent" in err


# ---------------------------------------------------------------------------
# Missing dependents index → FileNotFoundError propagates
# ---------------------------------------------------------------------------

def test_rollup_missing_dependents_raises(ctx: Context) -> None:
    """When dependents.json is absent, load_rollup_inputs raises FileNotFoundError."""
    _write_domain_node(ctx, "resource::test::thing", {
        "id": "resource::test::thing", "kind": "domain", "subkind": "resource",
        "title": "Thing", "summary": "", "definition_status": "stub",
        "structural_hash": "d001",
    })
    args = argparse.Namespace(
        entity_id="resource::test::thing",
        kind=None, depth=3, format="text",
    )
    with pytest.raises(FileNotFoundError, match="dependents"):
        cmd_rollup(args, ctx)


# ---------------------------------------------------------------------------
# Successful rollup — text format, no anchor (not_found is still valid)
# ---------------------------------------------------------------------------

def test_rollup_text_format_no_anchor(ctx: Context, capsys) -> None:
    """A domain node with no resolvable anchor produces text output, exits 0."""
    _write_dependents_index(ctx.depgraph_dir, {"by_target": {}})
    _write_domain_node(ctx, "resource::test::thing", {
        "id": "resource::test::thing", "kind": "domain", "subkind": "resource",
        "title": "Thing", "summary": "", "definition_status": "stub",
        "structural_hash": "d001",
        # No `source` field → anchor resolves to not_found
    })
    args = argparse.Namespace(
        entity_id="resource::test::thing",
        kind=None, depth=3, format="text",
    )
    rc = cmd_rollup(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    # format_rollup_text always returns some string (anchor info at minimum)
    assert isinstance(out, str)


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def test_rollup_json_format(ctx: Context, capsys) -> None:
    """--format json produces parseable JSON output."""
    _write_dependents_index(ctx.depgraph_dir, {"by_target": {}})
    _write_domain_node(ctx, "resource::test::jsonable", {
        "id": "resource::test::jsonable", "kind": "domain", "subkind": "resource",
        "title": "Jsonable", "summary": "", "definition_status": "stub",
        "structural_hash": "d002",
    })
    args = argparse.Namespace(
        entity_id="resource::test::jsonable",
        kind=None, depth=3, format="json",
    )
    rc = cmd_rollup(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# --kind filter applied post-compute
# ---------------------------------------------------------------------------

def test_rollup_kind_filter(ctx: Context, capsys) -> None:
    """--kind restricts output to the requested kinds (no crash on empty filter)."""
    _write_dependents_index(ctx.depgraph_dir, {"by_target": {}})
    _write_domain_node(ctx, "resource::test::filtered", {
        "id": "resource::test::filtered", "kind": "domain", "subkind": "resource",
        "title": "Filtered", "summary": "", "definition_status": "stub",
        "structural_hash": "d003",
    })
    args = argparse.Namespace(
        entity_id="resource::test::filtered",
        kind="model",  # filter to model only
        depth=3, format="text",
    )
    rc = cmd_rollup(args, ctx)
    assert rc == 0
