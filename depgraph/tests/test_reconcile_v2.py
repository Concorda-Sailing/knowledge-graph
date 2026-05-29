"""Tests for the v2 reconcile validate_corpus function and the regen entry point.

validate_corpus: checks orphan edges (targets not in corpus and not external::)
                 accepts external:: terminal targets.
regen end-to-end: tiny synthetic Python project → full v2 pipeline produces
                  nodes/ + by_target.json index.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

def _make_function_primitive(
    *,
    node_id: str,
    name: str,
    edges_out: list[dict] | None = None,
) -> dict:
    """Minimal valid v2 function primitive."""
    repo, rel_path, sym = node_id.split("::", 2)
    return {
        "schema_version": 2,
        "id": node_id,
        "primitive": "function",
        "name": name,
        "owner": None,
        "source": {
            "repo": repo,
            "path": rel_path,
            "language": "python",
            "line": 1,
            "end_line": 2,
        },
        "signature": {
            "parameters": [],
            "return_type": None,
            "is_async": False,
            "decorators": [],
        },
        "attributes": {},
        "structural_hash": "0" * 64,
        "kind": None,
        "extractor": "test",
        "edges_out": edges_out or [],
    }


# ---------------------------------------------------------------------------
# validate_corpus unit tests
# ---------------------------------------------------------------------------

def test_reconcile_flags_orphan_edge():
    from depgraph.extractors.reconcile import validate_corpus

    prims = [_make_function_primitive(
        node_id="r::a.py::f",
        name="f",
        edges_out=[{
            "target": "r::nowhere.py::ghost",
            "kind": "calls",
            "via": "fn",
            "where": "a.py:1",
            "confidence": "exact",
        }],
    )]
    report = validate_corpus(prims)
    assert len(report["orphan_edges"]) == 1
    assert report["orphan_edges"][0]["target"] == "r::nowhere.py::ghost"


def test_reconcile_accepts_external_terminal_targets():
    from depgraph.extractors.reconcile import validate_corpus

    prims = [_make_function_primitive(
        node_id="r::a.py::f",
        name="f",
        edges_out=[{
            "target": "external::pypi::sqlalchemy::Session.query",
            "kind": "db_access",
            "via": "session.query",
            "where": "a.py:1",
            "confidence": "exact",
        }],
    )]
    report = validate_corpus(prims)
    assert report["orphan_edges"] == []


def test_reconcile_accepts_internal_edge_that_resolves():
    from depgraph.extractors.reconcile import validate_corpus

    caller = _make_function_primitive(
        node_id="r::a.py::caller",
        name="caller",
        edges_out=[{
            "target": "r::a.py::callee",
            "kind": "calls",
            "via": "callee",
            "where": "a.py:2",
            "confidence": "exact",
        }],
    )
    callee = _make_function_primitive(node_id="r::a.py::callee", name="callee")
    report = validate_corpus([caller, callee])
    assert report["orphan_edges"] == []
    assert report["primitive_errors"] == []


def test_reconcile_reports_slug_collision():
    from depgraph.extractors.reconcile import validate_corpus

    # Two ids that slugify to the same filename: colons → underscores
    # "r::a b.py::f" and "r::a_b.py::f" both have spaces/underscores collapsing.
    p1 = _make_function_primitive(node_id="r::a.py::f", name="f")
    p2 = _make_function_primitive(node_id="r::a.py::f", name="f")
    # Make the second id distinct but slug-colliding
    p2 = dict(p2, id="r::a_py::f")
    p2["source"] = dict(p2["source"], path="a_py")
    report = validate_corpus([p1, p2])
    assert len(report["slug_collisions"]) >= 1


def test_reconcile_dependents_index_filename():
    """Regression for #43: reconcile.py used to wire DEPENDENTS_INDEX at the
    pre-rename `dependents.json` path while the rest of the framework writes
    to `by_target.json`. Post-#66 reconcile composes the path from the
    shared constant in `depgraph.lib.edges`, so the literal lives in exactly
    one place — verified here."""
    import inspect
    from depgraph.extractors import reconcile
    from depgraph.lib.edges import REVERSE_INDEX_FILENAME

    assert REVERSE_INDEX_FILENAME == "by_target.json"
    src = inspect.getsource(reconcile.main)
    assert "INDEX_DIR / REVERSE_INDEX_FILENAME" in src
    assert 'INDEX_DIR / "dependents.json"' not in src


# ---------------------------------------------------------------------------
# regen end-to-end test
# ---------------------------------------------------------------------------

@pytest.fixture
def tiny_project(tmp_path):
    api = tmp_path / "api"
    api.mkdir()
    (api / "routers.py").write_text(
        "def helper(): pass\n\n"
        "def create_event():\n"
        "    helper()\n"
    )
    return tmp_path


def test_regen_end_to_end(tiny_project, tmp_path):
    """Mode B regen: single synthetic Python repo → v2 corpus with indexes.

    The kg resolver treats --data-dir as the umbrella project root and appends
    /depgraph/ to get the actual depgraph data dir.  So we pass tmp_path as the
    umbrella root and look for output under tmp_path/depgraph/nodes/.
    """
    # The kg resolver appends /depgraph/ to --data-dir to get the depgraph dir.
    umbrella = tmp_path / "project"
    umbrella.mkdir()
    depgraph_dir = umbrella / "depgraph"

    result = subprocess.run(
        [
            sys.executable, "-m", "kg.cli",
            "depgraph", "regen",
            "--data-dir", str(umbrella),
            "--repo-key", "api",
            "--repo-path", str(tiny_project / "api"),
            "--languages", "python",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"regen failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    # helper() should be emitted as a function primitive
    helper = depgraph_dir / "nodes" / "functions" / "api__routers_py__helper.json"
    all_nodes = list(depgraph_dir.rglob("*.json")) if depgraph_dir.exists() else []
    assert helper.exists(), f"missing {helper}; nodes found: {all_nodes}"

    node = json.loads(helper.read_text())
    assert node["id"] == "api::routers.py::helper"
    assert node["primitive"] == "function"

    # by_target index should record the calls edge pointing at helper
    idx_path = depgraph_dir / "nodes" / "_index" / "by_target.json"
    assert idx_path.exists(), "by_target.json index not written"
    idx = json.loads(idx_path.read_text())

    assert "api::routers.py::helper" in idx, (
        f"helper missing from by_target; keys: {sorted(idx)[:10]}"
    )
    incoming = idx["api::routers.py::helper"]
    assert any(e.get("kind") == "calls" for e in incoming), (
        f"no calls edge in incoming: {incoming}"
    )

    # by_source index should also be present
    src_path = depgraph_dir / "nodes" / "_index" / "by_source.json"
    assert src_path.exists(), "by_source.json index not written"

    # _meta.json should record regen_status: complete
    meta = json.loads((depgraph_dir / "nodes" / "_meta.json").read_text())
    assert meta.get("regen_status") == "complete", f"meta: {meta}"


# ---------------------------------------------------------------------------
# Regression: the reverse index is built from the live `edges_out` field and
# written in the flat v2 schema.
#
# Before the v1/v2 unification, `reconcile.build_reverse_index` read the dead
# `depends_on` field (regen had already moved to `edges_out`) and wrote a
# wrapped `{"schema_version": 1, "by_target": {...}}` file. The post-edit Stop
# hook runs reconcile every turn, so on a v2 corpus it computed ZERO edges and
# clobbered `by_target.json` to empty — starving both `dossier-rank` (fan-out)
# and the pre-edit dependents injection (which expects the flat, unwrapped
# schema). The builder now lives once in `depgraph.lib.edges`, reads
# `edges_out`, and reconcile writes the same flat schema regen does.
# ---------------------------------------------------------------------------

def test_build_reverse_index_reads_edges_out():
    from depgraph.lib.edges import build_reverse_index

    caller = _make_function_primitive(
        node_id="r::a.py::caller",
        name="caller",
        edges_out=[{
            "target": "r::a.py::callee", "kind": "calls",
            "via": "callee", "where": "a.py:2", "confidence": "exact",
        }],
    )
    callee = _make_function_primitive(node_id="r::a.py::callee", name="callee")

    by_target, count = build_reverse_index([caller, callee])
    assert count == 1
    assert "r::a.py::callee" in by_target
    rec = by_target["r::a.py::callee"][0]
    assert rec["source"] == "r::a.py::caller"
    assert rec["kind"] == "calls"


def test_build_reverse_index_ignores_dead_depends_on_field():
    """A node carrying only the obsolete v1 `depends_on` edge (and empty
    edges_out) must yield an EMPTY index — proving the builder reads the live
    field, not the dead one."""
    from depgraph.lib.edges import build_reverse_index

    legacy = _make_function_primitive(node_id="r::a.py::caller", name="caller")
    legacy["depends_on"] = [{"target": "r::a.py::callee", "via": "callee"}]

    by_target, count = build_reverse_index([legacy])
    assert count == 0
    assert by_target == {}


def test_reconcile_builder_populated_for_v2_corpus():
    """reconcile.build_reverse_index over a v2 {id: (path, data)} map produces a
    populated index — the direct regression for the empty-clobber bug."""
    from depgraph.extractors.reconcile import build_reverse_index as recon_build

    caller = _make_function_primitive(
        node_id="r::a.py::caller",
        name="caller",
        edges_out=[{
            "target": "r::a.py::callee", "kind": "calls",
            "via": "callee", "where": "a.py:2", "confidence": "exact",
        }],
    )
    callee = _make_function_primitive(node_id="r::a.py::callee", name="callee")
    nodes = {
        "r::a.py::caller": (Path("ignored"), caller),
        "r::a.py::callee": (Path("ignored"), callee),
    }
    by_target, count = recon_build(nodes)
    assert count == 1
    assert "r::a.py::callee" in by_target


def test_reconcile_writes_flat_reverse_index_schema(tmp_path, monkeypatch):
    """reconcile must persist by_target.json in the flat v2 schema
    ({target_id: [...]}, no wrapper) — the shape pre_edit_inject and rollup
    read. Regression against the legacy wrapped {"schema_version":1,...} write."""
    from depgraph.extractors import reconcile

    idx_dir = tmp_path / "_index"
    monkeypatch.setattr(reconcile, "INDEX_DIR", idx_dir)
    monkeypatch.setattr(reconcile, "DEPENDENTS_INDEX", idx_dir / "by_target.json")

    by_target = {
        "r::a.py::callee": [{
            "source": "r::a.py::caller", "kind": "calls",
            "via": "callee", "where": "a.py:2", "confidence": "exact",
        }]
    }
    changed, path = reconcile.write_dependents_index(by_target)
    assert changed is True

    data = json.loads(path.read_text())
    # Flat schema: target ids are top-level keys, no wrapper.
    assert "schema_version" not in data
    assert "by_target" not in data
    assert data["r::a.py::callee"][0]["source"] == "r::a.py::caller"
