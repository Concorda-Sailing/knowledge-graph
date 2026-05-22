from depgraph.lib.edges import (
    EdgeKind, validate_edge, ALL_EDGE_KINDS, EDGE_KIND_RULES,
)


def test_edge_kinds_taxonomy_complete():
    expected = {
        "defines", "extends", "implements", "calls", "instantiates",
        "references", "references_orm", "references_table",
        "reads", "assigns", "decorates", "includes",
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


def test_extends_to_variable_requires_fuzzy_confidence():
    """Const-factory base classes (e.g. `const Base = createBase(...)`) are
    extracted as `variable` primitives. The inheritance arrow is real but
    the static taxonomy can't prove it; the extractor must emit it at
    confidence=fuzzy and the validator must require that gating (#86)."""
    fuzzy = {"source_kind": "class", "target_kind": "variable",
             "kind": "extends", "via": "class_decl",
             "where": "child.ts:10", "confidence": "fuzzy"}
    assert validate_edge(fuzzy) == []


def test_extends_to_variable_at_exact_confidence_still_errors():
    """Exact `extends -> variable` remains a taxonomy violation; the only
    permitted form is fuzzy. Catches extractor regressions (#86)."""
    exact = {"source_kind": "class", "target_kind": "variable",
             "kind": "extends", "via": "class_decl",
             "where": "child.ts:10", "confidence": "exact"}
    errors = validate_edge(exact)
    assert any("requires confidence" in e for e in errors), errors


def test_extends_to_class_still_exact():
    """The mainline `class Child extends Parent` case (both class
    primitives) must continue to validate at exact confidence (#86)."""
    edge = {"source_kind": "class", "target_kind": "class",
            "kind": "extends", "via": "class_decl",
            "where": "child.ts:10", "confidence": "exact"}
    assert validate_edge(edge) == []


def test_implements_to_variable_requires_fuzzy_confidence():
    """Symmetric case for `implements`: a class implementing a const-bound
    shape/brand resolves to a variable primitive and must be fuzzy (#86)."""
    fuzzy = {"source_kind": "class", "target_kind": "variable",
             "kind": "implements", "via": "class_decl",
             "where": "child.ts:10", "confidence": "fuzzy"}
    assert validate_edge(fuzzy) == []
    exact = {**fuzzy, "confidence": "exact"}
    assert any("requires confidence" in e for e in validate_edge(exact))
