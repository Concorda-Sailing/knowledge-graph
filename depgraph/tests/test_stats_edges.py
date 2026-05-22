"""Tests for `depgraph stats --edges` — confidence histogram + per-bucket
worklist (issue #53 Option A).

After Option A, the previously-collapsed `unresolved` bucket is split into
four specific values stamped at emit time:

  * `external`              — deliberate external library terminal
  * `unresolved_internal`   — resolver-gap (bug signal)
  * `unresolved_receiver`   — typed-receiver method call (gap)
  * `dynamic`               — reserved for getattr / computed dispatch

The `stats --edges` report reads the confidence field directly rather than
re-deriving from the target prefix, so the contract this suite locks down
is the printed sections and the `_group_key_for_target` collapse helper.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.stats import cmd_stats, _group_key_for_target


@pytest.mark.parametrize("target, expected_group", [
    # external libraries — collapsed to pkg
    ("external::npm::react::useState", "external::npm::react"),
    ("external::pypi::sqlalchemy::Session", "external::pypi::sqlalchemy"),
    # missed in-corpus — `unknown` slot, collapsed the same way
    ("external::pypi::unknown::BaseModel", "external::pypi::unknown"),
    ("external::npm::unknown::default", "external::npm::unknown"),
    # typed-receiver — receiver name + dotted method, kept verbatim
    ("external::unresolved::db.query", "external::unresolved::db.query"),
    ("external::unresolved::Receiver.method",
     "external::unresolved::Receiver.method"),
    # dynamic / computed callee — also kept verbatim
    ("external::unresolved::computed_callee",
     "external::unresolved::computed_callee"),
    # in-corpus or unrecognized shape — passed through unchanged
    ("repo::pkg/mod.py::cls", "repo::pkg/mod.py::cls"),
])
def test_group_key_for_target(target, expected_group):
    assert _group_key_for_target(target) == expected_group


def _make_ctx(depgraph: Path) -> Context:
    (depgraph / "nodes").mkdir(parents=True, exist_ok=True)
    return Context.from_data_dir(depgraph)


def _write_node(node_path: Path, *, node_id: str, edges: list[dict]) -> None:
    node_path.parent.mkdir(parents=True, exist_ok=True)
    node_path.write_text(json.dumps({
        "id": node_id,
        "primitive": "function",
        "name": node_id.split("::")[-1],
        "kind": "function",
        "source": {"repo": "r", "path": "a.py", "language": "python"},
        "edges_out": edges,
    }))


def test_stats_edges_reports_confidence_and_per_bucket_worklist(tmp_path, capsys):
    """End-to-end: a synthetic corpus with one edge per new confidence
    value prints the per-bucket counts and the gap-target prefixes worklist."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)

    _write_node(depgraph / "nodes" / "f1.json", node_id="r::a.py::f1", edges=[
        {"target": "r::a.py::g", "kind": "calls", "confidence": "exact",
         "via": "call", "where": "a.py:1"},
        {"target": "r::a.py::h", "kind": "imports", "confidence": "fuzzy",
         "via": "re_export", "where": "a.py:2"},
        {"target": "external::npm::react::useState", "kind": "calls",
         "confidence": "external", "via": "call", "where": "a.py:3"},
        {"target": "external::pypi::unknown::BaseModel", "kind": "extends",
         "confidence": "unresolved_internal", "via": "class_decl",
         "where": "a.py:4"},
        {"target": "external::unresolved::db.query", "kind": "calls",
         "confidence": "unresolved_receiver", "via": "method_call",
         "where": "a.py:5"},
        {"target": "external::unresolved::computed_callee", "kind": "calls",
         "confidence": "unresolved_receiver", "via": "computed_callee",
         "where": "a.py:6"},
    ])

    args = argparse.Namespace(telemetry=False, edges=True, unresolved_top=15)
    rc = cmd_stats(args, ctx)
    assert rc == 0

    out = capsys.readouterr().out

    def _has_row(label: str, count: int) -> bool:
        """Locate a row whose tokens are exactly [label_words..., str(count)]."""
        needle = label.split() + [str(count)]
        for line in out.splitlines():
            if line.split() == needle:
                return True
        return False

    # confidence histogram
    assert "## Edges by confidence" in out
    assert _has_row("exact", 1)
    assert _has_row("fuzzy", 1)
    assert _has_row("external", 1)
    assert _has_row("unresolved_internal", 1)
    assert _has_row("unresolved_receiver", 2)
    assert _has_row("dynamic", 0)
    assert _has_row("total", 6)

    # per-category breakdown — count + label
    assert "## Edges by confidence category" in out
    assert "1  external library" in out
    assert "1  missed in-corpus" in out
    assert "2  typed-receiver" in out

    # worklist of gap-target prefixes — must NOT include the `external`
    # bucket (that's the expected case, not a worklist item)
    assert "## Top gap-target prefixes" in out
    assert "external::pypi::unknown" in out
    assert "external::unresolved::db.query" in out
    # react is `external` confidence — excluded from the worklist
    assert "external::npm::react" not in out.split("Top gap-target prefixes")[-1]


def test_stats_edges_omitted_by_default(tmp_path, capsys):
    """Without --edges the edge sections must not render — keeps the default
    output a single screen."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)
    _write_node(depgraph / "nodes" / "f1.json", node_id="r::a.py::f1", edges=[
        {"target": "external::npm::react::useState", "kind": "calls",
         "confidence": "external", "via": "call", "where": "a.py:1"},
    ])

    args = argparse.Namespace(telemetry=False, edges=False, unresolved_top=15)
    assert cmd_stats(args, ctx) == 0
    out = capsys.readouterr().out
    assert "## Edges by confidence" not in out
    assert "## Edges by confidence category" not in out


def test_stats_edges_only_exact_skips_category_section(tmp_path, capsys):
    """When the histogram is non-empty but only `exact` / `fuzzy` edges
    exist, the category breakdown section is skipped rather than rendered
    empty."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)
    _write_node(depgraph / "nodes" / "f1.json", node_id="r::a.py::f1", edges=[
        {"target": "r::a.py::g", "kind": "calls", "confidence": "exact",
         "via": "call", "where": "a.py:1"},
    ])

    args = argparse.Namespace(telemetry=False, edges=True, unresolved_top=15)
    assert cmd_stats(args, ctx) == 0
    out = capsys.readouterr().out
    assert "## Edges by confidence" in out
    assert "## Edges by confidence category" not in out
    assert "## Top gap-target prefixes" not in out


def test_stats_edges_respects_unresolved_top(tmp_path, capsys):
    """--unresolved-top N caps the gap-target worklist size. `external`
    targets are NOT counted toward the worklist (they're the expected
    bucket, not a gap)."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)
    edges = [
        {"target": f"external::pypi::unknown::sym{i}", "kind": "calls",
         "confidence": "unresolved_internal", "via": "call", "where": "a.py:1"}
        for i in range(10)
    ]
    # Stagger the targets so they land in 10 distinct group prefixes.
    edges = [
        {"target": f"external::unresolved::recv{i}.method", "kind": "calls",
         "confidence": "unresolved_receiver", "via": "method_call",
         "where": "a.py:1"}
        for i in range(10)
    ]
    _write_node(depgraph / "nodes" / "f1.json", node_id="r::a.py::f1", edges=edges)

    args = argparse.Namespace(telemetry=False, edges=True, unresolved_top=3)
    assert cmd_stats(args, ctx) == 0
    out = capsys.readouterr().out
    assert "## Top gap-target prefixes (top 3)" in out
    prefix_lines = [ln for ln in out.splitlines()
                    if "external::unresolved::recv" in ln]
    assert len(prefix_lines) == 3
