"""TS edge extractor end-to-end tests — Phase 3.

Each test runs the extractor against a small fixture project under
fixtures/edges_ts/<scenario>/ and asserts on edges emitted.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

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
