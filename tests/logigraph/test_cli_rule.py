"""Tests for logigraph.lib.cli.rule — rule lifecycle handlers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from lib.cli.context import Context
from lib.cli.rule import (
    cmd_rule_rank,
    cmd_rule_draft,
    cmd_rule_finalize,
    cmd_rule_bump,
    cmd_rule_stub,
)


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
        "references_domain": ["resource::project::TODO"],
        "claims_code": [],
        "fan_out": 0,
        "confidence": "medium",
        "source": "",
        "definition_status": "stub",
        "structural_hash": "deadbeef",
        "dossier": f"dossiers/rules/{parts[1]}__{parts[2]}.md",
    }
    node.update(overrides)
    return node


# ===========================================================================
# cmd_rule_rank
# ===========================================================================

class TestCmdRuleRank:
    def test_no_rules_dir_exits_0(self, ctx: Context, capsys) -> None:
        """When the rules dir is absent, exits 0 with a message."""
        args = argparse.Namespace(status=None)
        rc = cmd_rule_rank(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "no rules directory" in out

    def test_empty_rules_dir_prints_header(self, ctx: Context, capsys) -> None:
        """An empty rules dir prints the header and no rows."""
        (ctx.NODES / "rules").mkdir(parents=True, exist_ok=True)
        args = argparse.Namespace(status=None)
        rc = cmd_rule_rank(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "status" in out  # header line

    def test_ranks_stub_before_human_reviewed(self, ctx: Context, capsys) -> None:
        """Stub rules sort before human_reviewed rules."""
        _write_rule_node(ctx, "rule::test::reviewed", _minimal_rule_node(
            "rule::test::reviewed", definition_status="human_reviewed",
        ))
        _write_rule_node(ctx, "rule::test::stub_rule", _minimal_rule_node(
            "rule::test::stub_rule", definition_status="stub",
        ))
        args = argparse.Namespace(status=None)
        rc = cmd_rule_rank(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        stub_pos = out.index("stub_rule")
        reviewed_pos = out.index("reviewed")
        assert stub_pos < reviewed_pos

    def test_status_filter(self, ctx: Context, capsys) -> None:
        """--status filters to only matching rows."""
        _write_rule_node(ctx, "rule::test::s1", _minimal_rule_node(
            "rule::test::s1", definition_status="stub",
        ))
        _write_rule_node(ctx, "rule::test::d1", _minimal_rule_node(
            "rule::test::d1", definition_status="llm_drafted",
        ))
        args = argparse.Namespace(status="stub")
        rc = cmd_rule_rank(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "s1" in out
        assert "d1" not in out


# ===========================================================================
# cmd_rule_stub
# ===========================================================================

class TestCmdRuleStub:
    def test_creates_node_file(self, ctx: Context, capsys) -> None:
        """Creates a JSON node file at the expected path."""
        args = argparse.Namespace(
            id="rule::test::new_rule",
            title="New Rule",
            statement="A new rule statement.",
            domain_ref=["resource::project::TODO"],
            claim=None,
            confidence="medium",
            source="",
            force=False,
        )
        rc = cmd_rule_stub(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "rules" / "test__new_rule.json"
        assert node_path.exists()
        node = json.loads(node_path.read_text())
        assert node["id"] == "rule::test::new_rule"
        assert node["definition_status"] == "stub"

    def test_refuses_non_rule_prefix(self, ctx: Context, capsys) -> None:
        """Exits 1 when id doesn't start with rule::."""
        args = argparse.Namespace(
            id="resource::test::thing",
            title=None, statement=None, domain_ref=None,
            claim=None, confidence="medium", source="", force=False,
        )
        rc = cmd_rule_stub(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "rule::" in err

    def test_refuses_overwrite_without_force(self, ctx: Context, capsys) -> None:
        """Exits 1 when node already exists and --force not set."""
        args = argparse.Namespace(
            id="rule::test::existing",
            title=None, statement=None, domain_ref=None,
            claim=None, confidence="medium", source="", force=False,
        )
        # Create first time
        cmd_rule_stub(args, ctx)
        # Try again without force
        rc = cmd_rule_stub(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "already exists" in err or "force" in err

    def test_force_flag_overwrites(self, ctx: Context, capsys) -> None:
        """--force allows overwriting an existing node."""
        args = argparse.Namespace(
            id="rule::test::overwrite_me",
            title="Title A", statement="Stmt A.", domain_ref=None,
            claim=None, confidence="medium", source="", force=False,
        )
        cmd_rule_stub(args, ctx)
        args.title = "Title B"
        args.force = True
        rc = cmd_rule_stub(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "rules" / "test__overwrite_me.json"
        node = json.loads(node_path.read_text())
        assert node["title"] == "Title B"

    def test_claim_bad_format_exits_1(self, ctx: Context, capsys) -> None:
        """--claim without ':' separator exits 1."""
        args = argparse.Namespace(
            id="rule::test::claim_bad",
            title=None, statement=None, domain_ref=None,
            claim=["nodepgraph_id"],
            confidence="medium", source="", force=False,
        )
        rc = cmd_rule_stub(args, ctx)
        assert rc == 1


# ===========================================================================
# cmd_rule_draft
# ===========================================================================

class TestCmdRuleDraft:
    def test_missing_node_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when no rule node exists."""
        args = argparse.Namespace(id="rule::test::ghost")
        rc = cmd_rule_draft(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "rule-stub" in err

    def test_emits_context_bundle(self, ctx: Context, capsys) -> None:
        """Prints a context bundle header and target rule section."""
        _write_rule_node(ctx, "rule::test::my_draft", _minimal_rule_node(
            "rule::test::my_draft",
        ))
        args = argparse.Namespace(id="rule::test::my_draft")
        rc = cmd_rule_draft(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "rule-draft context bundle" in out
        assert "rule::test::my_draft" in out
        assert "Target rule" in out


# ===========================================================================
# cmd_rule_finalize
# ===========================================================================

class TestCmdRuleFinalize:
    def test_missing_node_exits_1(self, ctx: Context, capsys, tmp_path) -> None:
        """Exits 1 when no rule node exists."""
        body_file = tmp_path / "body.md"
        body_file.write_text("## The rule\nContent.\n")
        args = argparse.Namespace(id="rule::test::ghost", body_file=str(body_file))
        rc = cmd_rule_finalize(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "rule-stub" in err

    def test_missing_body_file_exits_1(self, ctx: Context, capsys, tmp_path) -> None:
        """Exits 1 when the body file doesn't exist."""
        _write_rule_node(ctx, "rule::test::no_body", _minimal_rule_node("rule::test::no_body"))
        args = argparse.Namespace(
            id="rule::test::no_body",
            body_file=str(tmp_path / "missing.md"),
        )
        rc = cmd_rule_finalize(args, ctx)
        assert rc == 1

    def test_writes_dossier_with_frontmatter(self, ctx: Context, capsys, tmp_path) -> None:
        """Writes dossier to canonical path with YAML frontmatter."""
        rule_id = "rule::test::finalize_me"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id))
        body_file = tmp_path / "body.md"
        body_file.write_text("## The rule\nRule content here.\n")
        args = argparse.Namespace(id=rule_id, body_file=str(body_file))
        (ctx.LOGIGRAPH / "dossiers" / "rules").mkdir(parents=True, exist_ok=True)
        rc = cmd_rule_finalize(args, ctx)
        assert rc == 0
        dossier_path = ctx.LOGIGRAPH / "dossiers" / "rules" / "test__finalize_me.md"
        assert dossier_path.exists()
        content = dossier_path.read_text()
        assert "node_id: rule::test::finalize_me" in content
        assert "definition_status: llm_drafted" in content
        assert "## The rule" in content

    def test_bumps_node_to_llm_drafted(self, ctx: Context, capsys, tmp_path) -> None:
        """Updates the node JSON definition_status to llm_drafted."""
        rule_id = "rule::test::bump_node"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id))
        body_file = tmp_path / "body.md"
        body_file.write_text("## The rule\nContent.\n")
        args = argparse.Namespace(id=rule_id, body_file=str(body_file))
        (ctx.LOGIGRAPH / "dossiers" / "rules").mkdir(parents=True, exist_ok=True)
        cmd_rule_finalize(args, ctx)
        node_path = ctx.NODES / "rules" / "test__bump_node.json"
        node = json.loads(node_path.read_text())
        assert node["definition_status"] == "llm_drafted"


# ===========================================================================
# cmd_rule_bump
# ===========================================================================

class TestCmdRuleBump:
    def test_missing_node_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when no rule node exists."""
        args = argparse.Namespace(
            id="rule::test::ghost",
            status="human_reviewed",
            actor=None,
        )
        rc = cmd_rule_bump(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "no rule node" in err

    def test_bumps_node_status(self, ctx: Context, capsys, tmp_path, monkeypatch) -> None:
        """Updates definition_status in the JSON node file."""
        import subprocess
        # Stub out git to avoid actual git ops
        monkeypatch.setattr(
            "lib.cli._shared.subprocess.run",
            lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        )
        rule_id = "rule::test::to_bump"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id, definition_status="llm_drafted"))
        args = argparse.Namespace(id=rule_id, status="human_reviewed", actor="tester")
        rc = cmd_rule_bump(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "rules" / "test__to_bump.json"
        node = json.loads(node_path.read_text())
        assert node["definition_status"] == "human_reviewed"

    def test_bumps_dossier_frontmatter(self, ctx: Context, capsys, tmp_path, monkeypatch) -> None:
        """When a dossier exists, its frontmatter definition_status is updated."""
        monkeypatch.setattr(
            "lib.cli._shared.subprocess.run",
            lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        )
        rule_id = "rule::test::dossier_bump"
        _write_rule_node(ctx, rule_id, _minimal_rule_node(rule_id, definition_status="llm_drafted"))
        dossier_dir = ctx.LOGIGRAPH / "dossiers" / "rules"
        dossier_dir.mkdir(parents=True, exist_ok=True)
        dossier_path = dossier_dir / "test__dossier_bump.md"
        dossier_path.write_text(
            "---\nnode_id: rule::test::dossier_bump\n"
            "definition_status: llm_drafted\n"
            "last_reviewed: 2026-01-01\n"
            "last_reviewed_against_hash: oldhash\n"
            "---\n\n# Dossier bump\n\nContent.\n"
        )
        args = argparse.Namespace(id=rule_id, status="human_reviewed", actor="tester")
        rc = cmd_rule_bump(args, ctx)
        assert rc == 0
        content = dossier_path.read_text()
        assert "definition_status: human_reviewed" in content
