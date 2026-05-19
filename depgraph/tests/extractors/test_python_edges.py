"""Python edge extractor in-process tests — Phase 3.

Each test calls extract_repo against a small fixture under
fixtures/edges_py/<scenario>/ and asserts on edges emitted.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.edges import validate_edge

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


def test_extends_resolves_via_relative_import_py():
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_via_import"))
    user = next(p for p in prims if p["name"] == "User")
    ex = [e for e in user["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "fixture::pkg/base.py::BaseModel"
               and e["confidence"] == "exact" for e in ex), ex


def test_extends_resolves_via_absolute_import_py():
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_via_import"))
    account = next(p for p in prims if p["name"] == "Account")
    ex = [e for e in account["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "fixture::pkg/base.py::BaseModel"
               and e["confidence"] == "exact" for e in ex), ex


def test_extends_external_keeps_pkg_attribution_py():
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_external"))
    item = next(p for p in prims if p["name"] == "Item")
    ex = [e for e in item["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "external::pypi::pydantic::BaseModel"
               and e["confidence"] == "unresolved" for e in ex), ex


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


def test_decorates_edge_variable_source_framework_pattern_py():
    """Framework-style `@router.get("/x")` anchors the `decorates` edge to
    the module-level `router` variable. The edge target is the decorated
    function. Schema (#30) allows variable sources for this pattern."""
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    decorated = next(p for p in prims if p["name"] == "framework_decorated")
    router = next(p for p in prims if p["name"] == "router")
    assert router["primitive"] == "variable"

    incoming = [
        e for e in router["edges_out"]
        if e["kind"] == "decorates" and e["target"] == decorated["id"]
    ]
    assert incoming, "expected a decorates edge from router (variable) to framework_decorated"

    # The schema must accept this edge — validate it end-to-end.
    for e in incoming:
        errors = validate_edge({**e, "source_kind": router["primitive"],
                                       "target_kind": decorated["primitive"]})
        assert errors == [], errors


def test_decorates_edge_skips_module_source_py():
    """When a decorator name resolves through the imports map to a module
    id (rather than a specific symbol), the extractor must NOT emit a
    `decorates` edge — modules can't be decorators (#30)."""
    from depgraph.extractors.python.extract import _attach_decorator_edges

    primitives = [
        # A module that imports `something` from another module.
        {
            "id": "fixture::caller.py", "primitive": "module", "name": "caller.py",
            "owner": None, "source": {"path": "caller.py", "repo": "fixture",
                                         "language": "python", "line": 1, "end_line": 1},
            "signature": {}, "attributes": {}, "edges_out": [
                # imports edge whose target is a MODULE id (not a symbol).
                {"target": "fixture::pkg/__init__.py", "kind": "imports",
                 "local_binding": "something", "via": "import_from"},
            ],
        },
        # The module the import resolves to.
        {
            "id": "fixture::pkg/__init__.py", "primitive": "module", "name": "pkg/__init__.py",
            "owner": None, "source": {"path": "pkg/__init__.py", "repo": "fixture",
                                         "language": "python", "line": 1, "end_line": 1},
            "signature": {}, "attributes": {}, "edges_out": [],
        },
        # A function in caller.py that uses `@something` as a decorator.
        {
            "id": "fixture::caller.py::decorated_fn", "primitive": "function",
            "name": "decorated_fn", "owner": None,
            "source": {"path": "caller.py", "repo": "fixture",
                       "language": "python", "line": 10, "end_line": 12},
            "signature": {"decorators": ["something"]},
            "attributes": {}, "edges_out": [],
        },
    ]
    imports_by_path = {"caller.py": {"something": "fixture::pkg/__init__.py"}}

    _attach_decorator_edges(primitives, trees_by_path={},
                            imports_by_path=imports_by_path)

    # No decorates edge on the module — modules are never valid decorator sources.
    pkg_module = next(p for p in primitives if p["id"] == "fixture::pkg/__init__.py")
    decorates_on_module = [e for e in pkg_module["edges_out"] if e["kind"] == "decorates"]
    assert decorates_on_module == [], (
        f"module source must not emit decorates edges, got: {decorates_on_module}"
    )


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


# ---------------------------------------------------------------------------
# Blocker 1: absolute ImportFrom resolution
# ---------------------------------------------------------------------------

def test_absolute_import_resolves_to_internal_module(tmp_path):
    """from services.widget import create_widget → edge target is the
    create_widget function primitive inside services/widget.py."""
    (tmp_path / "services").mkdir()
    (tmp_path / "services" / "__init__.py").write_text("")
    (tmp_path / "services" / "widget.py").write_text(
        "def create_widget(): pass\n"
    )
    (tmp_path / "routers").mkdir()
    (tmp_path / "routers" / "__init__.py").write_text("")
    (tmp_path / "routers" / "widget.py").write_text(
        "from services.widget import create_widget\n"
        "def use_widget(): create_widget()\n"
    )
    prims = list(extract_repo(repo_key="fixture", repo_path=tmp_path))
    router_mod = next(
        p for p in prims
        if p["primitive"] == "module" and p["source"]["path"] == "routers/widget.py"
    )
    import_edges = [e for e in router_mod["edges_out"] if e["kind"] == "imports"]
    targets = {e["target"] for e in import_edges}
    # Should resolve to the function primitive, not the module
    assert "fixture::services/widget.py::create_widget" in targets, (
        f"expected create_widget function primitive in targets; got {targets}"
    )


def test_absolute_external_import_yields_external_terminal(tmp_path):
    """from sqlalchemy import text → edge target external::pypi::sqlalchemy::text."""
    (tmp_path / "db.py").write_text("from sqlalchemy import text\n")
    prims = list(extract_repo(repo_key="fixture", repo_path=tmp_path))
    mod = next(p for p in prims if p["source"]["path"] == "db.py"
               and p["primitive"] == "module")
    import_edges = [e for e in mod["edges_out"] if e["kind"] == "imports"]
    targets = {e["target"] for e in import_edges}
    assert "external::pypi::sqlalchemy::text" in targets, (
        f"expected external terminal; got {targets}"
    )


def test_absolute_aliased_import_captures_local_binding(tmp_path):
    """from sqlalchemy import text as t → local_binding='t'."""
    (tmp_path / "db.py").write_text("from sqlalchemy import text as t\n")
    prims = list(extract_repo(repo_key="fixture", repo_path=tmp_path))
    mod = next(p for p in prims if p["source"]["path"] == "db.py"
               and p["primitive"] == "module")
    edge = next(
        (e for e in mod["edges_out"]
         if e["kind"] == "imports" and "sqlalchemy" in e["target"]),
        None,
    )
    assert edge is not None, "expected an imports edge for sqlalchemy::text"
    assert edge["local_binding"] == "t", (
        f"expected local_binding='t'; got {edge['local_binding']!r}"
    )


# ---------------------------------------------------------------------------
# Task 3.7: Edge schema validation sweep
# ---------------------------------------------------------------------------

def _load_all_py_fixtures() -> list[dict]:
    """Load primitives from all edges_py fixtures into one flat list."""
    all_prims: list[dict] = []
    for scenario in FIXTURE_DIR.iterdir():
        if not scenario.is_dir():
            continue
        all_prims.extend(extract_repo(repo_key="fixture", repo_path=scenario))
    return all_prims


def test_all_emitted_edges_validate():
    """Every edge emitted by any Python fixture must pass schema validation.

    Builds (source_kind, target_kind) from the corpus's primitives_by_id,
    passes each edge through validate_edge. External terminals (unresolved
    targets) have target_kind=None, which validate_edge allows.
    """
    prims = _load_all_py_fixtures()
    primitives_by_id = {p["id"]: p for p in prims}

    errors_found = []
    for p in prims:
        for e in p["edges_out"]:
            validation_input = {**e, "source_kind": p["primitive"]}
            tgt = primitives_by_id.get(e["target"])
            if tgt:
                validation_input["target_kind"] = tgt["primitive"]
            errs = validate_edge(validation_input)
            if errs:
                errors_found.append((p["id"], e["target"], errs))

    assert not errors_found, (
        f"{len(errors_found)} edge(s) failed validation:\n"
        + "\n".join(f"  {src} -> {tgt}: {errs}"
                    for src, tgt, errs in errors_found[:10])
    )
