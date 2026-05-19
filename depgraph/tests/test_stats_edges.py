"""Tests for `depgraph stats --edges` — confidence histogram + categorized
unresolved-edge breakdown (issue #53 Option C).

The category boundaries are the contract; if the bucket logic shifts, the
"chase which unresolved class first?" question stops being answerable from
the report, so the categorization is what we lock down here rather than the
exact formatting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from depgraph.lib.cli.context import Context
from depgraph.lib.cli.stats import cmd_stats, _categorize_unresolved


@pytest.mark.parametrize("target, expected_category, expected_group", [
    # external libraries — collapsed to pkg
    ("external::npm::react::useState", "external_library", "external::npm::react"),
    ("external::pypi::sqlalchemy::Session", "external_library", "external::pypi::sqlalchemy"),
    # missed in-corpus — the resolver-bug bucket
    ("external::pypi::unknown::BaseModel", "missed_internal", "external::pypi::unknown"),
    ("external::npm::unknown::default", "missed_internal", "external::npm::unknown"),
    # typed-receiver method calls — receiver name + dotted method
    ("external::unresolved::db.query", "typed_receiver", "external::unresolved::db.query"),
    ("external::unresolved::Receiver.method", "typed_receiver",
     "external::unresolved::Receiver.method"),
    # dynamic / computed callee — no dotted method
    ("external::unresolved::computed_callee", "dynamic_or_other",
     "external::unresolved::computed_callee"),
    # in-corpus or unrecognized shape
    ("repo::pkg/mod.py::cls", "other", "repo::pkg/mod.py::cls"),
])
def test_categorize_unresolved(target, expected_category, expected_group):
    cat, group = _categorize_unresolved(target)
    assert cat == expected_category
    assert group == expected_group


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


def test_stats_edges_reports_confidence_and_categorized_unresolved(tmp_path, capsys):
    """End-to-end: a synthetic corpus with a mix of edge confidences and
    target shapes prints the categorization that lets a reader prioritize
    resolver work."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)

    # 1 exact, 1 fuzzy, then 4 unresolved spanning all four interesting categories
    _write_node(depgraph / "nodes" / "f1.json", node_id="r::a.py::f1", edges=[
        {"target": "r::a.py::g", "kind": "calls", "confidence": "exact",
         "via": "call", "where": "a.py:1"},
        {"target": "r::a.py::h", "kind": "imports", "confidence": "fuzzy",
         "via": "re_export", "where": "a.py:2"},
        {"target": "external::npm::react::useState", "kind": "calls",
         "confidence": "unresolved", "via": "call", "where": "a.py:3"},
        {"target": "external::pypi::unknown::BaseModel", "kind": "extends",
         "confidence": "unresolved", "via": "class_decl", "where": "a.py:4"},
        {"target": "external::unresolved::db.query", "kind": "calls",
         "confidence": "unresolved", "via": "method_call", "where": "a.py:5"},
        {"target": "external::unresolved::computed_callee", "kind": "calls",
         "confidence": "unresolved", "via": "computed_callee", "where": "a.py:6"},
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
    assert _has_row("unresolved", 4)
    assert _has_row("total", 6)

    # categorized unresolved — count + label
    assert "## Unresolved edges by category" in out
    assert "1  external library" in out
    assert "1  missed in-corpus" in out
    assert "1  typed-receiver" in out
    assert "1  dynamic / other" in out

    # top prefixes — the worklist
    assert "## Top unresolved prefixes" in out
    assert "external::npm::react" in out
    assert "external::pypi::unknown" in out
    assert "external::unresolved::db.query" in out


def test_stats_edges_omitted_by_default(tmp_path, capsys):
    """Without --edges the edge sections must not render — keeps the default
    output a single screen."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)
    _write_node(depgraph / "nodes" / "f1.json", node_id="r::a.py::f1", edges=[
        {"target": "external::npm::react::useState", "kind": "calls",
         "confidence": "unresolved", "via": "call", "where": "a.py:1"},
    ])

    args = argparse.Namespace(telemetry=False, edges=False, unresolved_top=15)
    assert cmd_stats(args, ctx) == 0
    out = capsys.readouterr().out
    assert "## Edges by confidence" not in out
    assert "## Unresolved edges by category" not in out


def test_stats_edges_empty_unresolved_skips_category_section(tmp_path, capsys):
    """When the histogram is non-empty but no unresolved exist, the category
    breakdown section is skipped rather than rendered empty."""
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
    assert "## Unresolved edges by category" not in out
    assert "## Top unresolved prefixes" not in out


def test_stats_edges_respects_unresolved_top(tmp_path, capsys):
    """--unresolved-top N caps the worklist size."""
    depgraph = tmp_path / "depgraph"
    ctx = _make_ctx(depgraph)
    edges = [
        {"target": f"external::npm::pkg{i}::sym", "kind": "calls",
         "confidence": "unresolved", "via": "call", "where": "a.py:1"}
        for i in range(10)
    ]
    _write_node(depgraph / "nodes" / "f1.json", node_id="r::a.py::f1", edges=edges)

    args = argparse.Namespace(telemetry=False, edges=True, unresolved_top=3)
    assert cmd_stats(args, ctx) == 0
    out = capsys.readouterr().out
    assert "## Top unresolved prefixes (top 3)" in out
    prefix_lines = [ln for ln in out.splitlines() if "external::npm::pkg" in ln]
    assert len(prefix_lines) == 3
