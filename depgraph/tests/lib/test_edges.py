from depgraph.lib.edges import (
    EdgeKind, validate_edge, ALL_EDGE_KINDS, EDGE_KIND_RULES,
    REVERSE_INDEX_FILENAME, FORWARD_INDEX_FILENAME,
)


def test_reverse_index_filename_constant():
    """#66: writer + readers must agree on the reverse-index filename.
    The constant pins the value at the single point that owns it."""
    assert REVERSE_INDEX_FILENAME == "by_target.json"


def test_forward_index_filename_constant():
    """#66: same shape for the forward index, written alongside by_target."""
    assert FORWARD_INDEX_FILENAME == "by_source.json"


def test_edge_kinds_taxonomy_complete():
    expected = {
        "defines", "extends", "implements", "calls", "instantiates",
        "references", "reads", "assigns", "decorates", "includes",
        "imports", "tests",
    }
    assert {k.value for k in EdgeKind} == expected


def test_validate_edge_calls_function_to_function_ok():
    edge = {"source_kind": "function", "target_kind": "function",
            "kind": "calls", "via": "function_call",
            "where": "foo.py:1", "confidence": "exact"}
    errors = validate_edge(edge)
    assert errors == [], errors


def test_validate_edge_extends_rejects_function_source():
    edge = {"source_kind": "function", "target_kind": "class",
            "kind": "extends", "via": "class_decl",
            "where": "foo.py:1", "confidence": "exact"}
    errors = validate_edge(edge)
    assert any("source" in e for e in errors), errors


def test_edge_kind_rules_documented_for_every_kind():
    """Every EdgeKind has explicit source-kind and target-kind rules."""
    for k in EdgeKind:
        assert k.value in EDGE_KIND_RULES, f"missing rules for {k.value}"
        rules = EDGE_KIND_RULES[k.value]
        assert "source" in rules and "target" in rules


def test_decorates_allows_variable_source():
    """Framework decorator-method-call pattern (`@router.get(...)`,
    `@app.route(...)`, `@click.command()`) anchors the source to the
    module-level variable holding the framework instance (#30)."""
    edge = {"source_kind": "variable", "target_kind": "function",
            "kind": "decorates", "via": "router.get",
            "where": "routers/auth.py:10", "confidence": "exact"}
    assert validate_edge(edge) == []


def test_decorates_still_rejects_module_source():
    """A module can never be a decorator. Extractors shouldn't emit these,
    and if they slip through the schema should flag them (#30)."""
    edge = {"source_kind": "module", "target_kind": "function",
            "kind": "decorates", "via": "something",
            "where": "x.py:1", "confidence": "exact"}
    errors = validate_edge(edge)
    assert any("source kind 'module'" in e for e in errors), errors


def test_reads_allows_class_target():
    """JS Context objects / class-typed-but-value-used bindings: a `reads`
    edge whose target is a class primitive is valid (#30)."""
    edge = {"source_kind": "function", "target_kind": "class",
            "kind": "reads", "via": "identifier_read",
            "where": "sidebar.tsx:10", "confidence": "exact"}
    assert validate_edge(edge) == []
