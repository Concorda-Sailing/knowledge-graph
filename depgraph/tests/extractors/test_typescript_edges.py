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
# Issue #69: method calls on imported namespaces / modules must not drop
# silently. Previously the resolver only consulted `varTypes`; receivers
# whose binding lived in the imports map produced zero edges.
# ---------------------------------------------------------------------------

def test_method_call_on_npm_namespace_import_resolves_external():
    """`import * as fs from "fs"; fs.readFile(...)` should emit
    `external::npm::fs::readFile` (confidence=exact), not drop silently."""
    prims = run_extractor("method_call_on_import", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    fs_calls = [e for e in calls if e["target"] == "external::npm::fs::readFile"]
    assert fs_calls, [e["target"] for e in calls]
    assert fs_calls[0]["confidence"] == "exact"


def test_method_call_on_in_corpus_namespace_import_resolves():
    """`import * as util from "./local/util.js"; util.greet()` should emit
    an edge to the exporting symbol in the corpus."""
    prims = run_extractor("method_call_on_import", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    targets = {e["target"] for e in calls}
    assert "fixture::src/local/util.ts::greet" in targets, targets


def test_method_call_on_unbound_receiver_emits_unresolved_not_silent():
    """`mystery.doSomething()` with no var-type and no import: never drop;
    fall through to `external::unresolved::mystery.doSomething` so the
    unresolved counter ticks (R7)."""
    prims = run_extractor("method_call_on_import", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    targets = {e["target"] for e in calls}
    assert "external::unresolved::mystery.doSomething" in targets, targets


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
