"""ORM detector and edge extraction: metaclass-based base classes
plus annotation-encoded relationship targets (#84).

Two related gaps the issue body calls out:

1. The canonical `_attach_orm_edges` path walks classes that
   transitively extend a known SQLAlchemy base name. Frameworks that
   plumb declarative wiring through a custom metaclass instead of
   inheritance never reach those names, so the only
   inheritance-agnostic ORM signal is the class-body
   `__tablename__ = "..."` assignment.

2. Some frameworks (SQLModel, etc.) encode the relationship target
   in the annotation rather than as a positional arg to the
   relationship call: `team: Team | None = Relationship(...)`. The
   canonical resolver expects a positional arg; this extra branch
   mines the target from the annotation.

Both fixtures use generic Account/Membership/Order shapes — no
framework-specific names — so the tests pin the wire shape, not a
particular consumer project.
"""
from __future__ import annotations

from pathlib import Path

from depgraph.extractors.python.extract import extract_repo

FIXTURE_DIR = (Path(__file__).parent / "fixtures" / "edges_py"
               / "orm_metaclass_base")
ANNOTATION_FIXTURE_DIR = (Path(__file__).parent / "fixtures" / "edges_py"
                          / "orm_annotation_target")


def _load_fixture() -> list[dict]:
    return list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR))


def _load_annotation_fixture() -> list[dict]:
    return list(extract_repo(repo_key="fixture",
                              repo_path=ANNOTATION_FIXTURE_DIR))


def test_metaclass_base_subclass_emits_references_orm():
    """`Account` extends `HybridBase` (metaclass-driven, no SQLAlchemy
    base in its MRO). The class body declares `__tablename__` and
    calls `relationship(Membership, ...)` — the extractor must treat
    the class as an ORM model on the tablename signal alone and emit
    the references_orm edge."""
    prims = _load_fixture()
    account = next(p for p in prims if p["name"] == "Account")
    ref_targets = {e["target"] for e in account["edges_out"]
                   if e["kind"] == "references_orm"}
    assert "fixture::models/membership.py::Membership" in ref_targets, ref_targets
    assert "fixture::models/order.py::Order" in ref_targets, ref_targets


def test_metaclass_base_subclass_emits_references_table_fk():
    """`Membership.account_id = Column(Integer, ForeignKey("accounts.id"))`
    must resolve to the `Account` class via the corpus-wide
    `__tablename__` index — confirms FK extraction also fires for
    tablename-only-detected models."""
    prims = _load_fixture()
    membership = next(p for p in prims if p["name"] == "Membership")
    fk_targets = {e["target"] for e in membership["edges_out"]
                  if e["kind"] == "references_table"}
    assert "fixture::models/account.py::Account" in fk_targets, fk_targets


def test_metaclass_base_itself_not_walked():
    """`HybridBase` has no `__tablename__` and extends nothing
    SQLAlchemy-flavoured — it must NOT accumulate references_orm /
    references_table edges itself, even though it sits at the top of
    the ORM family in the corpus."""
    prims = _load_fixture()
    base = next(p for p in prims if p["name"] == "HybridBase")
    orm_like = [e for e in base["edges_out"]
                if e["kind"] in {"references_orm", "references_table"}]
    assert orm_like == [], orm_like


# ---------------------------------------------------------------------------
# Annotation-encoded relationship targets (SQLModel-style #84)
# ---------------------------------------------------------------------------

def test_annotation_subscript_resolves_in_file_class():
    """`memberships: list[Membership] = Relationship(...)` — the
    annotation walker descends the Subscript and resolves `Membership`
    via the file's top-level symbol table. Same file as Account so the
    in-file path is exercised."""
    prims = _load_annotation_fixture()
    account = next(p for p in prims if p["name"] == "Account")
    ref_targets = {e["target"] for e in account["edges_out"]
                   if e["kind"] == "references_orm"}
    assert "fixture::models/membership.py::Membership" in ref_targets, ref_targets


def test_annotation_subscript_resolves_forward_ref_string():
    """`orders: list["Order"] = Relationship(...)` — forward-ref string
    inside a Subscript must resolve via the corpus-wide classname
    index (cross-file lookup)."""
    prims = _load_annotation_fixture()
    account = next(p for p in prims if p["name"] == "Account")
    ref_targets = {e["target"] for e in account["edges_out"]
                   if e["kind"] == "references_orm"}
    assert "fixture::models/order.py::Order" in ref_targets, ref_targets


def test_annotation_binop_resolves_class_drops_none():
    """`account: Account | None = Relationship(...)` — BinOp
    annotation; the walker visits both sides, filters `None` via the
    skip list, and resolves `Account`."""
    prims = _load_annotation_fixture()
    membership = next(p for p in prims if p["name"] == "Membership")
    ref_targets = {e["target"] for e in membership["edges_out"]
                   if e["kind"] == "references_orm"}
    assert "fixture::models/membership.py::Account" in ref_targets, ref_targets


def test_annotation_pass_does_not_double_emit_with_positional_arg():
    """When a `Relationship(...)` call has a positional arg, the
    annotation pass must skip — otherwise the same call site would
    accumulate two references_orm edges. We approximate this by
    confirming Account's edges are unique (no duplicates)."""
    prims = _load_annotation_fixture()
    account = next(p for p in prims if p["name"] == "Account")
    ref_edges = [e for e in account["edges_out"]
                 if e["kind"] == "references_orm"]
    targets = [e["target"] for e in ref_edges]
    assert len(targets) == len(set(targets)), targets
