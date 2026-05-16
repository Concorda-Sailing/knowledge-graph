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


def test_top_level_function():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "topLevel" in fns
    f = fns["topLevel"]
    assert f["owner"] is None
    assert f["signature"]["is_async"] is False
    assert f["signature"]["return_type"] == "string"
    assert [p["name"] for p in f["signature"]["parameters"]] == ["x"]

def test_async_function():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert fns["asyncFn"]["signature"]["is_async"] is True

def test_arrow_function_bound_to_const():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "arrow" in fns
    assert fns["arrow"]["owner"] is None

def test_class_method_has_owner():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function" and "." in p["name"]}
    names = set(fns.keys())
    assert "Holder.method" in names
    m = fns["Holder.method"]
    assert m["owner"] == "fixture::src/all.ts::Holder"

def test_static_method_captured():
    prims = run_extractor("functions")
    names = {p["name"] for p in prims if p["primitive"] == "function"}
    # Static methods always get the :static suffix in this extractor.
    assert "Holder.staticMethod:static" in names

def test_private_method_captured():
    prims = run_extractor("functions")
    names = {p["name"] for p in prims if p["primitive"] == "function"}
    assert "Holder.privateMethod" in names

def test_anonymous_default_export_gets_synthesized_name():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    # `export default function() {}` — no source-given name. Use module basename.
    assert "<default:all>" in fns
    assert fns["<default:all>"]["owner"] is None
    assert fns["<default:all>"]["signature"]["is_async"] is False

def test_ts_overload_stubs_skipped_only_impl_emitted():
    prims = run_extractor("functions")
    formats = [p for p in prims if p["primitive"] == "function"
               and p["name"] == "Holder.format"]
    assert len(formats) == 1, "overload stubs should be skipped; only impl emits"
    # The impl is the one with a body — return_type from the impl signature.
    assert formats[0]["signature"]["return_type"] == "string"

def test_jsx_returning_function_sets_attribute():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert fns["Header"]["signature"]["returns_jsx"] is True
    assert fns["Footer"]["signature"]["returns_jsx"] is True
    assert fns["notAComponent"]["signature"]["returns_jsx"] is False

def test_same_name_static_and_instance_method_disambiguate():
    """`shared()` and `static shared()` must produce distinct ids."""
    prims = run_extractor("functions")
    ids = {p["id"] for p in prims if p["primitive"] == "function"
           and p["owner"] == "fixture::src/all.ts::Holder"
           and p["name"].split(".")[-1].startswith("shared")}
    assert "fixture::src/all.ts::Holder.shared" in ids
    assert "fixture::src/all.ts::Holder.shared:static" in ids
    assert len(ids) == 2


def test_top_level_const_variable():
    prims = run_extractor("variables")
    vars_ = {p["name"]: p for p in prims if p["primitive"] == "variable"}
    assert "PI" in vars_
    assert vars_["PI"]["attributes"]["mutable"] is False

def test_top_level_let_variable():
    prims = run_extractor("variables")
    vars_ = {p["name"]: p for p in prims if p["primitive"] == "variable"}
    assert vars_["counter"]["attributes"]["mutable"] is True

def test_arrow_function_const_is_function_not_variable():
    """`const x = () => 1` should be function, not variable."""
    prims = run_extractor("functions")
    primitives_by_name = {p["name"]: p["primitive"] for p in prims}
    assert primitives_by_name.get("arrow") == "function"

def test_class_field_has_owner():
    prims = run_extractor("variables")
    fields = [p for p in prims if p["primitive"] == "variable" and p["owner"] is not None]
    names = {p["name"] for p in fields}
    assert "Settings.VERSION" in names
    assert "Settings.debug" in names
    assert "Settings.publicProp" in names


def test_package_primitive_per_dir_with_sources():
    prims = run_extractor("object_api_client")
    pkgs = {p["name"]: p for p in prims if p["primitive"] == "package"}
    # Expect packages for "src" and "src/lib"
    assert "src" in pkgs
    assert "src/lib" in pkgs

def test_object_literal_api_client_emits_class_and_members():
    prims = run_extractor("object_api_client")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "usersApi" in classes
    fns = {p["name"] for p in prims if p["primitive"] == "function" and p["owner"]}
    assert "usersApi.fetch" in fns
    assert "usersApi.create" in fns
    vars_ = {p["name"] for p in prims if p["primitive"] == "variable" and p["owner"]}
    assert "usersApi.endpoint" in vars_
