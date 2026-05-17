"""Tests for the service classifier (Task 5.5)."""
from depgraph.lib.classification.engine import classify_corpus


def test_function_with_db_access_and_called_by_endpoint_is_service():
    endpoint_fn = {
        "id": "r::routers/x.py::handler", "primitive": "function", "name": "handler",
        "owner": None,
        "source": {"path": "routers/x.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.get"]}, "attributes": {},
        "edges_out": [{"target": "r::services/x.py::do_work", "kind": "calls",
                       "via": "fn", "where": "routers/x.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    service_fn = {
        "id": "r::services/x.py::do_work", "primitive": "function", "name": "do_work",
        "owner": None,
        "source": {"path": "services/x.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "external::pypi::sqlalchemy::Session.query", "kind": "db_access",
                       "via": "session.query", "where": "services/x.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    decisions = classify_corpus([endpoint_fn, service_fn])
    assert decisions["r::services/x.py::do_work"].kind == "service"


def test_function_with_db_access_not_reachable_from_endpoint_is_not_service():
    orphan = {
        "id": "r::lib/orphan.py::helper", "primitive": "function", "name": "helper",
        "owner": None,
        "source": {"path": "lib/orphan.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "external::pypi::sqlalchemy::Session.query", "kind": "db_access",
                       "via": "session.query", "where": "lib/orphan.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    decisions = classify_corpus([orphan])
    assert decisions["r::lib/orphan.py::helper"].kind != "service"
