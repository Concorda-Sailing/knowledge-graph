from pathlib import Path
import json
import pytest
from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.primitives import validate_primitive

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "primitives_py"


def extract(scenario: str) -> list[dict]:
    return list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / scenario))


def test_module_per_py_file():
    prims = extract("modules_only")
    modules = [p for p in prims if p["primitive"] == "module"]
    paths = {m["source"]["path"] for m in modules}
    assert paths == {"pkg/__init__.py", "pkg/mod.py"}


def test_package_for_dir_with_init():
    prims = extract("modules_only")
    packages = [p for p in prims if p["primitive"] == "package"]
    names = {p["name"] for p in packages}
    assert "pkg" in names


def test_class_and_function():
    prims = extract("classes_and_functions")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}

    assert "Foo" in classes
    assert "top_level" in fns
    assert fns["top_level"]["signature"]["return_type"] == "str"
    assert [p["name"] for p in fns["top_level"]["signature"]["parameters"]] == ["x"]


def test_async_function():
    prims = extract("classes_and_functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert fns["async_fn"]["signature"]["is_async"] is True


def test_method_has_owner():
    prims = extract("classes_and_functions")
    methods = {p["name"]: p for p in prims if p["primitive"] == "function" and p["owner"]}
    assert "Foo.method" in methods
    assert methods["Foo.method"]["owner"] == "fixture::src.py::Foo"


def test_static_method_recorded():
    prims = extract("classes_and_functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "Foo.static_m" in fns
    assert "staticmethod" in fns["Foo.static_m"]["signature"]["decorators"]


def test_pep695_type_parameters():
    prims = extract("classes_and_functions")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert classes["GenericFoo"]["attributes"]["template_parameters"] == ["T", "U"]


def test_nested_class_extracted_with_dotted_qualname():
    prims = extract("classes_and_functions")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "Outer" in classes
    assert "Outer.Inner" in classes, f"missing nested class; got: {list(classes)}"
    inner = classes["Outer.Inner"]
    assert inner["owner"] == "fixture::src.py::Outer"
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "Outer.Inner.inner_method" in fns
    assert fns["Outer.Inner.inner_method"]["owner"] == "fixture::src.py::Outer.Inner"


def test_all_python_primitives_validate():
    for scenario in ("modules_only", "classes_and_functions"):
        for p in extract(scenario):
            errors = validate_primitive(p)
            assert not errors, f"{scenario}/{p.get('id')}: {errors}"
