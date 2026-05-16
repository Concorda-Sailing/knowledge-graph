"""Tests for logigraph.lib.cli.fan_out.cmd_fan_out."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.fan_out import cmd_fan_out


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


# ---------------------------------------------------------------------------
# No rules — header only, exits 0
# ---------------------------------------------------------------------------

def test_fan_out_no_rules_prints_header(ctx: Context, capsys) -> None:
    """With no rule nodes, only the header is printed."""
    args = argparse.Namespace(threshold=1)
    rc = cmd_fan_out(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "fan-out" in out
    assert "rule" in out


# ---------------------------------------------------------------------------
# Rule below threshold is omitted
# ---------------------------------------------------------------------------

def test_fan_out_threshold_filters(ctx: Context, capsys) -> None:
    """Rules whose fan-out is below threshold are omitted."""
    node = {
        "schema_version": 2,
        "id": "rule::test::low_fan",
        "kind": "rule",
        "title": "Low Fan",
        "statement": "Low.",
        "references_domain": [],
        "claims_code": [{"depgraph_id": "a::b::c", "role": "model"}],
        "definition_status": "stub",
        "structural_hash": "abc",
    }
    _write_rule_node(ctx, "rule::test::low_fan", node)
    args = argparse.Namespace(threshold=5)
    rc = cmd_fan_out(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rule::test::low_fan" not in out


# ---------------------------------------------------------------------------
# Rule at or above threshold is included
# ---------------------------------------------------------------------------

def test_fan_out_above_threshold_included(ctx: Context, capsys) -> None:
    """Rules at or above threshold appear in output."""
    claims = [{"depgraph_id": f"a::b::c{i}", "role": "model"} for i in range(3)]
    node = {
        "schema_version": 2,
        "id": "rule::test::high_fan",
        "kind": "rule",
        "title": "High Fan",
        "statement": "High.",
        "references_domain": [],
        "claims_code": claims,
        "definition_status": "stub",
        "structural_hash": "def",
    }
    _write_rule_node(ctx, "rule::test::high_fan", node)
    args = argparse.Namespace(threshold=3)
    rc = cmd_fan_out(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rule::test::high_fan" in out
    # fan-out value should be 3
    assert "3" in out


# ---------------------------------------------------------------------------
# fan_out field takes precedence over claims_code length
# ---------------------------------------------------------------------------

def test_fan_out_uses_fan_out_field_when_present(ctx: Context, capsys) -> None:
    """The fan_out field, when present, overrides len(claims_code)."""
    node = {
        "schema_version": 2,
        "id": "rule::test::explicit_fan",
        "kind": "rule",
        "title": "Explicit Fan",
        "statement": "Explicit.",
        "references_domain": [],
        "claims_code": [],  # empty — fan_out field should override
        "fan_out": 7,
        "definition_status": "stub",
        "structural_hash": "ghi",
    }
    _write_rule_node(ctx, "rule::test::explicit_fan", node)
    args = argparse.Namespace(threshold=1)
    rc = cmd_fan_out(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rule::test::explicit_fan" in out
    assert "7" in out


# ---------------------------------------------------------------------------
# Non-rule nodes are ignored
# ---------------------------------------------------------------------------

def test_fan_out_ignores_non_rule_nodes(ctx: Context, capsys) -> None:
    """Domain nodes are not included in fan-out output."""
    domain_dir = ctx.NODES / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    domain_node = {
        "schema_version": 1,
        "id": "resource::test::thing",
        "kind": "domain",
        "subkind": "resource",
        "title": "Thing",
        "summary": "A thing.",
        "definition_status": "stub",
        "structural_hash": "dom001",
    }
    (domain_dir / "resource__test__thing.json").write_text(json.dumps(domain_node) + "\n")
    args = argparse.Namespace(threshold=0)
    rc = cmd_fan_out(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "resource::test::thing" not in out
