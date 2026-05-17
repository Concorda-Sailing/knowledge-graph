from depgraph.lib.classification.engine import classify_corpus


def test_classify_corpus_returns_dict_id_to_decision():
    prims = [{
        "id": "x::y::Foo", "primitive": "function", "name": "Foo",
        "owner": None, "source": {"path": "y", "line": 1, "end_line": 1, "language": "typescript", "repo": "x"},
        "signature": {"decorators": []}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }]
    decisions = classify_corpus(prims)
    assert isinstance(decisions, dict)
    assert "x::y::Foo" in decisions
    # Decision is a dataclass; access by attribute. Default = unclassified.
    assert decisions["x::y::Foo"].kind is None
    assert decisions["x::y::Foo"].rule == "unclassified"


def test_extractor_set_kind_preserved():
    """SQL extractor sets kind='schema'; engine must not overwrite it."""
    prims = [{
        "id": "r::schema::users", "primitive": "class", "name": "users",
        "owner": None, "source": {"path": "schema/users", "line": 1, "end_line": 1, "language": "sql", "repo": "r"},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema", "extractor": "t", "schema_version": 2,
    }]
    decisions = classify_corpus(prims)
    assert decisions["r::schema::users"].kind == "schema"
    assert decisions["r::schema::users"].rule == "extractor_set"
