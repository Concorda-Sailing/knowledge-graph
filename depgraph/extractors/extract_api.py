#!/usr/bin/env python3
"""
extract_api.py — walk concorda-api FastAPI routers and emit endpoint + service + model nodes.

Strategy:
  1. Import main.app and walk app.routes for every Route/APIRoute.
  2. For each route: derive id `METHOD::/canonical/{path}`, signature
     (auth, request schema ref, response schema ref), and the source file:line
     of the endpoint function via inspect.getsourcefile / getsourcelines.
  3. For depends_on: parse the handler's body with `ast` and pick out
     - imported model classes (kind=model edges)
     - imported service functions (kind=service edges)
     - broadcast_event / websocket calls (kind=websocket edges)
     - direct DB queries on Model classes (kind=db_query edges)
  4. structural_hash = sha256 of canonical JSON of {method, path, auth,
     request_schema_dict, response_schema_dict, sorted handler signature}.
  5. Reconciler (separate pass) materializes reverse `dependents`.

This file emits a SKELETON node per route. Step (3) and parts of (4) are
marked TODO(impl) — the goal of this commit is to validate the design end-to-end
with one extractor doing the easy parts deterministically.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(os.environ.get("CONCORDA_API_PATH", Path.home() / "concorda-api")).resolve()
DEPGRAPH = Path(os.environ.get("CONCORDA_DEPGRAPH_PATH", Path.home() / "concorda" / "depgraph")).resolve()
NODES_DIR = DEPGRAPH / "nodes"
ENDPOINTS_DIR = NODES_DIR / "endpoints"
MODELS_DIR = NODES_DIR / "models"
SERVICES_DIR = NODES_DIR / "services"


# --------------------------------------------------------------------------- #
# Defect #8: AST-based endpoint extraction.                                    #
#                                                                              #
# Previously this module did `importlib.exec_module(main.py)` to get the live  #
# FastAPI app instance, then walked `app.routes`. That worked but executed     #
# every startup hook: DB connection, Stripe init, websocket manager,           #
# Alembic version check. The extractor wasn't pure — running it could in       #
# principle mutate state, send a metric, hold a connection. It was also slow.  #
#                                                                              #
# The AST approach: read main.py and routers/*.py via `ast.parse`, walk        #
# `@app.<method>` and `@router.<method>` decorators, combine main.py's         #
# `include_router(prefix=...)` map with each router's own paths.               #
#                                                                              #
# Trade-off: full Pydantic JSON-schema introspection is gone. Instead the      #
# request/response types are recorded by class-name (e.g. `PersonRead`).       #
# Renaming a Pydantic model still flips the structural_hash; field-level       #
# edits to a model don't directly flip the endpoint hash, but the *model*      #
# node's hash flips and is itself in the graph (defect #5).                    #
# --------------------------------------------------------------------------- #


def _string_constant(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _kwarg(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _name_of(node: ast.AST | None) -> str | None:
    """Best-effort name extraction from an annotation/default node.
       For `Depends(require_auth)` the inner Name is what we want."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _name_of(node.value)
    if isinstance(node, ast.Call):
        return _name_of(node.func)
    return None


def parse_main_router_includes() -> tuple[dict[str, str], list[dict]]:
    """Walk main.py for `app.include_router(X.router, prefix=Y)` and
    `@app.<method>` direct decorators. Returns (prefix_by_module, app_direct_routes).
       prefix_by_module: {router_module_basename: prefix} — used to combine
                         with each routers/<basename>.py's own decorator paths.
       app_direct_routes: list of {method, path, handler_node, source_path,
                                   handler_line} for decorators directly on app."""
    main_path = REPO / "main.py"
    tree = ast.parse(main_path.read_text())

    # Build name → module map from imports
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
        # Patterns: `invite.router` or `invite_router`
        local_name: str | None = None
        if isinstance(first, ast.Attribute) and isinstance(first.value, ast.Name):
            local_name = first.value.id
        elif isinstance(first, ast.Name):
            local_name = first.id
        if not local_name:
            continue
        module_dotted = import_map.get(local_name, local_name)
        # 'routers.invite' → 'invite'; for 'invite_router' the import would
        # typically be `from routers.invite import router as invite_router`,
        # whose dotted form is 'routers.invite.router'. Strip a trailing
        # `.router` if present.
        parts = module_dotted.split(".")
        if parts and parts[-1] == "router":
            parts = parts[:-1]
        module_basename = parts[-1] if parts else local_name

        prefix = ""
        prefix_arg = _kwarg(node, "prefix")
        if isinstance(prefix_arg, ast.Constant) and isinstance(prefix_arg.value, str):
            prefix = prefix_arg.value
        prefix_by_module[module_basename] = prefix

    # Direct @app.<method> decorators (root, health, etc).
    app_direct_routes: list[dict] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            df = dec.func
            if not (isinstance(df, ast.Attribute) and isinstance(df.value, ast.Name)):
                continue
            if df.value.id != "app":
                continue
            method = df.attr.upper()
            if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            path_arg = dec.args[0] if dec.args else None
            path = _string_constant(path_arg)
            if path is None:
                continue
            app_direct_routes.append({
                "method": method,
                "path": path,
                "handler_node": node,
                "source_path": "main.py",
                "handler_line": node.lineno,
                "decorator_call": dec,
            })

    return prefix_by_module, app_direct_routes


def parse_router_file(file_path: Path) -> tuple[str, list[dict]]:
    """Walk a routers/<file>.py. Returns (apirouter_prefix, decorator_routes).
       apirouter_prefix: the `prefix=` arg on `router = APIRouter(prefix=...)`
                          if any (almost always empty in concorda-api).
       decorator_routes: list of {method, path, handler_node, source_path,
                                  handler_line, decorator_call}."""
    tree = ast.parse(file_path.read_text())
    apirouter_prefix = ""
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "router":
                val = node.value
                if isinstance(val, ast.Call):
                    pre = _kwarg(val, "prefix")
                    if isinstance(pre, ast.Constant) and isinstance(pre.value, str):
                        apirouter_prefix = pre.value

    decorator_routes: list[dict] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            df = dec.func
            if not (isinstance(df, ast.Attribute) and isinstance(df.value, ast.Name)):
                continue
            if df.value.id != "router":
                continue
            method = df.attr.upper()
            if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            path_arg = dec.args[0] if dec.args else None
            path = _string_constant(path_arg)
            if path is None:
                continue
            decorator_routes.append({
                "method": method,
                "path": path,
                "handler_node": node,
                "source_path": file_path.relative_to(REPO).as_posix(),
                "handler_line": node.lineno,
                "decorator_call": dec,
            })

    return apirouter_prefix, decorator_routes


def detect_auth_from_handler_ast(handler_node: ast.AST) -> str:
    """AST equivalent of endpoint_auth: look at the function signature for
    `: <Type> = Depends(<dep_name>)` and classify by dep_name keyword."""
    if not isinstance(handler_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "none"
    args = handler_node.args
    # Defaults align with the trailing args (positional + keyword).
    pos_args = args.args + args.kwonlyargs
    defaults = list(args.defaults) + [d for d in args.kw_defaults if d is not None]
    # We only need the dep names — scan all defaults
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


def schema_name_for_response(decorator: ast.Call) -> str | None:
    rm = _kwarg(decorator, "response_model")
    if rm is None:
        return None
    return _name_of(rm)


def schema_name_for_request(handler_node: ast.AST) -> str | None:
    """First positional/keyword arg with a non-builtin annotation that isn't
    `Session`, `BackgroundTasks`, `Depends(...)`, or `Request`."""
    if not isinstance(handler_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    SKIP_TYPES = {"Session", "BackgroundTasks", "Request", "Response", "AuthUser", "WebSocket"}
    for arg in handler_node.args.args:
        if arg.annotation is None:
            continue
        type_name = _name_of(arg.annotation)
        if not type_name or type_name in SKIP_TYPES:
            continue
        # Skip path-param primitives
        if type_name in {"str", "int", "float", "bool", "UUID", "uuid", "List", "Dict", "Optional"}:
            continue
        return type_name
    return None


def extract_endpoints_via_ast(symbol_index: dict[str, dict]) -> list[dict]:
    """Defect #8: produce endpoint nodes purely from AST, no app import."""
    nodes: list[dict] = []

    prefix_by_module, app_direct = parse_main_router_includes()

    routes_to_emit: list[tuple[str, dict]] = []
    # `(full_prefix, route_dict)` for each route we'll emit
    for r in app_direct:
        routes_to_emit.append(("", r))

    routers_dir = REPO / "routers"
    if routers_dir.exists():
        for f in sorted(routers_dir.glob("*.py")):
            if f.name in ("__init__.py",):
                continue
            module_basename = f.stem
            main_prefix = prefix_by_module.get(module_basename, "")
            try:
                apirouter_prefix, decorator_routes = parse_router_file(f)
            except (OSError, SyntaxError):
                continue
            full_prefix = main_prefix + apirouter_prefix
            for r in decorator_routes:
                routes_to_emit.append((full_prefix, r))

    for full_prefix, r in routes_to_emit:
        full_path = full_prefix + r["path"]
        method = r["method"]
        nid = node_id_for_route(method, full_path)
        handler_node = r["handler_node"]
        decorator_call = r["decorator_call"]

        auth = detect_auth_from_handler_ast(handler_node)
        request_type_name = schema_name_for_request(handler_node)
        response_type_name = schema_name_for_response(decorator_call)

        # Walk handler body for depends_on edges (model + service references).
        rel_path = r["source_path"]
        edges = walk_handler_body_ast(handler_node, REPO / rel_path, symbol_index)

        node = {
            "schema_version": 1,
            "id": nid,
            "kind": "endpoint",
            "title": f"{method} {full_path}",
            "feature": None,
            "source": {
                "repo": "concorda-api",
                "path": rel_path,
                "symbol": getattr(handler_node, "name", None),
                "line": r["handler_line"],
            },
            "signature": {
                "method": method,
                "path": full_path,
                "auth": auth,
                "request_schema_ref": request_type_name,
                "response_schema_ref": response_type_name,
            },
            "structural_hash": structural_hash({
                "method": method,
                "path": canonical_path(full_path),
                "auth": auth,
                "request": request_type_name,
                "response": response_type_name,
            }),
            "depends_on": edges,
            "external_consumers": [],
            "tests": [],
            "dossier": f"dossiers/endpoints/{slugify_id(nid)}.md",
            "extractor": "extract_api.py",
            "warnings": [],
        }
        if response_type_name is None and method != "DELETE":
            node["warnings"].append({
                "code": "weakly_typed_response",
                "message": "Handler has no declared response_model; structural hash cannot detect response shape changes. See DRIFT.md scenario 3.",
                "where": f"{rel_path}:{r['handler_line']}",
            })
        nodes.append(node)

    return nodes


def walk_handler_body_ast(
    handler_node: ast.AST,
    src_file: Path,
    symbol_index: dict[str, dict],
) -> list[dict]:
    """Same dataflow as walk_handler_body but takes an already-parsed AST node
    and the file path explicitly, since we don't have a callable to inspect."""
    if not isinstance(handler_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    try:
        module_tree = ast.parse(src_file.read_text())
    except (OSError, SyntaxError):
        return []
    import_aliases: dict[str, str] = {}
    for node in module_tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local = alias.asname or alias.name
                import_aliases[local] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                import_aliases[local] = alias.name

    rel = src_file.resolve().relative_to(REPO).as_posix()
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for child in ast.walk(handler_node):
        if not isinstance(child, ast.Name):
            continue
        imported_name = import_aliases.get(child.id)
        if not imported_name:
            continue
        sym = symbol_index.get(imported_name)
        if not sym:
            continue
        target_id = make_qualified_id(sym["file"], imported_name)
        if sym["kind"] == "class":
            via = _via_for_class_symbol(sym["file"])
        elif imported_name in WEBSOCKET_SYMBOLS:
            via = "websocket"
        else:
            via = "import"
        key = (target_id, via)
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "target": target_id,
            "via": via,
            "where": f"{rel}:{child.lineno}",
            "confidence": "exact",
        })
    return edges


def canonical_path(path: str) -> str:
    """Replace named path params with positional placeholders so two routes
    that mean the same thing but spell their params differently produce the
    same id. See DRIFT.md scenario 16."""
    out, depth, idx = [], 0, 0
    for ch in path:
        if ch == "{":
            depth = 1
            out.append("{")
            continue
        if ch == "}" and depth:
            depth = 0
            out.append(f"{idx}" + "}")
            idx += 1
            continue
        if depth:
            continue
        out.append(ch)
    return "".join(out)


def slugify_id(node_id: str) -> str:
    return (
        node_id.replace("::", "__")
        .replace("/", "_")
        .replace("{", "")
        .replace("}", "")
        .strip("_")
    )


def node_id_for_route(method: str, path: str) -> str:
    return f"{method.upper()}::{canonical_path(path)}"


def endpoint_auth(handler) -> str:
    """Best-effort detection: scan the handler signature for our known auth
    Depends(...) markers. TODO(impl): walk full dependency tree."""
    try:
        sig = inspect.signature(handler)
    except (TypeError, ValueError):
        return "none"
    for p in sig.parameters.values():
        default = p.default
        if hasattr(default, "dependency"):
            dep_name = getattr(default.dependency, "__name__", "")
            if "admin" in dep_name.lower():
                return "admin"
            if "agent" in dep_name.lower():
                return "agent_token"
            if "auth" in dep_name.lower() or "user" in dep_name.lower():
                return "user"
    return "none"


def schema_dict_for(model) -> dict | None:
    """Return JSON-Schema-ish dict for a Pydantic model. Used for the
    structural hash and for downstream consumers. TODO(impl): handle Union,
    nested models, generics."""
    if model is None:
        return None
    if hasattr(model, "model_json_schema"):  # pydantic v2
        try:
            return model.model_json_schema()
        except Exception:
            return None
    if hasattr(model, "schema"):  # pydantic v1
        try:
            return model.schema()
        except Exception:
            return None
    return None


def structural_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------------------------------
# AST-based extraction: model + service nodes, and handler-body edge walking.
# Pure parsing — no importlib side-effects.

PROJECT_DIRS = ("models", "services", "utils", "routers", "schemas")


def discover_symbols(directories: list[Path]) -> dict[str, dict]:
    """For each directory, walk *.py files and record top-level class and
    function definitions. Returns name → {file: Path, kind: 'class'|'function',
    line: int}. Last definition wins on collision (rare in concorda-api)."""
    out: dict[str, dict] = {}
    for d in directories:
        if not d.exists():
            continue
        for f in sorted(d.rglob("*.py")):
            if "__pycache__" in f.parts:
                continue
            if f.name == "__init__.py":
                continue
            try:
                tree = ast.parse(f.read_text())
            except SyntaxError:
                continue
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    out[node.name] = {"file": f, "kind": "class", "line": node.lineno}
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[node.name] = {"file": f, "kind": "function", "line": node.lineno}
    return out


def make_qualified_id(file_path: Path, symbol: str) -> str:
    """concorda-api::<rel-path>::<symbol> — same id format as web (defect #11
    fix)."""
    rel = file_path.resolve().relative_to(REPO).as_posix()
    return f"concorda-api::{rel}::{symbol}"


def is_sqlalchemy_model(class_node: ast.ClassDef) -> bool:
    """A class is treated as a model if it inherits from BaseModel or has
    __tablename__. Loose, but matches concorda-api's convention."""
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id == "BaseModel":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
            return True
    for stmt in class_node.body:
        if isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__tablename__":
                    return True
    return False


def extract_model_nodes() -> list[dict]:
    """Walk concorda-api/models/*.py and emit one model node per SQLAlchemy
    class. Skips models/base.py (the abstract base) and __init__.py."""
    out = []
    models_root = REPO / "models"
    if not models_root.exists():
        return out
    now = datetime.now(timezone.utc).isoformat()
    head = git_head(REPO)
    for f in sorted(models_root.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        if f.name in ("__init__.py", "base.py"):
            continue
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not is_sqlalchemy_model(node):
                continue
            nid = make_qualified_id(f, node.name)
            rel = f.resolve().relative_to(REPO).as_posix()
            payload = {"name": node.name, "kind": "model", "tablename": _tablename_for(node)}
            n = {
                "schema_version": 1,
                "id": nid,
                "kind": "model",
                "title": node.name,
                "feature": None,
                "source": {"repo": "concorda-api", "path": rel, "symbol": node.name, "line": node.lineno},
                "signature": payload,
                "structural_hash": structural_hash(payload),
                "depends_on": [],
                "external_consumers": [],
                "tests": [],
                "dossier": f"dossiers/models/{slugify_id(nid)}.md",
                "extractor": "extract_api.py",
                "warnings": [],
            }
            out.append(n)
    return out


def _tablename_for(class_node: ast.ClassDef) -> str | None:
    for stmt in class_node.body:
        if isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__tablename__":
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        return stmt.value.value
    return None


def is_pydantic_schema(class_node: ast.ClassDef) -> bool:
    """Pydantic BaseModel subclass. The class lives in concorda-api/schemas/,
    where every public class is a request/response shape, so the directory is
    the strongest signal. We additionally accept anything inheriting from a
    `BaseModel` name for resilience."""
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id == "BaseModel":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
            return True
    # Many concorda schemas inherit from another schema (e.g. PersonRead extends
    # PersonBase). Default to True if we got here from a schemas/ file — caller
    # filters by directory.
    return False


def extract_schema_nodes() -> list[dict]:
    """Walk concorda-api/schemas/*.py and emit one schema node per Pydantic
    class. These are referenced by endpoints' response_model / request body
    annotations — making them nodes lets edits to a Pydantic shape surface
    every endpoint that consumes it."""
    out = []
    schemas_root = REPO / "schemas"
    if not schemas_root.exists():
        return out
    for f in sorted(schemas_root.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        if f.name == "__init__.py":
            continue
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            # In schemas/, every top-level class is a Pydantic schema by
            # convention. We don't gate on inheritance because schemas commonly
            # extend other schemas, not BaseModel directly.
            if node.name.startswith("_"):
                continue
            nid = make_qualified_id(f, node.name)
            rel = f.resolve().relative_to(REPO).as_posix()
            field_names = sorted([
                t.target.id if isinstance(t.target, ast.Name) else "?"
                for t in node.body
                if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
            ])
            payload = {"name": node.name, "kind": "schema", "fields": field_names}
            n = {
                "schema_version": 1,
                "id": nid,
                "kind": "schema",
                "title": node.name,
                "feature": None,
                "source": {"repo": "concorda-api", "path": rel, "symbol": node.name, "line": node.lineno},
                "signature": payload,
                "structural_hash": structural_hash(payload),
                "depends_on": [],
                "external_consumers": [],
                "tests": [],
                "dossier": f"dossiers/schemas/{slugify_id(nid)}.md",
                "extractor": "extract_api.py",
                "warnings": [],
            }
            out.append(n)
    return out


def extract_service_nodes() -> list[dict]:
    """Walk concorda-api/{services,utils}/*.py and emit one node per top-level
    function. These show up as call sites in handler bodies."""
    out = []
    now = datetime.now(timezone.utc).isoformat()
    head = git_head(REPO)
    for root in (REPO / "services", REPO / "utils"):
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.py")):
            if "__pycache__" in f.parts:
                continue
            if f.name == "__init__.py":
                continue
            try:
                tree = ast.parse(f.read_text())
            except SyntaxError:
                continue
            for node in tree.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name.startswith("_"):
                    continue  # private helpers
                nid = make_qualified_id(f, node.name)
                rel = f.resolve().relative_to(REPO).as_posix()
                payload = {"name": node.name, "kind": "service", "args": [a.arg for a in node.args.args]}
                n = {
                    "schema_version": 1,
                    "id": nid,
                    "kind": "service",
                    "title": node.name,
                    "feature": None,
                    "source": {"repo": "concorda-api", "path": rel, "symbol": node.name, "line": node.lineno},
                    "signature": payload,
                    "structural_hash": structural_hash(payload),
                    "depends_on": [],
                    "external_consumers": [],
                    "tests": [],
                    "dossier": f"dossiers/services/{slugify_id(nid)}.md",
                    "extractor": "extract_api.py",
                    "warnings": [],
                }
                out.append(n)
    return out


WEBSOCKET_SYMBOLS = {"broadcast_event", "broadcast_to_room", "send_to_user"}


def walk_handler_body(handler, symbol_index: dict[str, dict]) -> list[dict]:
    """Parse the module containing the handler, find the handler's def by name,
    and walk its body for Name/Attribute references. For each reference whose
    name is in symbol_index (a known model/service/util), emit a depends_on edge.

    Edge `via`:
      - db_query  : reference resolves to a model class
      - websocket : reference is a known broadcast helper
      - import    : everything else (service/util function)
    """
    src_file = inspect.getsourcefile(handler)
    if not src_file:
        return []
    try:
        module_src = Path(src_file).read_text()
        module_tree = ast.parse(module_src)
    except (OSError, SyntaxError):
        return []

    # Build local-name → imported-name map from module-level imports. We don't
    # care about the module path here — just whether the local name is one of
    # the symbols we tracked in symbol_index.
    import_aliases: dict[str, str] = {}
    for node in module_tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local = alias.asname or alias.name
                import_aliases[local] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                import_aliases[local] = alias.name

    # Find the handler function definition by name
    handler_node = None
    for node in module_tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == handler.__name__:
            handler_node = node
            break
    if handler_node is None:
        return []

    rel = Path(src_file).resolve().relative_to(REPO).as_posix()
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for child in ast.walk(handler_node):
        # Direct Name reference: `Person`, `BoatCrew`, `broadcast_event`
        names_to_check: list[tuple[str, int]] = []
        if isinstance(child, ast.Name):
            names_to_check.append((child.id, child.lineno))

        for name, lineno in names_to_check:
            imported_name = import_aliases.get(name)
            if not imported_name:
                continue
            sym = symbol_index.get(imported_name)
            if not sym:
                continue
            target_id = make_qualified_id(sym["file"], imported_name)
            if sym["kind"] == "class":
                via = "db_query"
            elif imported_name in WEBSOCKET_SYMBOLS:
                via = "websocket"
            else:
                via = "import"
            key = (target_id, via)
            if key in seen:
                continue
            seen.add(key)
            edges.append({
                "target": target_id,
                "via": via,
                "where": f"{rel}:{lineno}",
                "confidence": "exact",
            })

    return edges


def extract_one(route, symbol_index: dict[str, dict] | None = None) -> dict | None:
    if not hasattr(route, "endpoint") or not hasattr(route, "path"):
        return None
    handler = route.endpoint
    methods = sorted(getattr(route, "methods", []) or [])
    if not methods:
        return None

    # FastAPI routes can have multiple methods; we emit one node per method.
    nodes = []
    try:
        src_file = inspect.getsourcefile(handler)
        _, src_line = inspect.getsourcelines(handler)
    except (OSError, TypeError):
        src_file, src_line = None, None

    rel_path = (
        Path(src_file).resolve().relative_to(REPO).as_posix()
        if src_file
        else None
    )

    body_field = getattr(route, "body_field", None)
    request_type = getattr(getattr(body_field, "field_info", None), "annotation", None) if body_field else None
    request_schema = schema_dict_for(request_type)
    response_schema = schema_dict_for(getattr(route, "response_model", None))

    for method in methods:
        if method in ("HEAD", "OPTIONS"):
            continue
        nid = node_id_for_route(method, route.path)
        node = {
            "schema_version": 1,
            "id": nid,
            "kind": "endpoint",
            "title": f"{method} {route.path}",
            "feature": None,  # TODO(impl): infer from path prefix or override file
            "source": {
                "repo": "concorda-api",
                "path": rel_path,
                "symbol": handler.__name__,
                "line": src_line,
            },
            "signature": {
                "method": method,
                "path": route.path,
                "auth": endpoint_auth(handler),
                "request_schema_ref": (
                    f"#/components/{handler.__name__}/request"
                    if request_schema
                    else None
                ),
                "response_schema_ref": (
                    f"#/components/{handler.__name__}/response"
                    if response_schema
                    else None
                ),
            },
            "structural_hash": structural_hash(
                {
                    "method": method,
                    "path": canonical_path(route.path),
                    "auth": endpoint_auth(handler),
                    "request": request_schema,
                    "response": response_schema,
                }
            ),
            "depends_on": walk_handler_body(handler, symbol_index) if symbol_index else [],
            "external_consumers": [],
            "tests": [],
            "dossier": f"dossiers/endpoints/{slugify_id(nid)}.md",  # endpoint-specific path
            "extractor": "extract_api.py",
            "warnings": [],
        }
        if response_schema is None and method != "DELETE":
            node["warnings"].append(
                {
                    "code": "weakly_typed_response",
                    "message": "Handler has no declared response_model; structural hash cannot detect response shape changes. See DRIFT.md scenario 3.",
                    "where": f"{rel_path}:{src_line}" if rel_path else None,
                }
            )
        nodes.append(node)
    return nodes


def git_head(repo: Path) -> str | None:
    head = repo / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        ref = head.read_text().strip()
        if ref.startswith("ref:"):
            ref_path = repo / ".git" / ref.split(" ", 1)[1]
            if ref_path.exists():
                return ref_path.read_text().strip()[:12]
        return ref[:12]
    except OSError:
        return None


def _stable_view(data: dict) -> dict:
    """Defect #4: per-node files no longer carry transient fields, so the
    'stable view' is just the data itself. Kept as a function so the
    write-if-changed call site reads cleanly and so this is the single place
    to add field stripping in the future if a transient field re-appears."""
    return data


SCHEMAS_DIR = NODES_DIR / "schemas"


def _target_dir_for(kind: str) -> Path:
    return {
        "endpoint": ENDPOINTS_DIR,
        "model": MODELS_DIR,
        "service": SERVICES_DIR,
        "schema": SCHEMAS_DIR,
    }.get(kind, NODES_DIR / kind)


def _via_for_class_symbol(file_path: Path) -> str:
    """Classify a class reference by the directory it lives in:
       - models/   → db_query (SQLAlchemy models)
       - schemas/  → import (Pydantic request/response shapes)
       - anything else → import"""
    try:
        rel = file_path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return "import"
    if rel.startswith("models/"):
        return "db_query"
    return "import"


def write_node(node: dict, dry_run: bool = False) -> tuple[Path, bool]:
    """Write the node JSON if its stable view differs from what's on disk.
    Routes by kind: endpoints/, models/, services/. Bit-stable across regens.
    Defect #2: atomic write via tmp+rename so a crash mid-write never leaves
    a half-written JSON file (which would fail to parse on the next read)."""
    out_dir = _target_dir_for(node["kind"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slugify_id(node['id'])}.json"
    if dry_run:
        return out_path, False
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
        except (OSError, json.JSONDecodeError):
            existing = None
        if existing and _stable_view(existing) == _stable_view(node):
            return out_path, False
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(node, indent=2, sort_keys=True) + "\n")
    tmp.replace(out_path)
    return out_path, True


MANIFEST_DIR = NODES_DIR / "_manifests"


def write_manifest(extractor: str, claimed_ids: list[str]) -> None:
    """Defect #5: each extractor records exactly which ids it emitted this run.
    The reconciler can then distinguish 'this node's source is gone' (archive
    candidate) from 'this extractor didn't run' (preserve state). Atomic write
    via tmp+rename. Bit-stable when claimed_ids is unchanged."""
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = MANIFEST_DIR / f"{extractor}.json"
    payload = {
        "schema_version": 1,
        "extractor": extractor,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_ids": sorted(claimed_ids),
    }
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
            if existing.get("node_ids") == payload["node_ids"]:
                return  # bit-stable: same ids, skip the rewrite
        except (OSError, json.JSONDecodeError):
            pass
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    tmp.replace(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Only emit nodes whose source path matches this string.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    claimed_ids: list[str] = []

    # Phase 1: AST-only model + service + schema nodes. No app import needed.
    model_nodes = extract_model_nodes()
    service_nodes = extract_service_nodes()
    schema_nodes = extract_schema_nodes()
    model_written = service_written = schema_written = 0
    model_unchanged = service_unchanged = schema_unchanged = 0
    for n in model_nodes:
        _, did = write_node(n, dry_run=args.dry_run)
        if did:
            model_written += 1
        else:
            model_unchanged += 1
        claimed_ids.append(n["id"])
    for n in service_nodes:
        _, did = write_node(n, dry_run=args.dry_run)
        if did:
            service_written += 1
        else:
            service_unchanged += 1
        claimed_ids.append(n["id"])
    for n in schema_nodes:
        _, did = write_node(n, dry_run=args.dry_run)
        if did:
            schema_written += 1
        else:
            schema_unchanged += 1
        claimed_ids.append(n["id"])

    symbol_index = discover_symbols(
        [REPO / d for d in PROJECT_DIRS if (REPO / d).exists()]
    )

    # Defect #8: pure-AST endpoint extraction. No app import, no startup hooks
    # fired, no DB connection opened. ~10× faster than load_fastapi_app.
    endpoint_nodes = extract_endpoints_via_ast(symbol_index)
    ep_written = 0
    ep_unchanged = 0
    skipped = 0
    for n in endpoint_nodes:
        if args.only and args.only not in (n["source"]["path"] or ""):
            skipped += 1
            continue
        _, did_write = write_node(n, dry_run=args.dry_run)
        if did_write:
            ep_written += 1
        else:
            ep_unchanged += 1
        claimed_ids.append(n["id"])

    if not args.dry_run and not args.only:
        write_manifest("extract_api", claimed_ids)

    print(
        f"wrote {ep_written} endpoint ({ep_unchanged} unchanged), "
        f"{model_written} model ({model_unchanged} unchanged), "
        f"{service_written} service ({service_unchanged} unchanged), "
        f"{schema_written} schema ({schema_unchanged} unchanged), "
        f"skipped {skipped}, manifest={len(claimed_ids)} ids, dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
