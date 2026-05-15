"""Detect FastAPI endpoint definitions.

A function is an endpoint if its decorator list contains
`<obj>.<http_method>(...)` where http_method is one of
get/post/put/patch/delete/options/head, and <obj> is plausibly a
FastAPI / APIRouter instance (we don't try to type-resolve; the
decorator shape is enough in practice).
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from extractors.generic.python.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode,
)

_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}

_REQUEST_SKIP_TYPES = {
    "Session", "BackgroundTasks", "Request", "Response", "AuthUser", "WebSocket",
}
_REQUEST_PRIMITIVE_TYPES = {
    "str", "int", "float", "bool", "UUID", "uuid", "List", "Dict", "Optional",
}


def _endpoint_decorator(dec: ast.expr) -> tuple[str, str, ast.Call] | None:
    """If `dec` is a FastAPI route decorator, return (METHOD, route, call).
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
    return func.attr.upper(), first.value, dec


def _name_of(node: ast.AST | None) -> str | None:
    """Best-effort name extraction from an annotation/default node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _name_of(node.value)
    if isinstance(node, ast.Call):
        return _name_of(node.func)
    return None


def _kwarg(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _detect_auth(handler: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Reproduce extract_api.py:229-254 — scan handler param defaults for
    `Depends(<symbol>)` markers and classify by symbol substring."""
    args = handler.args
    defaults = list(args.defaults) + [d for d in args.kw_defaults if d is not None]
    for default in defaults:
        if not isinstance(default, ast.Call):
            continue
        if _name_of(default.func) != "Depends":
            continue
        if not default.args:
            continue
        dep_name = _name_of(default.args[0]) or ""
        lower = dep_name.lower()
        if "admin" in lower:
            return "admin"
        if "agent" in lower:
            return "agent_token"
        if "auth" in lower or "user" in lower:
            return "user"
    return "none"


def _request_type_name(handler: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Reproduce extract_api.py:264-280 — first positional/keyword arg with a
    non-builtin annotation that isn't Session/BackgroundTasks/etc."""
    for arg in handler.args.args:
        if arg.annotation is None:
            continue
        type_name = _name_of(arg.annotation)
        if not type_name or type_name in _REQUEST_SKIP_TYPES:
            continue
        if type_name in _REQUEST_PRIMITIVE_TYPES:
            continue
        return type_name
    return None


def _response_type_name(decorator_call: ast.Call) -> str | None:
    """Reproduce extract_api.py:257-261 — response_model= kwarg name."""
    rm = _kwarg(decorator_call, "response_model")
    if rm is None:
        return None
    return _name_of(rm)


def _string_constant(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _parse_main_prefix_map(repo_path: str) -> dict[str, str]:
    """Reproduce extract_api.py:95-146 — parse <repo>/main.py and return
    {router_module_basename: prefix}. Returns {} if main.py absent or
    unparseable."""
    if not repo_path:
        return {}
    main_path = Path(repo_path) / "main.py"
    if not main_path.exists():
        return {}
    try:
        tree = ast.parse(main_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return {}

    import_map: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                local = alias.asname or alias.name
                import_map[local] = f"{module}.{alias.name}".strip(".")

    prefix_by_module: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "include_router"):
            continue
        if not node.args:
            continue
        first = node.args[0]
        local_name: str | None = None
        if isinstance(first, ast.Attribute) and isinstance(first.value, ast.Name):
            local_name = first.value.id
        elif isinstance(first, ast.Name):
            local_name = first.id
        if not local_name:
            continue
        module_dotted = import_map.get(local_name, local_name)
        parts = module_dotted.split(".")
        if parts and parts[-1] == "router":
            parts = parts[:-1]
        module_basename = parts[-1] if parts else local_name

        prefix = ""
        prefix_arg = _kwarg(node, "prefix")
        if isinstance(prefix_arg, ast.Constant) and isinstance(prefix_arg.value, str):
            prefix = prefix_arg.value
        prefix_by_module[module_basename] = prefix
    return prefix_by_module


def _apirouter_prefix(tree: ast.AST) -> str:
    """Reproduce extract_api.py:181-196 — look for `router = APIRouter(prefix=X)`."""
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "router":
                val = node.value
                if isinstance(val, ast.Call):
                    pre = _kwarg(val, "prefix")
                    if isinstance(pre, ast.Constant) and isinstance(pre.value, str):
                        return pre.value
    return ""


def _full_prefix(file_path: str, tree: ast.AST, repo_path: str) -> str:
    """Combine main.py's include_router prefix with file's APIRouter prefix.

    For non-router files (e.g. main.py itself) returns empty string."""
    from pathlib import PurePosixPath
    parts = PurePosixPath(file_path).parts
    if not parts:
        return ""
    if parts[0] != "routers":
        return ""
    if len(parts) < 2:
        return ""
    module_basename = PurePosixPath(parts[-1]).stem
    main_prefix_map = _parse_main_prefix_map(repo_path)
    main_prefix = main_prefix_map.get(module_basename, "")
    apirouter_pref = _apirouter_prefix(tree)
    return main_prefix + apirouter_pref


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

        full_prefix = _full_prefix(ctx.file_path, tree, ctx.repo_path)

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
                        method, route, dec_call = result
                        path = full_prefix + route
                        auth = _detect_auth(node)
                        req_type = _request_type_name(node)
                        resp_type = _response_type_name(dec_call)
                        muts.append(RelabelNode(
                            node_id=prim["id"],
                            new_kind="endpoint",
                            metadata={
                                "method": method,
                                "path": path,
                                "route": route,  # legacy/internal — un-prefixed
                                "auth": auth,
                                "request_schema_ref": req_type,
                                "response_schema_ref": resp_type,
                                "request_type_name": req_type,
                                "response_type_name": resp_type,
                            },
                        ))
                        break
                self.generic_visit(node)

            visit_FunctionDef = _visit_fn
            visit_AsyncFunctionDef = _visit_fn

        V().visit(tree)
        return muts
