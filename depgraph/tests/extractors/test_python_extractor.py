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
