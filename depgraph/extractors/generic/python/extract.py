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
            )
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
