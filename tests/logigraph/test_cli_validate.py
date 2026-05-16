"""Tests for logigraph.lib.cli.validate.cmd_validate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.validate import cmd_validate


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _write_node(nodes_dir: Path, subdir: str, filename: str, node: dict) -> Path:
    d = nodes_dir / subdir
    d.mkdir(parents=True, exist_ok=True)
    p = d / filename
    p.write_text(json.dumps(node) + "\n")
    return p


def test_validate_empty_corpus_returns_0(ctx: Context) -> None:
    """No nodes → validate exits 0."""
    args = argparse.Namespace()
    rc = cmd_validate(args, ctx)
    assert rc == 0


def test_validate_unknown_kind_returns_1(ctx: Context) -> None:
    """A node with an unknown kind is flagged as invalid (exit 1)."""
    _write_node(
        ctx.NODES,
        "rules",
        "test__unknown_kind.json",
        {"id": "rule::test::unknown_kind", "kind": "bogus_kind"},
    )
    args = argparse.Namespace()
    rc = cmd_validate(args, ctx)
    assert rc == 1


def test_validate_stub_rule_no_dossier_check(ctx: Context) -> None:
    """A rule node with definition_status=stub and a missing dossier is NOT
    flagged for missing sections — the stub exemption applies. Uses a fully
    schema-valid rule node so the schema check passes cleanly."""
    _write_node(
        ctx.NODES,
        "rules",
        "test__stub_rule.json",
        {
            "schema_version": 2,
            "id": "rule::test::stub_rule",
            "kind": "rule",
            "title": "Test stub rule",
            "statement": "This is a test stub rule.",
            "references_domain": ["resource::test::thing"],
            "claims_code": [{"depgraph_id": "concorda-api::models/foo.py::Foo", "role": "enforces"}],
            "definition_status": "stub",
            "structural_hash": "abc123",
            "dossier": "dossiers/rules/test__stub_rule.md",
        },
    )
    args = argparse.Namespace()
    rc = cmd_validate(args, ctx)
    # No dossier file exists, but stub status exempts it → exit 0
    assert rc == 0
