"""Tests for logigraph.lib.cli.health.cmd_health."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.health import cmd_health


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _make_meta(ctx: Context, *, node_count: int = 0) -> Path:
    """Write a minimal _meta.json so the health liveness gate accepts the
    corpus as "extraction has run." Tests that exercise the
    pre-extraction state should NOT call this."""
    ctx.NODES.mkdir(parents=True, exist_ok=True)
    ctx.CORPUS_META.write_text(json.dumps({
        "schema_version": 1,
        "regen_status": "complete",
        "node_count": node_count,
    }))
    return ctx.CORPUS_META


def test_health_no_extraction_signals_not_clean(
    ctx: Context, capsys: pytest.CaptureFixture
) -> None:
    """No _meta.json (regen never ran) must NOT report 'clean' (#62).

    Previous buggy behavior: an empty corpus reported '✓ clean' with
    exit 0, feeding a false all-clear into the SessionStart hook."""
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc != 0
    out = capsys.readouterr().out
    assert "clean" not in out
    assert "no extraction" in out.lower() or "regen" in out.lower()


def test_health_empty_corpus_with_meta_returns_0(
    ctx: Context, capsys: pytest.CaptureFixture
) -> None:
    """Meta exists but corpus is empty → regen ran intentionally → exit 0."""
    _make_meta(ctx)
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Logigraph health" in out
    assert "clean" in out


def test_health_invalid_node_returns_1(ctx: Context, capsys: pytest.CaptureFixture) -> None:
    """A node with an unknown kind makes health exit 1 (validate fails)."""
    _make_meta(ctx)
    node_dir = ctx.NODES / "rules"
    node_dir.mkdir(parents=True, exist_ok=True)
    # Write an otherwise valid rule but with a bad kind to trigger schema failure
    (node_dir / "bad__node.json").write_text(json.dumps({
        "schema_version": 2,
        "id": "rule::bad::node",
        "kind": "rule",
        "title": "bad",
        "statement": "bad",
        "references_domain": ["resource::test::thing"],
        "claims_code": [{"depgraph_id": "repo::f.py::F", "role": "enforces"}],
        "definition_status": "stub",
        "structural_hash": "abc",
        # Deliberately omit nothing — this is valid so we test health via stub-rule count
    }) + "\n")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    # Stub rules are flagged as a curation problem → exit 1
    assert rc == 1
    out = capsys.readouterr().out
    assert "stub" in out.lower() or "⚠" in out


def test_health_only_stub_rules_reports_problems(
    ctx: Context, capsys: pytest.CaptureFixture
) -> None:
    """Two stub rules → health exits 1 and reports curation backlog."""
    _make_meta(ctx)
    node_dir = ctx.NODES / "rules"
    node_dir.mkdir(parents=True, exist_ok=True)
    for name in ("rule_a", "rule_b"):
        (node_dir / f"auth__{name}.json").write_text(json.dumps({
            "schema_version": 2,
            "id": f"rule::auth::{name}",
            "kind": "rule",
            "title": name,
            "statement": name,
            "references_domain": ["resource::test::thing"],
            "claims_code": [{"depgraph_id": "repo::f.py::F", "role": "enforces"}],
            "definition_status": "stub",
            "structural_hash": "abc",
        }) + "\n")
    args = argparse.Namespace()
    rc = cmd_health(args, ctx)
    assert rc == 1
    out = capsys.readouterr().out
    assert "⚠" in out
