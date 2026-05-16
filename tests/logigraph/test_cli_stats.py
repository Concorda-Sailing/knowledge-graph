"""Tests for logigraph.lib.cli.stats.cmd_stats."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.stats import cmd_stats


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


def _write_rule(nodes_dir: Path, rule_id: str, status: str = "stub") -> None:
    parts = rule_id.split("::", 2)
    d = nodes_dir / "rules"
    d.mkdir(parents=True, exist_ok=True)
    node = {
        "schema_version": 2,
        "id": rule_id,
        "kind": "rule",
        "title": rule_id,
        "statement": "test",
        "references_domain": ["resource::test::thing"],
        "claims_code": [{"depgraph_id": "repo::f.py::F", "role": "enforces"}],
        "definition_status": status,
        "structural_hash": "abc",
    }
    (d / f"{parts[1]}__{parts[2]}.json").write_text(json.dumps(node) + "\n")


def test_stats_empty_corpus(ctx: Context, capsys: pytest.CaptureFixture) -> None:
    """Empty corpus: exits 0 and prints header."""
    args = argparse.Namespace(telemetry=False)
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Logigraph stats" in out


def test_stats_counts_rules(ctx: Context, capsys: pytest.CaptureFixture) -> None:
    """Adds two rules and verifies count appears in output."""
    _write_rule(ctx.NODES, "rule::auth::one", "stub")
    _write_rule(ctx.NODES, "rule::auth::two", "human_reviewed")
    args = argparse.Namespace(telemetry=False)
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rules:" in out
    assert "2" in out


def test_stats_no_telemetry_section_without_flag(
    ctx: Context, capsys: pytest.CaptureFixture
) -> None:
    """Without --telemetry, the Telemetry section is absent."""
    args = argparse.Namespace(telemetry=False)
    cmd_stats(args, ctx)
    out = capsys.readouterr().out
    assert "Telemetry" not in out
