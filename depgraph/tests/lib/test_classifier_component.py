from depgraph.lib.classification.component import classify
from depgraph.lib.classification.config import default_config


def _prim(id_, name, primitive="function", owner=None,
          returns_jsx=False, decorators=None):
    return {
        "id": id_, "primitive": primitive, "name": name, "owner": owner,
        "source": {"path": "p.tsx", "line": 1, "end_line": 1, "language": "typescript", "repo": "r"},
        "signature": {"decorators": decorators or [], "returns_jsx": returns_jsx},
        "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }


def test_function_returning_jsx_is_component():
    p = _prim("r::p.tsx::MyComponent", "MyComponent", returns_jsx=True)
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert decisions["r::p.tsx::MyComponent"]["rule"] == "returns_jsx"


def test_pascalcase_arrow_const_with_jsx_is_component():
    p = _prim("r::p.tsx::Header", "Header", returns_jsx=True)
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert "r::p.tsx::Header" in decisions


def test_lowercase_function_returning_jsx_is_not_component():
    p = _prim("r::p.tsx::renderItem", "renderItem", returns_jsx=True)
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert decisions.get("r::p.tsx::renderItem", {}).get("rule") != "returns_jsx"
