"""Tests for logigraph.lib.cli.domain — domain-bump handler."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logigraph.lib.cli.context import Context
from logigraph.lib.cli.domain import cmd_domain_bump


@pytest.fixture
def ctx(data_dir: Path) -> Context:
    return Context.from_data_dir(data_dir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
        "structural_hash": "deadbeef",
        "dossier": f"dossiers/domain/{parts[0]}__{parts[1]}__{parts[2]}.md",
    }
    node.update(overrides)
    return node


# ===========================================================================
# cmd_domain_bump
# ===========================================================================

class TestCmdDomainBump:
    def test_invalid_id_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when the domain id is not valid."""
        args = argparse.Namespace(id="not::valid", status="human_reviewed", actor=None)
        rc = cmd_domain_bump(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "not a valid domain id" in err

    def test_missing_node_exits_1(self, ctx: Context, capsys) -> None:
        """Exits 1 when no domain node file exists."""
        args = argparse.Namespace(
            id="resource::test::ghost",
            status="human_reviewed",
            actor=None,
        )
        rc = cmd_domain_bump(args, ctx)
        assert rc == 1
        err = capsys.readouterr().err
        assert "no domain node" in err

    def test_bumps_node_status(self, ctx: Context, capsys, monkeypatch) -> None:
        """Updates definition_status in the JSON node file."""
        monkeypatch.setattr(
            "kg.shared.git.subprocess.run",
            lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        )
        domain_id = "resource::test::to_bump"
        _write_domain_node(ctx, domain_id, _minimal_domain_node(domain_id, definition_status="llm_drafted"))
        args = argparse.Namespace(id=domain_id, status="human_reviewed", actor="tester")
        rc = cmd_domain_bump(args, ctx)
        assert rc == 0
        node_path = ctx.NODES / "domain" / "resource__test__to_bump.json"
        node = json.loads(node_path.read_text())
        assert node["definition_status"] == "human_reviewed"

    def test_bumps_dossier_frontmatter(self, ctx: Context, capsys, monkeypatch) -> None:
        """When a dossier exists, its frontmatter definition_status is updated."""
        monkeypatch.setattr(
            "kg.shared.git.subprocess.run",
            lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        )
        domain_id = "resource::test::dossier_bump"
        _write_domain_node(ctx, domain_id, _minimal_domain_node(domain_id, definition_status="llm_drafted"))
        dossier_dir = ctx.LOGIGRAPH / "dossiers" / "domain"
        dossier_dir.mkdir(parents=True, exist_ok=True)
        dossier_path = dossier_dir / "resource__test__dossier_bump.md"
        dossier_path.write_text(
            "---\nnode_id: resource::test::dossier_bump\n"
            "definition_status: llm_drafted\n"
            "---\n\n## Content\n"
        )
        args = argparse.Namespace(id=domain_id, status="human_reviewed", actor="tester")
        rc = cmd_domain_bump(args, ctx)
        assert rc == 0
        content = dossier_path.read_text()
        assert "definition_status: human_reviewed" in content

    def test_prints_bumped_message(self, ctx: Context, capsys, monkeypatch) -> None:
        """Prints a confirmation line on success."""
        monkeypatch.setattr(
            "kg.shared.git.subprocess.run",
            lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        )
        domain_id = "role::test::print_bump"
        _write_domain_node(ctx, domain_id, _minimal_domain_node(domain_id))
        args = argparse.Namespace(id=domain_id, status="human_reviewed", actor="tester")
        rc = cmd_domain_bump(args, ctx)
        assert rc == 0
        out = capsys.readouterr().out
        assert "bumped" in out
        assert "human_reviewed" in out
