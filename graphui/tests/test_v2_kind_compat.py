"""Task 6.0: verify graphui can read v2 kind dirs without crashing.

Checks:
- load_depgraph_nodes() picks up nodes from schemas/, modules/, functions/
- KIND_LABELS covers all v2 kinds (no raw keys fall through in coverage_matrix)
- KIND_ORDER covers all v2 kinds (no unknown kind sorts to 99 by accident)
- coverage_matrix() runs without error and includes v2 kinds that appear in nodes
- /graph/api/nodes.json returns v2 nodes without crashing
- /graph/node/<id> returns 200 for a schema node
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# loader-level checks
# ---------------------------------------------------------------------------

def test_load_depgraph_nodes_includes_schema_kind(loader):
    nodes = loader.load_depgraph_nodes()
    kinds = {n.get("kind") for n in nodes}
    assert "schema" in kinds, "schema kind dir not picked up by load_depgraph_nodes"


def test_load_depgraph_nodes_includes_module_kind(loader):
    nodes = loader.load_depgraph_nodes()
    kinds = {n.get("kind") for n in nodes}
    assert "module" in kinds, "module kind dir not picked up by load_depgraph_nodes"


def test_load_depgraph_nodes_includes_function_kind(loader):
    nodes = loader.load_depgraph_nodes()
    kinds = {n.get("kind") for n in nodes}
    assert "function" in kinds, "function kind dir not picked up by load_depgraph_nodes"


def test_kind_labels_covers_v2_kinds(loader):
    v2_kinds = {"schema", "module", "package", "class", "function", "variable"}
    missing = v2_kinds - set(loader.KIND_LABELS.keys())
    assert not missing, f"KIND_LABELS missing v2 kinds: {missing}"


def test_coverage_matrix_includes_v2_kinds(loader):
    """coverage_matrix must run without error and include schema/module/function
    since the fixture corpus has nodes of those kinds."""
    matrix = loader.coverage_matrix()
    assert "schema" in matrix, "schema missing from coverage_matrix"
    assert "module" in matrix, "module missing from coverage_matrix"
    assert "function" in matrix, "function missing from coverage_matrix"


def test_coverage_matrix_no_crash_on_unknown_kind(loader):
    """Even if an unexpected kind appears on disk, coverage_matrix must not crash."""
    matrix = loader.coverage_matrix()
    assert isinstance(matrix, dict)


# ---------------------------------------------------------------------------
# KIND_ORDER in main.py
# ---------------------------------------------------------------------------

def test_kind_order_covers_v2_kinds(client):
    """Import main and verify KIND_ORDER contains all v2 kinds."""
    from app import main as mainmod
    v2_kinds = {"schema", "module", "package", "class", "function", "variable"}
    missing = v2_kinds - set(mainmod.KIND_ORDER)
    assert not missing, f"KIND_ORDER missing v2 kinds: {missing}"


# ---------------------------------------------------------------------------
# HTTP smoke tests
# ---------------------------------------------------------------------------

def test_nodes_json_includes_schema_node(client):
    resp = client.get("/graph/api/nodes.json")
    assert resp.status_code == 200
    nodes = resp.json()
    kinds = {n["kind"] for n in nodes}
    assert "schema" in kinds, f"schema kind missing from /api/nodes.json; got kinds: {kinds}"
    assert "module" in kinds, f"module kind missing from /api/nodes.json; got kinds: {kinds}"
    assert "function" in kinds, f"function kind missing from /api/nodes.json; got kinds: {kinds}"


def test_node_detail_schema_node_renders(client):
    resp = client.get("/graph/node/concorda-api::migrations/0010_crew.sql::CrewTable")
    assert resp.status_code == 200


def test_node_detail_module_node_renders(client):
    resp = client.get("/graph/node/concorda-api::app.py")
    assert resp.status_code == 200


def test_node_detail_function_node_renders(client):
    resp = client.get("/graph/node/concorda-api::utils.py::format_date")
    assert resp.status_code == 200
