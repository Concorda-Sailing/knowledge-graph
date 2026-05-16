"""TS primitive extractor end-to-end tests.

Each test runs the extractor against a small fixture project under
fixtures/primitives_ts/<scenario>/ and asserts on the primitive set
emitted.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "primitives_ts"
EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def run_extractor(fixture_name: str) -> list[dict]:
    """Run the extractor against the named fixture; return primitives list."""
    fixture_root = FIXTURE_DIR / fixture_name
    cmd = ["npx", "tsx", str(EXTRACTOR),
           "--repo-key", "fixture",
           "--repo-path", str(fixture_root),
           "--format", "ndjson"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=EXTRACTOR.parent, check=True)
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def test_module_primitive_for_each_source_file():
    prims = run_extractor("module_only")
    modules = [p for p in prims if p["primitive"] == "module"]
    assert len(modules) == 1
    m = modules[0]
    assert m["id"] == "fixture::src/hello.ts"
    assert m["source"]["language"] == "typescript"
    assert m["source"]["path"] == "src/hello.ts"


def test_class_declaration():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "Concrete" in classes
    c = classes["Concrete"]
    assert c["attributes"]["abstract"] is False
    assert c["attributes"]["instantiable"] is True

def test_abstract_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    c = classes["AbstractC"]
    assert c["attributes"]["abstract"] is True
    assert c["attributes"]["instantiable"] is False

def test_class_with_generics():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert classes["Generic"]["attributes"]["template_parameters"] == ["T", "U"]

def test_interface_as_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    i = classes["IFoo"]
    assert i["attributes"]["abstract"] is True
    assert i["attributes"]["instantiable"] is False

def test_enum_as_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "Color" in classes

def test_type_alias_as_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert classes["Json"]["attributes"]["instantiable"] is False
