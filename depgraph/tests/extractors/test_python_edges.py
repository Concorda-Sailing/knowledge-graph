"""Python edge extractor in-process tests — Phase 3.

Each test calls extract_repo against a small fixture under
fixtures/edges_py/<scenario>/ and asserts on edges emitted.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from depgraph.extractors.python.extract import extract_repo

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "edges_py"


# ---------------------------------------------------------------------------
# Task 3.1: defines edges
# ---------------------------------------------------------------------------

def test_defines_class_method_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "defines"))
    cls = next(p for p in prims if p["name"] == "Foo")
    targets = {e["target"] for e in cls["edges_out"] if e["kind"] == "defines"}
    assert "fixture::src.py::Foo.bar" in targets


# ---------------------------------------------------------------------------
# Task 3.2: extends / implements edges
# ---------------------------------------------------------------------------

def test_extends_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "inheritance"))
    child = next(p for p in prims if p["name"] == "Child")
    ex = [e for e in child["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "fixture::src.py::Base" for e in ex)


# ---------------------------------------------------------------------------
# Task 3.3: imports edges
# ---------------------------------------------------------------------------

def test_python_imports():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "imports"))
    mod_a = next(p for p in prims if p["source"]["path"] == "a.py"
                 and p["primitive"] == "module")
    imports = [e for e in mod_a["edges_out"] if e["kind"] == "imports"]
    assert any(e["target"] == "fixture::b.py::foo" for e in imports)


def test_aliased_import_records_local_binding():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "imports_aliased"))
    mod = next(p for p in prims if p["source"]["path"] == "a.py"
               and p["primitive"] == "module")
    edge = next(e for e in mod["edges_out"]
                if e["kind"] == "imports" and "foo" in e["target"])
    assert edge["local_binding"] == "bar"


# ---------------------------------------------------------------------------
# Task 3.4: calls + instantiates edges (intra-function type binding)
# ---------------------------------------------------------------------------

def test_calls_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src.py::helper" for e in calls)


def test_instantiates_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    root = next(p for p in prims if p["name"] == "root")
    insts = [e for e in root["edges_out"] if e["kind"] == "instantiates"]
    assert any(e["target"] == "fixture::src.py::Service" for e in insts)


def test_method_call_on_local_instance_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    do_works = [e for e in calls if e["target"] == "fixture::src.py::Service.do_work"]
    assert len(do_works) >= 2, f"expected 2 do_work calls from root, got {do_works}"


def test_method_call_on_parameter_annotation_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    handler = next(p for p in prims if p["name"] == "handler")
    calls = [e for e in handler["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src.py::Service.do_work" for e in calls)


# ---------------------------------------------------------------------------
# Task 3.5: reads / assigns / decorates edges
# ---------------------------------------------------------------------------

def test_reads_edge_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    reader = next(p for p in prims if p["name"] == "reader")
    reads = [e for e in reader["edges_out"] if e["kind"] == "reads"]
    assert any(e["target"] == "fixture::src.py::GLOBAL" for e in reads)


def test_assigns_edge_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    writer = next(p for p in prims if p["name"] == "writer")
    assigns = [e for e in writer["edges_out"] if e["kind"] == "assigns"]
    assert any(e["target"] == "fixture::src.py::GLOBAL" for e in assigns)


def test_decorates_edge_local_decorator_py():
    """A local decorator (`@local_dec`) produces a `decorates` edge from
    the decorator function primitive to the decorated function. External
    decorators (`@functools.lru_cache`) do NOT produce an edge — they're
    captured in `signature.decorators` instead, since the edge taxonomy
    disallows external terminals as edge sources."""
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    locally_decorated = next(p for p in prims if p["name"] == "locally_decorated")
    local_dec = next(p for p in prims if p["name"] == "local_dec")

    # Local decorator → edge present, source is local_dec
    incoming = [
        e for src_p in prims for e in src_p["edges_out"]
        if e["kind"] == "decorates" and e["target"] == locally_decorated["id"]
    ]
    assert incoming, "expected a decorates edge into `locally_decorated`"
    src_ids = {p["id"] for p in prims for e in p["edges_out"]
               if e["kind"] == "decorates" and e["target"] == locally_decorated["id"]}
    assert local_dec["id"] in src_ids


def test_external_decorator_not_an_edge_py():
    """`@functools.lru_cache()` records in signature.decorators but does
    not produce a decorates edge (no external-as-source edges)."""
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    decorated = next(p for p in prims if p["name"] == "decorated")

    # Captured in signature
    assert any("functools" in d or "lru_cache" in d
               for d in decorated["signature"]["decorators"])
    # No incoming decorates edge
    incoming = [
        e for src_p in prims for e in src_p["edges_out"]
        if e["kind"] == "decorates" and e["target"] == decorated["id"]
    ]
    assert incoming == [], (
        f"external decorator should not emit a decorates edge; got: {incoming}"
    )


# ---------------------------------------------------------------------------
# Task 3.6: tests edges (assertion-scoped)
# ---------------------------------------------------------------------------

def test_tests_edge_py_assertion_scoped():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "tests"))
    tfn = next(p for p in prims if p["name"] == "test_add")
    tests = [e for e in tfn["edges_out"] if e["kind"] == "tests"]
    targets = {e["target"] for e in tests}
    assert "fixture::src/math.py::add" in targets
    assert "fixture::src/math.py::normalize" in targets
    # helper imported but called outside an assert — not a subject
    assert "fixture::src/test_helpers.py::make_fixture" not in targets
