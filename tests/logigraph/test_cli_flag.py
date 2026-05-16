"""Tests for logigraph.lib.cli.flag — flag / unflag handlers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from lib.cli.context import Context
from lib.cli.flag import cmd_flag, cmd_unflag


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_rule_node(ctx: Context, node_id: str, node: dict) -> Path:
    rules_dir = ctx.NODES / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    parts = node_id.split("::")
    filename = f"{parts[1]}__{parts[2]}.json"
    p = rules_dir / filename
    p.write_text(json.dumps(node) + "\n")
    return p


def _minimal_rule_node(rule_id: str, **overrides) -> dict:
    parts = rule_id.split("::")
    node: dict = {
        "schema_version": 2,
        "id": rule_id,
        "kind": "rule",
        "title": parts[2].replace("_", " ").capitalize(),
        "statement": "Test statement.",
        "definition_status": "stub",
        "structural_hash": "deadbeef",
    }
    node.update(overrides)
    return node


def _write_domain_node(ctx: Context, node_id: str, node: dict) -> Path:
    domain_dir = ctx.NODES / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    parts = node_id.split("::")
    filename = f"{parts[0]}__{parts[1]}__{parts[2]}.json"
    p = domain_dir / filename
    p.write_text(json.dumps(node) + "\n")
    return p


def _minimal_domain_node(domain_id: str, **overrides) -> dict:
    parts = domain_id.split("::")
    node: dict = {
        "schema_version": 1,
        "id": domain_id,
        "kind": parts[0],
        "title": parts[2].replace("_", " ").capitalize(),
        "definition_status": "stub",
    }
    node.update(overrides)
    return node


def _stub_git(monkeypatch) -> None:
    monkeypatch.setattr(
        "lib.cli._shared.subprocess.run",
        lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )


# ===========================================================================
# cmd_flag
# ===========================================================================

class TestCmdFlag:
    def test_missing_node_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when no node exists for the given id."""
        args = argparse.Namespace(id="rule::test::ghost", reason=None, actor=None)
        rc = cmd_flag(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "no logigraph node" in err

    def test_flags_rule_node(self, ctx: Context, capsys, monkeypatch) -> None:
        """Sets flagged=True, flagged_by, flagged_at on a rule node."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::to_flag"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id))
        args = argparse.Namespace(id=rule_id, reason=None, actor="tester")
        rc = cmd_flag(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "rules" / "test__to_flag.json"
        node = json.loads(node_path.read_text())
        assert node["flagged"] is True
        assert node["flagged_by"] == "tester"
        assert "flagged_at" in node

    def test_flags_domain_node(self, ctx: Context, capsys, monkeypatch) -> None:
        """Sets flagged fields on a domain node."""
        _stub_git(monkeypatch)
        domain_id = "resource::test::to_flag"
        _write_domain_node(ctx, domain_id, _minimal_domain_node(domain_id))
        args = argparse.Namespace(id=domain_id, reason="known gap", actor="tester")
        rc = cmd_flag(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "domain" / "resource__test__to_flag.json"
        node = json.loads(node_path.read_text())
        assert node["flagged"] is True
        assert node["flagged_reason"] == "known gap"

    def test_reason_stored_in_node(self, ctx: Context, capsys, monkeypatch) -> None:
        """flagged_reason is written when --reason is provided."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::reason_flag"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id))
        args = argparse.Namespace(id=rule_id, reason="design defect", actor="tester")
        rc = cmd_flag(args, ctx)
        assert rc == 0
        node = json.loads((ctx.NODES / "rules" / "test__reason_flag.json").read_text())
        assert node.get("flagged_reason") == "design defect"

    def test_no_reason_clears_flagged_reason(self, ctx: Context, capsys, monkeypatch) -> None:
        """When no --reason is given, flagged_reason is absent from the node."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::no_reason_flag"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id, flagged_reason="old reason"))
        args = argparse.Namespace(id=rule_id, reason=None, actor="tester")
        rc = cmd_flag(args, ctx)
        assert rc == 0
        node = json.loads((ctx.NODES / "rules" / "test__no_reason_flag.json").read_text())
        assert "flagged_reason" not in node

    def test_idempotent_same_actor_and_reason(self, ctx: Context, capsys, monkeypatch) -> None:
        """Exits 0 without committing when already flagged with same actor+reason."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::idempotent_flag"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(
            rule_id, flagged=True, flagged_by="tester", flagged_reason="same reason",
        ))
        args = argparse.Namespace(id=rule_id, reason="same reason", actor="tester")
        rc = cmd_flag(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "already flagged" in out

    def test_prints_flagged_message(self, ctx: Context, capsys, monkeypatch) -> None:
        """Prints 'flagged <id> by <actor>' on success."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::print_flag"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id))
        args = argparse.Namespace(id=rule_id, reason=None, actor="tester")
        rc = cmd_flag(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "flagged" in out
        assert rule_id in out


# ===========================================================================
# cmd_unflag
# ===========================================================================

class TestCmdUnflag:
    def test_missing_node_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when no node exists for the given id."""
        args = argparse.Namespace(id="rule::test::ghost", actor=None)
        rc = cmd_unflag(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "no logigraph node" in err

    def test_not_flagged_is_idempotent(self, ctx: Context, capsys, monkeypatch) -> None:
        """Exits 0 without committing when node is not currently flagged."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::not_flagged"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id))
        args = argparse.Namespace(id=rule_id, actor=None)
        rc = cmd_unflag(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "not flagged" in out

    def test_clears_flag_fields(self, ctx: Context, capsys, monkeypatch) -> None:
        """Removes flagged, flagged_by, flagged_at, flagged_reason from node JSON."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::to_unflag"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(
            rule_id,
            flagged=True,
            flagged_by="tester",
            flagged_at="2026-05-15",
            flagged_reason="some reason",
        ))
        args = argparse.Namespace(id=rule_id, actor="tester")
        rc = cmd_unflag(args, ctx)
        assert rc == 0
        node = json.loads((ctx.NODES / "rules" / "test__to_unflag.json").read_text())
        for key in ("flagged", "flagged_by", "flagged_at", "flagged_reason"):
            assert key not in node

    def test_prints_unflagged_message(self, ctx: Context, capsys, monkeypatch) -> None:
        """Prints 'unflagged <id> by <actor>' on success."""
        _stub_git(monkeypatch)
        rule_id = "rule::test::print_unflag"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(
            rule_id, flagged=True, flagged_by="tester", flagged_at="2026-05-15",
        ))
        args = argparse.Namespace(id=rule_id, actor="tester")
        rc = cmd_unflag(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "unflagged" in out
        assert rule_id in out
