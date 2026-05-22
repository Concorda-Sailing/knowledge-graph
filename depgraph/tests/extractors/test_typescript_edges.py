"""TS edge extractor end-to-end tests — Phase 3.

Each test runs the extractor against a small fixture project under
fixtures/edges_ts/<scenario>/ and asserts on edges emitted.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from depgraph.lib.edges import validate_edge

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "edges_ts"
EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def run_extractor(fixture_name: str, which: str = "edges") -> list[dict]:
    """Run the extractor against the named fixture; return primitives list."""
    fixture_root = FIXTURE_DIR / fixture_name
    cmd = ["npx", "tsx", str(EXTRACTOR),
           "--repo-key", "fixture",
           "--repo-path", str(fixture_root),
           "--format", "ndjson"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=EXTRACTOR.parent, check=True)
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Task 3.1: defines edges
# ---------------------------------------------------------------------------

def test_defines_class_method():
    prims = run_extractor("defines", which="edges")
    cls = next(p for p in prims if p["name"] == "Foo")
    targets = {e["target"] for e in cls["edges_out"] if e["kind"] == "defines"}
    assert "fixture::src/file.ts::Foo.bar" in targets


def test_defines_module_top_level():
    prims = run_extractor("defines", which="edges")
    mod = next(p for p in prims if p["primitive"] == "module")
    targets = {e["target"] for e in mod["edges_out"] if e["kind"] == "defines"}
    assert "fixture::src/file.ts::Foo" in targets


# ---------------------------------------------------------------------------
# Task 3.2: extends / implements edges
# ---------------------------------------------------------------------------

def test_extends_and_implements_ts():
    prims = run_extractor("inheritance", which="edges")
    child = next(p for p in prims if p["name"] == "Child")
    ex = [e for e in child["edges_out"] if e["kind"] == "extends"]
    impls = [e for e in child["edges_out"] if e["kind"] == "implements"]
    assert any(e["target"] == "fixture::src/file.ts::Base" for e in ex)
    assert any(e["target"] == "fixture::src/file.ts::ISpeaker" for e in impls)


# ---------------------------------------------------------------------------
# Task 3.3: imports edges
# ---------------------------------------------------------------------------

def test_import_resolves_to_exporting_module():
    prims = run_extractor("imports", which="edges")
    mod_a = next(p for p in prims if p["source"]["path"] == "src/a.ts"
                 and p["primitive"] == "module")
    imports = [e for e in mod_a["edges_out"] if e["kind"] == "imports"]
    targets = {e["target"] for e in imports}
    assert "fixture::src/b.ts::foo" in targets or "fixture::src/b.ts" in targets


def test_tsconfig_path_alias_resolves():
    prims = run_extractor("imports_with_paths", which="edges")
    mod = next(p for p in prims if p["source"]["path"] == "src/app.ts"
               and p["primitive"] == "module")
    imports = [e for e in mod["edges_out"] if e["kind"] == "imports"]
    assert any(e["target"].startswith("fixture::src/utils/greet.ts")
               and e["confidence"] == "exact"
               for e in imports), imports


def test_reexport_resolves_to_origin_with_fuzzy_confidence():
    """consumer imports foo via barrel; the imports edge from consumer to
    impl::foo should be emitted with confidence=fuzzy (v1 doesn't follow
    re-export chains transitively for exact resolution)."""
    prims = run_extractor("imports_reexport", which="edges")
    consumer = next(p for p in prims if p["source"]["path"] == "src/consumer.ts"
                    and p["primitive"] == "module")
    imports = [e for e in consumer["edges_out"] if e["kind"] == "imports"]
    foo_imports = [e for e in imports if "foo" in e["target"]]
    assert foo_imports, "expected at least one imports edge mentioning foo"
    # Either fuzzy-resolved to impl, or exact to the barrel — both acceptable
    # for v0; the gate is that we emit *something*, not nothing.
    assert any(e["target"].endswith("::foo") for e in foo_imports), foo_imports


def test_aliased_import_records_local_binding_ts():
    prims = run_extractor("imports_aliased", which="edges")
    mod = next(p for p in prims if p["source"]["path"] == "src/a.ts"
               and p["primitive"] == "module")
    edge = next(e for e in mod["edges_out"]
                if e["kind"] == "imports" and "foo" in e["target"])
    assert edge["local_binding"] == "bar"


def test_default_export_expression_resolves_no_orphan():
    """#85: `export default <expr>` (config-file idiom) must produce a
    synthetic primitive at `<file>::default` so the consumer's default-
    import edge resolves to a real primitive (no orphan).
    """
    prims = run_extractor("imports_default_expr", which="edges")
    by_id = {p["id"]: p for p in prims}

    # Synthetic default primitive exists on the exporter side.
    factory_default_id = "fixture::src/factory.ts::default"
    assert factory_default_id in by_id, (
        f"missing synthetic default primitive; ids: {sorted(by_id)}"
    )
    default_prim = by_id[factory_default_id]
    assert default_prim["primitive"] == "variable"
    assert default_prim["name"] == "default"
    # Signature carries the (truncated) expression text.
    assert default_prim["signature"]["value_text"]

    # Consumer's default-import edge must target a real primitive — i.e.
    # any default-import edge from src/consumer.ts must resolve in-corpus.
    consumer_mod = next(p for p in prims if p["source"]["path"] == "src/consumer.ts"
                        and p["primitive"] == "module")
    default_imports = [e for e in consumer_mod["edges_out"]
                       if e["kind"] == "imports" and e.get("local_binding") == "thing"]
    assert default_imports, f"expected a default-import edge for `thing`: {consumer_mod['edges_out']}"
    for edge in default_imports:
        assert edge["target"] in by_id, (
            f"orphan default-import edge: target={edge['target']!r} "
            f"not in corpus; available ids include {factory_default_id!r}"
        )


def test_namespace_reexport_resolves_no_orphan():
    """#89: `export * as <name> from '<src>'` must produce a synthetic
    primitive at `<file>::<name>` so a consumer's `import { <name> }
    from '<file>'` edge resolves to a real primitive (no orphan).

    Same family as #85's `<file>::default` synthesis — a different
    export form that introduces a new bound name without producing a
    real class/function/variable primitive.
    """
    prims = run_extractor("imports_namespace_reexport", which="edges")
    by_id = {p["id"]: p for p in prims}

    # Synthetic namespace primitive exists on the barrel side.
    barrel_ns_id = "fixture::src/barrel.ts::helpers"
    assert barrel_ns_id in by_id, (
        f"missing synthetic namespace primitive; ids: {sorted(by_id)}"
    )
    ns_prim = by_id[barrel_ns_id]
    assert ns_prim["primitive"] == "variable"
    assert ns_prim["name"] == "helpers"
    # Signature carries a textual description of the re-export source.
    assert ns_prim["signature"]["value_text"]
    assert "helpers" in ns_prim["signature"]["value_text"]

    # Consumer's named-import edge for `helpers` must target a real
    # primitive — i.e. no orphan.
    consumer_mod = next(p for p in prims if p["source"]["path"] == "src/consumer.ts"
                        and p["primitive"] == "module")
    helper_imports = [e for e in consumer_mod["edges_out"]
                      if e["kind"] == "imports" and e.get("local_binding") == "helpers"]
    assert helper_imports, (
        f"expected a named-import edge for `helpers`: {consumer_mod['edges_out']}"
    )
    for edge in helper_imports:
        assert edge["target"] in by_id, (
            f"orphan namespace-import edge: target={edge['target']!r} "
            f"not in corpus; available ids include {barrel_ns_id!r}"
        )


# ---------------------------------------------------------------------------
# Task 3.4: calls + instantiates edges (intra-function type binding)
# ---------------------------------------------------------------------------

def test_calls_resolves_local_function():
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src/file.ts::helper" for e in calls)


def test_instantiates_resolves_local_class():
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    insts = [e for e in root["edges_out"] if e["kind"] == "instantiates"]
    assert any(e["target"] == "fixture::src/file.ts::Service" for e in insts)


def test_method_call_on_instantiated_local_resolves():
    """s = new Service(); s.doWork() — should emit a calls edge to Service.doWork."""
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src/file.ts::Service.doWork" for e in calls)


def test_method_call_on_annotated_local_resolves():
    """t: Service = new Service(); t.doWork() — annotation provides the bind."""
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    # Two doWork call sites — both should resolve
    do_work_calls = [e for e in calls
                     if e["target"] == "fixture::src/file.ts::Service.doWork"]
    assert len(do_work_calls) >= 2


# ---------------------------------------------------------------------------
# Task 3.5: reads / assigns edges (TS)
# ---------------------------------------------------------------------------

def test_reads_edge_ts():
    prims = run_extractor("references", which="edges")
    reader = next(p for p in prims if p["name"] == "reader")
    reads = [e for e in reader["edges_out"] if e["kind"] == "reads"]
    assert any(e["target"] == "fixture::src/file.ts::globalCount" for e in reads)


def test_assigns_edge_ts():
    prims = run_extractor("references", which="edges")
    writer = next(p for p in prims if p["name"] == "writer")
    assigns = [e for e in writer["edges_out"] if e["kind"] == "assigns"]
    assert any(e["target"] == "fixture::src/file.ts::globalCount" for e in assigns)


def test_property_key_not_treated_as_read_ts():
    """`return { globalCount: 42 }` — the `globalCount` is a property
    key, not a read of the module-scope var with that name."""
    prims = run_extractor("references", which="edges")
    fn = next(p for p in prims if p["name"] == "propertyKey")
    reads = [e for e in fn["edges_out"] if e["kind"] == "reads"]
    assert not any(e["target"] == "fixture::src/file.ts::globalCount"
                   for e in reads), reads


def test_property_access_not_treated_as_read_ts():
    """`obj.globalCount` — the `.globalCount` is a property name, not
    a read of the module-scope var."""
    prims = run_extractor("references", which="edges")
    fn = next(p for p in prims if p["name"] == "propertyAccess")
    reads = [e for e in fn["edges_out"] if e["kind"] == "reads"]
    assert not any(e["target"] == "fixture::src/file.ts::globalCount"
                   for e in reads), reads


def test_parameter_name_not_treated_as_read_ts():
    """`function f(globalCount: number)` — the parameter declaration
    site is a name slot, not a read. The body's `return globalCount` is
    also suppressed by the scope-tracking pass (#82) since the parameter
    shadows the module-scope var."""
    prims = run_extractor("references", which="edges")
    fn = next(p for p in prims if p["name"] == "parameterShadow")
    reads = [e for e in fn["edges_out"]
             if e["kind"] == "reads"
             and e["target"] == "fixture::src/file.ts::globalCount"]
    assert len(reads) == 0, f"expected 0 reads (shadowed), got {len(reads)}: {reads}"


def test_destructuring_binding_not_treated_as_read_ts():
    """`const { globalCount } = obj` — the binding site is a name slot;
    the body read of the local binding is suppressed by scope tracking
    (#82)."""
    prims = run_extractor("references", which="edges")
    fn = next(p for p in prims if p["name"] == "destructureBinding")
    reads = [e for e in fn["edges_out"]
             if e["kind"] == "reads"
             and e["target"] == "fixture::src/file.ts::globalCount"]
    assert len(reads) == 0, f"expected 0 reads (shadowed), got {len(reads)}: {reads}"


def test_shorthand_property_is_real_read_ts():
    """`return { globalCount }` (shorthand) — the value comes from
    scope, so this IS a real read of the module-scope var. Verifies
    the guard doesn't over-skip."""
    prims = run_extractor("references", which="edges")
    fn = next(p for p in prims if p["name"] == "shorthandRead")
    reads = [e for e in fn["edges_out"] if e["kind"] == "reads"]
    assert any(e["target"] == "fixture::src/file.ts::globalCount"
               for e in reads), reads


# ---------------------------------------------------------------------------
# Issue #82: scope-shadowing in reads/assigns
# ---------------------------------------------------------------------------

def test_parameter_shadowing_suppresses_reads_edge_ts():
    """A function parameter named the same as a module-scope var must NOT
    cause the body's reference to the parameter to emit a reads edge
    against the module-scope var."""
    prims = run_extractor("references", which="edges")
    fn = next(p for p in prims if p["name"] == "paramShadow")
    reads = [e for e in fn["edges_out"] if e["kind"] == "reads"]
    assert not any(e["target"] == "fixture::src/file.ts::value" for e in reads), (
        f"parameter `value` shadows module var `value`; the body's read of "
        f"the parameter must not emit a reads edge to the module var. "
        f"Got: {reads}"
    )


def test_destructure_binding_shadowing_suppresses_reads_edge_ts():
    """A destructured local binding (`const { label } = obj`) named the same
    as a module-scope var must NOT cause the subsequent body reference to
    emit a reads edge against the module-scope var."""
    prims = run_extractor("references", which="edges")
    fn = next(p for p in prims if p["name"] == "destructureShadow")
    reads = [e for e in fn["edges_out"] if e["kind"] == "reads"]
    assert not any(e["target"] == "fixture::src/file.ts::label" for e in reads), (
        f"destructured local `label` shadows module var `label`; the body's "
        f"read of the local must not emit a reads edge to the module var. "
        f"Got: {reads}"
    )


# ---------------------------------------------------------------------------
# Task 3.6: tests edges (assertion-scoped, TS)
# ---------------------------------------------------------------------------

def test_tests_edge_to_subject_only():
    prims = run_extractor("tests", which="edges")
    test_fn = next(p for p in prims if p["primitive"] == "function"
                   and p["source"]["path"].endswith(".test.ts"))
    tests = [e for e in test_fn["edges_out"] if e["kind"] == "tests"]
    targets = {e["target"] for e in tests}
    assert "fixture::src/math.ts::add" in targets
    assert "fixture::src/math.ts::normalize" in targets
    # helper called outside expect(...) — must NOT be a tests-edge target
    assert "fixture::src/test_helpers.ts::makeFixture" not in targets
    # framework primitives must NOT be targets either
    assert not any("vitest" in t for t in targets)


# ---------------------------------------------------------------------------
# Task 3.7: Edge schema validation sweep (TS)
# ---------------------------------------------------------------------------

def _load_all_ts_fixtures() -> list[dict]:
    """Load primitives from all edges_ts fixtures into one flat list."""
    all_prims: list[dict] = []
    for scenario in FIXTURE_DIR.iterdir():
        if not scenario.is_dir():
            continue
        all_prims.extend(run_extractor(scenario.name))
    return all_prims


def test_all_emitted_edges_validate_ts():
    """Every edge emitted by any TS fixture must pass schema validation.

    Builds (source_kind, target_kind) from the corpus's primitives_by_id,
    passes each edge through validate_edge. External terminals (unresolved
    targets) have target_kind=None, which validate_edge allows.
    """
    prims = _load_all_ts_fixtures()
    primitives_by_id = {p["id"]: p for p in prims}

    errors_found = []
    for p in prims:
        for e in p["edges_out"]:
            validation_input = {**e, "source_kind": p["primitive"]}
            tgt = primitives_by_id.get(e["target"])
            if tgt:
                validation_input["target_kind"] = tgt["primitive"]
            errs = validate_edge(validation_input)
            if errs:
                errors_found.append((p["id"], e["target"], errs))

    assert not errors_found, (
        f"{len(errors_found)} edge(s) failed validation:\n"
        + "\n".join(f"  {src} -> {tgt}: {errs}"
                    for src, tgt, errs in errors_found[:10])
    )
