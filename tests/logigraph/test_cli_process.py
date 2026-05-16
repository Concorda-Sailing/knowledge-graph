"""Tests for logigraph.lib.cli.process — process lifecycle handlers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from lib.cli.context import Context
from lib.cli.process import (
    cmd_process_rank,
    cmd_process_draft,
    cmd_process_finalize,
    cmd_process_bump,
    cmd_process_stub,
)


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_process_node(ctx: Context, node_id: str, node: dict) -> Path:
    proc_dir = ctx.NODES / "processes"
    proc_dir.mkdir(parents=True, exist_ok=True)
    parts = node_id.split("::")
    filename = f"{parts[1]}__{parts[2]}.json"
    p = proc_dir / filename
    p.write_text(json.dumps(node) + "\n")
    return p


def _minimal_process_node(process_id: str, **overrides) -> dict:
    parts = process_id.split("::")
    node: dict = {
        "schema_version": 2,
        "id": process_id,
        "kind": "process",
        "title": parts[2].replace("_", " ").capitalize(),
        "summary": "Test summary.",
        "flow": {"action": "User clicks something"},
        "steps": [],
        "definition_status": "stub",
        "structural_hash": "deadbeef",
        "dossier": f"dossiers/processes/{parts[1]}__{parts[2]}.md",
    }
    node.update(overrides)
    return node


# ===========================================================================
# cmd_process_rank
# ===========================================================================

class TestCmdProcessRank:
    def test_no_candidates_prints_header(self, ctx: Context, capsys) -> None:
        """When there are no depgraph nodes, emits the candidates header and 0 candidates."""
        args = argparse.Namespace(limit=30, format="text")
        rc = cmd_process_rank(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Process candidates" in out
        assert "0 candidates" in out

    def test_json_format_returns_list(self, ctx: Context, capsys) -> None:
        """--format json prints a JSON array."""
        args = argparse.Namespace(limit=30, format="json")
        rc = cmd_process_rank(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert isinstance(parsed, list)

    def test_limit_applied(self, ctx: Context, capsys) -> None:
        """--limit 0 results in an empty candidate list."""
        args = argparse.Namespace(limit=0, format="json")
        rc = cmd_process_rank(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed == []


# ===========================================================================
# cmd_process_stub
# ===========================================================================

class TestCmdProcessStub:
    def test_creates_node_file(self, ctx: Context, capsys) -> None:
        """Creates a JSON node file at the expected path."""
        args = argparse.Namespace(
            id="process::test::new_flow",
            title="New Flow",
            summary="A new flow summary.",
            flow_action="User clicks register",
            flow_endpoint=None,
            flow_ui_surface=None,
            step=["s1:Step one:depgraph::fake::node"],
            enforces_rule=[],
            force=False,
        )
        rc = cmd_process_stub(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "processes" / "test__new_flow.json"
        assert node_path.exists()
        node = json.loads(node_path.read_text())
        assert node["id"] == "process::test::new_flow"
        assert node["definition_status"] == "stub"
        assert node["kind"] == "process"

    def test_refuses_non_process_prefix(self, ctx: Context, capsys) -> None:
        """Exits 1 when id doesn't start with process::."""
        args = argparse.Namespace(
            id="rule::test::thing",
            title=None, summary=None, flow_action=None,
            flow_endpoint=None, flow_ui_surface=None,
            step=["s1:Step one:depgraph::fake::node"],
            enforces_rule=[], force=False,
        )
        rc = cmd_process_stub(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "process::" in err

    def test_requires_at_least_one_step(self, ctx: Context, capsys) -> None:
        """Exits 1 when no --step is provided."""
        args = argparse.Namespace(
            id="process::test::nostep_flow",
            title=None, summary=None, flow_action=None,
            flow_endpoint=None, flow_ui_surface=None,
            step=[],
            enforces_rule=[], force=False,
        )
        rc = cmd_process_stub(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "--step" in err

    def test_refuses_overwrite_without_force(self, ctx: Context, capsys) -> None:
        """Exits 1 when node already exists and --force not set."""
        args = argparse.Namespace(
            id="process::test::existing_flow",
            title=None, summary=None, flow_action=None,
            flow_endpoint=None, flow_ui_surface=None,
            step=["s1:Step one:depgraph::fake::node"],
            enforces_rule=[], force=False,
        )
        cmd_process_stub(args, ctx)
        rc = cmd_process_stub(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "already exists" in err or "force" in err

    def test_force_flag_overwrites(self, ctx: Context, capsys) -> None:
        """--force allows overwriting an existing node."""
        args = argparse.Namespace(
            id="process::test::overwrite_flow",
            title="Title A", summary="Summary A.", flow_action=None,
            flow_endpoint=None, flow_ui_surface=None,
            step=["s1:Step one:depgraph::fake::node"],
            enforces_rule=[], force=False,
        )
        cmd_process_stub(args, ctx)
        args.title = "Title B"
        args.force = True
        rc = cmd_process_stub(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "processes" / "test__overwrite_flow.json"
        node = json.loads(node_path.read_text())
        assert node["title"] == "Title B"

    def test_step_bad_format_exits_1(self, ctx: Context, capsys) -> None:
        """--step without proper colons exits 1."""
        args = argparse.Namespace(
            id="process::test::badstep_flow",
            title=None, summary=None, flow_action=None,
            flow_endpoint=None, flow_ui_surface=None,
            step=["s1:only_two_parts"],
            enforces_rule=[], force=False,
        )
        rc = cmd_process_stub(args, ctx)
        assert rc == 1

    def test_step_with_where_clause(self, ctx: Context, capsys) -> None:
        """--step with 'step_id:title:dg_id|where' parses the where clause."""
        args = argparse.Namespace(
            id="process::test::where_flow",
            title=None, summary=None, flow_action=None,
            flow_endpoint=None, flow_ui_surface=None,
            step=["s1:Step one:fake::node::id|inside accept()"],
            enforces_rule=[], force=False,
        )
        rc = cmd_process_stub(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "processes" / "test__where_flow.json"
        node = json.loads(node_path.read_text())
        claim = node["steps"][0]["claims_code"][0]
        assert claim["where"] == "inside accept()"

    def test_stub_prints_next_hint(self, ctx: Context, capsys) -> None:
        """Printed output mentions process-draft as next step."""
        args = argparse.Namespace(
            id="process::test::hint_flow",
            title=None, summary=None, flow_action=None,
            flow_endpoint=None, flow_ui_surface=None,
            step=["s1:Step one:depgraph::fake::node"],
            enforces_rule=[], force=False,
        )
        cmd_process_stub(args, ctx)
        out = capsys.readouterr().out
        assert "process-draft" in out


# ===========================================================================
# cmd_process_draft
# ===========================================================================

class TestCmdProcessDraft:
    def test_missing_node_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when no process node exists."""
        args = argparse.Namespace(id="process::test::ghost_flow")
        rc = cmd_process_draft(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "process-stub" in err

    def test_emits_context_bundle(self, ctx: Context, capsys) -> None:
        """Prints a context bundle header and target process section."""
        _write_process_node(ctx, "process::test::my_flow", _minimal_process_node(
            "process::test::my_flow",
        ))
        args = argparse.Namespace(id="process::test::my_flow")
        rc = cmd_process_draft(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "process-draft context bundle" in out
        assert "process::test::my_flow" in out
        assert "Target process" in out

    def test_emits_authoring_instructions(self, ctx: Context, capsys) -> None:
        """Context bundle includes authoring instructions."""
        _write_process_node(ctx, "process::test::instr_flow", _minimal_process_node(
            "process::test::instr_flow",
        ))
        args = argparse.Namespace(id="process::test::instr_flow")
        cmd_process_draft(args, ctx)
        out = capsys.readouterr().out
        assert "Authoring instructions" in out
        assert "process-finalize" in out


# ===========================================================================
# cmd_process_finalize
# ===========================================================================

class TestCmdProcessFinalize:
    def test_missing_node_exits_1(self, ctx: Context, capsys, tmp_path) -> None:
        """Exits 1 when no process node exists."""
        body_file = tmp_path / "body.md"
        body_file.write_text("## Why this is a process\nContent.\n")
        args = argparse.Namespace(
            id="process::test::ghost_flow",
            body_file=str(body_file),
            authored_by=[],
        )
        rc = cmd_process_finalize(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "process-stub" in err

    def test_missing_body_file_exits_1(self, ctx: Context, capsys, tmp_path) -> None:
        """Exits 1 when the body file doesn't exist."""
        _write_process_node(ctx, "process::test::no_body_flow", _minimal_process_node(
            "process::test::no_body_flow",
        ))
        args = argparse.Namespace(
            id="process::test::no_body_flow",
            body_file=str(tmp_path / "missing.md"),
            authored_by=[],
        )
        rc = cmd_process_finalize(args, ctx)
        assert rc == 1

    def test_writes_dossier_with_frontmatter(self, ctx: Context, capsys, tmp_path) -> None:
        """Writes dossier to canonical path with YAML frontmatter."""
        process_id = "process::test::finalize_flow"
        _write_process_node(ctx, process_id, _minimal_process_node(process_id))
        body_file = tmp_path / "body.md"
        body_file.write_text("## Why this is a process\nProcess content here.\n")
        args = argparse.Namespace(
            id=process_id,
            body_file=str(body_file),
            authored_by=[],
        )
        (ctx.LOGIGRAPH / "dossiers" / "processes").mkdir(parents=True, exist_ok=True)
        rc = cmd_process_finalize(args, ctx)
        assert rc == 0
        dossier_path = ctx.LOGIGRAPH / "dossiers" / "processes" / "test__finalize_flow.md"
        assert dossier_path.exists()
        content = dossier_path.read_text()
        assert "node_id: process::test::finalize_flow" in content
        assert "node_kind: process" in content
        assert "definition_status: llm_drafted" in content
        assert "## Why this is a process" in content

    def test_bumps_node_to_llm_drafted(self, ctx: Context, capsys, tmp_path) -> None:
        """Updates the node JSON definition_status to llm_drafted."""
        process_id = "process::test::bump_flow"
        _write_process_node(ctx, process_id, _minimal_process_node(process_id))
        body_file = tmp_path / "body.md"
        body_file.write_text("## Why this is a process\nContent.\n")
        args = argparse.Namespace(
            id=process_id,
            body_file=str(body_file),
            authored_by=[],
        )
        (ctx.LOGIGRAPH / "dossiers" / "processes").mkdir(parents=True, exist_ok=True)
        cmd_process_finalize(args, ctx)
        node_path = ctx.NODES / "processes" / "test__bump_flow.json"
        node = json.loads(node_path.read_text())
        assert node["definition_status"] == "llm_drafted"

    def test_authored_by_included_in_frontmatter(self, ctx: Context, capsys, tmp_path) -> None:
        """--authored-by actors appear in the dossier frontmatter."""
        process_id = "process::test::authored_flow"
        _write_process_node(ctx, process_id, _minimal_process_node(process_id))
        body_file = tmp_path / "body.md"
        body_file.write_text("## Why this is a process\nContent.\n")
        args = argparse.Namespace(
            id=process_id,
            body_file=str(body_file),
            authored_by=["claude-opus-4"],
        )
        (ctx.LOGIGRAPH / "dossiers" / "processes").mkdir(parents=True, exist_ok=True)
        cmd_process_finalize(args, ctx)
        dossier_path = ctx.LOGIGRAPH / "dossiers" / "processes" / "test__authored_flow.md"
        content = dossier_path.read_text()
        assert "authored_by" in content
        assert "claude-opus-4" in content

    def test_prints_next_hint(self, ctx: Context, capsys, tmp_path) -> None:
        """Printed output mentions process-bump as next step."""
        process_id = "process::test::hint2_flow"
        _write_process_node(ctx, process_id, _minimal_process_node(process_id))
        body_file = tmp_path / "body.md"
        body_file.write_text("## Why this is a process\nContent.\n")
        args = argparse.Namespace(
            id=process_id,
            body_file=str(body_file),
            authored_by=[],
        )
        (ctx.LOGIGRAPH / "dossiers" / "processes").mkdir(parents=True, exist_ok=True)
        cmd_process_finalize(args, ctx)
        out = capsys.readouterr().out
        assert "process-bump" in out


# ===========================================================================
# cmd_process_bump
# ===========================================================================

class TestCmdProcessBump:
    def test_missing_node_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when no process node exists."""
        args = argparse.Namespace(
            id="process::test::ghost_flow",
            status="human_reviewed",
            actor=None,
        )
        rc = cmd_process_bump(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "no process node" in err

    def test_bumps_node_status(self, ctx: Context, capsys, monkeypatch) -> None:
        """Updates definition_status in the JSON node file."""
        monkeypatch.setattr(
            "kg.shared.git.subprocess.run",
            lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        )
        process_id = "process::test::to_bump_flow"
        _write_process_node(ctx, process_id, _minimal_process_node(
            process_id, definition_status="llm_drafted",
        ))
        args = argparse.Namespace(id=process_id, status="human_reviewed", actor="tester")
        rc = cmd_process_bump(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "processes" / "test__to_bump_flow.json"
        node = json.loads(node_path.read_text())
        assert node["definition_status"] == "human_reviewed"

    def test_bumps_dossier_frontmatter(self, ctx: Context, capsys, monkeypatch) -> None:
        """When a dossier exists, its frontmatter definition_status is updated."""
        monkeypatch.setattr(
            "kg.shared.git.subprocess.run",
            lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        )
        process_id = "process::test::dossier_bump_flow"
        _write_process_node(ctx, process_id, _minimal_process_node(
            process_id, definition_status="llm_drafted",
        ))
        dossier_dir = ctx.LOGIGRAPH / "dossiers" / "processes"
        dossier_dir.mkdir(parents=True, exist_ok=True)
        dossier_path = dossier_dir / "test__dossier_bump_flow.md"
        dossier_path.write_text(
            "---\nnode_id: process::test::dossier_bump_flow\n"
            "definition_status: llm_drafted\n"
            "last_reviewed: 2026-01-01\n"
            "last_reviewed_against_hash: oldhash\n"
            "---\n\n# Dossier bump flow\n\nContent.\n"
        )
        args = argparse.Namespace(id=process_id, status="human_reviewed", actor="tester")
        rc = cmd_process_bump(args, ctx)
        assert rc == 0
        content = dossier_path.read_text()
        assert "definition_status: human_reviewed" in content

    def test_invalid_process_id_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 for a badly formed process id."""
        args = argparse.Namespace(
            id="notaprocess::bad",
            status="human_reviewed",
            actor=None,
        )
        rc = cmd_process_bump(args, ctx)
        assert rc == 1
