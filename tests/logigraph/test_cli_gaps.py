"""Tests for logigraph.lib.cli.gaps.cmd_gaps."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.gaps import cmd_gaps


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _write_rule_node(ctx: Context, node_id: str, node: dict) -> None:
    rules_dir = ctx.NODES / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    parts = node_id.split("::")
    p = rules_dir / f"{parts[1]}__{parts[2]}.json"
    p.write_text(json.dumps(node) + "\n")


def _write_domain_node(ctx: Context, node_id: str, node: dict) -> None:
    domain_dir = ctx.NODES / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    parts = node_id.split("::")
    p = domain_dir / f"{parts[0]}__{parts[1]}__{parts[2]}.json"
    p.write_text(json.dumps(node) + "\n")


def _write_depgraph_node(ctx: Context, node_id: str, node: dict) -> None:
    """Write a fake depgraph node into the fake-depgraph nodes dir."""
    dnodes = ctx.depgraph_dir / "nodes"
    dnodes.mkdir(parents=True, exist_ok=True)
    safe = node_id.replace("::", "__").replace("/", "_")
    (dnodes / f"{safe}.json").write_text(json.dumps(node) + "\n")


# ---------------------------------------------------------------------------
# No nodes → no gaps
# ---------------------------------------------------------------------------

def test_gaps_empty_corpus_no_gaps(ctx: Context, capsys) -> None:
    """Empty corpus prints 'no gaps' and exits 0."""
    args = argparse.Namespace()
    rc = cmd_gaps(args, ctx)
    assert rc == 0
    assert "no gaps" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# All claims valid → no gaps
# ---------------------------------------------------------------------------

def test_gaps_all_valid_no_gaps(ctx: Context, capsys) -> None:
    """A rule with a valid claim and valid domain ref reports no gaps."""
    _write_depgraph_node(ctx, "acme-api::models/foo.py::Foo", {
        "id": "acme-api::models/foo.py::Foo",
        "structural_hash": "hash_abc",
    })
    _write_domain_node(ctx, "resource::test::thing", {
        "id": "resource::test::thing", "kind": "domain", "subkind": "resource",
        "title": "Thing", "summary": "", "definition_status": "stub",
        "structural_hash": "d001",
    })
    _write_rule_node(ctx, "rule::test::ok_rule", {
        "id": "rule::test::ok_rule", "kind": "rule", "title": "OK",
        "statement": "OK.", "references_domain": ["resource::test::thing"],
        "claims_code": [{"depgraph_id": "acme-api::models/foo.py::Foo",
                         "role": "model", "remote_hash": "hash_abc"}],
        "definition_status": "stub", "structural_hash": "r001",
    })
    args = argparse.Namespace()
    rc = cmd_gaps(args, ctx)
    assert rc == 0
    assert "no gaps" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Orphan claim (depgraph_id not in depgraph corpus)
# ---------------------------------------------------------------------------

def test_gaps_orphan_claim(ctx: Context, capsys) -> None:
    """A claim referencing a non-existent depgraph node is an orphan claim."""
    _write_rule_node(ctx, "rule::test::orphan_claim_rule", {
        "id": "rule::test::orphan_claim_rule", "kind": "rule", "title": "Orphan",
        "statement": "Orphan.", "references_domain": [],
        "claims_code": [{"depgraph_id": "acme-api::missing/gone.py::Gone",
                         "role": "model"}],
        "definition_status": "stub", "structural_hash": "r002",
    })
    args = argparse.Namespace()
    rc = cmd_gaps(args, ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "ORPHAN CLAIMS" in out
    assert "acme-api::missing/gone.py::Gone" in out


# ---------------------------------------------------------------------------
# Orphan domain ref
# ---------------------------------------------------------------------------

def test_gaps_orphan_domain_ref(ctx: Context, capsys) -> None:
    """A rule referencing a non-existent domain node is an orphan domain ref."""
    _write_rule_node(ctx, "rule::test::orphan_domain_rule", {
        "id": "rule::test::orphan_domain_rule", "kind": "rule", "title": "OrphanDomain",
        "statement": "Orphan domain.", "references_domain": ["resource::test::nonexistent"],
        "claims_code": [],
        "definition_status": "stub", "structural_hash": "r003",
    })
    args = argparse.Namespace()
    rc = cmd_gaps(args, ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "ORPHAN DOMAIN REFS" in out
    assert "resource::test::nonexistent" in out


# ---------------------------------------------------------------------------
# Stale claim (remote_hash != structural_hash)
# ---------------------------------------------------------------------------

def test_gaps_stale_claim(ctx: Context, capsys) -> None:
    """A claim whose remote_hash differs from the current structural_hash is stale."""
    _write_depgraph_node(ctx, "acme-api::models/bar.py::Bar", {
        "id": "acme-api::models/bar.py::Bar",
        "structural_hash": "new_hash",
    })
    _write_rule_node(ctx, "rule::test::stale_rule", {
        "id": "rule::test::stale_rule", "kind": "rule", "title": "Stale",
        "statement": "Stale.", "references_domain": [],
        "claims_code": [{"depgraph_id": "acme-api::models/bar.py::Bar",
                         "role": "model", "remote_hash": "old_hash"}],
        "definition_status": "stub", "structural_hash": "r004",
    })
    args = argparse.Namespace()
    rc = cmd_gaps(args, ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "STALE CLAIMS" in out
    assert "acme-api::models/bar.py::Bar" in out
