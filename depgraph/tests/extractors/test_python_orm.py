"""SQLAlchemy ORM extractor pass (#54).

`_attach_orm_edges` walks classes that transitively extend a SQLAlchemy
ORM base and emits two new edge kinds:

  * `references_orm` — one per `relationship(Cls, ...)` /
    `relationship("Cls", ...)` call inside the class body.
  * `references_table` — one per `ForeignKey("table.col")` argument
    nested anywhere inside the class body (typically inside a
    `mapped_column(...)` Call).

These tests pin the four shapes the issue calls out (direct,
string-form, ForeignKey, and the negative case) plus a couple of
auxiliary guarantees (schema validation, idempotence-free seam with
the inheritance pass)."""
from __future__ import annotations

from pathlib import Path

from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.edges import validate_edge

FIXTURE_DIR = (Path(__file__).parent / "fixtures" / "edges_py"
               / "orm_relationships_and_fks")


def _load_orm_fixture() -> list[dict]:
    return list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR))


def test_relationship_direct_class_reference_emits_references_orm():
    """`relationship(Membership, ...)` in Account — the target is the
    in-corpus Membership class id."""
    prims = _load_orm_fixture()
    account = next(p for p in prims if p["name"] == "Account")
    ref_edges = [e for e in account["edges_out"]
                 if e["kind"] == "references_orm"]
    targets = {e["target"] for e in ref_edges}
    assert "fixture::models/membership.py::Membership" in targets, ref_edges
    # The relationship pass tags the via for downstream consumers.
    direct_edge = next(e for e in ref_edges
                       if e["target"] == "fixture::models/membership.py::Membership")
    assert direct_edge["via"] == "relationship_call"
    assert direct_edge["confidence"] == "exact"


def test_relationship_string_class_reference_emits_references_orm():
    """`relationship("Order", ...)` — string lookup against the
    corpus-wide classname index."""
    prims = _load_orm_fixture()
    account = next(p for p in prims if p["name"] == "Account")
    targets = {e["target"] for e in account["edges_out"]
               if e["kind"] == "references_orm"}
    assert "fixture::models/order.py::Order" in targets

    # And the reverse direction: Membership's string `relationship("Account", ...)`
    # resolves back to the Account class.
    membership = next(p for p in prims if p["name"] == "Membership")
    mb_targets = {e["target"] for e in membership["edges_out"]
                  if e["kind"] == "references_orm"}
    assert "fixture::models/account.py::Account" in mb_targets


def test_foreign_key_emits_references_table_edge():
    """`ForeignKey("accounts.id")` inside a mapped_column call resolves
    to the Account class id via the __tablename__ index."""
    prims = _load_orm_fixture()
    membership = next(p for p in prims if p["name"] == "Membership")
    fk_edges = [e for e in membership["edges_out"]
                if e["kind"] == "references_table"]
    targets = {e["target"] for e in fk_edges}
    assert "fixture::models/account.py::Account" in targets, fk_edges
    edge = next(e for e in fk_edges
                if e["target"] == "fixture::models/account.py::Account")
    assert edge["via"] == "foreign_key"
    assert edge["confidence"] == "exact"


def test_foreign_key_works_across_models():
    """Order also FKs to accounts — confirms the tablename index is
    corpus-wide rather than per-file."""
    prims = _load_orm_fixture()
    order = next(p for p in prims if p["name"] == "Order")
    fk_targets = {e["target"] for e in order["edges_out"]
                  if e["kind"] == "references_table"}
    assert "fixture::models/account.py::Account" in fk_targets


def test_non_orm_class_does_not_get_walked():
    """A class that does NOT inherit from a SQLAlchemy base must not
    accumulate `references_orm` / `references_table` edges, even when
    its body literally calls a function named `relationship(...)`."""
    prims = _load_orm_fixture()
    non_orm = next(p for p in prims if p["name"] == "NonOrmClass")
    orm_like_edges = [
        e for e in non_orm["edges_out"]
        if e["kind"] in {"references_orm", "references_table"}
    ]
    assert orm_like_edges == [], orm_like_edges


def test_orm_edges_validate_against_schema():
    """The two new edge kinds (`references_orm`, `references_table`)
    must be present in the EdgeKind taxonomy and validate cleanly with
    class -> class source/target."""
    prims = _load_orm_fixture()
    primitives_by_id = {p["id"]: p for p in prims}
    errors: list[tuple] = []
    for p in prims:
        if p["primitive"] != "class":
            continue
        for e in p["edges_out"]:
            if e["kind"] not in {"references_orm", "references_table"}:
                continue
            tgt = primitives_by_id.get(e["target"])
            errs = validate_edge({
                **e,
                "source_kind": p["primitive"],
                "target_kind": tgt["primitive"] if tgt else None,
            })
            if errs:
                errors.append((p["id"], e["target"], errs))
    assert not errors, errors


def test_orm_pass_does_not_emit_self_edges():
    """A relationship referencing the same class (e.g. tree-shaped
    self-joins like `parent = relationship("Account")` inside Account)
    must not produce a self-loop — the resolver explicitly drops the
    edge when source == target. Pinned defensively even though our
    fixture doesn't currently exercise the case."""
    prims = _load_orm_fixture()
    for p in prims:
        if p["primitive"] != "class":
            continue
        for e in p["edges_out"]:
            if e["kind"] in {"references_orm", "references_table"}:
                assert e["target"] != p["id"], (p["id"], e)
