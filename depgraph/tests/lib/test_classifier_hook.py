def test_use_prefix_calling_known_hook_is_hook():
    """Function named useFoo that has a calls-edge to a known hook (useState)
    classifies as hook."""
    p_user = {
        "id": "r::p.ts::useFoo", "primitive": "function", "name": "useFoo",
        "owner": None,
        "source": {"path": "p.ts", "line": 1, "end_line": 1, "language": "typescript", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "external::npm::react::useState", "kind": "calls",
                       "via": "fn", "where": "p.ts:2", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.hook import classify
    from depgraph.lib.classification.config import default_config
    decisions = classify([p_user], by_source={p_user["id"]: p_user["edges_out"]},
                         by_target={}, config=default_config(), decisions_so_far={})
    assert decisions[p_user["id"]]["rule"] == "use_prefix_calls_hook"
