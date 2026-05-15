# Language Extractors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship project-agnostic, language-specific extractors for Python, TypeScript/JavaScript, Go, and Rust, with a detector contract for framework recognition; lift Concorda's existing extractors into framework detector modules; deliver an evaluation harness foundation.

**Architecture:** Per `docs/superpowers/specs/2026-05-15-language-extractors-design.md`. Five-stage extractor contract (discover → parse → emit primitives → run detectors → write). Native parsers for Py/TS; `py-tree-sitter` for Go/Rust. Detectors are pure functions returning mutations against AST primitives. Project wiring via `[repos.*]` in `project.toml` with new `detectors` key and `{kg_dir}` substitution.

**Tech Stack:** Python 3.11 (stdlib `ast`, `py-tree-sitter` + grammars), Node + TypeScript Compiler API + `tsx`, pytest.

---

## File Structure

**New (framework):**
- `depgraph/extractors/generic/python/extract.py` — Python entry point.
- `depgraph/extractors/generic/python/detector_api.py` — Mutation types + Detector ABC.
- `depgraph/extractors/generic/python/detectors/{fastapi,sqlalchemy,pydantic,pytest}.py` — shipped detectors.
- `depgraph/extractors/generic/python/TEMPLATE_detector.py` — scaffold.
- `depgraph/extractors/generic/python/README.md`.
- `depgraph/extractors/generic/typescript/extract.ts` — TS entry point.
- `depgraph/extractors/generic/typescript/detector_api.ts` — Mutation types + Detector interface.
- `depgraph/extractors/generic/typescript/detectors/{react,vitest,route-calls}.ts`.
- `depgraph/extractors/generic/typescript/TEMPLATE_detector.ts`.
- `depgraph/extractors/generic/typescript/README.md` (already exists; update).
- `depgraph/extractors/generic/go/extract.py` — Go entry point (py-tree-sitter).
- `depgraph/extractors/generic/go/TEMPLATE_detector.py`.
- `depgraph/extractors/generic/go/README.md`.
- `depgraph/extractors/generic/rust/extract.py` — Rust entry point.
- `depgraph/extractors/generic/rust/TEMPLATE_detector.py`.
- `depgraph/extractors/generic/rust/README.md`.
- `depgraph/extractors/eval/harness.py` — case runner.
- `depgraph/extractors/eval/corpus/{python,typescript,go,rust}/_seed_*/` — seed cases.
- `depgraph/extractors/eval/README.md`.
- `depgraph/tests/extractors/test_python_extractor.py`.
- `depgraph/tests/extractors/test_python_detectors.py`.
- `depgraph/tests/extractors/test_typescript_extractor.py` (drives tsx via subprocess).
- `depgraph/tests/extractors/test_go_extractor.py`.
- `depgraph/tests/extractors/test_rust_extractor.py`.
- `depgraph/tests/extractors/test_eval_harness.py`.
- `CONTRIBUTING-detectors.md` (repo root).

**Modify (framework):**
- `depgraph/lib/config.py` — add `{kg_dir}` substitution; parse `detectors` key.
- `depgraph/bin/depgraph` — pass `--detector-path <data_dir>/extractors/detectors` to extractors when invoking.
- `depgraph/extractors/README.md` — describe the new layout.
- `README.md` (repo root) — runbook entries for "Add a new tracked repo" reference framework extractors + detector lists.
- `pyproject.toml` (depgraph) — add `tree-sitter`, `tree-sitter-go`, `tree-sitter-rust`, `tree-sitter-python` deps.

**Modify (Concorda data repo, in a separate commit at task 27):**
- `<concorda-knowledge-graph>/depgraph/project.toml` — flip extractor commands; add `detectors` lists.
- Delete `<concorda-knowledge-graph>/depgraph/extractors/extract_api.py`, `extract_web.ts`, `extract_tests.ts`.

---

## Conventions for every task

- TDD. Write the failing test first; verify it fails; implement; verify it passes; commit.
- Commits: imperative subject ≤ 70 chars; body lists what + why; trailer `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.
- Run tests from repo root: `pytest depgraph/tests/extractors/ -v`.
- TS tests shell out to `tsx`; install path is `~/tools/knowledge-graph/depgraph/extractors/generic/typescript/node_modules` (already set up — see `depgraph/extractors/generic/typescript/README.md`).
- Tree-sitter grammars install via pip: `pip install tree-sitter tree-sitter-go tree-sitter-rust tree-sitter-python`. Add to `depgraph/pyproject.toml` extras in Task 1.

---

## Task 1: Add tree-sitter dependencies + test scaffolding

**Files:**
- Modify: `depgraph/pyproject.toml`
- Create: `depgraph/tests/extractors/__init__.py`
- Create: `depgraph/tests/extractors/conftest.py`

- [ ] **Step 1: Read current pyproject**

Run: `cat depgraph/pyproject.toml`

- [ ] **Step 2: Add tree-sitter deps**

In `depgraph/pyproject.toml`, add to `[project] dependencies` (or the existing dependencies array):

```toml
"tree-sitter>=0.21",
"tree-sitter-go>=0.21",
"tree-sitter-rust>=0.21",
"tree-sitter-python>=0.21",
```

- [ ] **Step 3: Install and verify**

Run: `cd depgraph && pip install -e .`
Run: `python3 -c "import tree_sitter, tree_sitter_go, tree_sitter_rust, tree_sitter_python; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Create test package**

Create `depgraph/tests/extractors/__init__.py`:

```python
```

Create `depgraph/tests/extractors/conftest.py`:

```python
"""Shared fixtures for extractor tests."""
from pathlib import Path
import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create an empty repo dir; tests populate source files into it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create an empty data dir with nodes/ subdir."""
    data = tmp_path / "data"
    (data / "nodes").mkdir(parents=True)
    (data / "extractors" / "detectors").mkdir(parents=True)
    return data
```

- [ ] **Step 5: Commit**

```bash
git add depgraph/pyproject.toml depgraph/tests/extractors/
git commit -m "$(cat <<'EOF'
extractors: add tree-sitter deps + test scaffolding

Adds tree-sitter and language grammar deps for the Go/Rust extractors,
plus shared test fixtures (tmp_repo, tmp_data_dir) used by all four
extractor test suites.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Python detector API

**Files:**
- Create: `depgraph/extractors/generic/python/__init__.py`
- Create: `depgraph/extractors/generic/python/detector_api.py`
- Create: `depgraph/tests/extractors/test_python_detector_api.py`

- [ ] **Step 1: Write failing test**

Create `depgraph/tests/extractors/test_python_detector_api.py`:

```python
from extractors.generic.python.detector_api import (
    RelabelNode, AddEdge, AddNode, DetectorContext, Detector,
)


def test_relabel_node_carries_id_kind_metadata():
    m = RelabelNode(node_id="repo:foo.py:bar", new_kind="endpoint",
                    metadata={"route": "/x"})
    assert m.node_id == "repo:foo.py:bar"
    assert m.new_kind == "endpoint"
    assert m.metadata == {"route": "/x"}


def test_add_edge_carries_from_to_kind():
    e = AddEdge(from_id="a", to_id="b", kind="calls")
    assert (e.from_id, e.to_id, e.kind) == ("a", "b", "calls")


def test_add_node_carries_kind_payload():
    n = AddNode(kind="route_call", payload={"url": "/x"})
    assert n.kind == "route_call"
    assert n.payload == {"url": "/x"}


def test_detector_context_dataclass():
    ctx = DetectorContext(repo_key="api", file_path="foo.py",
                          project_config={"detectors": ["fastapi"]})
    assert ctx.repo_key == "api"


def test_detector_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        Detector()
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest depgraph/tests/extractors/test_python_detector_api.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

Create `depgraph/extractors/generic/python/__init__.py` (empty).

Create `depgraph/extractors/generic/python/detector_api.py`:

```python
"""Detector contract for the Python language extractor.

A detector receives the AST of one parsed file plus the AST-primitive
nodes already emitted for that file, and returns a list of mutations
that re-shape those primitives into framework-specific nodes
(endpoints, models, etc.).
"""
from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RelabelNode:
    node_id: str
    new_kind: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AddEdge:
    from_id: str
    to_id: str
    kind: str


@dataclass(frozen=True)
class AddNode:
    kind: str
    payload: dict[str, Any]


Mutation = RelabelNode | AddEdge | AddNode


@dataclass(frozen=True)
class DetectorContext:
    repo_key: str
    file_path: str
    project_config: dict[str, Any]


class Detector(ABC):
    """Abstract base. Subclasses implement detect()."""

    name: str = ""

    @abstractmethod
    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        """Return mutations to apply to `primitives`."""
```

- [ ] **Step 4: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_detector_api.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/ depgraph/tests/extractors/test_python_detector_api.py
git commit -m "$(cat <<'EOF'
extractors/python: detector API (Mutation types, Detector ABC)

Defines the contract every Python detector implements: receive an AST
plus emitted primitives, return a list of mutations (RelabelNode,
AddEdge, AddNode). Pure function; no I/O.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Python extractor — discover + parse stages

**Files:**
- Create: `depgraph/extractors/generic/python/extract.py` (skeleton through parse)
- Create: `depgraph/tests/extractors/test_python_extractor.py`

- [ ] **Step 1: Write failing test for discover**

Create `depgraph/tests/extractors/test_python_extractor.py`:

```python
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
```

- [ ] **Step 2: Verify failure**

Run: `pytest depgraph/tests/extractors/test_python_extractor.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement discover + parse**

Create `depgraph/extractors/generic/python/extract.py`:

```python
"""Python language extractor.

Five-stage contract: discover -> parse -> emit primitives -> run
detectors -> write. This file lands in stages across tasks 3, 4, 5.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator


DEFAULT_EXCLUDES = (
    ".venv", "venv", "__pycache__", ".git", ".tox", "node_modules",
    "dist", "build", "target", ".mypy_cache", ".pytest_cache",
)


def discover_files(
    root: Path,
    extra_excludes: list[str] | None = None,
) -> Iterator[Path]:
    """Yield `.py` files under `root`, skipping common build/vendor dirs."""
    excludes = set(DEFAULT_EXCLUDES) | set(extra_excludes or ())
    for path in sorted(root.rglob("*.py")):
        if any(part in excludes for part in path.relative_to(root).parts):
            continue
        yield path


def parse_file(path: Path) -> tuple[ast.AST | None, str | None]:
    """Parse a single file. Returns (tree, None) on success or
    (None, diagnostic_message) on syntax error."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        return ast.parse(source, filename=str(path)), None
    except SyntaxError as e:
        return None, f"parse_error: {path}:{e.lineno}: {e.msg}"
```

- [ ] **Step 4: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_extractor.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/extract.py depgraph/tests/extractors/test_python_extractor.py
git commit -m "$(cat <<'EOF'
extractors/python: discover + parse stages

Walks a repo for .py files, skipping common build/vendor dirs plus
per-repo exclude globs. Parses with stdlib ast; SyntaxError returns
a diagnostic string instead of crashing.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Python extractor — emit AST primitives

**Files:**
- Modify: `depgraph/extractors/generic/python/extract.py`
- Modify: `depgraph/tests/extractors/test_python_extractor.py`

- [ ] **Step 1: Write failing tests for primitives**

Append to `depgraph/tests/extractors/test_python_extractor.py`:

```python
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
```

- [ ] **Step 2: Verify failure**

Run: `pytest depgraph/tests/extractors/test_python_extractor.py -v`
Expected: 5 new tests fail (import error on `emit_primitives`).

- [ ] **Step 3: Implement emit_primitives**

Append to `depgraph/extractors/generic/python/extract.py`:

```python
def _qualname(stack: list[str], name: str) -> str:
    return ".".join(stack + [name])


def emit_primitives(
    tree: ast.AST,
    *,
    repo_key: str,
    rel_path: str,
) -> list[dict]:
    """Emit module/class/function/import_edge/call_edge primitive nodes."""
    nodes: list[dict] = []
    module_id = f"{repo_key}:{rel_path}:<module>"
    nodes.append({
        "id": module_id, "kind": "module",
        "repo": repo_key, "file": rel_path, "name": "<module>",
        "parent_id": None,
    })

    class_stack: list[str] = []
    current_fn_id: list[str | None] = [None]

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef):
            qual = _qualname(class_stack, node.name)
            cid = f"{repo_key}:{rel_path}:{qual}"
            parent = (
                f"{repo_key}:{rel_path}:{_qualname(class_stack[:-1], class_stack[-1])}"
                if class_stack else module_id
            ) if class_stack else module_id
            nodes.append({
                "id": cid, "kind": "class", "repo": repo_key,
                "file": rel_path, "name": node.name,
                "parent_id": parent, "line": node.lineno,
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "bases": [ast.unparse(b) for b in node.bases],
            })
            class_stack.append(node.name)
            self.generic_visit(node)
            class_stack.pop()

        def _visit_function(self, node):
            qual = _qualname(class_stack, node.name)
            fid = f"{repo_key}:{rel_path}:{qual}"
            parent = (
                f"{repo_key}:{rel_path}:{_qualname(class_stack[:-1], class_stack[-1])}"
                if class_stack else None
            )
            nodes.append({
                "id": fid, "kind": "function", "repo": repo_key,
                "file": rel_path, "name": node.name,
                "parent_id": parent, "line": node.lineno,
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "args": [a.arg for a in node.args.args],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })
            prev = current_fn_id[0]
            current_fn_id[0] = fid
            self.generic_visit(node)
            current_fn_id[0] = prev

        visit_FunctionDef = _visit_function
        visit_AsyncFunctionDef = _visit_function

        def visit_Import(self, node: ast.Import):
            for alias in node.names:
                nodes.append({
                    "id": f"{module_id}#import:{alias.name}",
                    "kind": "import_edge", "from_id": module_id,
                    "target": alias.name, "line": node.lineno,
                })

        def visit_ImportFrom(self, node: ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                target = f"{mod}.{alias.name}" if mod else alias.name
                nodes.append({
                    "id": f"{module_id}#import:{target}",
                    "kind": "import_edge", "from_id": module_id,
                    "target": target, "line": node.lineno,
                })

        def visit_Call(self, node: ast.Call):
            try:
                target = ast.unparse(node.func)
            except Exception:
                target = "<unparseable>"
            origin = current_fn_id[0] or module_id
            nodes.append({
                "id": f"{origin}#call:{target}:{node.lineno}",
                "kind": "call_edge", "from_id": origin,
                "target": target, "line": node.lineno,
            })
            self.generic_visit(node)

    Visitor().visit(tree)
    return nodes
```

- [ ] **Step 4: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_extractor.py -v`
Expected: 10 passed (5 from Task 3 + 5 new).

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/extract.py depgraph/tests/extractors/test_python_extractor.py
git commit -m "$(cat <<'EOF'
extractors/python: emit AST primitives

Emits module/class/function (incl. methods) plus import_edge and
call_edge primitives via stdlib ast. IDs use repo_key:rel_path:qualname.
Methods carry parent_id; calls attribute to nearest enclosing function.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Python extractor — detector loading + dispatch + write + CLI

**Files:**
- Modify: `depgraph/extractors/generic/python/extract.py`
- Modify: `depgraph/tests/extractors/test_python_extractor.py`

- [ ] **Step 1: Write failing tests**

Append to test file:

```python
import json
import subprocess
import sys

from extractors.generic.python.extract import (
    load_detectors, apply_mutations, write_nodes,
)
from extractors.generic.python.detector_api import RelabelNode, AddNode


def test_load_detector_from_framework_dir():
    detectors = load_detectors(names=["fastapi"], extra_paths=[])
    # fastapi detector not yet implemented; test only that loader doesn't
    # crash on a missing name with allow_missing=True
    pass


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
    (tmp_repo / "a.py").write_text("def hi(): pass\n")
    extractor = Path(__file__).resolve().parents[2] / "depgraph" / "extractors" / "generic" / "python" / "extract.py"
    r = subprocess.run(
        [sys.executable, str(extractor),
         "--repo-key", "r", "--repo-path", str(tmp_repo),
         "--data-dir", str(tmp_data_dir),
         "--detectors", ""],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "wrote" in r.stdout
    func_dir = tmp_data_dir / "nodes" / "functions"
    assert any(p.suffix == ".json" for p in func_dir.iterdir())
```

- [ ] **Step 2: Verify failure**

Run: `pytest depgraph/tests/extractors/test_python_extractor.py -v`
Expected: 6 new tests fail.

- [ ] **Step 3: Implement loader + apply + write + CLI**

Append to `depgraph/extractors/generic/python/extract.py`:

```python
import argparse
import importlib.util
import json
import sys
from typing import Iterable

from .detector_api import (
    Detector, DetectorContext, Mutation,
    RelabelNode, AddEdge, AddNode,
)


FRAMEWORK_DETECTOR_DIR = Path(__file__).parent / "detectors"


def _load_detector_module(path: Path) -> type[Detector] | None:
    spec = importlib.util.spec_from_file_location(f"detector_{path.stem}", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in vars(mod).values():
        if (isinstance(attr, type) and issubclass(attr, Detector)
                and attr is not Detector):
            return attr
    return None


def load_detectors(
    names: list[str],
    extra_paths: list[Path],
) -> list[Detector]:
    """Load detectors by name from framework dir + extra_paths."""
    if not names or names == [""]:
        return []
    search = [FRAMEWORK_DETECTOR_DIR, *extra_paths]
    loaded: list[Detector] = []
    for name in names:
        found_cls = None
        for d in search:
            candidate = d / f"{name}.py"
            if candidate.exists():
                found_cls = _load_detector_module(candidate)
                if found_cls:
                    break
        if found_cls is None:
            available = sorted(p.stem for d in search if d.exists()
                               for p in d.glob("*.py")
                               if not p.stem.startswith("_"))
            raise ValueError(
                f"unknown detector: {name!r}. available: {available}"
            )
        loaded.append(found_cls())
    return loaded


def apply_mutations(
    primitives: list[dict],
    mutations: Iterable[Mutation],
) -> list[dict]:
    by_id = {n["id"]: dict(n) for n in primitives}
    extras: list[dict] = []
    for m in mutations:
        if isinstance(m, RelabelNode):
            if m.node_id in by_id:
                by_id[m.node_id]["kind"] = m.new_kind
                by_id[m.node_id].update(m.metadata)
        elif isinstance(m, AddNode):
            payload = dict(m.payload)
            payload["kind"] = m.kind
            extras.append(payload)
        elif isinstance(m, AddEdge):
            extras.append({
                "id": f"{m.from_id}#edge:{m.kind}:{m.to_id}",
                "kind": f"{m.kind}_edge",
                "from_id": m.from_id, "to_id": m.to_id,
            })
    return list(by_id.values()) + extras


_KIND_DIR = {
    "module": "modules", "class": "classes", "function": "functions",
    "import_edge": "imports", "call_edge": "calls",
}


def _safe_filename(node_id: str) -> str:
    return node_id.replace("/", "__").replace(":", "__") + ".json"


def write_nodes(nodes: list[dict], data_dir: Path) -> None:
    for n in nodes:
        kind = n["kind"]
        sub = _KIND_DIR.get(kind, kind + "s")
        out_dir = data_dir / "nodes" / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / _safe_filename(n["id"])
        path.write_text(json.dumps(n, indent=2, sort_keys=True) + "\n")


def _run_detectors(
    detectors: list[Detector],
    tree: ast.AST,
    primitives: list[dict],
    ctx: DetectorContext,
) -> list[Mutation]:
    out: list[Mutation] = []
    for d in detectors:
        try:
            out.extend(d.detect(tree, primitives, ctx))
        except Exception as exc:
            print(f"detector_error: {d.name or type(d).__name__} "
                  f"on {ctx.file_path}: {exc}", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-key", required=True)
    p.add_argument("--repo-path", required=True, type=Path)
    p.add_argument("--data-dir", required=True, type=Path)
    p.add_argument("--detectors", default="")
    p.add_argument("--detector-path", action="append", default=[], type=Path)
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--only", default=None, type=Path)
    args = p.parse_args(argv)

    names = [n.strip() for n in args.detectors.split(",") if n.strip()]
    detectors = load_detectors(names, args.detector_path)

    files: Iterable[Path]
    if args.only:
        files = [args.only]
    else:
        files = list(discover_files(args.repo_path, args.exclude))

    total_nodes = 0
    labeled = 0
    skipped = 0
    all_nodes: list[dict] = []
    for f in files:
        rel = f.relative_to(args.repo_path).as_posix()
        tree, err = parse_file(f)
        if err:
            print(err, file=sys.stderr)
            skipped += 1
            continue
        prims = emit_primitives(tree, repo_key=args.repo_key, rel_path=rel)
        ctx = DetectorContext(
            repo_key=args.repo_key, file_path=rel,
            project_config={"detectors": names},
        )
        muts = _run_detectors(detectors, tree, prims, ctx)
        labeled += sum(1 for m in muts if isinstance(m, RelabelNode))
        nodes = apply_mutations(prims, muts)
        all_nodes.extend(nodes)
        total_nodes += len(nodes)

    write_nodes(all_nodes, args.data_dir)
    print(f"wrote {total_nodes} nodes ({labeled} labeled by detectors), "
          f"skipped {skipped} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_extractor.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/extract.py depgraph/tests/extractors/test_python_extractor.py
git commit -m "$(cat <<'EOF'
extractors/python: detector loading + dispatch + write + CLI

Completes the five-stage contract. Detectors load from framework
detectors/ plus optional --detector-path dirs; mutations apply to
primitives; per-kind node files write under data_dir/nodes/.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Python TEMPLATE detector + README

**Files:**
- Create: `depgraph/extractors/generic/python/TEMPLATE_detector.py`
- Create: `depgraph/extractors/generic/python/README.md`
- Create: `depgraph/extractors/generic/python/detectors/__init__.py`

- [ ] **Step 1: Create TEMPLATE**

Create `depgraph/extractors/generic/python/TEMPLATE_detector.py`:

```python
"""TEMPLATE: copy to detectors/<your_name>.py and fill in.

A detector recognizes a specific framework or pattern in Python source.
It receives the AST plus the primitives already emitted for one file,
and returns mutations that re-label primitives or add new nodes/edges.
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation,
    RelabelNode, AddEdge, AddNode,
)


class MyDetector(Detector):
    name = "my_detector"  # TODO: rename. Matches the filename without .py.

    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        mutations: list[Mutation] = []

        # TODO: walk `tree` looking for the construct you care about.
        # TODO: for each match, look up the corresponding primitive in
        #       `primitives` by node_id, and emit a RelabelNode mutation
        #       to change its kind + add metadata.

        # Example:
        # for node in ast.walk(tree):
        #     if isinstance(node, ast.FunctionDef) and is_my_pattern(node):
        #         node_id = f"{ctx.repo_key}:{ctx.file_path}:{node.name}"
        #         mutations.append(RelabelNode(
        #             node_id=node_id,
        #             new_kind="my_kind",
        #             metadata={"extra": "info"},
        #         ))

        return mutations
```

- [ ] **Step 2: Create detectors package**

Create `depgraph/extractors/generic/python/detectors/__init__.py` (empty).

- [ ] **Step 3: Create README**

Create `depgraph/extractors/generic/python/README.md`:

````markdown
# Python language extractor

Walks Python source with stdlib `ast`. Emits module/class/function
primitives plus import/call edges. Detectors layer on framework
semantics (FastAPI endpoints, SQLAlchemy models, etc.).

## Run

```bash
python3 extract.py \
  --repo-key api --repo-path ~/myproj-api \
  --data-dir ~/myproj-knowledge-graph/depgraph \
  --detectors fastapi,sqlalchemy,pydantic,pytest
```

## Authoring a detector

1. Copy `TEMPLATE_detector.py` to `detectors/<name>.py`.
2. Implement `detect()` — see the template for the contract.
3. Add a single-file test in `~/tools/knowledge-graph/depgraph/tests/extractors/test_python_detectors.py`.
4. Add an eval case under `eval/corpus/python/_seed_<name>/`.
5. Open a PR. See `CONTRIBUTING-detectors.md` at repo root.

## Detector lookup order

1. Framework dir: `~/tools/knowledge-graph/depgraph/extractors/generic/python/detectors/`.
2. Project-local: `<data-repo>/depgraph/extractors/detectors/` (via `--detector-path`).
````

- [ ] **Step 4: Commit**

```bash
git add depgraph/extractors/generic/python/TEMPLATE_detector.py depgraph/extractors/generic/python/README.md depgraph/extractors/generic/python/detectors/__init__.py
git commit -m "$(cat <<'EOF'
extractors/python: TEMPLATE + README

Scaffold for community detector PRs. README documents the five-stage
contract, run command, and contribution path.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: fastapi detector

**Reference:** `/home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_api.py` — port the FastAPI route recognition logic.

**Files:**
- Create: `depgraph/extractors/generic/python/detectors/fastapi.py`
- Create: `depgraph/tests/extractors/test_python_detectors.py`

- [ ] **Step 1: Read Concorda's FastAPI logic**

Run: `grep -n -A 30 'kind.*endpoint' /home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_api.py | head -100`

Identify the decorators that mark endpoints and the metadata extracted (route, method, response model). Take notes.

- [ ] **Step 2: Write failing tests**

Create `depgraph/tests/extractors/test_python_detectors.py`:

```python
import ast
from pathlib import Path

from extractors.generic.python.detector_api import (
    DetectorContext, RelabelNode,
)
from extractors.generic.python.detectors.fastapi import FastAPIDetector
from extractors.generic.python.extract import emit_primitives


def _run(src: str):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path="a.py")
    ctx = DetectorContext(repo_key="r", file_path="a.py", project_config={})
    return prims, FastAPIDetector().detect(tree, prims, ctx)


def test_fastapi_get_decorator_relabels_function():
    src = (
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/items')\n"
        "def list_items(): pass\n"
    )
    prims, muts = _run(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert len(rl) == 1
    assert rl[0].new_kind == "endpoint"
    assert rl[0].metadata["route"] == "/items"
    assert rl[0].metadata["method"] == "GET"


def test_fastapi_post_decorator():
    src = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.post('/x')\n"
        "def f(): pass\n"
    )
    _, muts = _run(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert rl[0].metadata["method"] == "POST"
    assert rl[0].metadata["route"] == "/x"


def test_fastapi_ignores_unrelated_decorators():
    src = "@property\ndef f(self): pass\n"
    _, muts = _run(src)
    assert muts == []


def test_fastapi_handles_async_endpoints():
    src = (
        "from fastapi import APIRouter\n"
        "r = APIRouter()\n"
        "@r.get('/x')\n"
        "async def f(): pass\n"
    )
    _, muts = _run(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert rl[0].new_kind == "endpoint"
```

- [ ] **Step 3: Verify failure**

Run: `pytest depgraph/tests/extractors/test_python_detectors.py -v`
Expected: import error — `fastapi` module not found.

- [ ] **Step 4: Implement detector**

Create `depgraph/extractors/generic/python/detectors/fastapi.py`:

```python
"""Detect FastAPI endpoint definitions.

A function is an endpoint if its decorator list contains
`<obj>.<http_method>(...)` where http_method is one of
get/post/put/patch/delete/options/head, and <obj> is plausibly a
FastAPI / APIRouter instance (we don't try to type-resolve; the
decorator shape is enough in practice).
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)

_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _endpoint_decorator(dec: ast.expr) -> tuple[str, str] | None:
    """If `dec` is a FastAPI route decorator, return (METHOD, route).
    Otherwise None."""
    if not isinstance(dec, ast.Call):
        return None
    func = dec.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in _METHODS:
        return None
    if not dec.args:
        return None
    first = dec.args[0]
    if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
        return None
    return func.attr.upper(), first.value


class FastAPIDetector(Detector):
    name = "fastapi"

    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        muts: list[Mutation] = []
        by_qualname: dict[str, dict] = {}
        for n in primitives:
            if n["kind"] == "function":
                qual = n["id"].split(":", 2)[-1]
                by_qualname[qual] = n

        class V(ast.NodeVisitor):
            def __init__(self):
                self.class_stack: list[str] = []

            def visit_ClassDef(self, node: ast.ClassDef):
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()

            def _visit_fn(self, node):
                qual = ".".join(self.class_stack + [node.name])
                prim = by_qualname.get(qual)
                if not prim:
                    return
                for dec in node.decorator_list:
                    result = _endpoint_decorator(dec)
                    if result:
                        method, route = result
                        muts.append(RelabelNode(
                            node_id=prim["id"],
                            new_kind="endpoint",
                            metadata={"route": route, "method": method},
                        ))
                        break
                self.generic_visit(node)

            visit_FunctionDef = _visit_fn
            visit_AsyncFunctionDef = _visit_fn

        V().visit(tree)
        return muts
```

- [ ] **Step 5: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_detectors.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/generic/python/detectors/fastapi.py depgraph/tests/extractors/test_python_detectors.py
git commit -m "$(cat <<'EOF'
extractors/python: fastapi detector

Recognizes @router.<method>(path) and @app.<method>(path) decorators
and relabels the decorated function as kind=endpoint with route +
method metadata. Lifted from Concorda's extract_api.py.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: sqlalchemy detector

**Reference:** `extract_api.py` SQLAlchemy section (`__tablename__`, `DeclarativeBase` subclass).

**Files:**
- Create: `depgraph/extractors/generic/python/detectors/sqlalchemy.py`
- Modify: `depgraph/tests/extractors/test_python_detectors.py`

- [ ] **Step 1: Read Concorda's SQLAlchemy logic**

Run: `grep -n -B 2 -A 25 'tablename\|DeclarativeBase\|kind.*model' /home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_api.py | head -80`

- [ ] **Step 2: Write failing tests**

Append to `depgraph/tests/extractors/test_python_detectors.py`:

```python
from extractors.generic.python.detectors.sqlalchemy import SQLAlchemyDetector


def _run_sa(src: str):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path="a.py")
    ctx = DetectorContext(repo_key="r", file_path="a.py", project_config={})
    return prims, SQLAlchemyDetector().detect(tree, prims, ctx)


def test_sqlalchemy_declarative_base_subclass_relabeled_model():
    src = (
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase): pass\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n"
    )
    _, muts = _run_sa(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    user = next(m for m in rl if m.node_id.endswith(":User"))
    assert user.new_kind == "model"
    assert user.metadata["tablename"] == "users"


def test_sqlalchemy_ignores_plain_class():
    src = "class Plain: pass\n"
    _, muts = _run_sa(src)
    assert muts == []
```

- [ ] **Step 3: Verify failure**

Run: `pytest depgraph/tests/extractors/test_python_detectors.py -v`
Expected: import error.

- [ ] **Step 4: Implement**

Create `depgraph/extractors/generic/python/detectors/sqlalchemy.py`:

```python
"""Detect SQLAlchemy model classes.

A class is a model if it (transitively) inherits from `DeclarativeBase`
or any class named `Base`. We don't follow imports across files; the
heuristic is: any class with `__tablename__` assigned at class body
scope, OR any class whose base list contains a name from a configured
set of base names ("Base", "DeclarativeBase").
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)


_BASE_NAMES = {"Base", "DeclarativeBase"}


def _tablename(cls: ast.ClassDef) -> str | None:
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        return stmt.value.value
    return None


def _has_model_base(cls: ast.ClassDef, model_classes: set[str]) -> bool:
    for base in cls.bases:
        if isinstance(base, ast.Name) and (base.id in _BASE_NAMES or base.id in model_classes):
            return True
        if isinstance(base, ast.Attribute) and base.attr in _BASE_NAMES:
            return True
    return False


class SQLAlchemyDetector(Detector):
    name = "sqlalchemy"

    def detect(
        self,
        tree: ast.AST,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        muts: list[Mutation] = []
        by_qualname = {
            n["id"].split(":", 2)[-1]: n
            for n in primitives if n["kind"] == "class"
        }
        model_classes: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                tn = _tablename(node)
                if tn or _has_model_base(node, model_classes):
                    model_classes.add(node.name)
                    prim = by_qualname.get(node.name)
                    if prim:
                        meta: dict[str, Any] = {}
                        if tn:
                            meta["tablename"] = tn
                        muts.append(RelabelNode(
                            node_id=prim["id"],
                            new_kind="model",
                            metadata=meta,
                        ))
        return muts
```

- [ ] **Step 5: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_detectors.py -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/generic/python/detectors/sqlalchemy.py depgraph/tests/extractors/test_python_detectors.py
git commit -m "$(cat <<'EOF'
extractors/python: sqlalchemy detector

Relabels classes that inherit from DeclarativeBase/Base or assign
__tablename__ as kind=model. Lifted from Concorda's extract_api.py.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: pydantic detector

**Files:**
- Create: `depgraph/extractors/generic/python/detectors/pydantic.py`
- Modify: `depgraph/tests/extractors/test_python_detectors.py`

- [ ] **Step 1: Read Concorda's Pydantic logic**

Run: `grep -n -B 2 -A 25 'BaseModel\|kind.*schema\|fields' /home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_api.py | head -80`

- [ ] **Step 2: Write failing tests**

Append:

```python
from extractors.generic.python.detectors.pydantic import PydanticDetector


def _run_pd(src: str):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path="a.py")
    ctx = DetectorContext(repo_key="r", file_path="a.py", project_config={})
    return prims, PydanticDetector().detect(tree, prims, ctx)


def test_pydantic_basemodel_subclass_relabeled_schema():
    src = (
        "from pydantic import BaseModel\n"
        "class UserIn(BaseModel):\n"
        "    name: str\n"
        "    age: int\n"
    )
    _, muts = _run_pd(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    assert len(rl) == 1
    assert rl[0].new_kind == "schema"
    assert sorted(rl[0].metadata["fields"]) == ["age", "name"]
```

- [ ] **Step 3: Verify failure / implement**

Create `depgraph/extractors/generic/python/detectors/pydantic.py`:

```python
"""Detect Pydantic schema classes.

A class is a schema if it (visibly) inherits from `BaseModel`. We
extract annotated field names from the class body.
"""
from __future__ import annotations

import ast
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)

_SCHEMA_BASES = {"BaseModel"}


def _field_names(cls: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for stmt in cls.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            names.append(stmt.target.id)
    return names


class PydanticDetector(Detector):
    name = "pydantic"

    def detect(self, tree, primitives, ctx):
        muts: list[Mutation] = []
        by_qualname = {
            n["id"].split(":", 2)[-1]: n
            for n in primitives if n["kind"] == "class"
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if any(
                    (isinstance(b, ast.Name) and b.id in _SCHEMA_BASES)
                    or (isinstance(b, ast.Attribute) and b.attr in _SCHEMA_BASES)
                    for b in node.bases
                ):
                    prim = by_qualname.get(node.name)
                    if prim:
                        muts.append(RelabelNode(
                            node_id=prim["id"],
                            new_kind="schema",
                            metadata={"fields": _field_names(node)},
                        ))
        return muts
```

- [ ] **Step 4: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_detectors.py -v`

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/detectors/pydantic.py depgraph/tests/extractors/test_python_detectors.py
git commit -m "$(cat <<'EOF'
extractors/python: pydantic detector

Relabels BaseModel subclasses as kind=schema with the list of
annotated field names. Lifted from Concorda's extract_api.py.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: pytest detector

**Files:**
- Create: `depgraph/extractors/generic/python/detectors/pytest.py`
- Modify: `depgraph/tests/extractors/test_python_detectors.py`

- [ ] **Step 1: Write failing test**

Append:

```python
from extractors.generic.python.detectors.pytest import PytestDetector


def _run_pt(src: str, rel="test_a.py"):
    tree = ast.parse(src)
    prims = emit_primitives(tree, repo_key="r", rel_path=rel)
    ctx = DetectorContext(repo_key="r", file_path=rel, project_config={})
    return prims, PytestDetector().detect(tree, prims, ctx)


def test_pytest_function_relabeled_test():
    src = "def test_x(): pass\ndef helper(): pass\n"
    _, muts = _run_pt(src)
    rl = [m for m in muts if isinstance(m, RelabelNode) and m.new_kind == "test"]
    ids = [m.node_id for m in rl]
    assert any(i.endswith(":test_x") for i in ids)
    assert not any(i.endswith(":helper") for i in ids)


def test_pytest_test_class_methods_relabeled():
    src = "class TestThing:\n    def test_m(self): pass\n    def helper(self): pass\n"
    _, muts = _run_pt(src)
    rl = [m for m in muts if isinstance(m, RelabelNode)]
    names = [m.node_id.split(":")[-1] for m in rl]
    assert "TestThing.test_m" in names
    assert "TestThing.helper" not in names


def test_pytest_only_fires_in_test_files():
    src = "def test_x(): pass\n"
    _, muts = _run_pt(src, rel="not_a_test.py")
    assert muts == []
```

- [ ] **Step 2: Verify failure / implement**

Create `depgraph/extractors/generic/python/detectors/pytest.py`:

```python
"""Detect pytest test functions/methods.

A function is a test if:
- the file matches `test_*.py` or `*_test.py`, AND
- the function name starts with `test_`, AND
- if inside a class, the class name starts with `Test`.
"""
from __future__ import annotations

import ast
from typing import Any
from pathlib import PurePosixPath

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)


def _is_test_file(path: str) -> bool:
    name = PurePosixPath(path).name
    return name.startswith("test_") or name.endswith("_test.py")


class PytestDetector(Detector):
    name = "pytest"

    def detect(self, tree, primitives, ctx):
        if not _is_test_file(ctx.file_path):
            return []
        by_qualname = {
            n["id"].split(":", 2)[-1]: n
            for n in primitives if n["kind"] == "function"
        }
        muts: list[Mutation] = []

        class V(ast.NodeVisitor):
            def __init__(self):
                self.class_stack: list[str] = []

            def visit_ClassDef(self, node):
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()

            def _visit_fn(self, node):
                if self.class_stack:
                    if not all(c.startswith("Test") for c in self.class_stack):
                        return
                if not node.name.startswith("test_"):
                    return
                qual = ".".join(self.class_stack + [node.name])
                prim = by_qualname.get(qual)
                if prim:
                    muts.append(RelabelNode(
                        node_id=prim["id"], new_kind="test", metadata={},
                    ))

            visit_FunctionDef = _visit_fn
            visit_AsyncFunctionDef = _visit_fn

        V().visit(tree)
        return muts
```

- [ ] **Step 3: Verify pass**

Run: `pytest depgraph/tests/extractors/test_python_detectors.py -v`

- [ ] **Step 4: Commit**

```bash
git add depgraph/extractors/generic/python/detectors/pytest.py depgraph/tests/extractors/test_python_detectors.py
git commit -m "$(cat <<'EOF'
extractors/python: pytest detector

Relabels test_* functions in test_*.py / *_test.py files (and methods
of Test* classes) as kind=test. Lifted from Concorda's extract_api.py.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: TypeScript detector API + extractor scaffolding

**Reference:** `/home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_web.ts`, plus the existing `depgraph/extractors/generic/typescript/route-calls.ts`.

**Files:**
- Create: `depgraph/extractors/generic/typescript/detector_api.ts`
- Create: `depgraph/extractors/generic/typescript/extract.ts`
- Create: `depgraph/tests/extractors/test_typescript_extractor.py`

- [ ] **Step 1: Write failing Python-driven test**

Create `depgraph/tests/extractors/test_typescript_extractor.py`:

```python
"""Drives the TS extractor via tsx subprocess. Asserts on emitted JSON."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

EXTRACTOR = (
    Path(__file__).resolve().parents[2]
    / "depgraph" / "extractors" / "generic" / "typescript" / "extract.ts"
)


pytestmark = pytest.mark.skipif(
    not shutil.which("npx"),
    reason="npx required for TS extractor tests",
)


def _run(repo: Path, data: Path, detectors: str = ""):
    r = subprocess.run(
        ["npx", "tsx", str(EXTRACTOR),
         "--repo-key", "r", "--repo-path", str(repo),
         "--data-dir", str(data), "--detectors", detectors],
        capture_output=True, text=True,
        cwd=EXTRACTOR.parent,
    )
    return r


def _read_nodes(data: Path, kind_subdir: str) -> list[dict]:
    d = data / "nodes" / kind_subdir
    if not d.exists():
        return []
    return [json.loads(p.read_text()) for p in d.iterdir()]


def test_ts_emits_module_per_file(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("export const x = 1\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    mods = _read_nodes(tmp_data_dir, "modules")
    assert any(m["file"] == "a.ts" for m in mods)


def test_ts_emits_function_primitive(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("export function f(){ return 1 }\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    fns = _read_nodes(tmp_data_dir, "functions")
    assert any(f["name"] == "f" for f in fns)


def test_ts_emits_import_edge(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text("import { x } from './b'\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    imports = _read_nodes(tmp_data_dir, "imports")
    assert any(e["target"] == "./b" for e in imports)
```

- [ ] **Step 2: Verify failure**

Run: `pytest depgraph/tests/extractors/test_typescript_extractor.py -v`
Expected: FAIL — extract.ts doesn't exist.

- [ ] **Step 3: Implement detector API**

Create `depgraph/extractors/generic/typescript/detector_api.ts`:

```typescript
import * as ts from "typescript";

export type RelabelNode = {
  type: "relabel";
  nodeId: string;
  newKind: string;
  metadata?: Record<string, unknown>;
};

export type AddEdge = {
  type: "edge";
  fromId: string;
  toId: string;
  kind: string;
};

export type AddNode = {
  type: "node";
  kind: string;
  payload: Record<string, unknown>;
};

export type Mutation = RelabelNode | AddEdge | AddNode;

export type DetectorContext = {
  repoKey: string;
  filePath: string;
  projectConfig: Record<string, unknown>;
};

export type Primitive = {
  id: string;
  kind: string;
  name?: string;
  file?: string;
  parentId?: string | null;
  [k: string]: unknown;
};

export interface Detector {
  name: string;
  detect(
    sourceFile: ts.SourceFile,
    primitives: Primitive[],
    ctx: DetectorContext,
  ): Mutation[];
}
```

- [ ] **Step 4: Implement extractor**

Create `depgraph/extractors/generic/typescript/extract.ts`:

```typescript
#!/usr/bin/env tsx
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
  RelabelNode, AddEdge, AddNode,
} from "./detector_api.js";

const DEFAULT_EXCLUDES = new Set([
  "node_modules", "dist", "build", ".git", "coverage", ".next",
  ".turbo", "target", ".venv",
]);
const SOURCE_EXTS = new Set([".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"]);

function* discoverFiles(root: string, extraExcludes: string[]): Generator<string> {
  const excludes = new Set([...DEFAULT_EXCLUDES, ...extraExcludes]);
  function* walk(dir: string): Generator<string> {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      const rel = path.relative(root, full).split(path.sep);
      if (rel.some((p) => excludes.has(p))) continue;
      if (entry.isDirectory()) yield* walk(full);
      else if (entry.isFile() && SOURCE_EXTS.has(path.extname(entry.name))) {
        yield full;
      }
    }
  }
  yield* walk(root);
}

function emitPrimitives(
  sf: ts.SourceFile,
  repoKey: string,
  relPath: string,
): Primitive[] {
  const out: Primitive[] = [];
  const moduleId = `${repoKey}:${relPath}:<module>`;
  out.push({
    id: moduleId, kind: "module", repo: repoKey, file: relPath,
    name: "<module>", parentId: null,
  });

  const classStack: string[] = [];
  let currentFnId: string | null = null;

  const visit = (node: ts.Node) => {
    if (ts.isClassDeclaration(node) && node.name) {
      const qual = [...classStack, node.name.text].join(".");
      const id = `${repoKey}:${relPath}:${qual}`;
      out.push({
        id, kind: "class", repo: repoKey, file: relPath,
        name: node.name.text, parentId: moduleId,
        line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
      });
      classStack.push(node.name.text);
      ts.forEachChild(node, visit);
      classStack.pop();
      return;
    }
    if (
      (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node) ||
       ts.isArrowFunction(node) || ts.isFunctionExpression(node)) &&
      "name" in node && node.name && ts.isIdentifier(node.name)
    ) {
      const name = node.name.text;
      const qual = [...classStack, name].join(".");
      const id = `${repoKey}:${relPath}:${qual}`;
      out.push({
        id, kind: "function", repo: repoKey, file: relPath,
        name, parentId: classStack.length ? `${repoKey}:${relPath}:${classStack.join(".")}` : null,
        line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        isExported: !!(node.modifiers || []).find(m => m.kind === ts.SyntaxKind.ExportKeyword),
      });
      const prevFn = currentFnId;
      currentFnId = id;
      ts.forEachChild(node, visit);
      currentFnId = prevFn;
      return;
    }
    if (ts.isImportDeclaration(node)) {
      const spec = node.moduleSpecifier;
      if (ts.isStringLiteral(spec)) {
        out.push({
          id: `${moduleId}#import:${spec.text}`,
          kind: "import_edge", from_id: moduleId,
          target: spec.text,
          line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        });
      }
    }
    if (ts.isCallExpression(node)) {
      let target = node.expression.getText(sf);
      const line = sf.getLineAndCharacterOfPosition(node.getStart()).line + 1;
      const origin = currentFnId ?? moduleId;
      out.push({
        id: `${origin}#call:${target}:${line}`,
        kind: "call_edge", from_id: origin, target, line,
      });
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  return out;
}

const KIND_DIR: Record<string, string> = {
  module: "modules", class: "classes", function: "functions",
  import_edge: "imports", call_edge: "calls",
};

function safeFilename(id: string): string {
  return id.replace(/\//g, "__").replace(/:/g, "__") + ".json";
}

function writeNodes(nodes: Primitive[], dataDir: string): void {
  for (const n of nodes) {
    const sub = KIND_DIR[n.kind as string] ?? `${n.kind}s`;
    const dir = path.join(dataDir, "nodes", sub);
    fs.mkdirSync(dir, { recursive: true });
    const sorted = Object.fromEntries(
      Object.entries(n).sort(([a],[b]) => a.localeCompare(b))
    );
    fs.writeFileSync(
      path.join(dir, safeFilename(n.id)),
      JSON.stringify(sorted, null, 2) + "\n",
    );
  }
}

function applyMutations(prims: Primitive[], muts: Mutation[]): Primitive[] {
  const byId = new Map(prims.map(p => [p.id, { ...p }]));
  const extras: Primitive[] = [];
  for (const m of muts) {
    if (m.type === "relabel") {
      const n = byId.get(m.nodeId);
      if (n) {
        n.kind = m.newKind;
        Object.assign(n, m.metadata ?? {});
      }
    } else if (m.type === "node") {
      extras.push({ id: m.payload.id as string, kind: m.kind, ...m.payload });
    } else if (m.type === "edge") {
      extras.push({
        id: `${m.fromId}#edge:${m.kind}:${m.toId}`,
        kind: `${m.kind}_edge`,
        from_id: m.fromId, to_id: m.toId,
      });
    }
  }
  return [...byId.values(), ...extras];
}

async function loadDetectors(names: string[], extraPaths: string[]): Promise<Detector[]> {
  if (names.length === 0) return [];
  const frameworkDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "detectors");
  const search = [frameworkDir, ...extraPaths];
  const out: Detector[] = [];
  for (const name of names) {
    let found: Detector | null = null;
    for (const dir of search) {
      const candidate = path.join(dir, `${name}.ts`);
      if (fs.existsSync(candidate)) {
        const mod = await import(pathToFileURL(candidate).href);
        const cls = Object.values(mod).find((v: any) =>
          typeof v === "function" && v.prototype && typeof v.prototype.detect === "function"
        ) as (new () => Detector) | undefined;
        if (cls) { found = new cls(); break; }
      }
    }
    if (!found) {
      throw new Error(`unknown detector: ${name}`);
    }
    out.push(found);
  }
  return out;
}

function parseArgs(argv: string[]) {
  const opts: Record<string, string | string[]> = {
    "--repo-key": "", "--repo-path": "", "--data-dir": "",
    "--detectors": "", "--detector-path": [], "--exclude": [], "--only": "",
  };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k in opts) {
      const v = argv[++i];
      if (Array.isArray(opts[k])) (opts[k] as string[]).push(v);
      else opts[k] = v;
    }
  }
  return opts;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const repoKey = args["--repo-key"] as string;
  const repoPath = args["--repo-path"] as string;
  const dataDir = args["--data-dir"] as string;
  const names = (args["--detectors"] as string).split(",").map(s => s.trim()).filter(Boolean);
  const detectors = await loadDetectors(names, args["--detector-path"] as string[]);
  const excludes = args["--exclude"] as string[];
  const only = args["--only"] as string;

  const files = only ? [only] : Array.from(discoverFiles(repoPath, excludes));
  let total = 0, labeled = 0, skipped = 0;
  const allNodes: Primitive[] = [];

  for (const f of files) {
    let source: string;
    try { source = fs.readFileSync(f, "utf-8"); }
    catch (e) { console.error(`parse_error: ${f}: ${e}`); skipped++; continue; }
    let sf: ts.SourceFile;
    try {
      sf = ts.createSourceFile(f, source, ts.ScriptTarget.Latest, true,
        f.endsWith(".tsx") || f.endsWith(".jsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    } catch (e) { console.error(`parse_error: ${f}: ${e}`); skipped++; continue; }

    const rel = path.relative(repoPath, f).split(path.sep).join("/");
    const prims = emitPrimitives(sf, repoKey, rel);
    const ctx: DetectorContext = {
      repoKey, filePath: rel, projectConfig: { detectors: names },
    };
    const muts: Mutation[] = [];
    for (const d of detectors) {
      try { muts.push(...d.detect(sf, prims, ctx)); }
      catch (e) { console.error(`detector_error: ${d.name} on ${rel}: ${e}`); }
    }
    labeled += muts.filter(m => m.type === "relabel").length;
    const nodes = applyMutations(prims, muts);
    allNodes.push(...nodes);
    total += nodes.length;
  }

  writeNodes(allNodes, dataDir);
  console.log(`wrote ${total} nodes (${labeled} labeled by detectors), skipped ${skipped} files`);
}

main().catch(e => { console.error(e); process.exit(1); });
```

- [ ] **Step 5: Verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_extractor.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/generic/typescript/extract.ts depgraph/extractors/generic/typescript/detector_api.ts depgraph/tests/extractors/test_typescript_extractor.py
git commit -m "$(cat <<'EOF'
extractors/typescript: detector API + entry point

Full five-stage extractor for TS/JS via the TypeScript Compiler API.
Emits module/class/function primitives plus import/call edges.
Detector loading mirrors the Python contract. Tests drive via tsx
subprocess and assert on emitted JSON.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: TypeScript TEMPLATE detector + README update

**Files:**
- Create: `depgraph/extractors/generic/typescript/TEMPLATE_detector.ts`
- Create: `depgraph/extractors/generic/typescript/detectors/.gitkeep`
- Modify: `depgraph/extractors/generic/typescript/README.md`

- [ ] **Step 1: Create TEMPLATE**

Create `depgraph/extractors/generic/typescript/TEMPLATE_detector.ts`:

```typescript
/**
 * TEMPLATE: copy to detectors/<your_name>.ts and fill in.
 *
 * A detector recognizes a specific framework or pattern in TS/JS
 * source. It receives the ts.SourceFile plus the primitives already
 * emitted for that file, and returns mutations.
 */
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
  RelabelNode, AddEdge, AddNode,
} from "../detector_api.js";

export class MyDetector implements Detector {
  name = "my_detector"; // TODO: rename; matches filename without .ts

  detect(
    sourceFile: ts.SourceFile,
    primitives: Primitive[],
    ctx: DetectorContext,
  ): Mutation[] {
    const mutations: Mutation[] = [];

    // TODO: walk sourceFile looking for the construct you care about.
    // TODO: for each match, find the primitive in `primitives` by id
    //       and emit a RelabelNode.

    // Example:
    // const visit = (node: ts.Node) => {
    //   if (ts.isFunctionDeclaration(node) && isMyPattern(node)) {
    //     const id = `${ctx.repoKey}:${ctx.filePath}:${node.name?.text}`;
    //     mutations.push({
    //       type: "relabel", nodeId: id, newKind: "my_kind",
    //       metadata: { extra: "info" },
    //     });
    //   }
    //   ts.forEachChild(node, visit);
    // };
    // visit(sourceFile);

    return mutations;
  }
}
```

- [ ] **Step 2: Create empty detectors dir**

Run: `mkdir -p depgraph/extractors/generic/typescript/detectors && touch depgraph/extractors/generic/typescript/detectors/.gitkeep`

- [ ] **Step 3: Update README**

Replace `depgraph/extractors/generic/typescript/README.md` with:

````markdown
# TypeScript / JavaScript language extractor

Walks JS/TS source with the [TypeScript Compiler API](https://github.com/microsoft/TypeScript-wiki/blob/master/Using-the-Compiler-API.md).
Run via `npx tsx extract.ts`.

## Setup (one-time)

```bash
cd ~/tools/knowledge-graph/depgraph/extractors/generic/typescript
npm install
```

## Run

```bash
npx tsx extract.ts \
  --repo-key web --repo-path ~/myproj-web \
  --data-dir ~/myproj-knowledge-graph/depgraph \
  --detectors react,vitest,route-calls
```

## Authoring a detector

1. Copy `TEMPLATE_detector.ts` to `detectors/<name>.ts`.
2. Implement `detect()`.
3. Add a test in `depgraph/tests/extractors/test_typescript_extractor.py` (drives via tsx subprocess).
4. Add an eval case under `eval/corpus/typescript/_seed_<name>/`.
5. Open a PR. See `CONTRIBUTING-detectors.md`.

## Detector lookup order

1. Framework dir: this directory's `detectors/`.
2. Project-local: `<data-repo>/depgraph/extractors/detectors/` (via `--detector-path`).
````

- [ ] **Step 4: Commit**

```bash
git add depgraph/extractors/generic/typescript/
git commit -m "$(cat <<'EOF'
extractors/typescript: TEMPLATE + README update

Scaffold for community detector PRs. README updated to reflect the
new entry point (extract.ts) and the detectors/ layout.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: react detector

**Reference:** `/home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_web.ts` — port component (PascalCase + JSX return) and hook (`use*` + calls other hooks) detection.

**Files:**
- Create: `depgraph/extractors/generic/typescript/detectors/react.ts`
- Modify: `depgraph/tests/extractors/test_typescript_extractor.py`

- [ ] **Step 1: Read Concorda's React logic**

Run: `grep -n -B 2 -A 25 'component\|JSX\|useState\|PascalCase\|hook' /home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_web.ts | head -120`

- [ ] **Step 2: Write failing tests**

Append to `test_typescript_extractor.py`:

```python
def test_react_component_relabeled(tmp_repo, tmp_data_dir):
    (tmp_repo / "C.tsx").write_text(
        "export function MyButton() { return <button>hi</button> }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    assert any(c["name"] == "MyButton" for c in comps)


def test_react_hook_relabeled(tmp_repo, tmp_data_dir):
    (tmp_repo / "h.ts").write_text(
        "import { useState } from 'react'\n"
        "export function useThing() { const [x, set] = useState(0); return x }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    hooks = _read_nodes(tmp_data_dir, "hooks")
    assert any(h["name"] == "useThing" for h in hooks)


def test_react_ignores_lowercase_function(tmp_repo, tmp_data_dir):
    (tmp_repo / "u.ts").write_text("export function helper() { return 1 }\n")
    r = _run(tmp_repo, tmp_data_dir, detectors="react")
    assert r.returncode == 0, r.stderr
    comps = _read_nodes(tmp_data_dir, "components")
    hooks = _read_nodes(tmp_data_dir, "hooks")
    assert not any(c["name"] == "helper" for c in comps + hooks)
```

- [ ] **Step 3: Verify failure / implement**

Create `depgraph/extractors/generic/typescript/detectors/react.ts`:

```typescript
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

function returnsJsx(fn: ts.FunctionLikeDeclaration): boolean {
  let found = false;
  function walk(node: ts.Node) {
    if (found) return;
    if (
      ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node) ||
      ts.isJsxFragment(node)
    ) {
      found = true;
      return;
    }
    ts.forEachChild(node, walk);
  }
  if (fn.body) walk(fn.body);
  return found;
}

function callsHook(fn: ts.FunctionLikeDeclaration): boolean {
  let found = false;
  function walk(node: ts.Node) {
    if (found) return;
    if (ts.isCallExpression(node)) {
      const t = node.expression.getText();
      const last = t.split(".").pop() || "";
      if (/^use[A-Z0-9]/.test(last)) {
        found = true;
        return;
      }
    }
    ts.forEachChild(node, walk);
  }
  if (fn.body) walk(fn.body);
  return found;
}

export class ReactDetector implements Detector {
  name = "react";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    const muts: Mutation[] = [];
    const byQualname = new Map<string, Primitive>();
    for (const p of primitives) {
      if (p.kind === "function") {
        const qual = p.id.split(":").slice(2).join(":");
        byQualname.set(qual, p);
      }
    }

    const visit = (node: ts.Node) => {
      if (
        (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) &&
        node.name && ts.isIdentifier(node.name)
      ) {
        const name = node.name.text;
        const prim = byQualname.get(name);
        if (prim) {
          if (/^[A-Z]/.test(name) && returnsJsx(node)) {
            muts.push({ type: "relabel", nodeId: prim.id, newKind: "component" });
          } else if (/^use[A-Z0-9]/.test(name) && callsHook(node)) {
            muts.push({ type: "relabel", nodeId: prim.id, newKind: "hook" });
          }
        }
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
    return muts;
  }
}
```

- [ ] **Step 4: Verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_extractor.py -v -k react`

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/typescript/detectors/react.ts depgraph/tests/extractors/test_typescript_extractor.py
git commit -m "$(cat <<'EOF'
extractors/typescript: react detector

Relabels PascalCase functions returning JSX as kind=component and
use*-prefixed functions that call other hooks as kind=hook.
Lifted from Concorda's extract_web.ts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: vitest detector

**Reference:** `/home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_tests.ts`.

**Files:**
- Create: `depgraph/extractors/generic/typescript/detectors/vitest.ts`
- Modify: `depgraph/tests/extractors/test_typescript_extractor.py`

- [ ] **Step 1: Read Concorda's logic**

Run: `head -100 /home/lgreenlee/concorda-knowledge-graph/depgraph/extractors/extract_tests.ts`

- [ ] **Step 2: Write failing test**

Append:

```python
def test_vitest_describe_emits_test_node(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.test.ts").write_text(
        "import { describe, it, expect } from 'vitest'\n"
        "describe('thing', () => { it('works', () => { expect(1).toBe(1) }) })\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    assert any(t.get("name") == "works" for t in tests)


def test_vitest_only_fires_in_test_files(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.ts").write_text(
        "describe('x', () => { it('y', () => {}) })\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="vitest")
    assert r.returncode == 0, r.stderr
    tests = _read_nodes(tmp_data_dir, "tests")
    assert tests == []
```

- [ ] **Step 3: Implement**

Create `depgraph/extractors/generic/typescript/detectors/vitest.ts`:

```typescript
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive, AddNode,
} from "../detector_api.js";

const TEST_FILE_RE = /(\.test|\.spec)\.(ts|tsx|js|jsx)$/;

export class VitestDetector implements Detector {
  name = "vitest";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    if (!TEST_FILE_RE.test(ctx.filePath)) return [];
    const muts: Mutation[] = [];
    const describeStack: string[] = [];

    const visit = (node: ts.Node) => {
      if (ts.isCallExpression(node) && ts.isIdentifier(node.expression)) {
        const fnName = node.expression.text;
        const firstArg = node.arguments[0];
        const label = firstArg && ts.isStringLiteralLike(firstArg) ? firstArg.text : "";
        if (fnName === "describe" && label) {
          describeStack.push(label);
          ts.forEachChild(node, visit);
          describeStack.pop();
          return;
        }
        if ((fnName === "it" || fnName === "test") && label) {
          const qual = [...describeStack, label].join(" > ");
          muts.push({
            type: "node",
            kind: "test",
            payload: {
              id: `${ctx.repoKey}:${ctx.filePath}:test:${qual}`,
              name: label,
              file: ctx.filePath,
              describe_path: [...describeStack],
              line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
            },
          });
        }
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
    return muts;
  }
}
```

- [ ] **Step 4: Verify**

Run: `pytest depgraph/tests/extractors/test_typescript_extractor.py -v -k vitest`

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/typescript/detectors/vitest.ts depgraph/tests/extractors/test_typescript_extractor.py
git commit -m "$(cat <<'EOF'
extractors/typescript: vitest detector

Walks describe/it/test calls in *.test.ts / *.spec.ts files and emits
kind=test nodes with describe_path. Lifted from Concorda's
extract_tests.ts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Promote route-calls.ts to a detector

**Files:**
- Move: `depgraph/extractors/generic/typescript/route-calls.ts` → `depgraph/extractors/generic/typescript/detectors/route-calls.ts`
- Modify: contents to implement Detector interface
- Modify: `depgraph/tests/extractors/test_typescript_extractor.py`

- [ ] **Step 1: Read existing route-calls.ts**

Run: `cat depgraph/extractors/generic/typescript/route-calls.ts`

- [ ] **Step 2: Write failing test**

Append:

```python
def test_route_calls_detector_emits_route_call(tmp_repo, tmp_data_dir):
    (tmp_repo / "client.ts").write_text(
        "async function load() { return fetch('/api/items') }\n"
    )
    r = _run(tmp_repo, tmp_data_dir, detectors="route-calls")
    assert r.returncode == 0, r.stderr
    calls = _read_nodes(tmp_data_dir, "route_calls")
    assert any(c.get("url") == "/api/items" for c in calls)
```

- [ ] **Step 3: Move and refactor**

Run: `git mv depgraph/extractors/generic/typescript/route-calls.ts depgraph/extractors/generic/typescript/detectors/route-calls.ts`

Replace contents with a Detector implementation (preserve the URL-extraction logic from the existing file; wrap it in the `Detector` interface):

```typescript
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

function extractUrl(node: ts.CallExpression): string | null {
  if (!ts.isIdentifier(node.expression) || node.expression.text !== "fetch") return null;
  const arg = node.arguments[0];
  if (arg && ts.isStringLiteralLike(arg)) return arg.text;
  if (arg && ts.isTemplateExpression(arg)) {
    // Preserve template literal head as best-effort target.
    return arg.head.text + "{...}";
  }
  return null;
}

export class RouteCallsDetector implements Detector {
  name = "route-calls";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    const muts: Mutation[] = [];
    let currentFnId: string | null = null;
    const byQualname = new Map<string, Primitive>();
    for (const p of primitives) {
      if (p.kind === "function") {
        byQualname.set(p.id.split(":").slice(2).join(":"), p);
      }
    }

    const visit = (node: ts.Node) => {
      let prevFn = currentFnId;
      if ((ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node))
          && node.name && ts.isIdentifier(node.name)) {
        const prim = byQualname.get(node.name.text);
        if (prim) currentFnId = prim.id;
      }
      if (ts.isCallExpression(node)) {
        const url = extractUrl(node);
        if (url) {
          const line = sf.getLineAndCharacterOfPosition(node.getStart()).line + 1;
          muts.push({
            type: "node", kind: "route_call",
            payload: {
              id: `${ctx.repoKey}:${ctx.filePath}:rc:${line}`,
              url, file: ctx.filePath, line,
              from_id: currentFnId,
            },
          });
        }
      }
      ts.forEachChild(node, visit);
      currentFnId = prevFn;
    };
    visit(sf);
    return muts;
  }
}
```

- [ ] **Step 4: Verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_extractor.py -v -k route_calls`

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/typescript/
git commit -m "$(cat <<'EOF'
extractors/typescript: promote route-calls to a detector

Moves route-calls.ts under detectors/ and wraps the existing URL
extraction in the Detector interface so it loads via the standard
--detectors flag instead of being a separate top-level extractor.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Go language extractor (tree-sitter)

**Files:**
- Create: `depgraph/extractors/generic/go/__init__.py`
- Create: `depgraph/extractors/generic/go/extract.py`
- Create: `depgraph/extractors/generic/go/detector_api.py`
- Create: `depgraph/extractors/generic/go/detectors/__init__.py`
- Create: `depgraph/extractors/generic/go/TEMPLATE_detector.py`
- Create: `depgraph/extractors/generic/go/README.md`
- Create: `depgraph/tests/extractors/test_go_extractor.py`

- [ ] **Step 1: Write failing test**

Create `depgraph/tests/extractors/test_go_extractor.py`:

```python
import json
import subprocess
import sys
from pathlib import Path
import pytest

EXTRACTOR = (
    Path(__file__).resolve().parents[2]
    / "depgraph" / "extractors" / "generic" / "go" / "extract.py"
)


def _run(repo: Path, data: Path, detectors=""):
    return subprocess.run(
        [sys.executable, str(EXTRACTOR),
         "--repo-key", "r", "--repo-path", str(repo),
         "--data-dir", str(data), "--detectors", detectors],
        capture_output=True, text=True,
    )


def _read(data: Path, sub: str) -> list[dict]:
    d = data / "nodes" / sub
    return [json.loads(p.read_text()) for p in d.iterdir()] if d.exists() else []


def test_go_emits_function(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.go").write_text("package x\nfunc Hi() {}\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(f["name"] == "Hi" for f in _read(tmp_data_dir, "functions"))


def test_go_emits_struct_as_class(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.go").write_text("package x\ntype User struct { Name string }\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(c["name"] == "User" for c in _read(tmp_data_dir, "classes"))


def test_go_emits_import_edge(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.go").write_text('package x\nimport "fmt"\nfunc Hi() { fmt.Println("hi") }\n')
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    imports = _read(tmp_data_dir, "imports")
    assert any(e["target"] == "fmt" for e in imports)
```

- [ ] **Step 2: Verify failure**

Run: `pytest depgraph/tests/extractors/test_go_extractor.py -v`
Expected: FAIL (no extractor).

- [ ] **Step 3: Implement detector_api (parallel to Python)**

Create `depgraph/extractors/generic/go/__init__.py` (empty) and `depgraph/extractors/generic/go/detectors/__init__.py` (empty).

Create `depgraph/extractors/generic/go/detector_api.py`:

```python
"""Detector contract for the Go language extractor.

Detectors receive a tree-sitter `Tree` plus the primitives already
emitted, and return mutations. Tree-sitter nodes are accessed via
`tree.root_node`; use `tree_sitter` Node API to walk.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tree_sitter import Tree


@dataclass(frozen=True)
class RelabelNode:
    node_id: str
    new_kind: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AddEdge:
    from_id: str
    to_id: str
    kind: str


@dataclass(frozen=True)
class AddNode:
    kind: str
    payload: dict[str, Any]


Mutation = RelabelNode | AddEdge | AddNode


@dataclass(frozen=True)
class DetectorContext:
    repo_key: str
    file_path: str
    project_config: dict[str, Any]


class Detector(ABC):
    name: str = ""

    @abstractmethod
    def detect(
        self,
        tree: Tree,
        primitives: list[dict[str, Any]],
        ctx: DetectorContext,
    ) -> list[Mutation]:
        ...
```

- [ ] **Step 4: Implement extractor**

Create `depgraph/extractors/generic/go/extract.py`:

```python
"""Go language extractor via tree-sitter."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import tree_sitter_go
from tree_sitter import Language, Parser, Tree, Node

from extractors.generic.go.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode, AddEdge, AddNode,
)

GO_LANG = Language(tree_sitter_go.language())
DEFAULT_EXCLUDES = (".git", "vendor", "node_modules", "dist", "build")
FRAMEWORK_DETECTOR_DIR = Path(__file__).parent / "detectors"


def discover_files(root: Path, extra_excludes: list[str] | None = None) -> Iterable[Path]:
    excludes = set(DEFAULT_EXCLUDES) | set(extra_excludes or ())
    for path in sorted(root.rglob("*.go")):
        if any(part in excludes for part in path.relative_to(root).parts):
            continue
        yield path


def parse_file(path: Path) -> tuple[Tree | None, str | None]:
    parser = Parser(GO_LANG)
    try:
        source = path.read_bytes()
        tree = parser.parse(source)
        return tree, None
    except Exception as e:
        return None, f"parse_error: {path}: {e}"


def _text(n: Node, source: bytes) -> str:
    return source[n.start_byte:n.end_byte].decode("utf-8", errors="replace")


def emit_primitives(tree: Tree, *, source: bytes, repo_key: str, rel_path: str) -> list[dict]:
    nodes: list[dict] = []
    module_id = f"{repo_key}:{rel_path}:<module>"
    nodes.append({
        "id": module_id, "kind": "module", "repo": repo_key,
        "file": rel_path, "name": "<module>", "parent_id": None,
    })

    def walk(node: Node, current_fn_id: str | None):
        if node.type == "function_declaration" or node.type == "method_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = _text(name_node, source)
                fid = f"{repo_key}:{rel_path}:{name}"
                nodes.append({
                    "id": fid, "kind": "function", "repo": repo_key,
                    "file": rel_path, "name": name, "parent_id": None,
                    "line": node.start_point[0] + 1,
                })
                for child in node.children:
                    walk(child, fid)
                return
        if node.type == "type_spec":
            name_node = node.child_by_field_name("name")
            type_node = node.child_by_field_name("type")
            if name_node and type_node and type_node.type in ("struct_type", "interface_type"):
                name = _text(name_node, source)
                nodes.append({
                    "id": f"{repo_key}:{rel_path}:{name}",
                    "kind": "class", "repo": repo_key, "file": rel_path,
                    "name": name, "parent_id": module_id,
                    "line": node.start_point[0] + 1,
                    "go_kind": type_node.type,
                })
        if node.type == "import_spec":
            path_node = node.child_by_field_name("path")
            if path_node:
                target = _text(path_node, source).strip('"')
                nodes.append({
                    "id": f"{module_id}#import:{target}",
                    "kind": "import_edge", "from_id": module_id,
                    "target": target, "line": node.start_point[0] + 1,
                })
        if node.type == "call_expression":
            fn_node = node.child_by_field_name("function")
            target = _text(fn_node, source) if fn_node else "<unknown>"
            origin = current_fn_id or module_id
            nodes.append({
                "id": f"{origin}#call:{target}:{node.start_point[0]+1}",
                "kind": "call_edge", "from_id": origin,
                "target": target, "line": node.start_point[0] + 1,
            })
        for child in node.children:
            walk(child, current_fn_id)

    walk(tree.root_node, None)
    return nodes


def _load_detector_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"go_detector_{path.stem}", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in vars(mod).values():
        if isinstance(attr, type) and issubclass(attr, Detector) and attr is not Detector:
            return attr
    return None


def load_detectors(names: list[str], extra_paths: list[Path]) -> list[Detector]:
    if not names or names == [""]:
        return []
    search = [FRAMEWORK_DETECTOR_DIR, *extra_paths]
    out: list[Detector] = []
    for name in names:
        found = None
        for d in search:
            candidate = d / f"{name}.py"
            if candidate.exists():
                found = _load_detector_module(candidate)
                if found:
                    break
        if not found:
            raise ValueError(f"unknown detector: {name}")
        out.append(found())
    return out


def apply_mutations(primitives, mutations):
    by_id = {n["id"]: dict(n) for n in primitives}
    extras = []
    for m in mutations:
        if isinstance(m, RelabelNode):
            if m.node_id in by_id:
                by_id[m.node_id]["kind"] = m.new_kind
                by_id[m.node_id].update(m.metadata)
        elif isinstance(m, AddNode):
            payload = dict(m.payload); payload["kind"] = m.kind
            extras.append(payload)
        elif isinstance(m, AddEdge):
            extras.append({
                "id": f"{m.from_id}#edge:{m.kind}:{m.to_id}",
                "kind": f"{m.kind}_edge",
                "from_id": m.from_id, "to_id": m.to_id,
            })
    return list(by_id.values()) + extras


_KIND_DIR = {
    "module": "modules", "class": "classes", "function": "functions",
    "import_edge": "imports", "call_edge": "calls",
}


def write_nodes(nodes: list[dict], data_dir: Path) -> None:
    for n in nodes:
        sub = _KIND_DIR.get(n["kind"], n["kind"] + "s")
        d = data_dir / "nodes" / sub
        d.mkdir(parents=True, exist_ok=True)
        fn = n["id"].replace("/", "__").replace(":", "__") + ".json"
        (d / fn).write_text(json.dumps(n, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--repo-key", required=True)
    p.add_argument("--repo-path", required=True, type=Path)
    p.add_argument("--data-dir", required=True, type=Path)
    p.add_argument("--detectors", default="")
    p.add_argument("--detector-path", action="append", default=[], type=Path)
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--only", default=None, type=Path)
    args = p.parse_args(argv)

    names = [n.strip() for n in args.detectors.split(",") if n.strip()]
    detectors = load_detectors(names, args.detector_path)

    files = [args.only] if args.only else list(discover_files(args.repo_path, args.exclude))
    total = labeled = skipped = 0
    all_nodes = []
    for f in files:
        rel = f.relative_to(args.repo_path).as_posix()
        tree, err = parse_file(f)
        if err:
            print(err, file=sys.stderr); skipped += 1; continue
        source = f.read_bytes()
        prims = emit_primitives(tree, source=source, repo_key=args.repo_key, rel_path=rel)
        ctx = DetectorContext(repo_key=args.repo_key, file_path=rel,
                              project_config={"detectors": names})
        muts = []
        for d in detectors:
            try:
                muts.extend(d.detect(tree, prims, ctx))
            except Exception as e:
                print(f"detector_error: {d.name} on {rel}: {e}", file=sys.stderr)
        labeled += sum(1 for m in muts if isinstance(m, RelabelNode))
        nodes = apply_mutations(prims, muts)
        all_nodes.extend(nodes); total += len(nodes)

    write_nodes(all_nodes, args.data_dir)
    print(f"wrote {total} nodes ({labeled} labeled by detectors), skipped {skipped} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Implement TEMPLATE + README**

Create `depgraph/extractors/generic/go/TEMPLATE_detector.py`:

```python
"""TEMPLATE: copy to detectors/<your_name>.py for Go framework recognition."""
from __future__ import annotations
from typing import Any
from tree_sitter import Tree
from extractors.generic.go.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode, AddEdge, AddNode,
)


class MyDetector(Detector):
    name = "my_detector"

    def detect(self, tree: Tree, primitives: list[dict[str, Any]],
               ctx: DetectorContext) -> list[Mutation]:
        muts: list[Mutation] = []
        # TODO: walk tree.root_node looking for the construct you care about.
        return muts
```

Create `depgraph/extractors/generic/go/README.md`:

````markdown
# Go language extractor

Walks Go source via `py-tree-sitter` + `tree-sitter-go`. Emits
module/class (struct/interface)/function primitives plus import/call
edges. No framework detectors shipped at launch — see
`CONTRIBUTING-detectors.md` to add one.

## Run

```bash
python3 extract.py --repo-key svc --repo-path ~/myproj-svc \
  --data-dir ~/myproj-knowledge-graph/depgraph --detectors ""
```
````

- [ ] **Step 6: Verify pass**

Run: `pytest depgraph/tests/extractors/test_go_extractor.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add depgraph/extractors/generic/go/ depgraph/tests/extractors/test_go_extractor.py
git commit -m "$(cat <<'EOF'
extractors/go: language extractor via py-tree-sitter

Five-stage extractor for Go. Emits module/class (struct/interface)/
function primitives plus import/call edges. TEMPLATE + README ship
for community detector PRs; no shipped detectors at launch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 17: Rust language extractor (tree-sitter)

**Files:**
- Create: `depgraph/extractors/generic/rust/__init__.py`
- Create: `depgraph/extractors/generic/rust/extract.py`
- Create: `depgraph/extractors/generic/rust/detector_api.py`
- Create: `depgraph/extractors/generic/rust/detectors/__init__.py`
- Create: `depgraph/extractors/generic/rust/TEMPLATE_detector.py`
- Create: `depgraph/extractors/generic/rust/README.md`
- Create: `depgraph/tests/extractors/test_rust_extractor.py`

- [ ] **Step 1: Write failing test**

Create `depgraph/tests/extractors/test_rust_extractor.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

EXTRACTOR = (
    Path(__file__).resolve().parents[2]
    / "depgraph" / "extractors" / "generic" / "rust" / "extract.py"
)


def _run(repo, data, detectors=""):
    return subprocess.run(
        [sys.executable, str(EXTRACTOR),
         "--repo-key", "r", "--repo-path", str(repo),
         "--data-dir", str(data), "--detectors", detectors],
        capture_output=True, text=True,
    )


def _read(data: Path, sub: str) -> list[dict]:
    d = data / "nodes" / sub
    return [json.loads(p.read_text()) for p in d.iterdir()] if d.exists() else []


def test_rust_emits_function(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.rs").write_text("fn hi() {}\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(f["name"] == "hi" for f in _read(tmp_data_dir, "functions"))


def test_rust_emits_struct_as_class(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.rs").write_text("struct User { name: String }\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    assert any(c["name"] == "User" for c in _read(tmp_data_dir, "classes"))


def test_rust_emits_use_as_import(tmp_repo, tmp_data_dir):
    (tmp_repo / "a.rs").write_text("use std::collections::HashMap;\nfn hi(){}\n")
    r = _run(tmp_repo, tmp_data_dir)
    assert r.returncode == 0, r.stderr
    imports = _read(tmp_data_dir, "imports")
    assert any("HashMap" in (e.get("target") or "") for e in imports)
```

- [ ] **Step 2: Implement (mirror Go's structure)**

Create `depgraph/extractors/generic/rust/__init__.py` (empty), `detectors/__init__.py` (empty).

Create `depgraph/extractors/generic/rust/detector_api.py`: identical to Go's `detector_api.py` (copy verbatim, change docstring to reference Rust). Tree-sitter API is the same shape.

Create `depgraph/extractors/generic/rust/extract.py`: same skeleton as Go's `extract.py`, with these differences:

```python
# Top:
import tree_sitter_rust
from tree_sitter import Language, Parser, Tree, Node
RUST_LANG = Language(tree_sitter_rust.language())
DEFAULT_EXCLUDES = (".git", "target", "node_modules", "dist", "build")

# File glob:
for path in sorted(root.rglob("*.rs")):

# Use RUST_LANG in parser:
parser = Parser(RUST_LANG)

# emit_primitives walker — replace function_declaration/type_spec/import_spec logic:
def walk(node: Node, current_fn_id: str | None):
    if node.type == "function_item":
        name_node = node.child_by_field_name("name")
        if name_node:
            name = _text(name_node, source)
            fid = f"{repo_key}:{rel_path}:{name}"
            nodes.append({
                "id": fid, "kind": "function", "repo": repo_key,
                "file": rel_path, "name": name, "parent_id": None,
                "line": node.start_point[0] + 1,
            })
            for child in node.children:
                walk(child, fid)
            return
    if node.type in ("struct_item", "enum_item", "trait_item"):
        name_node = node.child_by_field_name("name")
        if name_node:
            name = _text(name_node, source)
            nodes.append({
                "id": f"{repo_key}:{rel_path}:{name}",
                "kind": "class", "repo": repo_key, "file": rel_path,
                "name": name, "parent_id": module_id,
                "line": node.start_point[0] + 1,
                "rust_kind": node.type,
            })
    if node.type == "use_declaration":
        # Capture the full path, e.g. "std::collections::HashMap"
        target = _text(node, source).removeprefix("use").rstrip(";").strip()
        nodes.append({
            "id": f"{module_id}#import:{target}",
            "kind": "import_edge", "from_id": module_id,
            "target": target, "line": node.start_point[0] + 1,
        })
    if node.type == "call_expression":
        fn_node = node.child_by_field_name("function")
        target = _text(fn_node, source) if fn_node else "<unknown>"
        origin = current_fn_id or module_id
        nodes.append({
            "id": f"{origin}#call:{target}:{node.start_point[0]+1}",
            "kind": "call_edge", "from_id": origin,
            "target": target, "line": node.start_point[0] + 1,
        })
    for child in node.children:
        walk(child, current_fn_id)
```

Everything else (`load_detectors`, `apply_mutations`, `_KIND_DIR`, `write_nodes`, `main`) is identical to Go's `extract.py` with `from extractors.generic.rust.detector_api import …`.

Create `depgraph/extractors/generic/rust/TEMPLATE_detector.py`: same as Go's, with `from extractors.generic.rust.detector_api import …`.

Create `depgraph/extractors/generic/rust/README.md`: same shape as Go's README, swap "Go" → "Rust" and the example command path.

- [ ] **Step 3: Verify**

Run: `pytest depgraph/tests/extractors/test_rust_extractor.py -v`
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add depgraph/extractors/generic/rust/ depgraph/tests/extractors/test_rust_extractor.py
git commit -m "$(cat <<'EOF'
extractors/rust: language extractor via py-tree-sitter

Five-stage extractor for Rust. Emits module/class (struct/enum/trait)/
function primitives plus use-declaration imports and call edges.
TEMPLATE + README ship for community detector PRs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: Config — `{kg_dir}` substitution + `detectors` key

**Files:**
- Modify: `depgraph/lib/config.py`
- Modify (or create): `depgraph/tests/test_config.py`

- [ ] **Step 1: Read current config helpers**

Run: `cat depgraph/lib/config.py`

Identify the function that substitutes `{data_dir}` / `{path}` into `extractor` commands. (Likely a `resolve_extractor_command` or similar.)

- [ ] **Step 2: Write failing test**

Add to or create `depgraph/tests/test_config.py`:

```python
from pathlib import Path

from lib.config import resolve_extractor_command, repo_detectors


def test_kg_dir_substitution(tmp_path):
    cmd = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
    out = resolve_extractor_command(
        cmd, kg_dir=Path("/kg"), data_dir=tmp_path, repo_path=tmp_path,
    )
    assert out == ["python3", "/kg/depgraph/extractors/generic/python/extract.py"]


def test_repo_detectors_returns_list():
    repo_cfg = {"path": "x", "extractor": ["python3", "y"], "detectors": ["fastapi", "pytest"]}
    assert repo_detectors(repo_cfg) == ["fastapi", "pytest"]


def test_repo_detectors_default_empty():
    repo_cfg = {"path": "x", "extractor": ["python3", "y"]}
    assert repo_detectors(repo_cfg) == []
```

- [ ] **Step 3: Verify failure**

Run: `pytest depgraph/tests/test_config.py::test_kg_dir_substitution -v`
Expected: FAIL.

- [ ] **Step 4: Implement**

In `depgraph/lib/config.py`:

- Extend the existing extractor-command substitution function to also accept `kg_dir: Path` and replace `{kg_dir}` with `str(kg_dir)`. The framework root is `~/tools/knowledge-graph` (resolve via the existing primary-repo helper, or pass explicitly from `bin/depgraph`).
- Add a new top-level helper:

```python
def repo_detectors(repo_cfg: dict) -> list[str]:
    """Return the detectors list for a [repos.*] table; default empty."""
    val = repo_cfg.get("detectors", [])
    if not isinstance(val, list):
        raise ValueError(f"detectors must be a list, got {type(val).__name__}")
    return list(val)
```

- [ ] **Step 5: Verify pass**

Run: `pytest depgraph/tests/test_config.py -v`

- [ ] **Step 6: Commit**

```bash
git add depgraph/lib/config.py depgraph/tests/test_config.py
git commit -m "$(cat <<'EOF'
config: add {kg_dir} substitution + detectors key on [repos.*]

Lets project.toml point at framework extractors via {kg_dir} (resolves
to ~/tools/knowledge-graph) and lists detectors per-repo.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 19: `bin/depgraph regen` — wire `--detectors` and `--detector-path`

**Files:**
- Modify: `depgraph/bin/depgraph` (or wherever the regen subcommand orchestrates per-repo extractor invocation)

- [ ] **Step 1: Read current regen code**

Run: `grep -n -A 20 'def regen\|subprocess\|extractor' depgraph/bin/depgraph | head -80`

Identify where the extractor command is built for each `[repos.*]`.

- [ ] **Step 2: Modify command construction**

For each repo's extractor invocation, after the existing substitutions:

- Read `detectors = repo_detectors(repo_cfg)` from `lib.config`.
- If non-empty, append `["--detectors", ",".join(detectors)]` to the command.
- Append `["--detector-path", str(data_dir / "extractors" / "detectors")]` unconditionally — even with no detectors enabled this is a no-op.

- [ ] **Step 3: Write a smoke test**

Append to `depgraph/tests/test_config.py` (or create a `tests/test_regen.py` if cleaner — match the existing structure):

```python
def test_command_includes_detectors(tmp_path):
    # Use a tiny stub project.toml + monkeypatched extractor that
    # echoes its argv, then assert --detectors and --detector-path
    # appear. Implementation depends on the regen entry-point shape;
    # consult the existing regen subcommand and follow its testing
    # pattern (if any). If no regen tests exist yet, this is a
    # smoke check via subprocess that confirms the new flags reach
    # the extractor.
    pass  # Concrete assertion depends on regen entry-point shape.
```

If `bin/depgraph` has no existing regen unit-test surface, leave the smoke check as an inline assertion the engineer adds against whatever shape exists. The acceptance criterion is: a manual `bin/depgraph regen` against a tiny fixture project (built in step 4) must produce nodes with detector labels applied.

- [ ] **Step 4: Manual end-to-end verification**

Create a throwaway project to verify wiring:

```bash
mkdir -p /tmp/kg-smoke/src /tmp/kg-smoke-data/depgraph/extractors/detectors
cat > /tmp/kg-smoke/src/api.py <<'EOF'
from fastapi import APIRouter
router = APIRouter()
@router.get("/items")
def list_items(): pass
EOF
cat > /tmp/kg-smoke-data/depgraph/project.toml <<'EOF'
[project]
primary_repo = "api"

[repos.api]
path = "/tmp/kg-smoke"
extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
detectors = ["fastapi"]
EOF

DEPGRAPH_DATA_DIR=/tmp/kg-smoke-data/depgraph depgraph/bin/depgraph regen
ls /tmp/kg-smoke-data/depgraph/nodes/endpoints/  # should list a JSON file
```

Expected: at least one file in `nodes/endpoints/` whose JSON has `"kind": "endpoint"` and `"route": "/items"`.

- [ ] **Step 5: Commit**

```bash
git add depgraph/bin/depgraph
git commit -m "$(cat <<'EOF'
bin/depgraph: pass --detectors and --detector-path to extractors

regen now reads the detectors list from each [repos.*] table and
appends --detectors/--detector-path to the extractor command. Custom
project-local detectors at <data-repo>/depgraph/extractors/detectors/
get picked up automatically.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 20: Eval harness — case loader + deterministic mode

**Files:**
- Create: `depgraph/extractors/eval/__init__.py`
- Create: `depgraph/extractors/eval/harness.py`
- Create: `depgraph/extractors/eval/README.md`
- Create: `depgraph/tests/extractors/test_eval_harness.py`

- [ ] **Step 1: Write failing test**

Create `depgraph/tests/extractors/test_eval_harness.py`:

```python
import json
from pathlib import Path

import pytest

from extractors.eval.harness import (
    EvalCase, load_case, run_deterministic,
)


def test_load_case_parses_files(tmp_path: Path):
    case = tmp_path / "case1"
    (case / "source").mkdir(parents=True)
    (case / "source" / "a.py").write_text("def hi(): pass\n")
    (case / "expected.json").write_text(json.dumps({
        "nodes": {"function": ["r:a.py:hi"]},
    }))
    (case / "case.toml").write_text('detectors = []\nlanguage = "python"\n')
    c = load_case(case)
    assert isinstance(c, EvalCase)
    assert c.language == "python"
    assert c.expected["nodes"]["function"] == ["r:a.py:hi"]


def test_run_deterministic_reports_precision_recall(tmp_path: Path):
    case = tmp_path / "c"
    (case / "source").mkdir(parents=True)
    (case / "source" / "a.py").write_text("def hi(): pass\ndef ho(): pass\n")
    (case / "expected.json").write_text(json.dumps({
        "nodes": {"function": ["r:a.py:hi"]},  # intentionally incomplete
    }))
    (case / "case.toml").write_text('detectors = []\nlanguage = "python"\n')
    report = run_deterministic(case, repo_key="r")
    assert report["passed"] is True  # superset is OK; only declared expectations are checked
    assert report["precision"]["function"] == 1.0
    assert report["recall"]["function"] == 1.0
```

- [ ] **Step 2: Implement**

Create `depgraph/extractors/eval/__init__.py` (empty).

Create `depgraph/extractors/eval/harness.py`:

```python
"""Evaluation harness for language extractors.

Two modes:
- Deterministic: run extractor on case source/, diff against expected.json.
- Judgment: emit a package for a Claude Code session to review.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
EXTRACTORS = REPO_ROOT / "depgraph" / "extractors" / "generic"

LANG_TO_CMD = {
    "python": [sys.executable, str(EXTRACTORS / "python" / "extract.py")],
    "typescript": ["npx", "tsx", str(EXTRACTORS / "typescript" / "extract.ts")],
    "go": [sys.executable, str(EXTRACTORS / "go" / "extract.py")],
    "rust": [sys.executable, str(EXTRACTORS / "rust" / "extract.py")],
}


@dataclass(frozen=True)
class EvalCase:
    path: Path
    language: str
    detectors: list[str]
    expected: dict


def load_case(case_dir: Path) -> EvalCase:
    cfg = tomllib.loads((case_dir / "case.toml").read_text())
    expected = json.loads((case_dir / "expected.json").read_text())
    return EvalCase(
        path=case_dir,
        language=cfg["language"],
        detectors=cfg.get("detectors", []),
        expected=expected,
    )


def _run_extractor(case: EvalCase, repo_key: str, data_dir: Path) -> None:
    cmd = LANG_TO_CMD[case.language] + [
        "--repo-key", repo_key,
        "--repo-path", str(case.path / "source"),
        "--data-dir", str(data_dir),
        "--detectors", ",".join(case.detectors),
    ]
    cwd = (
        EXTRACTORS / case.language
        if case.language == "typescript" else None
    )
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"extractor failed: {r.stderr}")


def _collect_node_ids(data_dir: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    nodes_dir = data_dir / "nodes"
    if not nodes_dir.exists():
        return out
    for sub in nodes_dir.iterdir():
        if not sub.is_dir():
            continue
        for f in sub.glob("*.json"):
            n = json.loads(f.read_text())
            out.setdefault(n["kind"], set()).add(n["id"])
    return out


def run_deterministic(case_dir: Path, *, repo_key: str = "r") -> dict[str, Any]:
    case = load_case(case_dir)
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        _run_extractor(case, repo_key, data)
        emitted = _collect_node_ids(data)

    precision: dict[str, float] = {}
    recall: dict[str, float] = {}
    missing: dict[str, list[str]] = {}
    expected_nodes = case.expected.get("nodes", {})
    passed = True
    for kind, exp_ids in expected_nodes.items():
        exp = set(exp_ids)
        got = emitted.get(kind, set())
        tp = len(exp & got)
        precision[kind] = tp / len(got) if got else (1.0 if not exp else 0.0)
        recall[kind] = tp / len(exp) if exp else 1.0
        miss = sorted(exp - got)
        if miss:
            passed = False
            missing[kind] = miss
    return {
        "case": case_dir.name, "passed": passed,
        "precision": precision, "recall": recall, "missing": missing,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["run", "judge"])
    p.add_argument("language")
    p.add_argument("--case", default=None,
                   help="case name; default: all cases under corpus/<lang>/")
    args = p.parse_args(argv)

    corpus_dir = Path(__file__).parent / "corpus" / args.language
    cases = (
        [corpus_dir / args.case]
        if args.case else sorted(c for c in corpus_dir.iterdir() if c.is_dir())
    )
    any_failed = False
    for c in cases:
        if args.mode == "run":
            rpt = run_deterministic(c)
            print(json.dumps(rpt, indent=2))
            if not rpt["passed"]:
                any_failed = True
        else:
            from extractors.eval.judge import write_judgment_package
            out = write_judgment_package(c)
            print(f"judgment package written to {out}")
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Verify pass**

Run: `pytest depgraph/tests/extractors/test_eval_harness.py -v`
Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add depgraph/extractors/eval/ depgraph/tests/extractors/test_eval_harness.py
git commit -m "$(cat <<'EOF'
extractors/eval: harness with deterministic mode

Loads case dirs (source/, expected.json, case.toml), runs the
right language extractor against source/, diffs against expected
nodes, reports precision/recall per kind.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 21: Eval harness — judgment mode package writer

**Files:**
- Create: `depgraph/extractors/eval/judge.py`
- Modify: `depgraph/tests/extractors/test_eval_harness.py`

- [ ] **Step 1: Write failing test**

Append:

```python
from extractors.eval.judge import write_judgment_package


def test_judgment_package_contains_source_and_emitted_nodes(tmp_path: Path):
    case = tmp_path / "c"
    (case / "source").mkdir(parents=True)
    (case / "source" / "a.py").write_text("def hi(): pass\n")
    (case / "expected.json").write_text("{}")
    (case / "case.toml").write_text('detectors = []\nlanguage = "python"\n')
    (case / "judgments").mkdir(exist_ok=True)
    out = write_judgment_package(case)
    assert out.name == "pending.md"
    text = out.read_text()
    assert "def hi(): pass" in text
    assert "## Emitted nodes" in text
    assert "## Judgment prompt" in text
```

- [ ] **Step 2: Implement**

Create `depgraph/extractors/eval/judge.py`:

```python
"""Judgment-mode package writer.

Produces a stable Markdown artifact (source + emitted nodes + a fixed
prompt) for a Claude Code session to review. No SDK calls.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from extractors.eval.harness import load_case, _run_extractor, _collect_node_ids


PROMPT = """## Judgment prompt

Read the source tree above and the extractor's emitted nodes. List:

1. **Missed dependencies** — nodes/edges a reviewer would expect that
   the extractor did not produce. For each: severity (low/med/high),
   one-line description, suggested detector or extractor change.
2. **False positives** — emitted nodes that don't correspond to real
   constructs in the source. Same fields.
3. **Overall verdict** — one of: clean / acceptable-with-gaps / needs-work.

Save your judgment to `judgments/<YYYY-MM-DD>.md` (sibling of this file).
"""


def write_judgment_package(case_dir: Path) -> Path:
    case = load_case(case_dir)
    out_dir = case_dir / "judgments"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "pending.md"

    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        _run_extractor(case, repo_key="r", data_dir=data)
        emitted = _collect_node_ids(data)
        node_files: list[dict] = []
        nodes_dir = data / "nodes"
        if nodes_dir.exists():
            for sub in nodes_dir.iterdir():
                for f in sub.glob("*.json"):
                    node_files.append(json.loads(f.read_text()))

    lines = [
        f"# Judgment package: {case_dir.name}", "",
        f"Language: {case.language}",
        f"Detectors: {', '.join(case.detectors) or '(none)'}", "",
        "## Source",
        "",
    ]
    for src in sorted((case_dir / "source").rglob("*")):
        if src.is_file():
            rel = src.relative_to(case_dir / "source").as_posix()
            lines += [f"### `{rel}`", "", "```", src.read_text(), "```", ""]
    lines += [
        "## Emitted nodes",
        "",
        "```json",
        json.dumps(node_files, indent=2, sort_keys=True),
        "```",
        "",
        PROMPT,
    ]
    out.write_text("\n".join(lines))
    return out
```

- [ ] **Step 3: Verify pass**

Run: `pytest depgraph/tests/extractors/test_eval_harness.py::test_judgment_package_contains_source_and_emitted_nodes -v`

- [ ] **Step 4: Commit**

```bash
git add depgraph/extractors/eval/judge.py depgraph/tests/extractors/test_eval_harness.py
git commit -m "$(cat <<'EOF'
extractors/eval: judgment-mode package writer

Renders a Markdown package (source + emitted nodes + fixed prompt)
for a Claude Code session to review. No SDK calls; judgment files
land in case_dir/judgments/<date>.md and accumulate in git history.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 22: Seed corpus cases (one per language)

**Files:**
- Create: `depgraph/extractors/eval/corpus/python/_seed_imports/{source/a.py, expected.json, case.toml, README.md}`
- Create: `depgraph/extractors/eval/corpus/typescript/_seed_imports/{source/a.ts, expected.json, case.toml, README.md}`
- Create: `depgraph/extractors/eval/corpus/go/_seed_imports/{source/a.go, expected.json, case.toml, README.md}`
- Create: `depgraph/extractors/eval/corpus/rust/_seed_imports/{source/a.rs, expected.json, case.toml, README.md}`
- Create: `depgraph/extractors/eval/corpus/python/_seed_fastapi/{source/api.py, expected.json, case.toml, README.md}`
- Create: `depgraph/extractors/eval/corpus/typescript/_seed_react/{source/c.tsx, expected.json, case.toml, README.md}`
- Create: `depgraph/extractors/eval/README.md`

- [ ] **Step 1: Python `_seed_imports`**

`source/a.py`:
```python
import os
from pathlib import Path

def hi():
    print("ok")
```
`expected.json`:
```json
{
  "nodes": {
    "module": ["r:a.py:<module>"],
    "function": ["r:a.py:hi"]
  }
}
```
`case.toml`:
```toml
language = "python"
detectors = []
```
`README.md`: one paragraph: "Seed case for Python AST primitives. Verifies module + function emission."

- [ ] **Step 2: Python `_seed_fastapi`**

`source/api.py`:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/items")
def list_items():
    return []
```
`expected.json`:
```json
{
  "nodes": { "endpoint": ["r:api.py:list_items"] }
}
```
`case.toml`:
```toml
language = "python"
detectors = ["fastapi"]
```

- [ ] **Step 3: TypeScript `_seed_imports`**

`source/a.ts`:
```typescript
import { something } from "./b"
export function f() { return 1 }
```
`expected.json`:
```json
{
  "nodes": {
    "module": ["r:a.ts:<module>"],
    "function": ["r:a.ts:f"]
  }
}
```
`case.toml`:
```toml
language = "typescript"
detectors = []
```

- [ ] **Step 4: TypeScript `_seed_react`**

`source/Button.tsx`:
```tsx
export function Button({ label }: { label: string }) {
  return <button>{label}</button>
}
```
`expected.json`:
```json
{
  "nodes": { "component": ["r:Button.tsx:Button"] }
}
```
`case.toml`:
```toml
language = "typescript"
detectors = ["react"]
```

- [ ] **Step 5: Go `_seed_imports`**

`source/a.go`:
```go
package x
import "fmt"
func Hi() { fmt.Println("hi") }
```
`expected.json`:
```json
{
  "nodes": {
    "module": ["r:a.go:<module>"],
    "function": ["r:a.go:Hi"]
  }
}
```
`case.toml`:
```toml
language = "go"
detectors = []
```

- [ ] **Step 6: Rust `_seed_imports`**

`source/a.rs`:
```rust
use std::collections::HashMap;
fn hi() { println!("ok"); }
```
`expected.json`:
```json
{
  "nodes": {
    "module": ["r:a.rs:<module>"],
    "function": ["r:a.rs:hi"]
  }
}
```
`case.toml`:
```toml
language = "rust"
detectors = []
```

- [ ] **Step 7: Eval README**

Create `depgraph/extractors/eval/README.md`:

````markdown
# Evaluation harness

## Cases

Each case is a directory:

```
corpus/<lang>/<name>/
├── source/         input tree (small, real-ish code)
├── expected.json   declared ground truth: { "nodes": { "<kind>": ["<id>", ...] } }
├── case.toml       language + detectors to enable
├── README.md       what this case tests
└── judgments/      Claude-Code-session judgment files accumulate here
```

Only declared expectations are checked. Omitted fields = "don't care."

## Modes

```bash
# Deterministic (gates PRs):
python3 -m extractors.eval.harness run python --case _seed_imports
python3 -m extractors.eval.harness run python   # all python cases

# Judgment (advisory, hand-reviewed in a Claude Code session):
python3 -m extractors.eval.harness judge python --case _seed_fastapi
# Read corpus/python/_seed_fastapi/judgments/pending.md and save your
# judgment to corpus/python/_seed_fastapi/judgments/<YYYY-MM-DD>.md
```

## Authoring a new case

1. `mkdir corpus/<lang>/<name>` and populate `source/`, `expected.json`, `case.toml`, `README.md`.
2. Run `harness.py run <lang> --case <name>` and iterate until it passes (or until the gap is intentional and documented).
3. Commit. The case becomes part of CI from then on.
````

- [ ] **Step 8: Verify all cases pass**

Run: `python3 -m extractors.eval.harness run python`
Run: `python3 -m extractors.eval.harness run typescript`
Run: `python3 -m extractors.eval.harness run go`
Run: `python3 -m extractors.eval.harness run rust`

Expected: each prints JSON reports with `"passed": true`.

- [ ] **Step 9: Commit**

```bash
git add depgraph/extractors/eval/corpus/ depgraph/extractors/eval/README.md
git commit -m "$(cat <<'EOF'
extractors/eval: seed corpus + README

Six seed cases: _seed_imports per language (Py/TS/Go/Rust) plus
_seed_fastapi (Python) and _seed_react (TS) for the shipped
detectors. README documents case shape and modes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 23: CI hook — KG_EVAL=1 runs eval

**Files:**
- Modify: existing CI config (likely `.github/workflows/*.yml` if present; otherwise add a pytest entry)
- Modify: `depgraph/tests/extractors/test_eval_harness.py` (add a CI-driven test that runs all cases)

- [ ] **Step 1: Inspect current CI**

Run: `find . -maxdepth 3 -name '*.yml' -path '*.github*' 2>/dev/null; ls .github 2>/dev/null`

If a workflow exists, identify the test step.

- [ ] **Step 2: Add a CI-gated test**

Append to `depgraph/tests/extractors/test_eval_harness.py`:

```python
import os


@pytest.mark.skipif(
    not os.environ.get("KG_EVAL"),
    reason="KG_EVAL=1 to run full eval corpus",
)
def test_all_seed_cases_pass():
    from extractors.eval.harness import run_deterministic
    corpus = Path(__file__).resolve().parents[2] / "depgraph" / "extractors" / "eval" / "corpus"
    failures = []
    for lang_dir in corpus.iterdir():
        if not lang_dir.is_dir():
            continue
        for case_dir in lang_dir.iterdir():
            if not case_dir.is_dir():
                continue
            rpt = run_deterministic(case_dir)
            if not rpt["passed"]:
                failures.append((case_dir.name, rpt))
    assert not failures, f"eval regressions: {failures}"
```

- [ ] **Step 3: Add CI step**

If `.github/workflows/test.yml` (or equivalent) exists, add a step after the existing test invocation:

```yaml
      - name: Run extractor eval
        env:
          KG_EVAL: "1"
        run: pytest depgraph/tests/extractors/test_eval_harness.py::test_all_seed_cases_pass -v
```

If no workflow exists, skip the CI wiring; document that the local check is `KG_EVAL=1 pytest depgraph/tests/extractors/`.

- [ ] **Step 4: Verify locally**

Run: `KG_EVAL=1 pytest depgraph/tests/extractors/test_eval_harness.py::test_all_seed_cases_pass -v`
Expected: passes.

- [ ] **Step 5: Commit**

```bash
git add depgraph/tests/extractors/test_eval_harness.py .github/ 2>/dev/null || git add depgraph/tests/extractors/test_eval_harness.py
git commit -m "$(cat <<'EOF'
extractors/eval: CI hook + KG_EVAL=1 gate

KG_EVAL=1 pytest depgraph/tests/extractors/ runs the full corpus
against all language extractors. CI adds a step that sets KG_EVAL
on every PR.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 24: Concorda parity script

**Files:**
- Create: `scripts/concorda_parity.py` (lives in this branch only; not part of the long-term framework)

- [ ] **Step 1: Implement**

Create `scripts/concorda_parity.py`:

```python
#!/usr/bin/env python3
"""One-off: regen Concorda with framework extractors into a scratch
dir and diff against current <data>/nodes/. Acceptance criteria from
the spec: node count per kind must match within ±2% (floor ±1 node).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CONCORDA_DATA = Path.home() / "concorda-knowledge-graph" / "depgraph"
ACCEPTABLE_PCT = 0.02
ACCEPTABLE_FLOOR = 1


def count_nodes(data_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    nodes_dir = data_dir / "nodes"
    if not nodes_dir.exists():
        return counts
    for sub in nodes_dir.iterdir():
        if sub.is_dir() and not sub.name.startswith("_"):
            counts[sub.name] = sum(1 for _ in sub.glob("*.json"))
    return counts


def main() -> int:
    current = count_nodes(CONCORDA_DATA)
    print("Current Concorda node counts:")
    for k, v in sorted(current.items()):
        print(f"  {k}: {v}")

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "depgraph"
        shutil.copy(CONCORDA_DATA / "project.toml", Path(tmp))
        # User must manually craft a parity project.toml at $TMP/depgraph/project.toml
        # that points at framework extractors with the right detectors list.
        # See scripts/concorda_parity_project.toml for a reference layout.
        print(f"\nScratch dir: {scratch}")
        print("To complete parity:")
        print(f"  1. Copy scripts/concorda_parity_project.toml -> {scratch}/project.toml")
        print(f"  2. DEPGRAPH_DATA_DIR={scratch} ~/tools/knowledge-graph/depgraph/bin/depgraph regen")
        print(f"  3. Re-run this script to compute the diff after regen.")

    if "--diff" in sys.argv:
        scratch = Path(sys.argv[sys.argv.index("--diff") + 1])
        new = count_nodes(scratch)
        print("\nDiff (current -> new):")
        all_kinds = set(current) | set(new)
        regressions = []
        for k in sorted(all_kinds):
            c, n = current.get(k, 0), new.get(k, 0)
            diff = n - c
            tol = max(ACCEPTABLE_FLOOR, int(c * ACCEPTABLE_PCT))
            marker = " OK" if abs(diff) <= tol else " REGRESSION"
            print(f"  {k}: {c} -> {n} ({diff:+d}, tol ±{tol}){marker}")
            if abs(diff) > tol:
                regressions.append(k)
        return 0 if not regressions else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Also create `scripts/concorda_parity_project.toml` — a reference parity project.toml:

```toml
[project]
primary_repo = "api"

[logigraph]
data_dir = "~/concorda-knowledge-graph/logigraph"

[repos.api]
path = "~/concorda-api"
extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
detectors = ["fastapi", "sqlalchemy", "pydantic", "pytest"]
files_arg = "--only"

[repos.web]
path = "~/concorda-web"
extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]
detectors = ["react", "vitest", "route-calls"]
```

- [ ] **Step 2: Run parity**

```bash
python3 scripts/concorda_parity.py
# Follow the printed instructions to regen into scratch.
python3 scripts/concorda_parity.py --diff /tmp/scratch
```

Expected: prints diff per kind; non-zero exit if any kind exceeds tolerance. If regressions appear, file by file:

- If a missing endpoint/model/test indicates a detector gap: improve the detector, add a regression case in `eval/corpus/python/`, re-run.
- If a node-count change is intentional (e.g., new metadata format), document in the migration commit message.

Iterate until the diff is within tolerance.

- [ ] **Step 3: Commit**

```bash
git add scripts/
git commit -m "$(cat <<'EOF'
scripts: Concorda parity check (one-off, this branch)

Compares Concorda's current node counts against a regen with the
framework extractors. Used during the migration to verify the lift
preserves coverage within ±2% per kind (floor ±1 node).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 25: Flip Concorda's project.toml + delete old extractors

**Files (in Concorda data repo):**
- Modify: `~/concorda-knowledge-graph/depgraph/project.toml`
- Delete: `~/concorda-knowledge-graph/depgraph/extractors/extract_api.py`
- Delete: `~/concorda-knowledge-graph/depgraph/extractors/extract_web.ts`
- Delete: `~/concorda-knowledge-graph/depgraph/extractors/extract_tests.ts`
- Keep: `~/concorda-knowledge-graph/depgraph/extractors/ingest_route_calls.py` (separate task; out of scope for this lift)

> Run these commands in the Concorda data repo, not the framework repo.

- [ ] **Step 1: Verify parity is green**

Re-run Task 24's parity check. Do not proceed if any kind is outside tolerance.

- [ ] **Step 2: Flip project.toml**

In `~/concorda-knowledge-graph/depgraph/project.toml`, replace the `[repos.*]` extractor commands with framework references. Use the layout from `scripts/concorda_parity_project.toml` (Task 24).

- [ ] **Step 3: Delete old extractors**

```bash
cd ~/concorda-knowledge-graph
git rm depgraph/extractors/extract_api.py depgraph/extractors/extract_web.ts depgraph/extractors/extract_tests.ts
```

- [ ] **Step 4: Regen + verify**

```bash
DEPGRAPH_DATA_DIR=~/concorda-knowledge-graph/depgraph ~/tools/knowledge-graph/depgraph/bin/depgraph regen
DEPGRAPH_DATA_DIR=~/concorda-knowledge-graph/depgraph ~/tools/knowledge-graph/depgraph/bin/depgraph self-check
```

Expected: regen succeeds; self-check is green; node counts match the parity baseline.

- [ ] **Step 5: Commit in Concorda repo**

```bash
cd ~/concorda-knowledge-graph
git add depgraph/
git commit -m "$(cat <<'EOF'
depgraph: flip to framework language extractors

project.toml now points at ~/tools/knowledge-graph/depgraph/extractors/
generic/{python,typescript}/extract.* with detectors lists. Deletes
the bespoke extract_api.py / extract_web.ts / extract_tests.ts files
that the framework now subsumes.

Parity verified by scripts/concorda_parity.py (±2% per kind).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 26: Update depgraph/extractors/README.md

**Files:**
- Modify: `depgraph/extractors/README.md`

- [ ] **Step 1: Read current**

Run: `cat depgraph/extractors/README.md`

- [ ] **Step 2: Rewrite**

Replace the file with content that reflects the new shape:

````markdown
# Extractors

Project-agnostic, language-specific extractors. Each language has its
own entry point under `generic/<lang>/`; they all implement the same
five-stage contract (discover → parse → emit primitives → run
detectors → write).

| Script | Owned by | Reads | Emits |
|---|---|---|---|
| `reconcile.py` | framework (this dir) | all node files in the data dir | rewrites them with reverse `dependents`, marks stale dossiers, archives orphans |
| `generic/python/extract.py` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |
| `generic/typescript/extract.ts` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |
| `generic/go/extract.py` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |
| `generic/rust/extract.py` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |

## Wiring

In `<data-repo>/depgraph/project.toml`:

```toml
[repos.api]
path = "~/<project>-api"
extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
detectors = ["fastapi", "sqlalchemy", "pydantic", "pytest"]
files_arg = "--only"

[repos.web]
path = "~/<project>-web"
extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]
detectors = ["react", "vitest", "route-calls"]
```

Substitutions: `{kg_dir}` → `~/tools/knowledge-graph`; `{data_dir}` →
the depgraph data dir; `{path}` → the repo's resolved path.

## Detectors

Detectors layer framework-specific semantics on top of AST primitives.
Shipped detectors:

| Language | Detector | Recognizes |
|---|---|---|
| python | `fastapi` | `@router.<method>(path)` / `@app.<method>(path)` |
| python | `sqlalchemy` | `DeclarativeBase` subclasses; `__tablename__` |
| python | `pydantic` | `BaseModel` subclasses; field names |
| python | `pytest` | `test_*` in `test_*.py` / `*_test.py` |
| typescript | `react` | PascalCase + returns JSX → `component`; `use*` + calls hooks → `hook` |
| typescript | `vitest` | `describe`/`it`/`test` in `*.test.*` / `*.spec.*` |
| typescript | `route-calls` | `fetch(url)` call sites |

See each language's `README.md` for authoring guidance, and
`CONTRIBUTING-detectors.md` at the repo root for the PR process.

## Project-local detectors

A project can author its own detectors under
`<data-repo>/depgraph/extractors/detectors/<name>.py` (or `.ts`).
`bin/depgraph regen` passes `--detector-path` automatically; the
framework extractor searches both its own `detectors/` dir and the
project-local one.

## Authoring conventions

- Extractors must be **idempotent**.
- Extractors must write **only** under `<data_dir>/nodes/` (or stderr).
- Final summary line: `wrote N nodes (M labeled by detectors), skipped K files`.
- Non-zero exit on fatal failure. Per-file parse errors are non-fatal.
- Per-node files are **bit-stable**: no timestamps, no commit hashes, no derived data.
````

- [ ] **Step 3: Commit**

```bash
git add depgraph/extractors/README.md
git commit -m "$(cat <<'EOF'
docs: extractors README — new four-language layout + detectors

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 27: Update top-level README runbook

**Files:**
- Modify: `README.md` (repo root)

- [ ] **Step 1: Read current runbook section**

Run: `grep -n 'Add a new tracked repo' README.md`
Open the file at that line.

- [ ] **Step 2: Modify**

Replace the "Add a new tracked repo" runbook block with the new shape. The replacement should:

- Point at framework extractors with `{kg_dir}` substitution.
- List the shipped detectors per language.
- Explain that project-local detectors live at `<data-repo>/depgraph/extractors/detectors/`.

Example replacement (verbatim into the README):

```markdown
### When the user asks: "Add a new tracked repo"

1. Read the current `<data-repo>/depgraph/project.toml`.
2. Add a new `[repos.<key>]` table. Use a framework language extractor:
   - **Python:** `extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]`. Available detectors: `fastapi`, `sqlalchemy`, `pydantic`, `pytest`.
   - **TypeScript/JavaScript:** `extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]`. Available detectors: `react`, `vitest`, `route-calls`.
   - **Go:** `extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/go/extract.py"]`. No shipped detectors; primitives only.
   - **Rust:** `extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/rust/extract.py"]`. No shipped detectors.
   List the wanted detectors via `detectors = [...]`. Set `files_arg = "--only"` so the post-edit hook can target a single file.
3. If the project needs framework recognition the shipped detectors don't cover, author a project-local detector at `<data-repo>/depgraph/extractors/detectors/<name>.py` (or `.ts`). Copy the `TEMPLATE_detector.*` from the matching language dir. See `CONTRIBUTING-detectors.md` to upstream it as a PR.
4. Run `bin/depgraph regen` and confirm nodes appear under `<data-repo>/depgraph/nodes/`.
5. If logigraph rules will claim against the new repo, also add the `[repos.<key>]` table to `<data-repo>/logigraph/project.toml` so path-classification works for the logigraph hook.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: runbook — point new repos at framework language extractors

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 28: CONTRIBUTING-detectors.md

**Files:**
- Create: `CONTRIBUTING-detectors.md` (repo root)

- [ ] **Step 1: Write**

Create `CONTRIBUTING-detectors.md`:

````markdown
# Contributing a detector

Detectors are how the framework recognizes specific frameworks
(FastAPI, React, Vitest, …) on top of the language AST primitives.
This guide covers the PR process for upstreaming a new detector.

## Where things live

- Language entry points: `depgraph/extractors/generic/<lang>/extract.{py,ts}`
- Detector contract: `depgraph/extractors/generic/<lang>/detector_api.{py,ts}`
- Shipped detectors: `depgraph/extractors/generic/<lang>/detectors/`
- TEMPLATE: `depgraph/extractors/generic/<lang>/TEMPLATE_detector.{py,ts}`

## Steps

1. **Copy the TEMPLATE** for the right language into `detectors/<name>.{py,ts}`. Rename the class and the `name` field; the file's `name` field must match the filename.
2. **Implement `detect()`**. The contract is documented in `detector_api.{py,ts}`. Detectors must be pure functions of their inputs — no I/O, no globals, no side effects. Exceptions are caught at the extractor boundary, but a noisy detector hurts everyone.
3. **Add tests** in `depgraph/tests/extractors/test_<lang>_detectors.py`. Cover: the happy path; the negative case (no false positives on unrelated constructs); one realistic edge case from the framework you're recognizing.
4. **Add an eval case** under `depgraph/extractors/eval/corpus/<lang>/_seed_<name>/`. Tiny `source/` tree; `expected.json` listing the kinds your detector produces; `case.toml` with `language` and `detectors`. The case becomes part of CI from then on.
5. **Run the deterministic harness**: `python3 -m extractors.eval.harness run <lang> --case _seed_<name>` — must report `passed: true`.
6. **Open a PR** with: detector source, tests, eval case, and a short PR description explaining what framework you're recognizing and what node kind(s) you produce. Include a link to upstream docs for the framework if you can.

## Acceptance criteria

- Tests in `test_<lang>_detectors.py` pass.
- Eval case in `corpus/<lang>/_seed_<name>/` passes deterministic mode.
- No regression: `KG_EVAL=1 pytest depgraph/tests/extractors/` is green.
- The detector's `name` is unique across the language.
- The detector emits a documented `new_kind` — if it's a new kind not already in the framework, add it to `depgraph/extractors/README.md` and explain what it represents.

## Style

- Keep detectors small. If a detector grows past ~150 lines, consider whether it's recognizing one framework or two.
- Detectors compose: a project can enable multiple detectors against the same source. Don't try to be exhaustive in one file.
- Don't reach across files. A detector sees one AST + one file's primitives. Cross-file reasoning belongs in `reconcile.py`.

## Project-local detectors

If your detector is specific to one project, keep it in
`<data-repo>/depgraph/extractors/detectors/<name>.{py,ts}`. The
framework extractor picks it up automatically via `--detector-path`.
Promote to a framework PR once it stabilizes and could plausibly help
another project.
````

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING-detectors.md
git commit -m "$(cat <<'EOF'
docs: CONTRIBUTING-detectors.md

PR guide for upstreaming a framework detector: where files live,
test + eval-case requirements, acceptance criteria.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review

Run through this checklist before claiming the plan complete.

**Spec coverage (against `docs/superpowers/specs/2026-05-15-language-extractors-design.md`):**
- Architecture: Tasks 2-17 (all four languages + detector API + TEMPLATEs).
- Project wiring (`{kg_dir}` + `detectors` key): Tasks 18-19.
- Language extractor contract (five stages): Tasks 3-5 (Py), 11 (TS), 16 (Go), 17 (Rust).
- Detector contract: Task 2 (Py API), 11 (TS API), 16 (Go API), 17 (Rust API).
- Concorda lift table: Tasks 7-10 (Py detectors), 13-15 (TS detectors).
- Parity gate: Task 24.
- Concorda flip: Task 25.
- Eval harness — case shape: Task 20.
- Eval — deterministic mode: Task 20.
- Eval — judgment mode: Task 21.
- Seeding: Task 22.
- CI: Task 23.
- Error handling (parse/detector errors): wired into Tasks 5 (Py main), 11 (TS main), 16 (Go main), 17 (Rust main).
- Testing strategy: framework unit tests via Tasks 2-17; eval harness via Tasks 20-23.
- Rollout sequence: Tasks 1-28 in order match the spec's 7 rollout steps.
- README updates: Tasks 26-27.
- CONTRIBUTING-detectors.md: Task 28.

**Open items / known soft spots** (capture here so the executor sees them):

- **Task 19 smoke test is partial.** The test stub is intentional — the existing `bin/depgraph` may not have unit-test infrastructure. The acceptance criterion (manual end-to-end with `/tmp/kg-smoke/`) is concrete and runnable.
- **Task 23 CI step is conditional.** If `.github/workflows/*` doesn't exist, the CI wiring step degrades to a documented local command.
- **`ingest_route_calls.py` is not lifted.** Out of scope for this plan; it's a separate post-extraction step in Concorda that consumes the TS `route-calls.ts` output. After Task 15 promotes `route-calls.ts` into a detector, a follow-up plan can address `ingest_route_calls.py` if desired.

---

## Execution

**Plan complete and saved to `docs/superpowers/plans/2026-05-15-language-extractors.md`.** Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
