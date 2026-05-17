def test_route_decorator_makes_endpoint():
    p = {
        "id": "r::routers/events.py::create_event", "primitive": "function",
        "name": "create_event", "owner": None,
        "source": {"path": "routers/events.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.post"]}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.endpoint import classify
    from depgraph.lib.classification.config import default_config
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert decisions[p["id"]]["rule"] == "route_decorator"


def test_no_route_decorator_no_endpoint():
    p = {
        "id": "r::routers/events.py::helper", "primitive": "function",
        "name": "helper", "owner": None,
        "source": {"path": "routers/events.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.endpoint import classify
    from depgraph.lib.classification.config import default_config
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert p["id"] not in decisions
