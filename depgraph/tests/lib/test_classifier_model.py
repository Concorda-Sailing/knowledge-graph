"""Tests for the model classifier (Task 5.6)."""
from depgraph.lib.classification.engine import classify_corpus


def _user_class(edges_out):
    return {
        "id": "r::models/user.py::User", "primitive": "class", "name": "User",
        "owner": None,
        "source": {"path": "models/user.py", "line": 1, "end_line": 1,
                   "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": edges_out, "structural_hash": "0", "kind": None,
        "extractor": "t", "schema_version": 2,
    }


def _users_schema():
    return {
        "id": "r::schema::users", "primitive": "class", "name": "users",
        "owner": None,
        "source": {"path": "schema/users", "line": 1, "end_line": 1,
                   "language": "sql", "repo": "r"},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "t", "schema_version": 2,
    }


def test_orm_class_with_schema_reference_is_model():
    user = _user_class([
        {"target": "external::pypi::sqlalchemy::Base", "kind": "extends",
         "via": "class_decl", "where": "models/user.py:1", "confidence": "exact"},
        {"target": "r::schema::users", "kind": "references",
         "via": "__tablename__", "where": "models/user.py:2", "confidence": "exact"},
    ])
    decisions = classify_corpus([user, _users_schema()])
    assert decisions[user["id"]].kind == "model"
    # schema primitive's kind was set by the extractor; classifier must not change it
    assert decisions["r::schema::users"].kind == "schema"


def test_orm_class_without_schema_reference_is_not_model():
    """Extends Base but no references edge — treated as orphan mapper."""
    user = _user_class([
        {"target": "external::pypi::sqlalchemy::Base", "kind": "extends",
         "via": "class_decl", "where": "models/user.py:1", "confidence": "exact"},
    ])
    decisions = classify_corpus([user])
    assert decisions[user["id"]].kind != "model"


def test_schema_primitive_not_classified_as_model():
    schema = _users_schema()
    decisions = classify_corpus([schema])
    assert decisions[schema["id"]].kind == "schema"


def test_class_with_schema_reference_but_no_orm_extends_is_not_model():
    """References a schema via type_hint alone — no ORM base → not model."""
    cls = _user_class([
        {"target": "r::schema::users", "kind": "references",
         "via": "type_hint", "where": "models/user.py:1", "confidence": "exact"},
    ])
    decisions = classify_corpus([cls, _users_schema()])
    assert decisions[cls["id"]].kind != "model"


def test_orm_class_with_typehint_only_reference_is_not_model():
    """Extends Base AND references schema, but via=return_type_annotation —
    that's incidental, not an ORM mapping. The distinguishing marker is
    via in config.orm_schema_link_vias (default: {"__tablename__"})."""
    user = _user_class([
        {"target": "external::pypi::sqlalchemy::Base", "kind": "extends",
         "via": "class_decl", "where": "models/user.py:1", "confidence": "exact"},
        {"target": "r::schema::users", "kind": "references",
         "via": "return_type_annotation", "where": "models/user.py:5",
         "confidence": "exact"},
    ])
    decisions = classify_corpus([user, _users_schema()])
    assert decisions[user["id"]].kind != "model"
