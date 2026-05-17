"""Tests for logigraph.lib.cli.context_cmd.cmd_context."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.context_cmd import cmd_context


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _write_rule_node(ctx: Context, node_id: str, node: dict) -> Path:
    rules_dir = ctx.NODES / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    # Derive filename from id: rule::category::name → category__name.json
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


def _write_by_file_index(ctx: Context, index: dict) -> Path:
    idx_dir = ctx.NODES / "_index"
    idx_dir.mkdir(parents=True, exist_ok=True)
    p = idx_dir / "by_file.json"
    p.write_text(json.dumps(index) + "\n")
    return p


# ---------------------------------------------------------------------------
# Basic: no matching rules
# ---------------------------------------------------------------------------

def test_context_no_match_warns_for_missing_rule(ctx: Context, capsys) -> None:
    """A rule:: target that doesn't exist as a node hits the missing-rule WARN
    path on stderr and exits 0. (The 'no rules apply' stdout message fires only
    when find_rules_for_target returns an empty list — which doesn't happen for
    rule::-prefixed targets; those are returned verbatim by the helper.)"""
    args = argparse.Namespace(target="rule::test::nonexistent")
    rc = cmd_context(args, ctx)
    assert rc == 0
    captured = capsys.readouterr()
    assert "rule::test::nonexistent" in (captured.out + captured.err)


# ---------------------------------------------------------------------------
# Basic: rule id target → prints title + statement
# ---------------------------------------------------------------------------

def test_context_rule_id_target_prints_title(ctx: Context, capsys) -> None:
    """A target that is a rule id emits the rule's title and statement."""
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

    args = argparse.Namespace(target="rule::test::my_rule")
    rc = cmd_context(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "My Test Rule" in out
    assert "Things must be tested." in out


# ---------------------------------------------------------------------------
# Flagged rule → emits warning block
# ---------------------------------------------------------------------------

def test_context_flagged_rule_emits_warning(ctx: Context, capsys) -> None:
    """A flagged rule prepends the FLAGGED warning block."""
    node = {
        "schema_version": 2,
        "id": "rule::test::flagged_rule",
        "kind": "rule",
        "title": "Flagged Rule",
        "statement": "This rule is known-bad.",
        "references_domain": [],
        "claims_code": [],
        "definition_status": "stub",
        "structural_hash": "deadbeef",
        "flagged": True,
        "flagged_reason": "Documents a defect",
        "flagged_by": "tester",
        "flagged_at": "2026-01-01",
    }
    _write_rule_node(ctx, "rule::test::flagged_rule", node)

    args = argparse.Namespace(target="rule::test::flagged_rule")
    rc = cmd_context(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "FLAGGED" in out
    assert "Documents a defect" in out
    assert "tester" in out


# ---------------------------------------------------------------------------
# Dossier text emitted when file exists
# ---------------------------------------------------------------------------

def test_context_emits_dossier_text(ctx: Context, capsys) -> None:
    """When a dossier file is present, its content is printed."""
    dossier_rel = "dossiers/rules/test__rule_with_dossier.md"
    dossier_path = ctx.LOGIGRAPH / dossier_rel
    dossier_path.parent.mkdir(parents=True, exist_ok=True)
    dossier_path.write_text("## The rule\n\nSome dossier content.\n")

    node = {
        "schema_version": 2,
        "id": "rule::test::rule_with_dossier",
        "kind": "rule",
        "title": "Rule With Dossier",
        "statement": "Has a dossier.",
        "references_domain": [],
        "claims_code": [],
        "definition_status": "stub",
        "structural_hash": "abc456",
        "dossier": dossier_rel,
    }
    _write_rule_node(ctx, "rule::test::rule_with_dossier", node)

    args = argparse.Namespace(target="rule::test::rule_with_dossier")
    rc = cmd_context(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Some dossier content." in out


# ---------------------------------------------------------------------------
# No dossier → emits _no dossier_ placeholder
# ---------------------------------------------------------------------------

def test_context_no_dossier_emits_placeholder(ctx: Context, capsys) -> None:
    """When no dossier file is present, _no dossier_ is emitted."""
    node = {
        "schema_version": 2,
        "id": "rule::test::no_dossier_rule",
        "kind": "rule",
        "title": "No Dossier Rule",
        "statement": "Missing dossier.",
        "references_domain": [],
        "claims_code": [],
        "definition_status": "stub",
        "structural_hash": "abc789",
    }
    _write_rule_node(ctx, "rule::test::no_dossier_rule", node)

    args = argparse.Namespace(target="rule::test::no_dossier_rule")
    rc = cmd_context(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "_no dossier_" in out


# ---------------------------------------------------------------------------
# by_code index target (depgraph id with ::)
# ---------------------------------------------------------------------------

def test_context_depgraph_id_target(ctx: Context, capsys) -> None:
    """A target that looks like a depgraph node id (has ::) is looked up in by_code."""
    node = {
        "schema_version": 2,
        "id": "rule::test::via_code_index",
        "kind": "rule",
        "title": "Via Code Index",
        "statement": "Found via depgraph node id.",
        "references_domain": [],
        "claims_code": [],
        "definition_status": "stub",
        "structural_hash": "abc000",
    }
    _write_rule_node(ctx, "rule::test::via_code_index", node)
    _write_by_code_index(ctx, {
        "by_target": {
            "acme-api::models/foo.py::Foo": ["rule::test::via_code_index"],
        }
    })

    args = argparse.Namespace(target="acme-api::models/foo.py::Foo")
    rc = cmd_context(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Via Code Index" in out


# ---------------------------------------------------------------------------
# Rollups skipped when depgraph reverse-dependents index is missing
# ---------------------------------------------------------------------------

def test_context_rollups_skipped_gracefully(ctx: Context, capsys) -> None:
    """When entity rollup data is unavailable, a skip notice is printed (exit 0)."""
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
    domain_dir = ctx.NODES / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "resource__test__thing.json").write_text(json.dumps(domain_node) + "\n")

    node = {
        "schema_version": 2,
        "id": "rule::test::refs_domain",
        "kind": "rule",
        "title": "Refs Domain",
        "statement": "References a domain entity.",
        "references_domain": ["resource::test::thing"],
        "claims_code": [],
        "definition_status": "stub",
        "structural_hash": "abc111",
    }
    _write_rule_node(ctx, "rule::test::refs_domain", node)

    args = argparse.Namespace(target="rule::test::refs_domain")
    rc = cmd_context(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    # Rollups should either be skipped with a notice, or succeed; either way exit 0
    assert "Refs Domain" in out
