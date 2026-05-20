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


def test_extends_resolves_through_package_barrel_reexport_py():
    """`from pkg import BaseModel` where pkg/__init__.py does
    `from .base import BaseModel` — the imports pass chases the re-export
    (see commit 03eb61f) so extends should land on the defining symbol."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_via_import"))
    session = next(p for p in prims if p["name"] == "Session")
    ex = [e for e in session["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "fixture::pkg/base.py::BaseModel"
               and e["confidence"] == "exact" for e in ex), ex


def test_extends_attribute_base_in_corpus_module_py():
    """`import base; class X(base.BaseModel)` — module is in-corpus,
    attr resolves to the class via the module's symbol table."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_attribute_base"))
    cls = next(p for p in prims if p["name"] == "FromInCorpusModule")
    ex = [e for e in cls["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "fixture::base.py::BaseModel"
               and e["confidence"] == "exact"
               for e in ex), ex


def test_extends_attribute_base_external_module_py():
    """`import sqlalchemy; class X(sqlalchemy.Base)` — external module +
    attr → `external::pypi::sqlalchemy::Base` (synthesized) with
    `unresolved` confidence matching the upstream import."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_attribute_base"))
    cls = next(p for p in prims if p["name"] == "FromExternalModule")
    ex = [e for e in cls["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "external::pypi::sqlalchemy::Base"
               and e["confidence"] == "unresolved"
               for e in ex), ex


def test_extends_attribute_base_unknown_attr_falls_back_py():
    """In-corpus module + non-existent attr → falls through to the
    unresolved sentinel rather than crashing or emitting a wrong-shape
    edge."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_attribute_base"))
    cls = next(p for p in prims if p["name"] == "FromInCorpusUnknownAttr")
    ex = [e for e in cls["edges_out"] if e["kind"] == "extends"]
    # The attr lookup misses (NotARealClass isn't defined in base.py),
    # so resolution falls through to the leaf-name `_name_from_base`
    # path, which returns "NotARealClass" and then hits the unknown
    # sentinel since nothing named NotARealClass is in scope.
    assert any(e["target"] == "external::pypi::unknown::NotARealClass"
               and e["confidence"] == "unresolved"
               for e in ex), ex


def test_extends_external_keeps_pkg_attribution_py():
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "inheritance_external"))
    item = next(p for p in prims if p["name"] == "Item")
    ex = [e for e in item["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "external::pypi::pydantic::BaseModel"
               and e["confidence"] == "unresolved" for e in ex), ex


def test_extends_attribute_base_multilevel_py():
    """`import sqlalchemy.orm; class X(sqlalchemy.orm.DeclarativeBase)` —
    base AST is `Attribute(Attribute(Name("sqlalchemy"), "orm"),
    "DeclarativeBase")`. Walker chases the chain to the root Name and
    uses `sqlalchemy` (the actual local binding) to look up the imports
    table — same target shape as the single-level external case."""
    prims = list(extract_repo(
        repo_key="fixture",
        repo_path=FIXTURE_DIR / "inheritance_multilevel_attribute_base",
    ))
    cls = next(p for p in prims if p["name"] == "Account")
    ex = [e for e in cls["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "external::pypi::sqlalchemy::DeclarativeBase"
               and e["confidence"] == "unresolved"
               for e in ex), ex


def test_extends_builtin_base_py():
    """`class Membership(list)` — `list` isn't in the imports table
    (implicit at runtime), so the inheritance pass needs to recognize
    it as a builtin and emit `external::builtins::list` rather than
    `external::pypi::unknown::list`."""
    prims = list(extract_repo(
        repo_key="fixture", repo_path=FIXTURE_DIR / "inheritance_builtin_base"
    ))
    cls = next(p for p in prims if p["name"] == "Membership")
    ex = [e for e in cls["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "external::builtins::list"
               and e["confidence"] == "unresolved"
               for e in ex), ex
    # Sanity: the same fixture's `MembershipError(Exception)` uses the
    # same path — confirms the set covers both container and exception
    # builtins.
    err_cls = next(p for p in prims if p["name"] == "MembershipError")
    err_ex = [e for e in err_cls["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "external::builtins::Exception"
               and e["confidence"] == "unresolved"
               for e in err_ex), err_ex


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


# Method calls on receivers typed by external classes route through the
# imports table to an `external::pypi::<pkg>::<class>::<method>` target.
# Confidence is `unresolved` to match the source import chain — the
# upstream `from pkg import X` edge is itself unresolved (we never parsed
# the package), so building an `exact` downstream edge would overclaim.

def test_method_call_external_param_annotation_py():
    """`db: Session` from sqlalchemy.orm — `db.query()` targets
    `external::pypi::sqlalchemy::Session::query` with `unresolved`."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "list_users")
    calls = [e for e in fn["edges_out"] if e["kind"] == "calls"]
    assert any(
        e["target"] == "external::pypi::sqlalchemy::Session::query"
        and e["confidence"] == "unresolved"
        and e["via"] == "method_call"
        for e in calls
    ), calls
    # Should NOT contain the pre-fix unresolved shape on `db`.
    assert not any(
        e["target"].startswith("external::unresolved::db.") for e in calls
    ), calls


def test_method_call_external_param_emits_multiple_methods_py():
    """Two distinct method calls on the same external-typed receiver
    each emit a separate edge — confirms the resolver isn't deduplicating
    by receiver."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "commit_tx")
    method_targets = {
        e["target"] for e in fn["edges_out"]
        if e["kind"] == "calls" and e["via"] == "method_call"
    }
    assert "external::pypi::sqlalchemy::Session::add" in method_targets
    assert "external::pypi::sqlalchemy::Session::commit" in method_targets


def test_method_call_annotated_param_py():
    """`db: Annotated[Session, ...]` (the FastAPI Depends shape) — the
    annotation root walker pulls Session out of the Annotated wrapper."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "annotated_param")
    calls = [e for e in fn["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "external::pypi::sqlalchemy::Session::refresh"
               and e["confidence"] == "unresolved"
               for e in calls), calls


def test_method_call_optional_param_py():
    """`db: Optional[Session]` — same unwrap as Annotated."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "optional_param")
    calls = [e for e in fn["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "external::pypi::sqlalchemy::Session::flush"
               and e["confidence"] == "unresolved"
               for e in calls), calls


def test_method_call_external_param_different_pkg_py():
    """APIRouter from fastapi — confirms the resolver routes attribution
    to the importing package, not just `sqlalchemy`."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "register")
    calls = [e for e in fn["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "external::pypi::fastapi::APIRouter::get"
               and e["confidence"] == "unresolved"
               for e in calls), calls


def test_method_call_annassign_external_class_py():
    """`db: Session = _get_session()` inside a function — AnnAssign also
    seeds var_types from the external-typed annotation."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "reassigned")
    calls = [e for e in fn["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "external::pypi::sqlalchemy::Session::rollback"
               and e["confidence"] == "unresolved"
               for e in calls), calls


def test_method_call_pattern2_external_constructor_py():
    """`db = Session(); db.query(...)` — Pattern 2 (assignment from a
    constructor) now seeds var_types for external-shaped class targets,
    matching the symmetry Pattern 1 (AnnAssign) already had."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "constructed")
    calls = [e for e in fn["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "external::pypi::sqlalchemy::Session::query"
               and e["confidence"] == "unresolved"
               and e["via"] == "method_call"
               for e in calls), calls
    # Should NOT contain the pre-fix unresolved-on-`db` shape.
    assert not any(
        e["target"].startswith("external::unresolved::db.")
        and e["via"] == "method_call"
        for e in calls
    ), calls


def test_method_call_union_receiver_emits_per_branch_py():
    """`x: Union[Session, Connection]; x.execute(...)` emits one edge per
    Union branch — each at `unresolved` since external method existence
    isn't verified, but the reverse index sees both classes as consumers."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "method_call_external_recv"))
    fn = next(p for p in prims if p["name"] == "union_recv")
    method_targets = {
        e["target"] for e in fn["edges_out"]
        if e["kind"] == "calls" and e["via"] == "method_call"
    }
    assert "external::pypi::sqlalchemy::Session::execute" in method_targets
    assert "external::pypi::sqlalchemy::Connection::execute" in method_targets


# Annotation walker missing-cases: string forward refs, builtin
# receivers, and `typing.X` builtin aliases. All exercise the
# `_annotation_root_names` / `_annotation_class_ids` resolution.

def _annotation_walker_calls(fn_name: str) -> list[dict]:
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "annotation_walker_cases"))
    fn = next(p for p in prims if p["name"] == fn_name)
    return [e for e in fn["edges_out"] if e["kind"] == "calls"]


def test_method_call_string_forward_ref_py():
    """`db: 'Session'` resolves like the unquoted form."""
    calls = _annotation_walker_calls("string_forward_ref")
    assert any(e["target"] == "external::pypi::sqlalchemy::Session::flush"
               and e["confidence"] == "unresolved"
               for e in calls), calls


def test_method_call_string_forward_ref_wrapped_py():
    """`db: 'Optional[Session]'` — walker parses the string and unwraps."""
    calls = _annotation_walker_calls("string_forward_ref_wrapped")
    assert any(e["target"] == "external::pypi::sqlalchemy::Session::commit"
               and e["confidence"] == "unresolved"
               for e in calls), calls


def test_method_call_builtin_list_py():
    """`xs: list; xs.append(...)` attributes to `external::builtins::list`."""
    calls = _annotation_walker_calls("builtin_list")
    assert any(e["target"] == "external::builtins::list::append"
               and e["confidence"] == "unresolved"
               and e["via"] == "method_call"
               for e in calls), calls


def test_method_call_builtin_dict_py():
    """`m: dict; m.get(...)` attributes to `external::builtins::dict`."""
    calls = _annotation_walker_calls("builtin_dict")
    assert any(e["target"] == "external::builtins::dict::get"
               for e in calls), calls


def test_method_call_pep585_generic_py():
    """`xs: list[int]` — non-transparent generic; container type is `list`."""
    calls = _annotation_walker_calls("pep585_generic")
    assert any(e["target"] == "external::builtins::list::append"
               for e in calls), calls


def test_method_call_typing_list_import_form_py():
    """`from typing import List; xs: List[int]` — alias rewrites to `list`,
    not `external::pypi::typing::List`."""
    calls = _annotation_walker_calls("typing_list_from_import")
    assert any(e["target"] == "external::builtins::list::append"
               for e in calls), calls
    assert not any(
        "typing::List" in e["target"] for e in calls
    ), f"typing.List leak: {calls}"


def test_method_call_typing_dict_import_form_py():
    """Same as List but for Dict."""
    calls = _annotation_walker_calls("typing_dict_from_import")
    assert any(e["target"] == "external::builtins::dict::get"
               for e in calls), calls


def test_method_call_typing_list_attribute_form_py():
    """`import typing; xs: typing.List[int]` — attribute-access form of
    the typing alias resolves to the builtin."""
    calls = _annotation_walker_calls("typing_list_via_attribute")
    assert any(e["target"] == "external::builtins::list::append"
               for e in calls), calls


def test_method_call_in_corpus_unknown_method_still_unresolved_py():
    """Regression guard: in-corpus class + method-not-on-class should
    keep emitting the unresolved sentinel — only the external-receiver
    path changes."""
    prims = list(extract_repo(repo_key="fixture",
                              repo_path=FIXTURE_DIR / "calls"))
    handler = next(p for p in prims if p["name"] == "handler")
    calls = [e for e in handler["edges_out"] if e["kind"] == "calls"]
    # `Service.do_work` resolves exact (it exists). Sanity-check that the
    # taxonomy invariant holds: every method_call edge from `handler` is
    # either an in-corpus method id or an unresolved sentinel.
    for e in calls:
        if e["via"] != "method_call":
            continue
        assert (e["confidence"] == "exact"
                and e["target"] == "fixture::src.py::Service.do_work") or \
               (e["confidence"] == "unresolved"
                and e["target"].startswith("external::unresolved::")), e


def test_method_call_walrus_receiver_py():
    """`if db := Session(): db.query(...)` — `ast.NamedExpr` now seeds
    var_types the same way Pattern 2 (`x = SomeClass()`) does, so the
    downstream `db.query` attributes to
    `external::pypi::sqlalchemy::Session::query` instead of the
    `external::unresolved::db.query` sentinel."""
    prims = list(extract_repo(
        repo_key="fixture",
        repo_path=FIXTURE_DIR / "walrus_operator_receiver",
    ))
    fn = next(p for p in prims if p["name"] == "use_walrus")
    calls = [e for e in fn["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "external::pypi::sqlalchemy::Session::query"
               and e["confidence"] == "unresolved"
               and e["via"] == "method_call"
               for e in calls), calls
    # And the pre-fix unresolved-on-`db` shape must NOT be present.
    assert not any(
        e["target"].startswith("external::unresolved::db.")
        and e["via"] == "method_call"
        for e in calls
    ), calls


def test_method_call_vararg_kwarg_annotations_py():
    """`def fan_out(*conns: Connection, **opts: Order)` — both `vararg`
    and `kwarg` annotations now seed var_types. Receiver semantics are
    a simplification (runtime is `tuple[Connection, ...]` /
    `dict[str, Order]`) — see fixture docstring — but the bound name
    type maps to the annotation target, which is the minimal correct
    first step."""
    prims = list(extract_repo(
        repo_key="fixture",
        repo_path=FIXTURE_DIR / "vararg_kwarg_annotations",
    ))
    fn = next(p for p in prims if p["name"] == "fan_out")
    method_targets = {
        e["target"] for e in fn["edges_out"]
        if e["kind"] == "calls" and e["via"] == "method_call"
    }
    # `conns.append(...)` — vararg-annotated receiver
    assert "external::pypi::sqlalchemy::Connection::append" in method_targets, (
        method_targets
    )
    # `opts.commit()` — kwarg-annotated receiver
    assert "external::pypi::app::Order::commit" in method_targets, (
        method_targets
    )
    # Pre-fix sentinels must NOT appear for either name.
    assert not any(
        e["target"].startswith("external::unresolved::conns.")
        for e in fn["edges_out"]
    ), fn["edges_out"]
    assert not any(
        e["target"].startswith("external::unresolved::opts.")
        for e in fn["edges_out"]
    ), fn["edges_out"]


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
