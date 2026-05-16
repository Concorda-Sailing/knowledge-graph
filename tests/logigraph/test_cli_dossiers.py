"""Tests for logigraph.lib.cli.dossiers.cmd_dossiers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.dossiers import cmd_dossiers


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


# ---------------------------------------------------------------------------
# Empty corpus — basic stats header emitted, exits 0
# ---------------------------------------------------------------------------

def test_dossiers_empty_corpus_exits_0(ctx: Context, capsys) -> None:
    """dossiers with empty corpus emits stats header and exits 0."""
    args = argparse.Namespace()
    rc = cmd_dossiers(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Logigraph stats" in out


# ---------------------------------------------------------------------------
# telemetry is forced False (alias behaviour)
# ---------------------------------------------------------------------------

def test_dossiers_forces_telemetry_false(ctx: Context, capsys) -> None:
    """dossiers always sets telemetry=False regardless of what args had before."""
    args = argparse.Namespace(telemetry=True)  # would be overridden
    rc = cmd_dossiers(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    # Telemetry section must NOT appear (telemetry=False suppresses it)
    assert "Telemetry" not in out


# ---------------------------------------------------------------------------
# --status flag accepted without error (subparser registers it)
# ---------------------------------------------------------------------------

def test_dossiers_status_flag_accepted(ctx: Context, capsys) -> None:
    """--status flag is accepted; dossiers still delegates to stats cleanly."""
    args = argparse.Namespace(status=True)
    rc = cmd_dossiers(args, ctx)
    assert rc == 0


# ---------------------------------------------------------------------------
# Rule nodes appear in stats output
# ---------------------------------------------------------------------------

def test_dossiers_counts_rules(ctx: Context, capsys) -> None:
    """Rule nodes are counted and reported via the delegated stats call."""
    rules_dir = ctx.NODES / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    node = {
        "id": "rule::test::one", "kind": "rule", "title": "One",
        "statement": "One.", "references_domain": [], "claims_code": [],
        "definition_status": "stub", "structural_hash": "r001",
    }
    (rules_dir / "test__one.json").write_text(json.dumps(node) + "\n")

    args = argparse.Namespace()
    rc = cmd_dossiers(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "rules:" in out
    assert "1" in out
