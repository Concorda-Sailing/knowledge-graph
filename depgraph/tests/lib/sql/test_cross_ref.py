from pathlib import Path
from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.sql.cross_ref import attach_model_schema_references

FIXTURES = Path(__file__).parent / "fixtures"


def test_model_class_references_matching_schema():
    """User Python class with __tablename__='users' references the
    SQL-sourced users table."""
    py_prims = list(extract_repo(repo_key="fixture",
                                  repo_path=FIXTURES / "orm_models"))
    schema_prims = [{
        "id": "fixture::schema::users",
        "primitive": "class", "name": "users", "owner": None,
        "source": {"repo": "fixture", "path": "schema/users",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }]
    all_prims = py_prims + schema_prims
    attach_model_schema_references(all_prims)
    user_class = next(p for p in all_prims
                      if p["name"] == "User" and p["primitive"] == "class")
    refs = [e for e in user_class["edges_out"] if e["kind"] == "references"]
    assert any(e["target"] == "fixture::schema::users" for e in refs)


def test_model_with_no_tablename_no_reference():
    """A Python class without __tablename__ does not get a schema reference,
    even if a matching schema primitive exists by name."""
    py_prims = [{
        "id": "fixture::orm/other.py::Other",
        "primitive": "class", "name": "Other", "owner": None,
        "source": {"repo": "fixture", "path": "orm/other.py",
                   "language": "python", "line": 1, "end_line": 2},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": None,
        "extractor": "test", "schema_version": 2,
    }]
    schema_prims = [{
        "id": "fixture::schema::Other", "primitive": "class", "name": "Other",
        "owner": None,
        "source": {"repo": "fixture", "path": "schema/Other",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }]
    all_prims = py_prims + schema_prims
    attach_model_schema_references(all_prims)
    other = py_prims[0]
    refs = [e for e in other["edges_out"] if e["kind"] == "references"]
    assert refs == []
