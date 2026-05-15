from pathlib import Path
from extractors.generic.python.extract import (
    discover_files, parse_file, DEFAULT_EXCLUDES,
)


def test_discover_finds_py_files(tmp_repo: Path):
    (tmp_repo / "a.py").write_text("x = 1")
    (tmp_repo / "sub").mkdir()
    (tmp_repo / "sub" / "b.py").write_text("y = 2")
    (tmp_repo / "README.md").write_text("# nope")
    found = sorted(p.relative_to(tmp_repo).as_posix() for p in discover_files(tmp_repo))
    assert found == ["a.py", "sub/b.py"]


def test_discover_skips_default_excludes(tmp_repo: Path):
    (tmp_repo / "keep.py").write_text("x = 1")
    (tmp_repo / ".venv").mkdir()
    (tmp_repo / ".venv" / "skip.py").write_text("x = 1")
    (tmp_repo / "node_modules").mkdir()
    (tmp_repo / "node_modules" / "skip.py").write_text("x = 1")
    found = [p.relative_to(tmp_repo).as_posix() for p in discover_files(tmp_repo)]
    assert found == ["keep.py"]


def test_discover_respects_extra_excludes(tmp_repo: Path):
    (tmp_repo / "keep.py").write_text("x = 1")
    (tmp_repo / "build").mkdir()
    (tmp_repo / "build" / "skip.py").write_text("x = 1")
    found = [p.relative_to(tmp_repo).as_posix() for p in discover_files(tmp_repo, extra_excludes=["build"])]
    assert found == ["keep.py"]


def test_parse_file_returns_module_node(tmp_repo: Path):
    f = tmp_repo / "a.py"
    f.write_text("def hi(): pass\n")
    tree, err = parse_file(f)
    assert err is None
    assert tree is not None


def test_parse_file_returns_diagnostic_on_syntax_error(tmp_repo: Path):
    f = tmp_repo / "bad.py"
    f.write_text("def (\n")
    tree, err = parse_file(f)
    assert tree is None
    assert err is not None
    assert "bad.py" in err


from extractors.generic.python.extract import emit_primitives


def test_emit_module_primitive(tmp_repo: Path):
    f = tmp_repo / "a.py"; f.write_text("")
    tree, _ = parse_file(f)
    nodes = emit_primitives(tree, repo_key="r", rel_path="a.py")
    mods = [n for n in nodes if n["kind"] == "module"]
    assert len(mods) == 1
    assert mods[0]["id"] == "r:a.py:<module>"


def test_emit_class_and_methods(tmp_repo: Path):
    src = "class C:\n    def m(self): pass\n"
    f = tmp_repo / "a.py"; f.write_text(src)
    tree, _ = parse_file(f)
    nodes = emit_primitives(tree, repo_key="r", rel_path="a.py")
    cls = next(n for n in nodes if n["kind"] == "class" and n["name"] == "C")
    meth = next(n for n in nodes if n["kind"] == "function" and n["name"] == "m")
    assert meth["parent_id"] == cls["id"]
    assert cls["id"] == "r:a.py:C"
    assert meth["id"] == "r:a.py:C.m"


def test_emit_top_level_function(tmp_repo: Path):
    f = tmp_repo / "a.py"; f.write_text("def hi(): pass\n")
    tree, _ = parse_file(f)
    nodes = emit_primitives(tree, repo_key="r", rel_path="a.py")
    fns = [n for n in nodes if n["kind"] == "function"]
    assert len(fns) == 1
    assert fns[0]["id"] == "r:a.py:hi"
    assert fns[0]["parent_id"] is None


def test_emit_import_edge(tmp_repo: Path):
    f = tmp_repo / "a.py"; f.write_text("import os\nfrom x.y import z\n")
    tree, _ = parse_file(f)
    nodes = emit_primitives(tree, repo_key="r", rel_path="a.py")
    edges = [n for n in nodes if n["kind"] == "import_edge"]
    targets = sorted(e["target"] for e in edges)
    assert targets == ["os", "x.y.z"]


def test_emit_call_edge(tmp_repo: Path):
    src = "def hi():\n    print('x')\n"
    f = tmp_repo / "a.py"; f.write_text(src)
    tree, _ = parse_file(f)
    nodes = emit_primitives(tree, repo_key="r", rel_path="a.py")
    calls = [n for n in nodes if n["kind"] == "call_edge"]
    assert any(c["target"] == "print" and c["from_id"] == "r:a.py:hi" for c in calls)


import json
import subprocess
import sys

from extractors.generic.python.extract import (
    load_detectors, apply_mutations, write_nodes,
)
from extractors.generic.python.detector_api import RelabelNode, AddNode


def test_load_detector_from_framework_dir():
    detectors = load_detectors(names=["fastapi"], extra_paths=[])
    assert len(detectors) == 1
    assert detectors[0].name == "fastapi"


def test_load_detector_missing_raises():
    import pytest
    with pytest.raises(ValueError, match="unknown detector"):
        load_detectors(names=["nope_xyz"], extra_paths=[])


def test_apply_mutations_relabels_node():
    prims = [{"id": "x", "kind": "function", "name": "hi"}]
    muts = [RelabelNode(node_id="x", new_kind="endpoint", metadata={"route": "/x"})]
    out = apply_mutations(prims, muts)
    rel = next(n for n in out if n["id"] == "x")
    assert rel["kind"] == "endpoint"
    assert rel["route"] == "/x"


def test_apply_mutations_adds_node():
    prims = []
    muts = [AddNode(kind="route_call", payload={"url": "/x", "id": "rc1"})]
    out = apply_mutations(prims, muts)
    assert any(n["id"] == "rc1" and n["kind"] == "route_call" for n in out)


def test_write_nodes_creates_per_kind_dirs(tmp_data_dir):
    nodes = [
        {"id": "r:a.py:f", "kind": "function", "name": "f", "file": "a.py"},
        {"id": "r:a.py:<module>", "kind": "module", "name": "<module>"},
    ]
    write_nodes(nodes, tmp_data_dir)
    assert (tmp_data_dir / "nodes" / "functions" / "r__a.py__f.json").exists()
    assert (tmp_data_dir / "nodes" / "modules" / "r__a.py__<module>.json").exists()


def test_cli_end_to_end(tmp_repo, tmp_data_dir):
    """End-to-end smoke: the CLI runs detectors + canonicalize and writes
    canonical nodes only. Primitive kinds are dropped post-canonicalize
    (see § Canonical Node Contracts), so we exercise the service detector
    which produces a canonical `service` node from `services/a.py`."""
    services = tmp_repo / "services"
    services.mkdir()
    (services / "a.py").write_text("def hi(): pass\n")
    extractor = (
        Path(__file__).resolve().parents[3]
        / "depgraph" / "extractors" / "generic" / "python" / "extract.py"
    )
    r = subprocess.run(
        [sys.executable, str(extractor),
         "--repo-key", "r", "--repo-path", str(tmp_repo),
         "--data-dir", str(tmp_data_dir),
         "--detectors", "service"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "wrote" in r.stdout
    services_dir = tmp_data_dir / "nodes" / "services"
    assert services_dir.exists(), r.stdout
    assert any(p.suffix == ".json" for p in services_dir.iterdir())
