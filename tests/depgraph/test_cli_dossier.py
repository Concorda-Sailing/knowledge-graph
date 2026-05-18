"""Tests for depgraph.lib.cli.dossier — all 4 lifecycle handlers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.dossier import (
    cmd_dossier_rank,
    cmd_dossier_draft,
    cmd_dossier_finalize,
    cmd_dossier_bump,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(
    ctx: Context,
    node_id: str,
    *,
    kind: str = "model",
    repo: str = "test-api",
    path: str = "models/foo.py",
    structural_hash: str = "aabbccdd11223344",
    dossier: str | None = None,
) -> Path:
    node_file = ctx.NODES / f"{node_id.replace('::', '_').replace('/', '_')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "schema_version": 1,
        "id": node_id,
        "kind": kind,
        "source": {"repo": repo, "path": path, "line": 1},
        "extractor": "python",
        "structural_hash": structural_hash,
    }
    if dossier is not None:
        data["dossier"] = dossier
    node_file.write_text(json.dumps(data))
    return node_file


def _make_dossier(
    ctx: Context,
    rel: str,
    *,
    structural_hash: str = "aabbccdd11223344",
    status: str = "llm_drafted",
) -> Path:
    p = ctx.DEPGRAPH / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\nnode_id: test-api::models/foo.py::Foo\n"
        f"last_reviewed_against_hash: {structural_hash}\n"
        f"status: {status}\n---\n\n# Foo\n\nBody text.\n"
    )
    return p


# ---------------------------------------------------------------------------
# dossier-rank
# ---------------------------------------------------------------------------

def test_dossier_rank_outputs_header(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: with no nodes, rank still prints the table header."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(
        only_stale=False,
        only_unreviewed=True,
        tier=None,
        limit=50,
        include_tests=False,
    )
    rc = cmd_dossier_rank(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "fan" in out
    assert "total:" in out


def test_dossier_rank_lists_unreviewed_node(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose dossier has status: unreviewed shows up in rank output."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/foo.py/Foo.md"
    _make_node(ctx, "test-api::models/foo.py::Foo", dossier=dossier_rel)
    # Write a dossier with status: unreviewed (no last_reviewed_against_hash)
    p = ctx.DEPGRAPH / dossier_rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\nstatus: unreviewed\n---\n\n# Foo\n\nBody.\n")
    args = argparse.Namespace(
        only_stale=False,
        only_unreviewed=True,
        tier=None,
        limit=50,
        include_tests=False,
    )
    rc = cmd_dossier_rank(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-api::models/foo.py::Foo" in out


def test_dossier_rank_only_unreviewed_includes_missing_state(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """On a fresh corpus, every node's dossier state is 'missing' (no file).
    `--only-unreviewed` must surface those — otherwise the documented
    on-ramp from `depgraph health` returns 0 nodes (#35)."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(ctx, "test-api::models/foo.py::Foo")  # no dossier file written
    args = argparse.Namespace(
        only_stale=False, only_unreviewed=True,
        tier=None, limit=50, include_tests=False,
    )
    rc = cmd_dossier_rank(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-api::models/foo.py::Foo" in out
    assert "missing" in out  # the state column should show 'missing'


def test_dossier_rank_only_unreviewed_excludes_current_dossier(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A node whose dossier is `current` is filtered out by --only-unreviewed."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/done.py/Done.md"
    _make_node(ctx, "test-api::models/done.py::Done", dossier=dossier_rel)
    p = ctx.DEPGRAPH / dossier_rel
    p.parent.mkdir(parents=True, exist_ok=True)
    # Frontmatter that resolves to state=current: status absent (defaults to
    # "current" in _dossier_state) and last_reviewed_against_hash matches.
    p.write_text(
        "---\nlast_reviewed_against_hash: aabbccdd11223344\n---\n\n"
        "# Done\n\nbody\n"
    )
    args = argparse.Namespace(
        only_stale=False, only_unreviewed=True,
        tier=None, limit=50, include_tests=False,
    )
    rc = cmd_dossier_rank(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-api::models/done.py::Done" not in out
    assert "total: 0 nodes" in out


def test_dossier_rank_only_unreviewed_flag_actually_toggles(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With --only-unreviewed *off*, even `current` dossiers are listed.
    Asserts the flag actually controls behavior (#35: prior version had
    `default=True` on top of `action='store_true'` so the flag was inert)."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/done.py/Done.md"
    _make_node(ctx, "test-api::models/done.py::Done", dossier=dossier_rel)
    p = ctx.DEPGRAPH / dossier_rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\nlast_reviewed_against_hash: aabbccdd11223344\n---\n\nbody\n")
    args = argparse.Namespace(
        only_stale=False, only_unreviewed=False,
        tier=None, limit=50, include_tests=False,
    )
    cmd_dossier_rank(args, ctx)
    out = capsys.readouterr().out
    assert "test-api::models/done.py::Done" in out


def test_dossier_rank_subparser_only_unreviewed_default_is_false() -> None:
    """`--only-unreviewed` registered with action='store_true' must default
    to False; omitting it should not implicitly filter (#35)."""
    from depgraph.lib.cli.dossier import register

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register(sub)
    parsed = parser.parse_args(["dossier-rank", "--tier", "A"])
    assert parsed.only_unreviewed is False
    parsed2 = parser.parse_args(["dossier-rank", "--only-unreviewed"])
    assert parsed2.only_unreviewed is True


# ---------------------------------------------------------------------------
# dossier-draft
# ---------------------------------------------------------------------------

def test_dossier_draft_outputs_prompt(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: draft emits an LLM prompt referencing the node id."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        dossier="dossiers/test-api/models/foo.py/Foo.md",
    )
    (data_dir / "project.toml").write_text(
        '[project]\nname = "test"\n\n'
        '[repos.test-api]\npath = "/nonexistent/test-api"\n'
    )
    args = argparse.Namespace(target="test-api::models/foo.py::Foo")
    rc = cmd_dossier_draft(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "test-api::models/foo.py::Foo" in out
    assert "dossier-finalize" in out


def test_dossier_draft_missing_node_returns_1(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """draft with an unknown id returns exit code 1."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(target="no-such::node")
    rc = cmd_dossier_draft(args, ctx)
    assert rc == 1


# ---------------------------------------------------------------------------
# dossier-draft --auto: summarizer-backed dossier writing
# ---------------------------------------------------------------------------

def _draft_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        target="test-api::models/foo.py::Foo",
        auto=True, model=None, tools=False, max_turns=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _seed_node_and_repo(ctx: Context, data_dir: Path) -> None:
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        dossier="dossiers/test-api/models/foo.py/Foo.md",
    )
    (data_dir / "project.toml").write_text(
        '[project]\nname = "test"\n\n'
        '[repos.test-api]\npath = "/nonexistent/test-api"\n\n'
        '[summarizer]\n'
        'default_model = "local-gemma"\n\n'
        '[summarizer.models.local-gemma]\n'
        'spec = "openai"\n'
        'endpoint = "http://localhost:8080/v1"\n'
        'model = "gemma-2-9b-it"\n'
    )


def test_dossier_draft_auto_writes_dossier_with_llm_drafted_status(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--auto routes the prompt through the configured model and writes the
    response into the canonical dossier path with status: llm_drafted."""
    ctx = Context.from_data_dir(data_dir)
    _seed_node_and_repo(ctx, data_dir)

    from depgraph.lib.summarizer.agent import AgentResult
    from depgraph.lib.cli import dossier as dossier_mod

    captured: dict = {}

    def fake_run_agent(client, *, user_prompt, tools=None, tool_handlers=None,
                       max_turns=8, **kw):
        captured["prompt"] = user_prompt
        captured["tools"] = tools
        captured["max_turns"] = max_turns
        return AgentResult(
            text="## Purpose\n\nFoo is a model.\n",
            turns=1, stop_reason="end_turn",
            usage_totals={"input_tokens": 100, "output_tokens": 20},
        )

    monkeypatch.setattr(dossier_mod, "_save_drafted_dossier",
                        dossier_mod._save_drafted_dossier)  # keep real path
    # Patch the agent loop inside the summarizer module so the test never
    # hits the network.
    import depgraph.lib.summarizer as summarizer_pkg
    monkeypatch.setattr(summarizer_pkg, "run_agent", fake_run_agent)

    rc = cmd_dossier_draft(_draft_args(), ctx)
    assert rc == 0

    written = ctx.DEPGRAPH / "dossiers/test-api/models/foo.py/Foo.md"
    assert written.exists()
    text = written.read_text()
    assert "status: llm_drafted" in text
    assert "authored_by:" in text
    assert "local-gemma" in text
    assert "Foo is a model" in text
    # The prompt the agent saw mentions the node id.
    assert "test-api::models/foo.py::Foo" in captured["prompt"]
    # No tools by default.
    assert captured["tools"] is None


def test_dossier_draft_auto_with_tools_passes_handlers(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--auto --tools materializes the builtin tool set."""
    ctx = Context.from_data_dir(data_dir)
    _seed_node_and_repo(ctx, data_dir)

    from depgraph.lib.summarizer.agent import AgentResult
    import depgraph.lib.summarizer as summarizer_pkg

    captured: dict = {}

    def fake_run_agent(client, *, user_prompt, tools=None, tool_handlers=None,
                       max_turns=8, **kw):
        captured["tools"] = tools
        captured["handlers"] = tool_handlers
        return AgentResult(text="## Purpose\n\nbody.\n", turns=1, stop_reason="end_turn")

    monkeypatch.setattr(summarizer_pkg, "run_agent", fake_run_agent)

    rc = cmd_dossier_draft(_draft_args(tools=True), ctx)
    assert rc == 0
    assert captured["tools"] is not None
    tool_names = {t.name for t in captured["tools"]}
    assert {"read_source", "dependents_of", "node_info", "recent_history"} <= tool_names
    assert set(captured["handlers"].keys()) == tool_names


def test_dossier_draft_auto_no_summarizer_config_returns_1(
    data_dir: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """--auto without any [summarizer.models.*] entries fails cleanly."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(
        ctx, "test-api::models/foo.py::Foo",
        dossier="dossiers/test-api/models/foo.py/Foo.md",
    )
    (data_dir / "project.toml").write_text(
        '[project]\nname = "t"\n[repos.test-api]\npath = "/n"\n'
    )
    rc = cmd_dossier_draft(_draft_args(), ctx)
    assert rc == 1
    err = capsys.readouterr().err
    assert "no [summarizer.models.*] configured" in err


def test_dossier_draft_auto_empty_response_returns_1(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """If the model returns an empty body, don't write a dossier."""
    ctx = Context.from_data_dir(data_dir)
    _seed_node_and_repo(ctx, data_dir)

    from depgraph.lib.summarizer.agent import AgentResult
    import depgraph.lib.summarizer as summarizer_pkg

    monkeypatch.setattr(
        summarizer_pkg, "run_agent",
        lambda *a, **kw: AgentResult(text="", turns=1, stop_reason="end_turn"),
    )

    rc = cmd_dossier_draft(_draft_args(), ctx)
    assert rc == 1
    assert "empty body" in capsys.readouterr().err
    # No dossier written.
    assert not (ctx.DEPGRAPH / "dossiers/test-api/models/foo.py/Foo.md").exists()


def test_dossier_draft_auto_unknown_model_returns_1(
    data_dir: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """--model pointing at an undeclared key fails cleanly."""
    ctx = Context.from_data_dir(data_dir)
    _seed_node_and_repo(ctx, data_dir)
    rc = cmd_dossier_draft(_draft_args(model="ghost"), ctx)
    assert rc == 1
    assert "not configured" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# dossier-finalize
# ---------------------------------------------------------------------------

def test_dossier_finalize_writes_body(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: finalize writes the dossier file with frontmatter."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/foo.py/Foo.md"
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        dossier=dossier_rel,
    )

    body_file = tmp_path / "body.md"
    body_file.write_text("## Purpose\nDoes things.\n")

    args = argparse.Namespace(
        node_id="test-api::models/foo.py::Foo",
        body_file=str(body_file),
        authored_by=[],
    )
    rc = cmd_dossier_finalize(args, ctx)
    assert rc == 0

    dossier_path = ctx.DEPGRAPH / dossier_rel
    assert dossier_path.exists()
    text = dossier_path.read_text()
    assert "status: llm_drafted" in text
    assert "## Purpose" in text


def test_dossier_finalize_missing_node_returns_1(
    data_dir: Path, tmp_path: Path
) -> None:
    """finalize with unknown node_id returns exit code 1."""
    ctx = Context.from_data_dir(data_dir)
    body_file = tmp_path / "body.md"
    body_file.write_text("## Purpose\nDoes things.\n")
    args = argparse.Namespace(
        node_id="no-such::node",
        body_file=str(body_file),
        authored_by=[],
    )
    rc = cmd_dossier_finalize(args, ctx)
    assert rc == 1


# ---------------------------------------------------------------------------
# dossier-bump
# ---------------------------------------------------------------------------

def test_dossier_bump_updates_status(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: bump updates status from llm_drafted to current."""
    ctx = Context.from_data_dir(data_dir)
    dossier_rel = "dossiers/test-api/models/foo.py/Foo.md"
    _make_node(
        ctx,
        "test-api::models/foo.py::Foo",
        dossier=dossier_rel,
    )
    _make_dossier(ctx, dossier_rel, status="llm_drafted")

    args = argparse.Namespace(
        node_id="test-api::models/foo.py::Foo",
        status="current",
    )
    rc = cmd_dossier_bump(args, ctx)
    assert rc == 0

    text = (ctx.DEPGRAPH / dossier_rel).read_text()
    assert "status: current" in text


def test_dossier_bump_missing_node_returns_1(
    data_dir: Path,
) -> None:
    """bump with unknown node_id returns exit code 1."""
    ctx = Context.from_data_dir(data_dir)
    args = argparse.Namespace(node_id="no-such::node", status="current")
    rc = cmd_dossier_bump(args, ctx)
    assert rc == 1
