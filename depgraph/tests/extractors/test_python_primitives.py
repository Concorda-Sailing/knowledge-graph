from pathlib import Path
import json
import pytest
from depgraph.extractors.python.extract import extract_repo

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
