"""Tests for logigraph.lib.cli.rules_for.cmd_rules_for."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from lib.cli.context import Context
from lib.cli.rules_for import cmd_rules_for


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _write_rule_node(ctx: Context, node_id: str, node: dict) -> Path:
    rules_dir = ctx.NODES / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    parts = node_id.split("::")
    filename = f"{parts[1]}__{parts[2]}.json"
    p = rules_dir / filename
    p.write_text(json.dumps(node) + "\n")
    return p


def _write_by_code_index(ctx: Context, index: dict) -> Path:
    idx_dir = ctx.NODES / "_index"
    idx_dir.mkdir(parents=True, exist_ok=True)
    p = idx_dir / "by_code.json"
    p.write_text(json.dumps(index) + "\n")
    return p


# ---------------------------------------------------------------------------
# Missing index
# ---------------------------------------------------------------------------

def test_rules_for_missing_index_exits_1(ctx: Context, capsys) -> None:
    """When by_code index is absent, exits 1 with stderr message."""
    args = argparse.Namespace(depgraph_id="concorda-api::models/foo.py::Foo")
    rc = cmd_rules_for(args, ctx)
    assert rc == 1
    err = capsys.readouterr().err
    assert "regen" in err


# ---------------------------------------------------------------------------
# No matching rules
# ---------------------------------------------------------------------------

def test_rules_for_no_match_prints_and_exits_0(ctx: Context, capsys) -> None:
    """A depgraph_id with no rules prints a message and exits 0."""
    _write_by_code_index(ctx, {"by_target": {}})
    args = argparse.Namespace(depgraph_id="concorda-api::models/foo.py::Foo")
    rc = cmd_rules_for(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "no rules claim" in out
    assert "concorda-api::models/foo.py::Foo" in out


# ---------------------------------------------------------------------------
# Matching rule — with statement
# ---------------------------------------------------------------------------

def test_rules_for_with_statement(ctx: Context, capsys) -> None:
    """A matched rule emits id, title, and statement."""
    node = {
        "schema_version": 2,
        "id": "rule::test::my_rule",
        "kind": "rule",
        "title": "My Test Rule",
        "statement": "Things must be tested.",
        "references_domain": [],
        "claims_code": [],
        "definition_status": "stub",
        "structural_hash": "abc123",
    }
    _write_rule_node(ctx, "rule::test::my_rule", node)
    _write_by_code_index(ctx, {
        "by_target": {
            "concorda-api::models/foo.py::Foo": ["rule::test::my_rule"],
        }
    })
    args = argparse.Namespace(depgraph_id="concorda-api::models/foo.py::Foo")
    rc = cmd_rules_for(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rule::test::my_rule" in out
    assert "My Test Rule" in out
    assert "Things must be tested." in out
    assert "→" in out


# ---------------------------------------------------------------------------
# Matching rule — no statement
# ---------------------------------------------------------------------------

def test_rules_for_no_statement_omits_arrow(ctx: Context, capsys) -> None:
    """A matched rule with no statement omits the → line."""
    node = {
        "schema_version": 2,
        "id": "rule::test::no_stmt",
        "kind": "rule",
        "title": "No Statement Rule",
        "statement": "",
        "references_domain": [],
        "claims_code": [],
        "definition_status": "stub",
        "structural_hash": "xyz",
    }
    _write_rule_node(ctx, "rule::test::no_stmt", node)
    _write_by_code_index(ctx, {
        "by_target": {
            "concorda-api::models/bar.py::Bar": ["rule::test::no_stmt"],
        }
    })
    args = argparse.Namespace(depgraph_id="concorda-api::models/bar.py::Bar")
    rc = cmd_rules_for(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rule::test::no_stmt" in out
    assert "→" not in out


# ---------------------------------------------------------------------------
# Index points to rule id not in nodes (graceful fallback)
# ---------------------------------------------------------------------------

def test_rules_for_missing_node_falls_back_to_id(ctx: Context, capsys) -> None:
    """When the index points to a rule not in nodes, falls back to using the id as title."""
    _write_by_code_index(ctx, {
        "by_target": {
            "concorda-api::models/baz.py::Baz": ["rule::test::ghost"],
        }
    })
    args = argparse.Namespace(depgraph_id="concorda-api::models/baz.py::Baz")
    rc = cmd_rules_for(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rule::test::ghost" in out
