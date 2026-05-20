"""Coverage-caveats detector + registry tests (#55).

The detectors operate over the v2 primitive dict shape — same
`primitive`/`name`/`edges_out`/`signature` keys the extractors emit.
We build small in-memory primitives rather than running extraction so
the test stays focused on the predicate logic.
"""
from __future__ import annotations

import pytest

from depgraph.lib.coverage_caveats import (
    CAVEAT_REGISTRY,
    aggregate_caveat_counts,
    caveat_description,
    caveat_title,
    stamp_caveats,
)


def _class(id_: str, *, extends: list[str] | None = None) -> dict:
    """Minimal class primitive — just enough for the detectors."""
    return {
        "id": id_,
        "primitive": "class",
        "name": id_.rsplit("::", 1)[-1],
        "signature": {},
        "edges_out": [
            {"target": t, "kind": "extends", "via": "class_extends",
             "confidence": "exact", "where": "?"}
            for t in (extends or [])
        ],
    }


def _function(id_: str, *, route: tuple[str, str] | None = None) -> dict:
    sig: dict = {}
    if route is not None:
        sig["method"], sig["path"] = route
    return {
        "id": id_,
        "primitive": "function",
        "name": id_.rsplit("::", 1)[-1],
        "signature": sig,
        "edges_out": [],
    }


# ---------------------------------------------------------------------------
# Registry contract
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(CAVEAT_REGISTRY))
def test_every_registered_caveat_has_title_and_description(name):
    title, desc = CAVEAT_REGISTRY[name]
    assert title and isinstance(title, str)
    assert desc and isinstance(desc, str)
    assert caveat_title(name) == title
    assert caveat_description(name) == desc


def test_caveat_lookups_for_unknown_name_fall_back_safely():
    # Title falls back to the enum (so the dossier still renders something
    # readable if an extractor stamps an unregistered value).
    assert caveat_title("totally_made_up") == "totally_made_up"
    assert caveat_description("totally_made_up") is None


# ---------------------------------------------------------------------------
# SQLAlchemy detector
# ---------------------------------------------------------------------------

def test_class_extending_declarativebase_directly_is_sqla_model():
    boat = _class("api::models/boat.py::Boat",
                  extends=["external::pypi::sqlalchemy::DeclarativeBase"])
    n = stamp_caveats([boat])
    assert n == 1
    assert "orm_relationships_not_extracted" in boat["coverage_caveats"]
    assert "fk_references_not_extracted" in boat["coverage_caveats"]


def test_class_extending_base_via_in_corpus_resolves_transitively():
    """Project convention: `Base = declarative_base()`, then every model
    extends `Base`. The framework's barrel-reexport / inheritance resolver
    sets the `extends` target to the in-corpus `Base` class id — which in
    turn extends the SQLAlchemy `DeclarativeBase`. The detector must
    chase the chain."""
    base = _class("api::models/base.py::Base",
                  extends=["external::pypi::sqlalchemy::DeclarativeBase"])
    boat = _class("api::models/boat.py::Boat",
                  extends=["api::models/base.py::Base"])
    stamp_caveats([base, boat])
    assert "orm_relationships_not_extracted" in boat["coverage_caveats"]
    # The Base class itself is also a SQLA model in this taxonomy — that's
    # correct: it inherits DeclarativeBase directly.
    assert "orm_relationships_not_extracted" in base["coverage_caveats"]


def test_plain_class_gets_no_orm_caveat():
    plain = _class("api::util/timer.py::Timer", extends=[])
    n = stamp_caveats([plain])
    assert n == 0
    assert "coverage_caveats" not in plain


def test_class_extending_unrelated_thing_gets_no_orm_caveat():
    """Avoid false positives — extending an unrelated base must not stamp."""
    sub = _class("api::services/foo.py::Foo",
                 extends=["external::pypi::abc::ABC"])
    n = stamp_caveats([sub])
    assert n == 0


# ---------------------------------------------------------------------------
# Pydantic detector
# ---------------------------------------------------------------------------

def test_class_extending_basemodel_is_pydantic():
    user = _class("api::schemas/user.py::User",
                  extends=["external::pypi::pydantic::BaseModel"])
    stamp_caveats([user])
    assert "pydantic_refs_not_extracted" in user["coverage_caveats"]


def test_class_can_carry_both_orm_and_pydantic_caveats_independently():
    """A class that somehow inherits from both surfaces both gaps; the
    detector doesn't claim mutual exclusion."""
    weird = _class("api::weird/x.py::X",
                   extends=[
                       "external::pypi::sqlalchemy::DeclarativeBase",
                       "external::pypi::pydantic::BaseModel",
                   ])
    stamp_caveats([weird])
    cs = weird["coverage_caveats"]
    assert "orm_relationships_not_extracted" in cs
    assert "pydantic_refs_not_extracted" in cs


# ---------------------------------------------------------------------------
# FastAPI endpoint detector
# ---------------------------------------------------------------------------

def test_function_with_route_signature_gets_fastapi_caveat():
    ep = _function("api::routers/users.py::get_me",
                   route=("GET", "/api/users/me"))
    stamp_caveats([ep])
    assert "fastapi_depends_chain_not_traced" in ep["coverage_caveats"]


def test_plain_function_gets_no_fastapi_caveat():
    fn = _function("api::util/timer.py::now", route=None)
    n = stamp_caveats([fn])
    assert n == 0


# ---------------------------------------------------------------------------
# Typed-receiver-unresolved detector (#78)
# ---------------------------------------------------------------------------

def _function_with_edges(id_: str, *, edges: list[dict]) -> dict:
    """Function primitive with caller-supplied outgoing edges — used to
    exercise the unresolved-receiver detector without going through the
    full extractor."""
    return {
        "id": id_,
        "primitive": "function",
        "name": id_.rsplit("::", 1)[-1],
        "signature": {},
        "edges_out": edges,
    }


def test_method_call_to_external_unresolved_gets_typed_receiver_caveat():
    """Positive case: an outgoing `method_call` edge whose target lives
    under `external::unresolved::` is exactly the shape the extractor
    emits when it couldn't infer the receiver's type."""
    fn = _function_with_edges(
        "api::services/foo.py::do_work",
        edges=[
            {"target": "external::unresolved::db.query",
             "kind": "calls", "via": "method_call",
             "confidence": "unresolved", "where": "foo.py:5"},
        ],
    )
    stamp_caveats([fn])
    assert "typed_receiver_unresolved" in fn["coverage_caveats"]


def test_resolved_method_call_does_not_stamp_typed_receiver_caveat():
    """Negative case: a `method_call` edge that resolved to an in-corpus
    target must not trigger the caveat — the gap the caveat names isn't
    present."""
    fn = _function_with_edges(
        "api::services/foo.py::do_work",
        edges=[
            {"target": "api::models/user.py::User.save",
             "kind": "calls", "via": "method_call",
             "confidence": "exact", "where": "foo.py:5"},
        ],
    )
    n = stamp_caveats([fn])
    assert n == 0
    assert "coverage_caveats" not in fn


def test_non_method_call_external_unresolved_does_not_stamp():
    """The detector is specific to `via=method_call` — an unresolved
    import or other edge kind targeting `external::unresolved::` must
    not stamp the receiver caveat (that's a different gap)."""
    fn = _function_with_edges(
        "api::services/foo.py::do_work",
        edges=[
            {"target": "external::unresolved::some_module",
             "kind": "imports", "via": "import",
             "confidence": "unresolved", "where": "foo.py:1"},
        ],
    )
    n = stamp_caveats([fn])
    assert n == 0


def test_typed_receiver_caveat_is_idempotent():
    """Re-stamping a primitive that already carries the caveat must not
    produce a duplicate entry."""
    fn = _function_with_edges(
        "api::services/foo.py::do_work",
        edges=[
            {"target": "external::unresolved::db.query",
             "kind": "calls", "via": "method_call",
             "confidence": "unresolved", "where": "foo.py:5"},
        ],
    )
    stamp_caveats([fn])
    first = list(fn["coverage_caveats"])
    stamp_caveats([fn])
    assert fn["coverage_caveats"] == first
    assert fn["coverage_caveats"].count("typed_receiver_unresolved") == 1


def test_typed_receiver_caveat_coexists_with_fastapi_caveat():
    """A FastAPI endpoint that also has unresolved method calls gets
    both caveats — detectors are independent."""
    ep = _function(
        "api::routers/users.py::get_me",
        route=("GET", "/api/users/me"),
    )
    ep["edges_out"] = [
        {"target": "external::unresolved::session.commit",
         "kind": "calls", "via": "method_call",
         "confidence": "unresolved", "where": "users.py:7"},
    ]
    stamp_caveats([ep])
    cs = ep["coverage_caveats"]
    assert "fastapi_depends_chain_not_traced" in cs
    assert "typed_receiver_unresolved" in cs


# ---------------------------------------------------------------------------
# Stamping is idempotent + sorted
# ---------------------------------------------------------------------------

def test_stamp_caveats_is_idempotent_and_sorted():
    """Re-running on a corpus that already has caveats stamped produces
    the same list. Pre-existing caveats are preserved (e.g. ones stamped
    by a future external detector)."""
    boat = _class("api::models/boat.py::Boat",
                  extends=["external::pypi::sqlalchemy::DeclarativeBase"])
    stamp_caveats([boat])
    first = list(boat["coverage_caveats"])
    stamp_caveats([boat])
    assert boat["coverage_caveats"] == first
    assert boat["coverage_caveats"] == sorted(boat["coverage_caveats"])


def test_stamp_preserves_externally_stamped_caveats():
    """If a later plugin stamps a custom caveat, the framework's
    re-stamping pass must not strip it."""
    boat = _class("api::models/boat.py::Boat",
                  extends=["external::pypi::sqlalchemy::DeclarativeBase"])
    boat["coverage_caveats"] = ["custom_plugin_caveat"]
    stamp_caveats([boat])
    assert "custom_plugin_caveat" in boat["coverage_caveats"]
    assert "orm_relationships_not_extracted" in boat["coverage_caveats"]


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def test_aggregate_caveat_counts():
    a = _class("api::a::A", extends=["external::pypi::sqlalchemy::DeclarativeBase"])
    b = _class("api::b::B", extends=["external::pypi::sqlalchemy::DeclarativeBase"])
    c = _class("api::c::C", extends=["external::pypi::pydantic::BaseModel"])
    stamp_caveats([a, b, c])
    counts = aggregate_caveat_counts([a, b, c])
    assert counts["orm_relationships_not_extracted"] == 2
    assert counts["fk_references_not_extracted"] == 2
    assert counts["pydantic_refs_not_extracted"] == 1
