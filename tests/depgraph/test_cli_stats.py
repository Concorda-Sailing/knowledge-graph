"""Tests for depgraph.lib.cli.stats."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.stats import cmd_stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(
    ctx: Context,
    node_id: str,
    *,
    kind: str = "model",
    dossier: str | None = None,
) -> Path:
    """Write a minimal valid node JSON under nodes/."""
    node_file = ctx.NODES / f"{node_id.replace('::', '_')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "schema_version": 1,
        "id": node_id,
        "kind": kind,
        "source": {"repo": "test-api", "path": "models/foo.py"},
        "extractor": "python",
        "structural_hash": "aabbccdd11223344",
    }
    if dossier is not None:
        data["dossier"] = dossier
    node_file.write_text(json.dumps(data))
    return node_file


def _make_dossier(ctx: Context, rel_path: str, *, status: str = "current") -> Path:
    """Write a minimal dossier under ctx.DEPGRAPH/rel_path."""
    full = ctx.DEPGRAPH / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(
        f"---\nstatus: {status}\n---\n## The rule\nsome content\n"
    )
    return full


def _write_jsonl(path: Path, events: list[dict]) -> None:
    """Write JSONL telemetry events to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def _make_args(**overrides) -> argparse.Namespace:
    """Build a Namespace that mirrors what `register()`'s parser would
    produce — so tests don't break every time a new flag lands."""
    defaults = {"telemetry": False, "edges": False, "unresolved_top": 15}
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests: corpus rollup
# ---------------------------------------------------------------------------

def test_stats_empty_graph(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty nodes/ → prints header with 0 total, returns 0."""
    ctx = Context.from_data_dir(data_dir)
    args = _make_args()
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Depgraph stats" in out
    assert "total nodes: 0" in out
    # No kind/tier rows printed
    assert "tier" in out.lower()  # header still printed


def test_stats_single_node_missing_dossier(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """One node with no dossier → shows 1 total, miss=1."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(ctx, "test-api::models/foo.py::Foo", kind="model")
    args = _make_args()
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "total nodes: 1" in out
    # The model row for tier C should show miss=1
    assert "model" in out


def test_stats_node_with_current_dossier(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Node with a current dossier → cur=1, miss=0."""
    ctx = Context.from_data_dir(data_dir)
    _make_dossier(ctx, "dossiers/foo.md", status="current")
    _make_node(ctx, "test-api::models/foo.py::Foo", kind="model",
               dossier="dossiers/foo.md")
    args = _make_args()
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "total nodes: 1" in out
    assert "model" in out
    # Coverage pct should be 100% (cur=1)
    assert "100%" in out


def test_stats_node_with_llm_drafted_dossier(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Node with llm_drafted dossier → llm=1, coverage still 100%."""
    ctx = Context.from_data_dir(data_dir)
    _make_dossier(ctx, "dossiers/bar.md", status="llm_drafted")
    _make_node(ctx, "test-api::models/bar.py::Bar", kind="model",
               dossier="dossiers/bar.md")
    args = _make_args()
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "total nodes: 1" in out
    assert "100%" in out


def test_stats_multiple_nodes_mixed_kinds(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Multiple nodes of different kinds → each kind appears in output."""
    ctx = Context.from_data_dir(data_dir)
    _make_node(ctx, "test-api::models/foo.py::Foo", kind="model")
    _make_node(ctx, "test-api::routes/bar.py::BarRoute", kind="route")
    _make_node(ctx, "test-api::models/baz.py::Baz", kind="model")
    args = _make_args()
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "total nodes: 3" in out
    assert "model" in out
    assert "route" in out


def test_stats_skips_underscore_files(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Files starting with _ or inside _* directories are skipped."""
    ctx = Context.from_data_dir(data_dir)
    # Regular node
    _make_node(ctx, "test-api::models/foo.py::Foo", kind="model")
    # Meta/index files that should be skipped
    (ctx.NODES / "_meta.json").write_text(json.dumps({"schema_version": 1}))
    index_dir = ctx.NODES / "_index"
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "by_target.json").write_text(json.dumps({}))
    args = _make_args()
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    # Only 1 real node
    assert "total nodes: 1" in out


# ---------------------------------------------------------------------------
# Tests: telemetry
# ---------------------------------------------------------------------------

def test_stats_telemetry_no_log_files(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--telemetry with no log files → shows 0 counts, no crash."""
    ctx = Context.from_data_dir(data_dir)
    args = _make_args(telemetry=True)
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Telemetry (all-time)" in out
    assert "total injections:        0" in out
    assert "total acknowledgments:   0" in out
    assert "Telemetry (last 7 days)" in out


def test_stats_telemetry_with_events(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--telemetry with events in both logs → counts reflected."""
    import datetime as dt
    ctx = Context.from_data_dir(data_dir)

    now = dt.datetime.now(dt.timezone.utc)
    recent_ts = (now - dt.timedelta(hours=1)).isoformat()
    old_ts = (now - dt.timedelta(days=30)).isoformat()

    injections = [
        {"node_id": "n1", "ts": recent_ts},
        {"node_id": "n1", "ts": recent_ts},
        {"node_id": "n2", "ts": old_ts},
    ]
    acks = [
        {"node_id": "n1", "ts": recent_ts},
    ]
    _write_jsonl(ctx.INJECTIONS_LOG, injections)
    _write_jsonl(ctx.ACKS_LOG, acks)

    args = _make_args(telemetry=True)
    rc = cmd_stats(args, ctx)
    assert rc == 0
    out = capsys.readouterr().out
    assert "total injections:        3" in out
    assert "total acknowledgments:   1" in out
    # Last 7 days: only 2 recent injections
    assert "injections:              2" in out
    assert "acknowledgments:         1" in out
    # Top-injected section
    assert "Top-injected nodes" in out
    assert "n1" in out
