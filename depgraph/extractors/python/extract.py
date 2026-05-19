"""Python primitive extractor — schema v2 layered substrate.

Walks every .py under repo_path, emits module / package / class / function /
variable primitives. No kind decisions; classification is a later step.

Memory model (R6, #71): each file's AST is parsed once, then dropped before
the next file. Cross-file passes operate on compact per-file "facts" dicts
(names, line numbers, relations) rather than live ast.Module objects. This
keeps peak resident memory bounded by O(facts_size_per_repo) instead of
O(AST_size_per_repo) — the latter dominates `kg depgraph regen` on
moderate Python corpora.

The TS-side mirror is open issue #47 (`sf.forget`).
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, Sequence

from depgraph.lib.edges import EdgeKind
from depgraph.lib.path_filters import included

from .canonical import canonical_id, structural_hash


EXTRACTOR_TAG = "depgraph/extractors/python/extract.py@2026-05-19"
SCHEMA_VERSION = 2


# ---------------------------------------------------------------------------
# Per-resolver hit-rate counters (R7, issue #77)
# ---------------------------------------------------------------------------
#
# Each resolver branch ticks a counter keyed by (resolver_name, outcome) so the
# `kg depgraph stats` report can answer "how often does <branch> resolve vs fall
# through?". The counter survives across files within one extract_repo() run
# (call resolution is per-file, but we want an aggregate across the corpus) and
# is exposed via `consume_resolver_stats()` — a read-then-reset accessor that
# regen.py drains after each extractor call.
#
# Outcomes are a closed set:
#   hit         resolved to an in-corpus or canonical external target with
#               exact confidence
#   fuzzy       resolved heuristically (re-export chase, wildcard imports,
#               etc.) — confidence carries through to the edge as 'fuzzy'
#   fallthrough resolver gave up and either emitted an unresolved sentinel
#               or nothing at all
#
# Module-level state is the lightest touch given the post-#71 streaming
# refactor: the resolver branches sit several call-frames deep inside
# extract_repo(), threading a Counter dict through every signature would be
# noisier than the value of the isolation.

_RESOLVER_STATS: dict[tuple[str, str], int] = {}


def _tick(resolver: str, outcome: str) -> None:
    """Bump the (resolver, outcome) counter."""
    key = (resolver, outcome)
    _RESOLVER_STATS[key] = _RESOLVER_STATS.get(key, 0) + 1


def consume_resolver_stats() -> dict[tuple[str, str], int]:
    """Return the accumulated resolver-stats counter and reset it.

    Called by regen.py after each `extract_repo()` so per-repo counters can be
    merged into the corpus-wide `_meta.json::resolver_stats` map. Returning a
    copy of the live dict (rather than handing the live dict over) keeps the
    contract symmetric with the TS side, which serializes its counter then
    discards it.
    """
    snapshot = dict(_RESOLVER_STATS)
    _RESOLVER_STATS.clear()
    return snapshot


def _base_primitive(*, schema_id: str, primitive: str, name: str,
                    owner: str | None, repo: str, path: str,
                    line: int, end_line: int, signature: dict,
                    attributes_overrides: dict | None = None,
                    structural_payload: dict) -> dict:
    attrs = {"abstract": False, "generated": False, "external": False,
             "template_parameters": [], "macro": False, "mutable": True,
             "instantiable": True, "inheritable": True}
    attrs.update(attributes_overrides or {})
    return {
        "schema_version": SCHEMA_VERSION,
        "id": schema_id,
        "primitive": primitive,
        "name": name,
        "owner": owner,
        "source": {"repo": repo, "path": path, "language": "python",
                   "line": line, "end_line": end_line},
        "signature": signature,
        "attributes": attrs,
        "edges_out": [],
        "structural_hash": structural_hash(structural_payload),
        "kind": None,
        "extractor": EXTRACTOR_TAG,
    }


_HARDCODED_SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules"}


def _iter_py_files(
    repo_path: Path,
    *,
    include_paths: Sequence[str] = (),
    exclude_paths: Sequence[str] = (),
) -> Iterator[Path]:
    """Yield every .py under repo_path subject to:
      1. Hardcoded skip dirs (__pycache__, virtualenvs, node_modules) — always.
      2. include_paths — if non-empty, file's rel-path must match at least one.
      3. exclude_paths — file's rel-path must match none.
    """
    for p in repo_path.rglob("*.py"):
        if any(part in _HARDCODED_SKIP_DIRS for part in p.parts):
            continue
        rel = str(p.relative_to(repo_path))
        if not included(rel, include_paths=include_paths, exclude_paths=exclude_paths):
            continue
        yield p


def extract_repo(
    *,
    repo_key: str,
    repo_path: Path,
    include_paths: Sequence[str] = (),
    exclude_paths: Sequence[str] = (),
) -> Iterator[dict]:
    primitives: list[dict] = []
    # Per-file facts harvested while the AST is live; the AST itself is
    # dropped immediately after. See _collect_file_facts() for the shape.
    facts_by_path: dict[str, dict] = {}

    files = sorted(_iter_py_files(
        repo_path,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    ))

    # packages: dirs that contain __init__.py
    package_dirs = set()
    for f in files:
        rel = f.relative_to(repo_path)
        if rel.name == "__init__.py":
            package_dirs.add(str(rel.parent))
    for pkg_path in sorted(package_dirs):
        primitives.append(_base_primitive(
            schema_id=f"{repo_key}::{pkg_path}",
            primitive="package", name=pkg_path, owner=None,
            repo=repo_key, path=pkg_path, line=0, end_line=0,
            signature={}, structural_payload={"kind": "package", "path": pkg_path},
        ))

    # modules — single-pass over files: parse AST, extract primitives,
    # harvest facts the cross-file passes will need, then drop the AST.
    for f in files:
        rel = str(f.relative_to(repo_path))
        text = f.read_text()
        tree = ast.parse(text)
        end_line = len(text.splitlines()) or 1
        primitives.append(_base_primitive(
            schema_id=f"{repo_key}::{rel}",
            primitive="module", name=rel, owner=None,
            repo=repo_key, path=rel, line=1, end_line=end_line,
            signature={}, structural_payload={"kind": "module", "path": rel},
        ))
        primitives.extend(_walk_module_body(tree, repo_key=repo_key, rel_path=rel))
        # Compact intermediate digest used by every cross-file resolver pass.
        # Designed to be << sizeof(tree); see _collect_file_facts() for the
        # exact shape. The local `tree` binding falls out of scope at the
        # end of this loop iteration, so the AST is eligible for GC before
        # the next file is parsed.
        facts_by_path[rel] = _collect_file_facts(tree, rel_path=rel)
        del tree

    # L2 edge resolution passes (ordered: each pass may read edges added by prior)
    _attach_defines_edges(primitives)
    _attach_imports_edges(primitives, facts_by_path=facts_by_path,
                          repo_key=repo_key, repo_path=repo_path)
    imports_by_path = _build_imports_by_path(primitives)
    _attach_inheritance_edges(primitives, facts_by_path=facts_by_path,
                               imports_by_path=imports_by_path)
    _attach_call_edges(primitives, facts_by_path=facts_by_path)
    _attach_var_access_edges(primitives, facts_by_path=facts_by_path)

    _attach_decorator_edges(primitives, imports_by_path=imports_by_path)
    _attach_tests_edges(primitives, facts_by_path=facts_by_path)

    yield from primitives


# ---------------------------------------------------------------------------
# Phase 1: per-file fact collection
# ---------------------------------------------------------------------------

def _collect_file_facts(tree: ast.Module, *, rel_path: str) -> dict:
    """Walk a single file's AST once and return a compact dict capturing
    everything the cross-file resolver passes will need. The AST itself is
    dropped after this returns.

    Shape:
        {
          "imports":     list[dict]   — per import statement, see _import_record
          "top_classes": list[dict]   — top-level ClassDef name / lineno / bases
          "functions":   list[dict]   — every (Async)FunctionDef anywhere in the
                                        tree, with the ordered event stream the
                                        body-walking passes consume
        }

    The event stream for each function preserves the order of `ast.walk(fn)`
    — call resolution mutates a var_types map mid-walk, so order is load-
    bearing. See _emit_function_facts() for the event schema.
    """
    imports: list[dict] = []
    top_classes: list[dict] = []
    functions: list[dict] = []

    # Top-level ClassDefs (only top-level — nested classes don't get
    # inheritance resolution per current behavior).
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            top_classes.append({
                "name": node.name,
                "lineno": node.lineno,
                "bases": [_name_from_base(b) for b in node.bases],
            })

    # Imports anywhere in the tree (current behavior uses ast.walk so nested
    # imports inside functions are also captured).
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.append({
                "stmt": "Import",
                "lineno": node.lineno,
                "names": [(a.name, a.asname) for a in node.names],
            })
        elif isinstance(node, ast.ImportFrom):
            imports.append({
                "stmt": "ImportFrom",
                "lineno": node.lineno,
                "level": node.level or 0,
                "module": node.module or "",
                "names": [(a.name, a.asname) for a in node.names],
            })

    # Module-scope variable names — used to filter Name events down to the
    # ones the var-access pass actually cares about. Computed up front so we
    # can drop irrelevant Name events at collection time instead of carrying
    # them in memory until Phase 2.
    module_scope_var_names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            module_scope_var_names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    module_scope_var_names.add(tgt.id)

    # Function records — every FunctionDef / AsyncFunctionDef in the tree.
    # Mirrors `ast.walk(tree)` filtered to function-defs to match the order
    # the existing call/var-access/tests passes used.
    for fn_node in ast.walk(tree):
        if isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_emit_function_facts(
                fn_node,
                module_scope_var_names=module_scope_var_names,
            ))

    return {
        "imports": imports,
        "top_classes": top_classes,
        "functions": functions,
    }


def _emit_function_facts(fn_node: ast.FunctionDef | ast.AsyncFunctionDef,
                          *, module_scope_var_names: set[str]) -> dict:
    """Build the per-function intermediate. Schema:

        {
          "lineno":        int,
          "is_async":      bool,  (unused downstream but cheap to record)
          "name":          str,
          "is_test_fn":    bool — name starts with test_ OR has @pytest.* decorator
          "param_ann_roots": dict[arg_name -> root_name | None]
              from _annotation_root_name on each param's annotation
          "events":        list[dict] in ast.walk(fn_node) order.
              Each event is one of:
                {"op": "annassign_typed", "target": str, "ann_root": str|None}
                {"op": "assign_call_name", "target": str, "callee": str}
                {"op": "call",
                   "lineno": int,
                   "func_kind": "name" | "attr_on_name" | "attr_on_other" | "other",
                   "callee_name":    str|None,   # for func_kind == "name"
                   "receiver_name":  str|None,   # for func_kind == "attr_on_name"
                   "attr_name":      str|None,   # for any Attribute callee
                   "in_assert":      bool,
                }
                {"op": "name", "id": str, "ctx": "load"|"store", "lineno": int}
                   (only emitted when id is in module_scope_var_names — keeps
                    the event list small for non-tracked names)
        }
    """
    # Param annotation roots. Annotation expressions are reduced to a single
    # representative root name via _annotation_root_name; the full ast.expr
    # isn't carried into Phase 2.
    param_ann_roots: dict[str, str | None] = {}
    for arg in fn_node.args.args + fn_node.args.kwonlyargs:
        if arg.annotation is not None:
            param_ann_roots[arg.arg] = _annotation_root_name(arg.annotation)

    is_test_fn = fn_node.name.startswith("test_") or any(
        _decorator_name(d).startswith("pytest.") for d in fn_node.decorator_list
    )

    # Build child->parent map so we can stamp each Call event with whether
    # it's inside an ast.Assert. The tests pass needs this — computing it
    # here means we don't need to retain the AST.
    parents: dict[int, ast.AST] = {}
    for sub in ast.walk(fn_node):
        for child in ast.iter_child_nodes(sub):
            parents[id(child)] = sub

    def _in_assert(node: ast.AST) -> bool:
        cur = parents.get(id(node))
        while cur is not None:
            if isinstance(cur, ast.Assert):
                return True
            cur = parents.get(id(cur))
        return False

    events: list[dict] = []
    for sub in ast.walk(fn_node):
        # Type-binding events for the call resolver's var_types map.
        # Pattern 1: x: SomeClass = ...
        if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
            events.append({
                "op": "annassign_typed",
                "target": sub.target.id,
                "ann_root": _annotation_root_name(sub.annotation),
            })

        # Pattern 2: x = SomeClass(...) — only the single-target, Name-callee
        # shape feeds var_types in the call pass.
        if (isinstance(sub, ast.Assign)
                and len(sub.targets) == 1
                and isinstance(sub.targets[0], ast.Name)
                and isinstance(sub.value, ast.Call)
                and isinstance(sub.value.func, ast.Name)):
            events.append({
                "op": "assign_call_name",
                "target": sub.targets[0].id,
                "callee": sub.value.func.id,
            })

        # Call events — normalized to a func_kind tag plus the names the
        # resolver needs. The original ast.Call is discarded.
        if isinstance(sub, ast.Call):
            func = sub.func
            ev: dict = {
                "op": "call",
                "lineno": sub.lineno,
                "in_assert": _in_assert(sub),
                "callee_name": None,
                "receiver_name": None,
                "attr_name": None,
            }
            if isinstance(func, ast.Name):
                ev["func_kind"] = "name"
                ev["callee_name"] = func.id
            elif isinstance(func, ast.Attribute):
                ev["attr_name"] = func.attr
                if isinstance(func.value, ast.Name):
                    ev["func_kind"] = "attr_on_name"
                    ev["receiver_name"] = func.value.id
                else:
                    ev["func_kind"] = "attr_on_other"
            else:
                ev["func_kind"] = "other"
            events.append(ev)

        # Name events for the reads/assigns pass — only emit when the name
        # could possibly match a module-scope variable. This is the main
        # memory win: most Name nodes never feed an edge.
        if isinstance(sub, ast.Name) and sub.id in module_scope_var_names:
            if isinstance(sub.ctx, ast.Load):
                events.append({"op": "name", "id": sub.id,
                               "ctx": "load", "lineno": sub.lineno})
            elif isinstance(sub.ctx, ast.Store):
                events.append({"op": "name", "id": sub.id,
                               "ctx": "store", "lineno": sub.lineno})

    return {
        "lineno": fn_node.lineno,
        "is_async": isinstance(fn_node, ast.AsyncFunctionDef),
        "name": fn_node.name,
        "is_test_fn": is_test_fn,
        "param_ann_roots": param_ann_roots,
        "events": events,
    }


def _build_imports_by_path(primitives: list[dict]) -> dict[str, dict[str, str]]:
    """Helper used by passes that need {path -> {local_binding -> target_id}}.
    Reads imports edges from module primitives' edges_out."""
    out: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] != "module":
            continue
        for e in p["edges_out"]:
            if e["kind"] != "imports":
                continue
            lb = e.get("local_binding")
            if lb:
                out.setdefault(p["source"]["path"], {})[lb] = e["target"]
    return out


def _decorator_name(dec: ast.expr) -> str:
    if isinstance(dec, ast.Name):
        return dec.id
    if isinstance(dec, ast.Attribute):
        return f"{_decorator_name(dec.value)}.{dec.attr}"
    if isinstance(dec, ast.Call):
        return _decorator_name(dec.func)
    return ast.unparse(dec)


_ROUTE_DECORATOR_VERBS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _route_info_from_decorators(decorators: list[ast.expr]) -> tuple[str, str] | None:
    """Best-effort extraction of (METHOD, path) from any decorator that
    looks like `<prefix>.<verb>("/path", ...)` — FastAPI/Starlette and
    Flask's typed-verb decorators (`@app.get("/x")`) both fit this shape.

    Returns None if no decorator matches or the path arg isn't a literal
    string. The endpoint classifier still owns the kind verdict; this
    function only feeds the cross-repo route-call join, which needs the
    `(method, path)` shape on the endpoint's signature."""
    for dec in decorators:
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if not isinstance(func, ast.Attribute):
            continue
        verb = func.attr.lower()
        if verb not in _ROUTE_DECORATOR_VERBS:
            continue
        if not dec.args:
            continue
        first = dec.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return verb.upper(), first.value
    return None


def _annotation_text(ann: ast.expr | None) -> str | None:
    return ast.unparse(ann) if ann is not None else None


def _walk_module_body(tree: ast.Module, *, repo_key: str, rel_path: str) -> list[dict]:
    out: list[dict] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.extend(_emit_class(node, repo_key=repo_key, rel_path=rel_path))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(_function_primitive(node, owner=None,
                                           repo_key=repo_key, rel_path=rel_path))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            out.extend(_variable_primitives(node, owner=None,
                                            repo_key=repo_key, rel_path=rel_path))
    return out


def _emit_class(node: ast.ClassDef, *, repo_key: str, rel_path: str,
                parent_qualname: str | None = None) -> list[dict]:
    """Emit a class primitive plus its members. Recurses into nested classes.

    `parent_qualname` is the dotted name of the enclosing class chain, used
    to build nested ids like `Outer.Inner` and `Outer.Inner.method`.
    """
    out: list[dict] = []
    qualname = f"{parent_qualname}.{node.name}" if parent_qualname else node.name
    class_id = canonical_id(repo_key, rel_path, qualname)
    owner = canonical_id(repo_key, rel_path, parent_qualname) if parent_qualname else None
    tparams = [tp.name for tp in getattr(node, "type_params", [])]
    out.append(_base_primitive(
        schema_id=class_id, primitive="class", name=qualname, owner=owner,
        repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
        signature={"decorators": [_decorator_name(d) for d in node.decorator_list]},
        attributes_overrides={"abstract": False, "instantiable": True,
                              "template_parameters": tparams},
        structural_payload={"primitive": "class", "name": qualname,
                            "signature": {"decorators": [_decorator_name(d) for d in node.decorator_list],
                                          "bases": [ast.unparse(b) for b in node.bases]},
                            "body_text": ast.unparse(node)},
    ))
    for child in node.body:
        if isinstance(child, ast.ClassDef):
            # Nested class — recurse with this class as parent. The
            # recursive call builds the dotted qualname (Outer.Inner) and
            # sets `owner` to the enclosing class id.
            out.extend(_emit_class(child, repo_key=repo_key, rel_path=rel_path,
                                   parent_qualname=qualname))
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # `owner` carries the parent's full canonical id; the function
            # primitive derives its symbol as `<owner-qualname>.<name>`,
            # which works for nested classes since the owner's id ends
            # with the dotted qualname (Outer.Inner).
            out.append(_function_primitive(child, owner=class_id, repo_key=repo_key,
                                           rel_path=rel_path))
        elif isinstance(child, (ast.Assign, ast.AnnAssign)):
            out.extend(_variable_primitives(child, owner=class_id, repo_key=repo_key,
                                            rel_path=rel_path))
    return out


def _property_role(decorator_names: list[str], fn_name: str) -> str | None:
    """Return ':getter' / ':setter' / ':deleter' if the function is part of
    a property triple; None for normal methods.
    """
    for d in decorator_names:
        if d == "property":
            return ":getter"
        if d == f"{fn_name}.setter":
            return ":setter"
        if d == f"{fn_name}.deleter":
            return ":deleter"
    return None


def _function_primitive(node: ast.FunctionDef | ast.AsyncFunctionDef,
                        *, owner: str | None, repo_key: str, rel_path: str) -> dict:
    dec_names = [_decorator_name(d) for d in node.decorator_list]
    prop_suffix = _property_role(dec_names, node.name) or ""
    base_symbol = f"{owner.split('::')[-1]}.{node.name}" if owner else node.name
    symbol = f"{base_symbol}{prop_suffix}"
    params = [{"name": a.arg, "type_annotation": _annotation_text(a.annotation),
               "default": None}
              for a in node.args.args + node.args.kwonlyargs]
    tparams = [tp.name for tp in getattr(node, "type_params", [])]
    body_text = ast.unparse(node)  # full def + body, canonicalized by ast.unparse
    signature = {
        "parameters": params,
        "return_type": _annotation_text(node.returns),
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "decorators": dec_names,
    }
    route = _route_info_from_decorators(node.decorator_list)
    if route is not None:
        signature["method"], signature["path"] = route
    return _base_primitive(
        schema_id=canonical_id(repo_key, rel_path, symbol),
        primitive="function", name=symbol, owner=owner,
        repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
        signature=signature,
        attributes_overrides={"template_parameters": tparams,
                              "instantiable": False, "inheritable": False},
        # Per spec: name + signature + scope body. Include body so two
        # functions with the same signature but different bodies hash
        # differently.
        structural_payload={"primitive": "function", "name": symbol,
                            "signature": signature, "body_text": body_text},
    )


def _variable_primitives(node: ast.Assign | ast.AnnAssign,
                         *, owner: str | None, repo_key: str, rel_path: str) -> list[dict]:
    out: list[dict] = []
    if isinstance(node, ast.AnnAssign):
        targets = [node.target]
        type_ann = _annotation_text(node.annotation)
    else:
        targets = node.targets
        type_ann = None
    # RHS value text — needed by the SQL cross-ref pass to read
    # `__tablename__ = "users"`. For AnnAssign the value may be absent
    # (`x: int` with no initializer); record None in that case.
    value_text = ast.unparse(node.value) if node.value is not None else None
    for tgt in targets:
        if not isinstance(tgt, ast.Name):
            continue
        symbol = f"{owner.split('::')[-1]}.{tgt.id}" if owner else tgt.id
        out.append(_base_primitive(
            schema_id=canonical_id(repo_key, rel_path, symbol),
            primitive="variable", name=symbol, owner=owner,
            repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
            signature={"type_annotation": type_ann, "value_text": value_text},
            attributes_overrides={"mutable": tgt.id != tgt.id.upper(),
                                  "instantiable": False, "inheritable": False},
            # Per spec: hash includes name + signature + body. For a
            # variable the "body" is its initializer expression.
            structural_payload={"primitive": "variable", "name": symbol,
                                "signature": {"type_annotation": type_ann,
                                              "value_text": value_text},
                                "body_text": value_text or ""},
        ))
    return out


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.1: defines
# ---------------------------------------------------------------------------

def _attach_defines_edges(primitives: list[dict]) -> None:
    """For every module/class/package, attach `defines` edges to its children
    in-place. Module → top-level class/function/variable, class → members,
    package → immediate child modules."""
    for p in primitives:
        if p["primitive"] == "module":
            path = p["source"]["path"]
            for child in primitives:
                if child["id"] == p["id"]:
                    continue
                if (child["source"]["path"] == path
                        and child["owner"] is None
                        and child["primitive"] in {"class", "function", "variable"}):
                    p["edges_out"].append({
                        "target": child["id"],
                        "kind": EdgeKind.DEFINES.value,
                        "via": "lexical_scope",
                        "where": f"{path}:{child['source']['line']}",
                        "confidence": "exact",
                    })
        elif p["primitive"] == "class":
            for child in primitives:
                if child.get("owner") == p["id"]:
                    p["edges_out"].append({
                        "target": child["id"],
                        "kind": EdgeKind.DEFINES.value,
                        "via": "class_body",
                        "where": f"{p['source']['path']}:{child['source']['line']}",
                        "confidence": "exact",
                    })
        elif p["primitive"] == "package":
            pkg_path = p["source"]["path"]
            for child in primitives:
                if child["primitive"] != "module":
                    continue
                child_path = child["source"]["path"]
                # immediate child: directory portion of child_path == pkg_path
                child_dir = (child_path.rsplit("/", 1)[0]
                             if "/" in child_path else "")
                if child_dir == pkg_path:
                    p["edges_out"].append({
                        "target": child["id"],
                        "kind": EdgeKind.DEFINES.value,
                        "via": "package_member",
                        "where": f"{pkg_path}/",
                        "confidence": "exact",
                    })


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.2: extends / implements
# ---------------------------------------------------------------------------

def _attach_inheritance_edges(primitives: list[dict],
                               *, facts_by_path: dict[str, dict],
                               imports_by_path: dict[str, dict[str, str]]) -> None:
    """Resolve each top-level class's base names to local class ids and append
    `extends` edges in-place.

    Resolution order for each base name:
      1. Top-level class in the same module.
      2. The module's imports table (`from .base import BaseModel` etc.) — uses
         the target the imports pass already resolved, so re-exports and
         absolute/relative imports are handled uniformly. The target must look
         like a class (in-corpus class id, or external symbol id of the form
         `external::pypi::<pkg>::<symbol>`) to be accepted; module-shaped
         targets fall through to the unresolved sentinel to keep `extends`
         taxonomy-valid.
      3. `external::pypi::unknown::<name>` with `unresolved` confidence.
    """
    # top-level class name -> id, per file
    by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] == "class" and p["owner"] is None:
            by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    classes_by_id = {p["id"]: p for p in primitives if p["primitive"] == "class"}

    for path, facts in facts_by_path.items():
        local_names = by_path.get(path, {})
        imports = imports_by_path.get(path, {})
        for cls in facts["top_classes"]:
            class_id = local_names.get(cls["name"])
            if not class_id:
                continue
            target_class = classes_by_id[class_id]
            for base_name in cls["bases"]:
                if base_name is None:
                    continue
                target_id = local_names.get(base_name)
                if target_id:
                    _tick("python.extends.local", "hit")
                    target_class["edges_out"].append({
                        "target": target_id,
                        "kind": EdgeKind.EXTENDS.value,
                        "via": "class_decl",
                        "where": f"{path}:{cls['lineno']}",
                        "confidence": "exact",
                    })
                    continue
                imported = imports.get(base_name)
                if imported and imported in classes_by_id:
                    _tick("python.extends.imports_table", "hit")
                    target_class["edges_out"].append({
                        "target": imported,
                        "kind": EdgeKind.EXTENDS.value,
                        "via": "class_decl",
                        "where": f"{path}:{cls['lineno']}",
                        "confidence": "exact",
                    })
                    continue
                if imported and _is_external_symbol_id(imported):
                    # Imports table found an external symbol — emit with
                    # unresolved confidence (we don't verify the symbol is
                    # class-shaped). Counts as a fallthrough on the
                    # imports_table branch so the hit rate stays a clean
                    # "in-corpus class fraction".
                    _tick("python.extends.imports_table", "fallthrough")
                    target_class["edges_out"].append({
                        "target": imported,
                        "kind": EdgeKind.EXTENDS.value,
                        "via": "class_decl",
                        "where": f"{path}:{cls['lineno']}",
                        "confidence": "unresolved",
                    })
                    continue
                _tick("python.extends.unknown", "fallthrough")
                target_class["edges_out"].append({
                    "target": f"external::pypi::unknown::{base_name}",
                    "kind": EdgeKind.EXTENDS.value,
                    "via": "class_decl",
                    "where": f"{path}:{cls['lineno']}",
                    "confidence": "unresolved",
                })


def _is_external_symbol_id(target_id: str) -> bool:
    """external::pypi::<pkg>::<symbol> shape — distinguishes a symbol id
    (4 components) from a bare package id (3 components, `external::pypi::pkg`).
    Only symbol-shaped ids represent something that could be a class."""
    return target_id.startswith("external::") and len(target_id.split("::")) >= 4


def _is_class_target(target_id: str | None, classes_by_id: dict) -> bool:
    """Predicate for "this target is class-shaped". An annotation in type
    position can name an in-corpus class, an external symbol (e.g.
    `external::pypi::sqlalchemy::Session`), or — incorrectly — a module
    binding. The last case is filtered out by rejecting bare-package
    externals and in-corpus module ids."""
    if target_id is None:
        return False
    if target_id in classes_by_id:
        return True
    if target_id.startswith("external::"):
        return _is_external_symbol_id(target_id)
    return False


def _annotation_root_name(ann: ast.expr) -> str | None:
    """Extract the most-likely class name from a type annotation. Handles
    bare names (`Session`), generic subscripts (`Optional[Session]`,
    `Annotated[Session, Depends(get_db)]`), and dotted access
    (`orm.Session`). Returns the inner type name when the outer wrapper is
    one of the well-known transparent generics (Optional/Union/Annotated/
    ClassVar/Final); otherwise returns the outer name (so `List[Item]`
    returns `List`, since `.append()` is called on the List)."""
    if isinstance(ann, ast.Name):
        return ann.id
    if isinstance(ann, ast.Attribute):
        return ann.attr
    if isinstance(ann, ast.Subscript):
        outer = _annotation_root_name(ann.value)
        if outer in {"Optional", "Union", "Annotated", "ClassVar", "Final"}:
            slice_node = ann.slice
            if isinstance(slice_node, ast.Tuple) and slice_node.elts:
                return _annotation_root_name(slice_node.elts[0])
            return _annotation_root_name(slice_node)
        return outer
    return None


def _name_from_base(base: ast.expr) -> str | None:
    """Recover the rightmost name from a base class expression.
    e.g. `Base` -> 'Base', `pkg.Base` -> 'Base', `Generic[T]` -> 'Generic'."""
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    if isinstance(base, ast.Subscript):
        return _name_from_base(base.value)
    return None


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.3: imports
# ---------------------------------------------------------------------------

def _attach_imports_edges(primitives: list[dict],
                           *, facts_by_path: dict[str, dict],
                           repo_key: str, repo_path: Path) -> None:
    """Emit `imports` edges with `local_binding` on the owning module
    primitive, driven by the import statement records harvested in Phase 1."""
    # Build module index: dotted-module-name -> primitive id
    # e.g. "a" -> "fixture::a.py", "pkg.sub" -> "fixture::pkg/sub.py"
    module_index: dict[str, str] = {}
    # Also index by path for quick lookup
    mod_by_path: dict[str, dict] = {}
    # Reverse: module_id -> source path (used by absolute ImportFrom resolution)
    mod_id_to_path: dict[str, str] = {}
    for p in primitives:
        if p["primitive"] == "module":
            mod_by_path[p["source"]["path"]] = p
            mod_id_to_path[p["id"]] = p["source"]["path"]
            # Convert path to dotted form: "pkg/sub.py" -> "pkg.sub"
            dotted = p["source"]["path"]
            if dotted.endswith(".py"):
                dotted = dotted[:-3]
            dotted = dotted.replace("/", ".")
            if dotted.endswith(".__init__"):
                dotted = dotted[: -len(".__init__")]
            module_index[dotted] = p["id"]

    # Build symbol_index: module_path -> {name -> id}
    sym_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["owner"] is None and p["primitive"] in {"class", "function", "variable"}:
            sym_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    for path, facts in facts_by_path.items():
        mod_prim = mod_by_path.get(path)
        if mod_prim is None:
            continue

        for imp in facts["imports"]:
            if imp["stmt"] == "ImportFrom":
                level = imp["level"]
                module_name = imp["module"]
                lineno = imp["lineno"]
                if level > 0:
                    # Relative import: resolve from this file's directory
                    parts = path.replace("\\", "/").split("/")
                    # parts[-1] is the filename; go up `level` directories
                    base_parts = parts[:-level] if level <= len(parts) - 1 else []
                    if module_name:
                        base_parts = base_parts + module_name.split(".")
                    candidate_path = "/".join(base_parts) + ".py" if base_parts else ""
                    # Also check __init__.py form
                    candidate_init = "/".join(base_parts) + "/__init__.py" if base_parts else ""
                    target_mod_prim = (mod_by_path.get(candidate_path)
                                       or mod_by_path.get(candidate_init))
                    for alias_name, alias_asname in imp["names"]:
                        # `from .pkg import *`: emit a single module-level edge.
                        # The `*` doesn't bind to a single name, so there's no
                        # meaningful local_binding, and confidence is fuzzy —
                        # the actual symbol set depends on the target's __all__
                        # / module contents and isn't statically analyzed here.
                        if alias_name == "*":
                            if target_mod_prim:
                                _tick("python.imports.wildcard", "fuzzy")
                                mod_prim["edges_out"].append({
                                    "target": target_mod_prim["id"],
                                    "kind": EdgeKind.IMPORTS.value, "via": "wildcard_import",
                                    "where": f"{path}:{lineno}",
                                    "confidence": "fuzzy",
                                })
                            else:
                                _tick("python.imports.wildcard", "fallthrough")
                            continue
                        local_binding = alias_asname or alias_name
                        if target_mod_prim:
                            # Try to find the named symbol in the target module
                            target_syms = sym_by_path.get(target_mod_prim["source"]["path"], {})
                            sym_id = target_syms.get(alias_name)
                            if sym_id:
                                target = sym_id
                                confidence = "exact"
                            else:
                                target = target_mod_prim["id"]
                                confidence = "exact"
                            _tick("python.imports.from_module", "hit")
                        else:
                            # Can't resolve — external or unindexed
                            root_pkg = module_name.split(".")[0] if module_name else "unknown"
                            target = f"external::pypi::{root_pkg}::{alias_name}"
                            confidence = "unresolved"
                            _tick("python.imports.from_module", "fallthrough")
                        mod_prim["edges_out"].append({
                            "target": target,
                            "kind": EdgeKind.IMPORTS.value,
                            "via": "import_from",
                            "where": f"{path}:{lineno}",
                            "confidence": confidence,
                            "local_binding": local_binding,
                            "imported_name": alias_name,
                        })
                else:
                    # Absolute ImportFrom: from X.Y.Z import name
                    # Look up the module by dotted path; then try to resolve
                    # the imported name to a top-level symbol in that module.
                    target_mod_id = module_index.get(module_name) if module_name else None
                    for alias_name, alias_asname in imp["names"]:
                        # `from x import *`: emit a single module-level edge.
                        # See the relative branch above for the rationale.
                        if alias_name == "*":
                            if target_mod_id:
                                _tick("python.imports.wildcard", "fuzzy")
                                mod_prim["edges_out"].append({
                                    "target": target_mod_id,
                                    "kind": EdgeKind.IMPORTS.value, "via": "wildcard_import",
                                    "where": f"{path}:{lineno}",
                                    "confidence": "fuzzy",
                                })
                            elif module_name:
                                _tick("python.imports.wildcard", "fallthrough")
                                root_pkg = module_name.split(".")[0]
                                mod_prim["edges_out"].append({
                                    "target": f"external::pypi::{root_pkg}",
                                    "kind": EdgeKind.IMPORTS.value, "via": "wildcard_import",
                                    "where": f"{path}:{lineno}",
                                    "confidence": "unresolved",
                                })
                            else:
                                _tick("python.imports.wildcard", "fallthrough")
                            continue
                        local_binding = alias_asname or alias_name
                        if target_mod_id:
                            # Module is tracked — look for the symbol inside it
                            target_mod_path = mod_id_to_path.get(target_mod_id)
                            sym_id = (sym_by_path.get(target_mod_path or "", {})
                                      .get(alias_name))
                            if sym_id:
                                target = sym_id
                            else:
                                target = target_mod_id
                            confidence = "exact"
                            _tick("python.imports.from_module", "hit")
                        else:
                            # Module not in corpus — external package
                            root_pkg = module_name.split(".")[0] if module_name else "unknown"
                            target = f"external::pypi::{root_pkg}::{alias_name}"
                            confidence = "unresolved"
                            _tick("python.imports.from_module", "fallthrough")
                        mod_prim["edges_out"].append({
                            "target": target,
                            "kind": EdgeKind.IMPORTS.value,
                            "via": "import_from",
                            "where": f"{path}:{lineno}",
                            "confidence": confidence,
                            "local_binding": local_binding,
                            "imported_name": alias_name,
                        })

            elif imp["stmt"] == "Import":
                lineno = imp["lineno"]
                for alias_name, alias_asname in imp["names"]:
                    local_binding = alias_asname or alias_name
                    # Absolute import — look up by dotted name
                    target_id = module_index.get(alias_name)
                    if target_id:
                        target = target_id
                        confidence = "exact"
                        _tick("python.imports.module", "hit")
                    else:
                        root_pkg = alias_name.split(".")[0]
                        target = f"external::pypi::{root_pkg}"
                        confidence = "unresolved"
                        _tick("python.imports.module", "fallthrough")
                    mod_prim["edges_out"].append({
                        "target": target,
                        "kind": EdgeKind.IMPORTS.value,
                        "via": "import",
                        "where": f"{path}:{lineno}",
                        "confidence": confidence,
                        "local_binding": local_binding,
                    })

    _resolve_package_reexports(primitives)


def _resolve_package_reexports(primitives: list[dict]) -> None:
    """Rewrite `import_from` edges that target a package `__init__.py` to
    point at the underlying defining symbol when the package re-exports the
    requested name.

    Why: `from pkg import Name` collapses to the `pkg/__init__.py` module
    when the per-file symbol index doesn't find `Name` directly defined
    there — but `pkg/__init__.py` typically re-exports `Name` via
    `from .sub import Name`. Without this pass, every consumer of a barrel-
    exported symbol appears to import the package rather than the symbol,
    silently under-counting the symbol's reverse dependencies.

    Iterates to a fixpoint (capped) so transitive re-exports through
    multiple `__init__.py` layers also resolve.
    """
    # Identify package __init__.py modules and map their re-exports:
    #   pkg_module_id -> {exposed_name -> target_id}
    # exposed_name is the package edge's local_binding (i.e. what the
    # package names the symbol externally).
    pkg_ids: set[str] = set()
    for p in primitives:
        if p["primitive"] != "module":
            continue
        src = p["source"]["path"]
        if src.endswith("/__init__.py") or src == "__init__.py":
            pkg_ids.add(p["id"])

    def build_reexports() -> dict[str, dict[str, str]]:
        out: dict[str, dict[str, str]] = {}
        for p in primitives:
            if p["id"] not in pkg_ids:
                continue
            m: dict[str, str] = {}
            for e in p["edges_out"]:
                if e.get("kind") != "imports":
                    continue
                if e.get("via") not in ("import_from", "import"):
                    continue
                lb = e.get("local_binding")
                tgt = e.get("target")
                if lb and tgt:
                    m[lb] = tgt
            out[p["id"]] = m
        return out

    for _ in range(10):
        reexports = build_reexports()
        changed = False
        for p in primitives:
            if p["primitive"] != "module":
                continue
            for e in p["edges_out"]:
                if e.get("kind") != "imports" or e.get("via") != "import_from":
                    continue
                tgt = e.get("target")
                if tgt not in pkg_ids:
                    continue
                requested = e.get("imported_name")
                if not requested:
                    continue
                real = reexports.get(tgt, {}).get(requested)
                if real and real != tgt:
                    e["target"] = real
                    changed = True
        if not changed:
            break


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.4: calls + instantiates
# ---------------------------------------------------------------------------

def _attach_call_edges(primitives: list[dict],
                        *, facts_by_path: dict[str, dict]) -> None:
    """For each function primitive, replay the per-function event stream and
    emit calls / instantiates edges. Resolves method calls on local variables
    when the variable's type is known from (a) `x = SomeClass(...)` assignment,
    (b) `x: SomeClass = ...` annotated assignment, (c) parameter annotations
    on the enclosing function."""
    # Index local top-level symbols per file
    local_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p.get("owner") is not None:
            continue
        if p["primitive"] not in {"class", "function", "variable"}:
            continue
        local_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    classes_by_id = {p["id"]: p for p in primitives if p["primitive"] == "class"}
    # Primitive-kind index for taxonomy-correct edge emission. `calls` targets
    # must be functions and `instantiates` targets must be classes (per
    # depgraph/lib/edges.py::EDGE_KIND_RULES); a bare-name call resolving to a
    # variable holding a callable produces no `calls` edge — the reads pass
    # picks up the identifier reference separately.
    functions_by_id = {p["id"] for p in primitives if p["primitive"] == "function"}

    # Index methods: class_id -> {method_local_name -> method_id}
    methods_by_class: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] == "function" and p.get("owner") in classes_by_id:
            # p["name"] is like "ClassName.method_name" — take last segment
            method_local = p["name"].split(".")[-1]
            methods_by_class.setdefault(p["owner"], {})[method_local] = p["id"]

    # Imports local_binding -> target_id, per file (built from edges already attached)
    imports_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] != "module":
            continue
        for e in p["edges_out"]:
            if e["kind"] != "imports":
                continue
            lb = e.get("local_binding")
            if lb:
                imports_by_path.setdefault(p["source"]["path"], {})[lb] = e["target"]

    # Index function primitives by (path, lineno) so we can map fact records
    # back to their primitive. Multiple function-defs can share a line only
    # in pathological code; the first match wins (same lookup the AST-based
    # version used via `next(...)`).
    fn_prim_by_loc: dict[tuple[str, int], dict] = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        key = (p["source"]["path"], p["source"]["line"])
        fn_prim_by_loc.setdefault(key, p)

    for path, facts in facts_by_path.items():
        local_names = local_by_path.get(path, {})
        imports = imports_by_path.get(path, {})

        for fn in facts["functions"]:
            fn_prim = fn_prim_by_loc.get((path, fn["lineno"]))
            if fn_prim is None:
                continue

            # Seed type binding from parameter annotations. Annotation
            # position implies the target is a class — accept both in-corpus
            # classes and external symbol-shaped ids (e.g. SQLAlchemy
            # `Session`, FastAPI `APIRouter`). Module-shaped externals
            # (3-component ids) are rejected so a bare `import foo` doesn't
            # masquerade as a type.
            var_types: dict[str, str] = {}  # local_name -> class_id
            for arg_name, ann_root in fn["param_ann_roots"].items():
                if ann_root is None:
                    continue
                target_id = local_names.get(ann_root) or imports.get(ann_root)
                if _is_class_target(target_id, classes_by_id):
                    var_types[arg_name] = target_id

            # Replay the event stream in walk order. var_types updates and
            # call emissions interleave exactly as they did when this was a
            # live ast.walk(fn_node) loop.
            for ev in fn["events"]:
                op = ev["op"]
                # Pattern 1: x: SomeClass = ...
                if op == "annassign_typed":
                    ann_root = ev["ann_root"]
                    if ann_root is not None:
                        cid = local_names.get(ann_root) or imports.get(ann_root)
                        if _is_class_target(cid, classes_by_id):
                            var_types[ev["target"]] = cid
                    continue

                # Pattern 2: x = SomeClass(...)
                if op == "assign_call_name":
                    cname = ev["callee"]
                    cid = local_names.get(cname) or imports.get(cname)
                    if cid and cid in classes_by_id:
                        var_types[ev["target"]] = cid
                    continue

                # Emit edges for each Call event
                if op == "call":
                    edges = _resolve_call_edge(
                        ev,
                        local_names=local_names,
                        imports=imports,
                        classes_by_id=classes_by_id,
                        functions_by_id=functions_by_id,
                        methods_by_class=methods_by_class,
                        var_types=var_types,
                        path=path,
                    )
                    fn_prim["edges_out"].extend(edges)


def _resolve_call_edge(call: dict, *, local_names: dict, imports: dict,
                        classes_by_id: dict, functions_by_id: set,
                        methods_by_class: dict,
                        var_types: dict, path: str) -> list[dict]:
    """Return a list of edge dicts for a single call event.

    `call` is a normalized event dict produced in Phase 1, not a live
    ast.Call node — fields are `func_kind`, `lineno`, and the names the
    resolver needs (`callee_name`, `receiver_name`, `attr_name`).
    """
    func_kind = call["func_kind"]
    lineno = call["lineno"]

    if func_kind == "name":
        # Bare name: helper() or Service()
        name = call["callee_name"]
        target = local_names.get(name) or imports.get(name)
        if target is None:
            _tick("python.call.bare_name", "fallthrough")
            return []
        if target in classes_by_id:
            kind = EdgeKind.INSTANTIATES.value
        elif target in functions_by_id or target.startswith("external::"):
            # External terminals (e.g. `external::pypi::requests::get`) skip
            # target-kind validation in reconcile and carry semantically-
            # meaningful information about the call site — keep them.
            kind = EdgeKind.CALLS.value
        else:
            # Target is an in-corpus variable, module, or other non-callable
            # primitive. Skip the edge: the reads pass picks up the identifier
            # reference, preserving call-graph reachability without violating
            # the calls/instantiates target-kind rules.
            _tick("python.call.bare_name", "fallthrough")
            return []
        _tick("python.call.bare_name", "hit")
        return [{"target": target, "kind": kind, "via": "function_call",
                  "where": f"{path}:{lineno}", "confidence": "exact"}]

    if func_kind == "attr_on_name":
        # Method call: receiver.method(...)
        recv = call["receiver_name"]
        method = call["attr_name"]
        recv_class_id = var_types.get(recv)
        if recv_class_id is None:
            # Module-named receiver fallback: `import requests;
            # requests.get(...)` leaves `var_types[recv]` unset because
            # the receiver isn't a typed local — it's a name bound by
            # an import statement. Consult the imports table to recover
            # the canonical external target.
            imported = imports.get(recv)
            if imported and imported.startswith("external::"):
                # External package: emit `external::pypi::<pkg>::<method>`
                # by appending the method name as an extra id segment.
                # The imports pass typically stores a bare-package id
                # (3-component, from `import requests`) here; symbol-id
                # receivers are unusual but the same suffix shape stays
                # parseable downstream.
                _tick("python.call.method_via_imports", "hit")
                return [{"target": f"{imported}::{method}",
                          "kind": EdgeKind.CALLS.value,
                          "via": "method_call",
                          "where": f"{path}:{lineno}",
                          "confidence": "exact"}]
            # TODO(#68 follow-up): in-corpus module-named receivers
            # (`import mymod; mymod.foo()`) should resolve `foo` to the
            # function id defined inside `mymod`. Requires a
            # module-id -> {symbol_name: symbol_id} index threaded into
            # this function; deferred to keep this change focused on
            # the external-package case from the issue.
            _tick("python.call.method_unresolved", "fallthrough")
            return [{"target": f"external::unresolved::{recv}.{method}",
                      "kind": EdgeKind.CALLS.value, "via": "method_call",
                      "where": f"{path}:{lineno}",
                      "confidence": "unresolved"}]
        if recv_class_id.startswith("external::"):
            # External typed receiver (e.g. `db: Session` from sqlalchemy).
            # Receiver class is known exactly; method existence on the
            # external class isn't verified, but the edge is exact for
            # graph-traversal purposes.
            _tick("python.call.method_via_var_types", "hit")
            return [{"target": f"{recv_class_id}::{method}",
                      "kind": EdgeKind.CALLS.value, "via": "method_call",
                      "where": f"{path}:{lineno}",
                      "confidence": "exact"}]
        method_id = methods_by_class.get(recv_class_id, {}).get(method)
        if method_id:
            _tick("python.call.method_via_var_types", "hit")
            return [{"target": method_id, "kind": EdgeKind.CALLS.value,
                      "via": "method_call",
                      "where": f"{path}:{lineno}",
                      "confidence": "exact"}]
        # Receiver class is known but the method isn't on it — surface as a
        # fallthrough on the same resolver so we can read the hit rate as
        # "of typed-receiver calls, how many landed on a known method".
        _tick("python.call.method_via_var_types", "fallthrough")
        return [{"target": f"external::unresolved::{recv_class_id}.{method}",
                  "kind": EdgeKind.CALLS.value, "via": "method_call",
                  "where": f"{path}:{lineno}",
                  "confidence": "unresolved"}]

    if func_kind == "attr_on_other":
        # Chained attribute (a.b.c()) — unresolved for v0
        _tick("python.call.attr_on_other", "fallthrough")
        return []

    # Computed callee (getattr, call[0](), etc.) — emit unresolved rather than
    # silently dropping, so the call site is preserved in the corpus.
    _tick("python.call.computed_callee", "fallthrough")
    return [{"target": "external::unresolved::computed_callee",
              "kind": EdgeKind.CALLS.value, "via": "computed_callee",
              "where": f"{path}:{lineno}",
              "confidence": "unresolved"}]


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.5: reads / assigns
# ---------------------------------------------------------------------------

def _attach_var_access_edges(primitives: list[dict],
                               *, facts_by_path: dict[str, dict]) -> None:
    """For each function, replay the per-function `name` events and emit
    `reads` / `assigns` edges to module-scope variables defined in the same
    file. Function-local variables are intentionally NOT tracked — only
    module-scope `VAR = value` style."""
    by_path: dict[str, dict[str, str]] = {}  # path -> { var_name -> var_id }
    for p in primitives:
        if p["primitive"] == "variable" and p.get("owner") is None:
            by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    fn_prim_by_loc: dict[tuple[str, int], dict] = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        key = (p["source"]["path"], p["source"]["line"])
        fn_prim_by_loc.setdefault(key, p)

    for path, facts in facts_by_path.items():
        local_vars = by_path.get(path, {})
        if not local_vars:
            continue
        for fn in facts["functions"]:
            fn_prim = fn_prim_by_loc.get((path, fn["lineno"]))
            if fn_prim is None:
                continue
            for ev in fn["events"]:
                if ev["op"] != "name":
                    continue
                name_id = ev["id"]
                # Name events were already filtered at collection time to
                # only ids in module_scope_var_names, but check again — the
                # var-name set is recomputed here from primitives (same
                # source data, but defensive).
                if name_id not in local_vars:
                    continue
                var_id = local_vars[name_id]
                if ev["ctx"] == "load":
                    fn_prim["edges_out"].append({
                        "target": var_id, "kind": EdgeKind.READS.value,
                        "via": "name_load",
                        "where": f"{path}:{ev['lineno']}",
                        "confidence": "exact",
                    })
                elif ev["ctx"] == "store":
                    fn_prim["edges_out"].append({
                        "target": var_id, "kind": EdgeKind.ASSIGNS.value,
                        "via": "name_store",
                        "where": f"{path}:{ev['lineno']}",
                        "confidence": "exact",
                    })


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.5: decorates
# ---------------------------------------------------------------------------

def _attach_decorator_edges(primitives: list[dict],
                              *, imports_by_path: dict[str, dict[str, str]]) -> None:
    """For each function/class, if any decorator resolves to a locally-defined
    function, class, OR module-level variable, emit a `decorates` edge from
    that source primitive to the decorated function/class.

    `variable` sources support the framework decorator-method-call pattern
    that is ubiquitous in web frameworks — `@router.get("/x")` (FastAPI),
    `@app.route("/x")` (Flask), `@click.command()`, `@admin.register(X)`
    — where the syntactic source of the decoration is a module-level
    variable and the actual decorator is the method-call result (#30).

    External decorators (e.g. @functools.lru_cache, @pytest.fixture) do NOT
    produce edges — the edge taxonomy disallows external terminals as edge
    sources. Those are captured in `signature.decorators` only.

    Module/package sources are also skipped — when the decorator name's
    head resolves through the imports map to a module id (rather than a
    specific symbol), emitting an edge with module-source isn't useful
    and trips the EdgeKind constraint.

    Reads decorator names from each primitive's already-extracted
    `signature.decorators` — does not touch the AST.
    """
    local_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p.get("owner") is None and p["primitive"] in {"class", "function", "variable"}:
            local_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    primitives_by_id = {q["id"]: q for q in primitives}

    for p in primitives:
        if p["primitive"] not in {"class", "function"}:
            continue
        decorators = p.get("signature", {}).get("decorators", [])
        if not decorators:
            continue
        path = p["source"]["path"]
        locals_ = local_by_path.get(path, {})
        imports = imports_by_path.get(path, {})
        for dec in decorators:
            head = dec.split(".")[0]
            source_id = locals_.get(head) or imports.get(head)
            if source_id is None:
                # Completely unknown — external, no edge
                continue
            if source_id.startswith("external::"):
                # Imported from external package — no edge (same rule)
                continue
            source_prim = primitives_by_id.get(source_id)
            if source_prim is None:
                continue
            # The decorator name's head may resolve through the imports map to
            # a module id (e.g. `from models import X` where reconcile pinned
            # the edge to the module rather than to X-the-symbol). A module
            # isn't a valid decorator source per the EdgeKind taxonomy, and
            # the framework-decorator-call pattern that does justify a
            # variable source doesn't apply to module sources — skip (#30).
            if source_prim["primitive"] in {"module", "package"}:
                continue
            source_prim["edges_out"].append({
                "target": p["id"], "kind": EdgeKind.DECORATES.value,
                "via": dec,
                "where": f"{path}:{p['source']['line']}",
                "confidence": "exact",
            })


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.6: tests (assertion-scoped)
# ---------------------------------------------------------------------------

# Test framework primitives: calls to these inside asserts do NOT get
# `tests` edges — they are framework machinery, not code under test.
# Inlined here as a constant until Phase 5 ClassificationConfig exists.
# Rationale: keeping changes scoped to Phase 3; ClassificationConfig will
# subsume this in Phase 5 without any test changes.
_PY_TEST_FRAMEWORK_PRIMITIVES: frozenset[str] = frozenset({
    "pytest", "fixture", "mark", "raises", "warns",
    "assert_called", "assert_called_once", "assert_called_with",
    "mock", "patch", "MagicMock", "Mock",
})


def _attach_tests_edges(primitives: list[dict],
                         *, facts_by_path: dict[str, dict]) -> None:
    """For each test function, emit `tests` edges to call targets that appear
    inside an ast.Assert node. Calls outside assert expressions (e.g. helper
    setup calls) do NOT produce edges.

    Uses the per-call `in_assert` flag stamped during Phase 1 instead of
    walking the AST again — the ancestor-Assert check is computed once when
    the tree is live, then carried on the call event.
    """
    # Build imports index per file so we can resolve called names to ids
    imports_by_path_local = _build_imports_by_path(primitives)

    # Also build module-local symbol index per file
    local_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p.get("owner") is None and p["primitive"] in {"class", "function", "variable"}:
            local_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    fn_prim_by_loc: dict[tuple[str, int], dict] = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        key = (p["source"]["path"], p["source"]["line"])
        fn_prim_by_loc.setdefault(key, p)

    for path, facts in facts_by_path.items():
        if not _is_test_path_py(path):
            continue
        local_names = local_by_path.get(path, {})
        imports = imports_by_path_local.get(path, {})

        for fn in facts["functions"]:
            if not fn["is_test_fn"]:
                continue
            fn_prim = fn_prim_by_loc.get((path, fn["lineno"]))
            if fn_prim is None:
                continue

            for ev in fn["events"]:
                if ev["op"] != "call":
                    continue
                if not ev["in_assert"]:
                    continue
                # Replicates _callee_name_py: for Name callee use the id,
                # for any Attribute callee use the attr name.
                func_kind = ev["func_kind"]
                if func_kind == "name":
                    callee_name = ev["callee_name"]
                elif func_kind in ("attr_on_name", "attr_on_other"):
                    callee_name = ev["attr_name"]
                else:
                    callee_name = None
                if callee_name in _PY_TEST_FRAMEWORK_PRIMITIVES:
                    continue
                if callee_name is None:
                    continue
                target_id = local_names.get(callee_name) or imports.get(callee_name)
                if target_id and not target_id.startswith("external::"):
                    fn_prim["edges_out"].append({
                        "target": target_id, "kind": EdgeKind.TESTS.value,
                        "via": "asserted_call",
                        "where": f"{path}:{ev['lineno']}",
                        "confidence": "exact",
                    })


def _is_test_path_py(path: str) -> bool:
    """True if path matches test_*.py or *_test.py naming convention."""
    last = path.rsplit("/", 1)[-1]
    return last.startswith("test_") or last.endswith("_test.py")
