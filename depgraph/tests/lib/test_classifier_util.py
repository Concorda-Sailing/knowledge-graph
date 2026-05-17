"""Tests for the util classifier (Task 5.7)."""
from depgraph.lib.classification.engine import classify_corpus


def test_function_called_by_classified_endpoint_is_util():
    endpoint_fn = {
        "id": "r::routers/x.py::handler", "primitive": "function", "name": "handler",
        "owner": None,
        "source": {"path": "routers/x.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.get"]}, "attributes": {},
        "edges_out": [{"target": "r::utils/format.py::format_date", "kind": "calls",
                       "via": "fn", "where": "routers/x.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    util_fn = {
        "id": "r::utils/format.py::format_date", "primitive": "function", "name": "format_date",
        "owner": None,
        "source": {"path": "utils/format.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    decisions = classify_corpus([endpoint_fn, util_fn])
    assert decisions[endpoint_fn["id"]].kind == "endpoint"
    assert decisions[util_fn["id"]].kind == "util"


def test_function_called_only_by_unclassified_is_not_util():
    """If the only caller is itself unclassified, the callee isn't util."""
    a = {
        "id": "r::lib/a.py::a_fn", "primitive": "function", "name": "a_fn",
        "owner": None,
        "source": {"path": "lib/a.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "r::lib/b.py::b_fn", "kind": "calls",
                       "via": "fn", "where": "lib/a.py:2", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    b = {**a, "id": "r::lib/b.py::b_fn", "name": "b_fn",
         "source": {**a["source"], "path": "lib/b.py"}, "edges_out": []}
    decisions = classify_corpus([a, b])
    assert decisions[b["id"]].kind != "util"


def test_transitive_util_chain():
    """endpoint → util A → util B → util C → leaf. All four classify as util
    in a single BFS pass (no fixed-point loop needed in the engine)."""
    endpoint = {
        "id": "r::p.py::handler", "primitive": "function", "name": "handler",
        "owner": None,
        "source": {"path": "p.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.get"]}, "attributes": {},
        "edges_out": [{"target": "r::a.py::a_fn", "kind": "calls",
                       "via": "fn", "where": "p.py:2", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }

    def _util(id_, name, calls_target):
        edges = []
        if calls_target:
            edges = [{"target": calls_target, "kind": "calls",
                      "via": "fn", "where": f"{name}.py:1", "confidence": "exact"}]
        return {
            "id": id_, "primitive": "function", "name": name, "owner": None,
            "source": {"path": f"{name}.py", "line": 1, "end_line": 1,
                       "language": "python", "repo": "r"},
            "signature": {"decorators": []}, "attributes": {},
            "edges_out": edges, "structural_hash": "0", "kind": None,
            "extractor": "t", "schema_version": 2,
        }

    a = _util("r::a.py::a_fn", "a_fn", "r::b.py::b_fn")
    b = _util("r::b.py::b_fn", "b_fn", "r::c.py::c_fn")
    c = _util("r::c.py::c_fn", "c_fn", "r::leaf.py::leaf")
    leaf = _util("r::leaf.py::leaf", "leaf", None)  # no outbound; BFS must terminate

    decisions = classify_corpus([endpoint, a, b, c, leaf])
    assert decisions[endpoint["id"]].kind == "endpoint"
    assert decisions[a["id"]].kind == "util"
    assert decisions[b["id"]].kind == "util"
    assert decisions[c["id"]].kind == "util"
    assert decisions[leaf["id"]].kind == "util"
