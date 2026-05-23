"""Python primitive extractor — schema v2 layered substrate.

Walks every .py under repo_path, emits module / package / class / function /
variable primitives. No kind decisions; classification is a later step.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterator, Sequence

from depgraph.lib.path_filters import included

from .canonical import canonical_id, structural_hash
from depgraph.lib.edges import confidence_for_external_target


EXTRACTOR_TAG = "depgraph/extractors/python/extract.py@2026-05-23a"
SCHEMA_VERSION = 2

# Builtins commonly used as parameter / variable type annotations. When an
# annotation resolves to one of these, we emit a synthetic
# `external::builtins::<name>` target so method calls on the typed receiver
# attribute correctly (e.g. `xs: list; xs.append(...)` → `list::append`).
# Receivers typed as `int`/`bool`/etc. rarely have downstream method calls
# in practice but are included for completeness.
_BUILTIN_CLASS_NAMES: frozenset[str] = frozenset({
    "list", "dict", "set", "frozenset", "tuple",
    "str", "bytes", "bytearray",
    "int", "float", "complex", "bool",
    "object", "type", "slice", "range",
    "Exception", "BaseException",
})

# typing.* generic aliases that resolve to a builtin at runtime. PEP 585
# deprecated these in favor of the lower-case builtins, but `typing.List`
# still shows up in older code; mapping them keeps method-call attribution
# on the right receiver (`xs.append()` goes to `list`, not `typing.List`).
_TYPING_BUILTIN_ALIASES: dict[str, str] = {
    "List": "list", "Dict": "dict", "Set": "set",
    "FrozenSet": "frozenset", "Tuple": "tuple",
    "Type": "type",
}


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
    trees_by_path: dict[str, ast.Module] = {}

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

    # modules
    for f in files:
        rel = str(f.relative_to(repo_path))
        text = f.read_text()
        tree = ast.parse(text)
        trees_by_path[rel] = tree
        end_line = len(text.splitlines()) or 1
        primitives.append(_base_primitive(
            schema_id=f"{repo_key}::{rel}",
            primitive="module", name=rel, owner=None,
            repo=repo_key, path=rel, line=1, end_line=end_line,
            signature={}, structural_payload={"kind": "module", "path": rel},
        ))
        primitives.extend(_walk_module_body(tree, repo_key=repo_key, rel_path=rel))

    # L2 edge resolution passes (ordered: each pass may read edges added by prior)
    _attach_defines_edges(primitives)
    _attach_imports_edges(primitives, trees_by_path=trees_by_path, repo_key=repo_key,
                          repo_path=repo_path)
    imports_by_path = _build_imports_by_path(primitives)
    _attach_inheritance_edges(primitives, trees_by_path=trees_by_path,
                               imports_by_path=imports_by_path)
    _attach_call_edges(primitives, trees_by_path=trees_by_path)
    _attach_var_access_edges(primitives, trees_by_path=trees_by_path)

    _attach_decorator_edges(primitives, trees_by_path=trees_by_path,
                             imports_by_path=imports_by_path)
    _attach_tests_edges(primitives, trees_by_path=trees_by_path)
    # SQLAlchemy ORM relationships + ForeignKey edges (#54). Runs AFTER
    # imports / extends so the ORM model detector can chase the
    # inheritance chain to a SQLAlchemy base and so `relationship(Cls)`
    # / `relationship("Cls")` target lookups have the symbol indexes
    # they need.
    _attach_orm_edges(primitives, trees_by_path=trees_by_path,
                       imports_by_path=imports_by_path)

    yield from primitives


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
                        "kind": "defines",
                        "via": "lexical_scope",
                        "where": f"{path}:{child['source']['line']}",
                        "confidence": "exact",
                    })
        elif p["primitive"] == "class":
            for child in primitives:
                if child.get("owner") == p["id"]:
                    p["edges_out"].append({
                        "target": child["id"],
                        "kind": "defines",
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
                        "kind": "defines",
                        "via": "package_member",
                        "where": f"{pkg_path}/",
                        "confidence": "exact",
                    })


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.2: extends / implements
# ---------------------------------------------------------------------------

def _attach_inheritance_edges(primitives: list[dict],
                               *, trees_by_path: dict[str, ast.Module],
                               imports_by_path: dict[str, dict[str, str]]) -> None:
    """Walk each class's bases AST, resolve base names to local class ids,
    append `extends` edges in-place.

    Resolution order for each base expression:
      1. Attribute-style (`module.Class`): resolve `module` via the imports
         table to a target module id, then look up `Class` in that module's
         symbol table. Handles `import base; class X(base.BaseModel)` and
         `import sqlalchemy; class X(sqlalchemy.Base)` (external module +
         attr → synthesized symbol id).
      2. Top-level class in the same module.
      3. The module's imports table (`from .base import BaseModel`) — uses
         the target the imports pass already resolved, so re-exports and
         absolute/relative imports are handled uniformly. Must look class-
         shaped (in-corpus class id, or external symbol-shaped id) to be
         accepted; module-shaped targets fall through.
      4. `external::pypi::unknown::<name>` with `unresolved` confidence.
    """
    # top-level class name -> id, per file
    by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] == "class" and p["owner"] is None:
            by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    classes_by_id = {p["id"]: p for p in primitives if p["primitive"] == "class"}

    # module id -> {symbol_name -> primitive_id}: needed to resolve
    # attribute-style bases (`module.Class`) where `module` is bound by
    # an `import module` and `Class` lives inside that module's file.
    mod_id_to_path: dict[str, str] = {}
    for p in primitives:
        if p["primitive"] == "module":
            mod_id_to_path[p["id"]] = p["source"]["path"]
    sym_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["owner"] is None and p["primitive"] in {"class", "function", "variable"}:
            sym_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    for path, tree in trees_by_path.items():
        local_names = by_path.get(path, {})
        imports = imports_by_path.get(path, {})
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            class_id = local_names.get(node.name)
            if not class_id:
                continue
            target_class = classes_by_id[class_id]
            for base in node.bases:
                # Attribute-style: `module.Class` and `a.b.Class` (incl.
                # `Subscript` of an Attribute, e.g. `module.Generic[T]`).
                # For `a.b.Class` we try the longest-to-shortest dotted
                # prefix of the attribute chain against the imports table:
                # `import a.b` records `local_binding="a.b"`, while
                # `import a` (then `a.b.Class`) records `"a"`. Trying the
                # longest prefix first lands on the most specific match.
                attr_base = base.value if isinstance(base, ast.Subscript) else base
                if isinstance(attr_base, ast.Attribute):
                    chain = _attribute_chain(attr_base.value)
                    attr_name = attr_base.attr
                    mod_target = None
                    if chain:
                        # Try longest -> shortest: ['a.b.c', 'a.b', 'a'].
                        for cut in range(len(chain), 0, -1):
                            key = ".".join(chain[:cut])
                            if key in imports:
                                mod_target = imports[key]
                                break
                        if mod_target:
                            if mod_target.startswith("external::"):
                                # `import sqlalchemy; class X(sqlalchemy.Base)`
                                # or `import a.b; class X(a.b.Class)`:
                                # synthesize `<external_module_id>::<attr>`
                                # so the seam is queryable. Confidence
                                # is `external` (known external library;
                                # see edges.confidence_for_external_target).
                                ext_target = f"{mod_target}::{attr_name}"
                                target_class["edges_out"].append({
                                    "target": ext_target,
                                    "kind": "extends",
                                    "via": "class_decl",
                                    "where": f"{path}:{node.lineno}",
                                    "confidence": confidence_for_external_target(ext_target),
                                })
                                continue
                            # In-corpus module: look up the attr in its
                            # symbols. For `import base; class X(base.Class)`
                            # the imports table has `"base"` -> the module
                            # id, and we look up `Class` inside that file's
                            # symbol table. Multi-level dotted prefixes
                            # (`a.b`) match the same way when the imports
                            # pass has recorded them.
                            target_path = mod_id_to_path.get(mod_target)
                            if target_path:
                                sym_id = sym_by_path.get(target_path, {}).get(attr_name)
                                if sym_id and sym_id in classes_by_id:
                                    target_class["edges_out"].append({
                                        "target": sym_id,
                                        "kind": "extends",
                                        "via": "class_decl",
                                        "where": f"{path}:{node.lineno}",
                                        "confidence": "exact",
                                    })
                                    continue
                base_name = _name_from_base(base)
                if base_name is None:
                    continue
                target_id = local_names.get(base_name)
                if target_id:
                    target_class["edges_out"].append({
                        "target": target_id,
                        "kind": "extends",
                        "via": "class_decl",
                        "where": f"{path}:{node.lineno}",
                        "confidence": "exact",
                    })
                    continue
                imported = imports.get(base_name)
                if imported and imported in classes_by_id:
                    target_class["edges_out"].append({
                        "target": imported,
                        "kind": "extends",
                        "via": "class_decl",
                        "where": f"{path}:{node.lineno}",
                        "confidence": "exact",
                    })
                    continue
                if imported and _is_external_symbol_id(imported):
                    target_class["edges_out"].append({
                        "target": imported,
                        "kind": "extends",
                        "via": "class_decl",
                        "where": f"{path}:{node.lineno}",
                        "confidence": confidence_for_external_target(imported),
                    })
                    continue
                # Builtin class extension (`class X(list)`,
                # `class CustomError(Exception)`). `list` / `Exception`
                # aren't in the imports table (implicit at runtime), so
                # without this branch they fall to
                # `external::pypi::unknown::list`. Emit the synthetic
                # `external::builtins::<name>` target — same pattern
                # `_annotation_class_ids` uses for builtin-typed
                # receivers. Confidence is `external` (the builtin
                # ecosystem is a deliberately-unindexed terminal).
                if base_name in _BUILTIN_CLASS_NAMES:
                    builtin_target = f"external::builtins::{base_name}"
                    target_class["edges_out"].append({
                        "target": builtin_target,
                        "kind": "extends",
                        "via": "class_decl",
                        "where": f"{path}:{node.lineno}",
                        "confidence": confidence_for_external_target(builtin_target),
                    })
                    continue
                fallback_target = f"external::pypi::unknown::{base_name}"
                target_class["edges_out"].append({
                    "target": fallback_target,
                    "kind": "extends",
                    "via": "class_decl",
                    "where": f"{path}:{node.lineno}",
                    "confidence": confidence_for_external_target(fallback_target),
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


def _annotation_class_ids(ann: ast.expr, local_names: dict, imports: dict,
                           classes_by_id: dict) -> list[str]:
    """Resolve a type annotation to the list of class-shaped target ids it
    names. Wrapper around `_annotation_root_names` that does the
    name -> id lookup, rewrites `typing.X` aliases to their builtin
    equivalents, and emits a synthetic `external::builtins::<name>`
    target for builtin classes.

    Returns [] when nothing class-shaped resolves; otherwise one id per
    Union branch (or a single id for non-Union annotations)."""
    out: list[str] = []
    for name in _annotation_root_names(ann):
        # typing.* alias rewrite — only when the source binding came from
        # the typing module (`from typing import List`). Without that
        # guard a local `class List` would also be rewritten.
        if name in _TYPING_BUILTIN_ALIASES:
            resolved = imports.get(name)
            if resolved and "::typing::" in resolved:
                name = _TYPING_BUILTIN_ALIASES[name]
        if name in _BUILTIN_CLASS_NAMES:
            out.append(f"external::builtins::{name}")
            continue
        cid = local_names.get(name) or imports.get(name)
        if _is_class_target(cid, classes_by_id):
            out.append(cid)
    return out


def _annotation_root_names(ann: ast.expr) -> list[str]:
    """Recover candidate class names from a type annotation.

    Returns a list because `Union[A, B]` legitimately resolves to two
    candidate receiver types — callers can then emit one edge per branch.
    Single-type annotations return a one-element list; annotations from
    which no static name can be recovered return an empty list.

    Unwraps the transparent generics (`Optional`/`Union`/`Annotated`/
    `ClassVar`/`Final`) written bare or as `typing.X`. For non-transparent
    generics like `List[Item]`, returns the container name (`["List"]`) —
    method calls are on the container, not the element."""
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        # String forward ref: `db: 'Session'` or `xs: 'list[int]'`. Parse
        # the string back into an expression and recurse so wrapper-unwrap
        # logic (Optional/Union/etc.) applies the same way as for unquoted
        # annotations. SyntaxError → unrecoverable, drop to [].
        try:
            parsed = ast.parse(ann.value.strip(), mode="eval").body
        except SyntaxError:
            return []
        return _annotation_root_names(parsed)
    if isinstance(ann, ast.Name):
        return [ann.id]
    if isinstance(ann, ast.Attribute):
        return [ann.attr]
    if isinstance(ann, ast.Subscript):
        if isinstance(ann.value, ast.Name):
            outer_name: str | None = ann.value.id
        elif isinstance(ann.value, ast.Attribute):
            outer_name = ann.value.attr  # `typing.Union` etc.
            # `typing.List[...]` form: rewrite the alias here so attribute-
            # access typing usage attributes to the builtin (`list`) the
            # same way `from typing import List` does via the imports
            # table in `_annotation_class_ids`. Without this branch only
            # the import-form gets the rewrite.
            if (isinstance(ann.value.value, ast.Name)
                    and ann.value.value.id == "typing"
                    and outer_name in _TYPING_BUILTIN_ALIASES):
                outer_name = _TYPING_BUILTIN_ALIASES[outer_name]
        else:
            outer_name = None
        if outer_name in {"Union", "Optional", "Annotated", "ClassVar", "Final"}:
            slice_node = ann.slice
            if outer_name == "Union" and isinstance(slice_node, ast.Tuple):
                names: list[str] = []
                for elt in slice_node.elts:
                    names.extend(_annotation_root_names(elt))
                return names
            if isinstance(slice_node, ast.Tuple) and slice_node.elts:
                # Annotated[T, ...] / ClassVar[T, ...] — only the first matters
                return _annotation_root_names(slice_node.elts[0])
            return _annotation_root_names(slice_node)
        if outer_name is not None:
            return [outer_name]
        return []
    return []


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


def _attribute_chain(node: ast.expr) -> list[str]:
    """Flatten an attribute access into its dotted-name parts, leftmost
    first. Returns [] for shapes that don't bottom out in a Name (e.g.
    `Call(...).foo`).

    Examples:
      Name("a")                                            -> ["a"]
      Attribute(Name("a"), "b")                            -> ["a", "b"]
      Attribute(Attribute(Name("a"), "b"), "c")            -> ["a", "b", "c"]

    Callers join arbitrary prefixes to match against the imports table:
    `import a.b` records `local_binding="a.b"` (the full dotted form);
    `import a` records just `"a"`. Trying longest-prefix-first picks the
    most specific binding.
    """
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        inner = _attribute_chain(node.value)
        if not inner:
            return []
        return inner + [node.attr]
    return []


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.3: imports
# ---------------------------------------------------------------------------

def _registered_name_aliases(
    repo_path: Path, module_index: dict[str, str]
) -> dict[str, str]:
    """Return {registered_name -> module_id} for any package names declared
    in `pyproject.toml` (PEP 621 `[project].name` or `[tool.poetry].name`)
    or `setup.cfg` (`[metadata].name`) at the repo root, when the in-corpus
    layout contains a module whose dotted name ends with that registered
    name.

    The lookup prefers a module whose path ends with `<name>/__init__.py`
    (the package case) over a flat `<name>.py` module, but accepts either.
    A `src/`-layout (`src/<name>/__init__.py`, dotted `src.<name>`) is the
    canonical case this is intended to repair: `import <name>` from
    `examples/...` or `tests/...` would otherwise miss the in-corpus
    package and fall back to `external::pypi::<name>`.

    Returns an empty dict if no manifest is present, no package name is
    declared, or no module's dotted name ends with the registered name.
    """
    import tomllib
    import configparser

    names: list[str] = []
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text())
        except (OSError, ValueError, tomllib.TOMLDecodeError):
            data = {}
        project = data.get("project") or {}
        if isinstance(project, dict):
            n = project.get("name")
            if isinstance(n, str) and n:
                names.append(n)
        poetry = (data.get("tool") or {}).get("poetry") or {}
        if isinstance(poetry, dict):
            n = poetry.get("name")
            if isinstance(n, str) and n and n not in names:
                names.append(n)
        # Poetry / hatch / setuptools `packages = [{include = "..."}]` and
        # `[tool.setuptools.packages.find]` are intentionally not parsed
        # here — those configure WHICH dirs ship as the package, not the
        # registered import name. The PyPI/registered name is what we
        # need for import resolution and lives at the simpler keys above.
    setup_cfg = repo_path / "setup.cfg"
    if setup_cfg.exists():
        try:
            cp = configparser.ConfigParser()
            cp.read(setup_cfg)
            if cp.has_option("metadata", "name"):
                n = cp.get("metadata", "name").strip()
                if n and n not in names:
                    names.append(n)
        except (OSError, configparser.Error):
            pass

    if not names:
        return {}

    # Python package names allow `-` but the import-name form requires `_`
    # (PyPI normalizes underscores/hyphens; the importable identifier is
    # underscore-only). Try both shapes for each declared name.
    candidates: list[str] = []
    for n in names:
        candidates.append(n)
        norm = n.replace("-", "_")
        if norm != n:
            candidates.append(norm)

    out: dict[str, str] = {}
    for name in candidates:
        if name in module_index:
            # Already resolvable by its own dotted name — no aliasing needed.
            continue
        # Search the module index for any module whose dotted name ends
        # with `.<name>` AND originates from a package `__init__.py`.
        # Prefer the shortest matching dotted name (closest-to-root) so a
        # nested submodule named `<name>` doesn't shadow the top-level
        # registered package.
        best: tuple[int, str] | None = None
        for dotted, mod_id in module_index.items():
            if dotted == name:
                best = (0, mod_id)
                break
            if dotted.endswith("." + name) and mod_id.endswith("/__init__.py"):
                segments = dotted.count(".") + 1
                if best is None or segments < best[0]:
                    best = (segments, mod_id)
        if best is not None:
            out[name] = best[1]
    return out


def _attach_imports_edges(primitives: list[dict],
                           *, trees_by_path: dict[str, ast.Module],
                           repo_key: str, repo_path: Path) -> None:
    """Walk ast.Import / ast.ImportFrom in each module, emit `imports` edges
    with `local_binding` on the owning module primitive."""
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

    # Cross-binding: when the repo declares a package name in pyproject.toml
    # (or setup.cfg) and the in-corpus layout puts that package under a
    # prefix like `src/<name>/__init__.py`, `import <name>` from a sibling
    # subtree (e.g. `examples/foo.py` doing `import click`) would otherwise
    # miss the in-corpus module and fall back to `external::pypi::<name>`.
    # Add the registered name as an alias so the import resolves to the
    # in-corpus module id. This is the load-bearing fix for the
    # "registered-name from sibling directory" pattern that monorepos and
    # `src/`-layout single-package repos share.
    for alias_name, alias_target_id in _registered_name_aliases(
        repo_path, module_index
    ).items():
        # Don't shadow an existing exact-path mapping — only fill the gap.
        module_index.setdefault(alias_name, alias_target_id)

    # symbol index: module_id -> {symbol_name -> primitive_id}
    symbol_index: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p.get("owner") is None:
            continue
        owner_id = p["owner"]
        # owner is a module id when the owner's primitive == "module"
        # (functions/classes at module scope have owner=None, so this
        # catches class members — skip those; we want module-level symbols
        # indexed under the module id)
        # Actually: module-level symbols have owner=None. We need the
        # module->symbol mapping built differently:
    # Build symbol_index: module_path -> {name -> id}
    sym_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["owner"] is None and p["primitive"] in {"class", "function", "variable"}:
            sym_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    for path, tree in trees_by_path.items():
        mod_prim = mod_by_path.get(path)
        if mod_prim is None:
            continue
        local_syms = sym_by_path.get(path, {})

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                level = node.level or 0
                module_name = node.module or ""
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
                    for alias in node.names:
                        # `from .pkg import *`: emit a single module-level edge.
                        # The `*` doesn't bind to a single name, so there's no
                        # meaningful local_binding, and confidence is fuzzy —
                        # the actual symbol set depends on the target's __all__
                        # / module contents and isn't statically analyzed here.
                        if alias.name == "*":
                            if target_mod_prim:
                                mod_prim["edges_out"].append({
                                    "target": target_mod_prim["id"],
                                    "kind": "imports", "via": "wildcard_import",
                                    "where": f"{path}:{node.lineno}",
                                    "confidence": "fuzzy",
                                })
                            continue
                        local_binding = alias.asname or alias.name
                        if target_mod_prim:
                            # Try to find the named symbol in the target module
                            target_syms = sym_by_path.get(target_mod_prim["source"]["path"], {})
                            sym_id = target_syms.get(alias.name)
                            if sym_id:
                                target = sym_id
                                confidence = "exact"
                            else:
                                target = target_mod_prim["id"]
                                confidence = "exact"
                        else:
                            # Can't resolve — external or unindexed
                            root_pkg = module_name.split(".")[0] if module_name else "unknown"
                            target = f"external::pypi::{root_pkg}::{alias.name}"
                            confidence = confidence_for_external_target(target)
                        mod_prim["edges_out"].append({
                            "target": target,
                            "kind": "imports",
                            "via": "import_from",
                            "where": f"{path}:{node.lineno}",
                            "confidence": confidence,
                            "local_binding": local_binding,
                            "imported_name": alias.name,
                        })
                else:
                    # Absolute ImportFrom: from X.Y.Z import name
                    # Look up the module by dotted path; then try to resolve
                    # the imported name to a top-level symbol in that module.
                    target_mod_id = module_index.get(module_name) if module_name else None
                    for alias in node.names:
                        # `from x import *`: emit a single module-level edge.
                        # See the relative branch above for the rationale.
                        if alias.name == "*":
                            if target_mod_id:
                                mod_prim["edges_out"].append({
                                    "target": target_mod_id,
                                    "kind": "imports", "via": "wildcard_import",
                                    "where": f"{path}:{node.lineno}",
                                    "confidence": "fuzzy",
                                })
                            elif module_name:
                                root_pkg = module_name.split(".")[0]
                                wildcard_target = f"external::pypi::{root_pkg}"
                                mod_prim["edges_out"].append({
                                    "target": wildcard_target,
                                    "kind": "imports", "via": "wildcard_import",
                                    "where": f"{path}:{node.lineno}",
                                    "confidence": confidence_for_external_target(wildcard_target),
                                })
                            continue
                        local_binding = alias.asname or alias.name
                        if target_mod_id:
                            # Module is tracked — look for the symbol inside it
                            target_mod_path = mod_id_to_path.get(target_mod_id)
                            sym_id = (sym_by_path.get(target_mod_path or "", {})
                                      .get(alias.name))
                            if sym_id:
                                target = sym_id
                            else:
                                target = target_mod_id
                            confidence = "exact"
                        else:
                            # Module not in corpus — external package
                            root_pkg = module_name.split(".")[0] if module_name else "unknown"
                            target = f"external::pypi::{root_pkg}::{alias.name}"
                            confidence = confidence_for_external_target(target)
                        mod_prim["edges_out"].append({
                            "target": target,
                            "kind": "imports",
                            "via": "import_from",
                            "where": f"{path}:{node.lineno}",
                            "confidence": confidence,
                            "local_binding": local_binding,
                            "imported_name": alias.name,
                        })

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    local_binding = alias.asname or alias.name
                    # Absolute import — look up by dotted name
                    target_id = module_index.get(alias.name)
                    if target_id:
                        target = target_id
                        confidence = "exact"
                    else:
                        root_pkg = alias.name.split(".")[0]
                        target = f"external::pypi::{root_pkg}"
                        confidence = confidence_for_external_target(target)
                    mod_prim["edges_out"].append({
                        "target": target,
                        "kind": "imports",
                        "via": "import",
                        "where": f"{path}:{node.lineno}",
                        "confidence": confidence,
                        "local_binding": local_binding,
                    })

    _resolve_package_reexports(primitives, mod_id_to_path, sym_by_path)


_REEXPORT_FIXPOINT_CAP = 10


def _resolve_package_reexports(primitives: list[dict],
                                mod_id_to_path: dict[str, str],
                                sym_by_path: dict[str, dict[str, str]]) -> None:
    """Rewrite `import_from` edges that target a package `__init__.py` to
    point at the underlying defining symbol when the package re-exports the
    requested name.

    Why: `from pkg import Name` collapses to the `pkg/__init__.py` module
    when the per-file symbol index doesn't find `Name` directly defined
    there — but `pkg/__init__.py` typically re-exports `Name` via either
    `from .sub import Name` (named) or `from .sub import *` (wildcard).
    Without this pass, every consumer of a barrel-exported symbol appears
    to import the package rather than the symbol, silently under-counting
    the symbol's reverse dependencies.

    Iterates to a fixpoint (capped) so transitive re-exports through
    multiple `__init__.py` layers — and through chained wildcard barrels
    — also resolve.
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

    def build_reexports(prev: dict[str, dict[str, str]] | None
                        ) -> dict[str, dict[str, str]]:
        out: dict[str, dict[str, str]] = {}
        for p in primitives:
            if p["id"] not in pkg_ids:
                continue
            m: dict[str, str] = {}
            for e in p["edges_out"]:
                if e.get("kind") != "imports":
                    continue
                via = e.get("via")
                tgt = e.get("target")
                if not tgt:
                    continue
                if via in ("import_from", "import"):
                    lb = e.get("local_binding")
                    if lb:
                        m[lb] = tgt
                elif via == "wildcard_import":
                    # `from .sub import *`: re-export every public top-level
                    # symbol of the target module. Python's default semantics
                    # (when `__all__` isn't defined) is "everything not
                    # starting with underscore"; honoring `__all__` would
                    # require a separate AST pass — over-include is the
                    # safer default since downstream consumers only see an
                    # edge if they actually wrote the name.
                    target_path = mod_id_to_path.get(tgt)
                    if target_path:
                        for sym_name, sym_id in sym_by_path.get(target_path, {}).items():
                            if not sym_name.startswith("_"):
                                m.setdefault(sym_name, sym_id)
                    # Chain through the target's own re-export map (so
                    # `pkg/__init__.py: from .subpkg import *` chains
                    # transitively into subpkg's re-exports). Uses the
                    # previous iteration's snapshot — the fixpoint loop
                    # propagates over multiple iterations.
                    if prev:
                        for sym_name, sym_id in prev.get(tgt, {}).items():
                            if not sym_name.startswith("_"):
                                m.setdefault(sym_name, sym_id)
            out[p["id"]] = m
        return out

    # Two-condition fixpoint: keep iterating while EITHER (a) edges are
    # still being rewritten OR (b) the re-export map is still settling.
    # Both matter independently — chained wildcards
    # (`pkg/__init__.py: from .inner import *` → `inner/__init__.py:
    # from .leaf import *`) settle in the map across iterations even when
    # no consumer edge is changing on that iteration. Stopping on
    # edges-only would miss those.
    prev_reexports: dict[str, dict[str, str]] = {}
    converged = False
    for _ in range(_REEXPORT_FIXPOINT_CAP):
        reexports = build_reexports(prev=prev_reexports)
        edges_changed = False
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
                    edges_changed = True
        reexports_changed = (reexports != prev_reexports)
        if not edges_changed and not reexports_changed:
            converged = True
            break
        prev_reexports = reexports
    if not converged:
        print(
            f"[depgraph/extractors/python] package re-export resolution did "
            f"not converge within {_REEXPORT_FIXPOINT_CAP} iterations. Some "
            f"`from pkg import X` edges may still target a package module "
            f"rather than the underlying defining symbol. This usually "
            f"means barrel re-exports are nested more than "
            f"{_REEXPORT_FIXPOINT_CAP} levels deep — raise the cap or "
            f"flatten the barrel layout.",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.4: calls + instantiates
# ---------------------------------------------------------------------------

def _attach_call_edges(primitives: list[dict],
                        *, trees_by_path: dict[str, ast.Module]) -> None:
    """For each function primitive, walk its body and emit calls /
    instantiates edges. Resolves method calls on local variables when the
    variable's type is known from (a) `x = SomeClass(...)` assignment,
    (b) `x: SomeClass = ...` annotated assignment, (c) parameter
    annotations on the enclosing function."""
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

    # Module-id -> {name -> primitive_id} for the b2 imports fallback. A
    # name resolves first to a top-level symbol DEFINED in that module
    # (class/function/variable at module scope), then to a name re-exported
    # via `from .X import Y as Y` (the imports pass has already chased
    # those to their defining symbol IDs in `_resolve_package_reexports`).
    # The second source covers the canonical barrel-package case: `click`
    # is a registered name aliasing `src/click/__init__.py`, but `echo` is
    # not defined in `__init__.py` directly — it's `from .utils import
    # echo as echo`, so it lives in the imports table.
    symbols_by_module: dict[str, dict[str, str]] = {}
    mod_id_by_path: dict[str, str] = {}
    for p in primitives:
        if p["primitive"] == "module":
            mod_id_by_path[p["source"]["path"]] = p["id"]
    for p in primitives:
        if p.get("owner") is None and p["primitive"] in {"class", "function", "variable"}:
            mod_id = mod_id_by_path.get(p["source"]["path"])
            if mod_id is not None:
                symbols_by_module.setdefault(mod_id, {})[p["name"]] = p["id"]
    # Layer in the re-exported names from the imports pass. Only include
    # in-corpus targets — external `local_binding`s here would re-leak.
    for p in primitives:
        if p["primitive"] != "module":
            continue
        for e in p["edges_out"]:
            if e.get("kind") != "imports":
                continue
            lb = e.get("local_binding")
            tgt = e.get("target")
            if not lb or not tgt or tgt.startswith("external::"):
                continue
            bucket = symbols_by_module.setdefault(p["id"], {})
            bucket.setdefault(lb, tgt)

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

    for path, tree in trees_by_path.items():
        local_names = local_by_path.get(path, {})
        imports = imports_by_path.get(path, {})

        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fn_prim = next(
                (p for p in primitives
                 if p["primitive"] == "function"
                    and p["source"]["path"] == path
                    and p["source"]["line"] == fn_node.lineno),
                None,
            )
            if fn_prim is None:
                continue

            # Seed type binding from parameter annotations. Annotation
            # position implies the target is class-shaped — accept in-corpus
            # classes and external symbol-shaped ids (e.g. SQLAlchemy
            # `Session`, FastAPI `APIRouter`). Module-shaped externals
            # (3-component ids) are rejected so a bare `import foo` doesn't
            # masquerade as a type. `Union[A, B]` seeds both branches so
            # method calls on the bound name emit one edge per receiver.
            #
            # `vararg` (`*args: T`) and `kwarg` (`**kwargs: T`) are included
            # alongside the positional/kwonly arg lists. The runtime type of
            # `args` is `tuple[T, ...]` and `kwargs` is `dict[str, T]`, but
            # seeding the bound name's type as `T` is the minimal-but-still-
            # useful first step: the more accurate model would distinguish
            # the container from its elements, but that's a separate
            # iteration-target problem (issue #83 sub-item 2). See also
            # follow-up: method calls on `args` as a tuple aren't modeled.
            var_types: dict[str, list[str]] = {}  # local_name -> [class_id, ...]
            seed_args = list(fn_node.args.args) + list(fn_node.args.kwonlyargs)
            if fn_node.args.vararg is not None:
                seed_args.append(fn_node.args.vararg)
            if fn_node.args.kwarg is not None:
                seed_args.append(fn_node.args.kwarg)
            for arg in seed_args:
                if arg.annotation is None:
                    continue
                cids = _annotation_class_ids(arg.annotation, local_names,
                                              imports, classes_by_id)
                if cids:
                    var_types[arg.arg] = cids

            # #91 (b1): seed `self` to the enclosing class id when the
            # function is a method. The function primitive's `owner` is
            # exactly the class id for methods (set in `_emit_class`), so
            # there's no need to re-discover the enclosing scope from the
            # AST. Before this fix, every `self.method(...)` call inside
            # a class body emitted `external::unresolved::self.method` —
            # 21.5% of pallets-click's unresolved_receiver leak.
            owner = fn_prim.get("owner")
            if owner is not None and owner in classes_by_id:
                # Only seed if the function actually has a `self`-shaped
                # first param. `@staticmethod` / `@classmethod` don't have
                # an instance receiver. We accept any first-arg name
                # (some codebases use `this`/`_`) so the seeding is
                # robust to convention.
                pos_args = fn_node.args.args
                if pos_args:
                    decorators = {_decorator_name(d) for d in fn_node.decorator_list}
                    if "staticmethod" not in decorators:
                        # classmethod's first arg is the class itself, not
                        # an instance — but binding `cls` to the class id
                        # is still correct (calls like `cls.helper(...)`
                        # resolve the same way method calls do).
                        var_types[pos_args[0].arg] = [owner]

            # Walk body in source order; update var_types on assignments,
            # emit edges for each Call node
            for sub in ast.walk(fn_node):
                # Pattern 1: x: SomeClass = ...
                if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                    cids = _annotation_class_ids(sub.annotation, local_names,
                                                  imports, classes_by_id)
                    if cids:
                        var_types[sub.target.id] = cids

                # Pattern 2: x = SomeClass(...). Single-typed by definition —
                # one constructor name — so always a one-element list.
                # `_is_class_target` accepts external symbol-shaped ids so
                # the SQLAlchemy `db = Session()` shape seeds too; downstream
                # method calls on external receivers carry `unresolved`
                # confidence to match the source import chain.
                if (isinstance(sub, ast.Assign)
                        and len(sub.targets) == 1
                        and isinstance(sub.targets[0], ast.Name)
                        and isinstance(sub.value, ast.Call)
                        and isinstance(sub.value.func, ast.Name)):
                    cname = sub.value.func.id
                    cid = local_names.get(cname) or imports.get(cname)
                    if _is_class_target(cid, classes_by_id):
                        var_types[sub.targets[0].id] = [cid]

                # Pattern 3: walrus operator (`if db := Session(): ...`).
                # `ast.NamedExpr` isn't reached by the Assign / AnnAssign
                # branches above — it's its own node type. Same shape as
                # Pattern 2 (name = constructor-call) so reuse the rule.
                if (isinstance(sub, ast.NamedExpr)
                        and isinstance(sub.target, ast.Name)
                        and isinstance(sub.value, ast.Call)
                        and isinstance(sub.value.func, ast.Name)):
                    cname = sub.value.func.id
                    cid = local_names.get(cname) or imports.get(cname)
                    if _is_class_target(cid, classes_by_id):
                        var_types[sub.target.id] = [cid]

                # #91 (b3) Pattern 4: `with Cls(...) as x:` — the binding
                # lives in an `ast.withitem.optional_vars`, not in an
                # Assign/AnnAssign/NamedExpr node, so the patterns above
                # never see it. SQLAlchemy's `with Session(engine) as
                # session:` is the canonical case; every `session.X(...)`
                # call inside the block leaks to unresolved_receiver
                # without this seeding.
                if isinstance(sub, (ast.With, ast.AsyncWith)):
                    for item in sub.items:
                        if (isinstance(item.optional_vars, ast.Name)
                                and isinstance(item.context_expr, ast.Call)
                                and isinstance(item.context_expr.func, ast.Name)):
                            cname = item.context_expr.func.id
                            cid = local_names.get(cname) or imports.get(cname)
                            if _is_class_target(cid, classes_by_id):
                                var_types[item.optional_vars.id] = [cid]

                # Emit edges for each Call node
                if isinstance(sub, ast.Call):
                    edges = _resolve_call_edge(
                        sub,
                        local_names=local_names,
                        imports=imports,
                        classes_by_id=classes_by_id,
                        functions_by_id=functions_by_id,
                        methods_by_class=methods_by_class,
                        var_types=var_types,
                        symbols_by_module=symbols_by_module,
                        path=path,
                    )
                    fn_prim["edges_out"].extend(edges)


def _resolve_call_edge(call: ast.Call, *, local_names: dict, imports: dict,
                        classes_by_id: dict, functions_by_id: set,
                        methods_by_class: dict,
                        var_types: dict,
                        symbols_by_module: dict | None = None,
                        path: str) -> list[dict]:
    """Return a list of edge dicts for a single Call node."""
    if isinstance(call.func, ast.Name):
        # Bare name: helper() or Service()
        name = call.func.id
        target = local_names.get(name) or imports.get(name)
        if target is None:
            return []
        if target in classes_by_id:
            kind = "instantiates"
        elif target in functions_by_id or target.startswith("external::"):
            # External terminals (e.g. `external::pypi::requests::get`) skip
            # target-kind validation in reconcile and carry semantically-
            # meaningful information about the call site — keep them.
            kind = "calls"
        else:
            # Target is an in-corpus variable, module, or other non-callable
            # primitive. Skip the edge: the reads pass picks up the identifier
            # reference, preserving call-graph reachability without violating
            # the calls/instantiates target-kind rules.
            return []
        return [{"target": target, "kind": kind, "via": "function_call",
                  "where": f"{path}:{call.lineno}", "confidence": "exact"}]

    if isinstance(call.func, ast.Attribute):
        # Method call: receiver.method(...)
        if isinstance(call.func.value, ast.Name):
            recv = call.func.value.id
            method = call.func.attr
            recv_class_ids = var_types.get(recv) or []
            if not recv_class_ids:
                # #91 (b2): imports fallback. When the receiver isn't
                # type-bound but IS an imported name pointing at an
                # in-corpus module (e.g. `import click; click.echo(...)`
                # from an examples/ subtree, after the cross-binding pass
                # aliased the registered name to the in-corpus module
                # id), resolve `method` as a top-level symbol of that
                # module. `symbols_by_module` includes both directly-
                # defined names and re-exported ones so a barrel package
                # like `click` (where `echo` is `from .utils import echo
                # as echo`) still resolves.
                if symbols_by_module is not None:
                    import_target = imports.get(recv)
                    if (import_target is not None
                            and not import_target.startswith("external::")):
                        sym_id = symbols_by_module.get(import_target, {}).get(method)
                        if sym_id:
                            # Mirror the bare-name branch's target-kind
                            # gate: class → instantiates, function (or
                            # external terminal — can happen when the
                            # symbol re-export chased through to a
                            # third-party id) → calls, anything else
                            # (e.g. a variable holding a callable) is
                            # dropped here; the reads pass keeps the
                            # identifier reachable.
                            if sym_id in classes_by_id:
                                sym_kind = "instantiates"
                            elif (sym_id in functions_by_id
                                    or sym_id.startswith("external::")):
                                sym_kind = "calls"
                            else:
                                sym_kind = None
                            if sym_kind is not None:
                                return [{"target": sym_id,
                                          "kind": sym_kind, "via": "method_call",
                                          "where": f"{path}:{call.lineno}",
                                          "confidence": "exact"}]
                unr_target = f"external::unresolved::{recv}.{method}"
                return [{"target": unr_target,
                          "kind": "calls", "via": "method_call",
                          "where": f"{path}:{call.lineno}",
                          "confidence": confidence_for_external_target(unr_target)}]
            edges: list[dict] = []
            for recv_class_id in recv_class_ids:
                if recv_class_id.startswith("external::"):
                    # External typed receiver: we know the binding name but
                    # never parsed the package, so neither class shape nor
                    # method existence is verified. Confidence is `external`
                    # to mirror the upstream `from pkg import X` edge.
                    ext_target = f"{recv_class_id}::{method}"
                    edges.append({"target": ext_target,
                                   "kind": "calls", "via": "method_call",
                                   "where": f"{path}:{call.lineno}",
                                   "confidence": confidence_for_external_target(ext_target)})
                    continue
                method_id = methods_by_class.get(recv_class_id, {}).get(method)
                if method_id:
                    edges.append({"target": method_id, "kind": "calls",
                                   "via": "method_call",
                                   "where": f"{path}:{call.lineno}",
                                   "confidence": "exact"})
                else:
                    sentinel = f"external::unresolved::{recv_class_id}.{method}"
                    edges.append({"target": sentinel,
                                   "kind": "calls", "via": "method_call",
                                   "where": f"{path}:{call.lineno}",
                                   "confidence": confidence_for_external_target(sentinel)})
            return edges
        # Chained attribute (a.b.c()) — dropped for v0 (see EDGE-2).
        return []

    # Computed callee (getattr, call[0](), etc.) — emit an
    # `unresolved_receiver` edge rather than silently dropping, so the call
    # site is preserved in the corpus. NB: per issue #53, this *is* the
    # dynamic-callee shape; once a dedicated detector lands, it'll move to
    # confidence=dynamic with its own target prefix.
    callee_target = "external::unresolved::computed_callee"
    return [{"target": callee_target,
              "kind": "calls", "via": "computed_callee",
              "where": f"{path}:{call.lineno}",
              "confidence": confidence_for_external_target(callee_target)}]


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.5: reads / assigns
# ---------------------------------------------------------------------------

def _attach_var_access_edges(primitives: list[dict],
                               *, trees_by_path: dict[str, ast.Module]) -> None:
    """For each function, walk body and emit `reads` / `assigns` edges to
    module-scope variables defined in the same file. Function-local variables
    are intentionally NOT tracked — only module-scope `VAR = value` style."""
    by_path: dict[str, dict[str, str]] = {}  # path -> { var_name -> var_id }
    for p in primitives:
        if p["primitive"] == "variable" and p.get("owner") is None:
            by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    for path, tree in trees_by_path.items():
        local_vars = by_path.get(path, {})
        if not local_vars:
            continue
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fn_prim = next(
                (p for p in primitives
                 if p["primitive"] == "function"
                    and p["source"]["path"] == path
                    and p["source"]["line"] == fn_node.lineno),
                None,
            )
            if fn_prim is None:
                continue
            for sub in ast.walk(fn_node):
                if isinstance(sub, ast.Name) and sub.id in local_vars:
                    var_id = local_vars[sub.id]
                    if isinstance(sub.ctx, ast.Load):
                        fn_prim["edges_out"].append({
                            "target": var_id, "kind": "reads",
                            "via": "name_load",
                            "where": f"{path}:{sub.lineno}",
                            "confidence": "exact",
                        })
                    elif isinstance(sub.ctx, ast.Store):
                        fn_prim["edges_out"].append({
                            "target": var_id, "kind": "assigns",
                            "via": "name_store",
                            "where": f"{path}:{sub.lineno}",
                            "confidence": "exact",
                        })


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.5: decorates
# ---------------------------------------------------------------------------

def _attach_decorator_edges(primitives: list[dict],
                              *, trees_by_path: dict[str, ast.Module],
                              imports_by_path: dict[str, dict[str, str]]) -> None:
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
                "target": p["id"], "kind": "decorates",
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
                         *, trees_by_path: dict[str, ast.Module]) -> None:
    """For each test function, emit `tests` edges to call targets that appear
    inside an ast.Assert node. Calls outside assert expressions (e.g. helper
    setup calls) do NOT produce edges."""
    # Build imports index per file so we can resolve called names to ids
    imports_by_path_local = _build_imports_by_path(primitives)

    # Also build module-local symbol index per file
    local_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p.get("owner") is None and p["primitive"] in {"class", "function", "variable"}:
            local_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    for path, tree in trees_by_path.items():
        if not _is_test_path_py(path):
            continue
        local_names = local_by_path.get(path, {})
        imports = imports_by_path_local.get(path, {})

        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _is_test_function_py(fn_node):
                continue
            fn_prim = next(
                (p for p in primitives
                 if p["primitive"] == "function"
                    and p["source"]["path"] == path
                    and p["source"]["line"] == fn_node.lineno),
                None,
            )
            if fn_prim is None:
                continue

            # Build child->parent map once for the whole function body
            parents: dict[int, ast.AST] = {}
            for sub in ast.walk(fn_node):
                for child in ast.iter_child_nodes(sub):
                    parents[id(child)] = sub

            for sub in ast.walk(fn_node):
                if not isinstance(sub, ast.Call):
                    continue
                if not _is_assertion_scoped_py(sub, parents):
                    continue
                callee_name = _callee_name_py(sub.func)
                if callee_name in _PY_TEST_FRAMEWORK_PRIMITIVES:
                    continue
                if callee_name is None:
                    continue
                target_id = local_names.get(callee_name) or imports.get(callee_name)
                if target_id and not target_id.startswith("external::"):
                    fn_prim["edges_out"].append({
                        "target": target_id, "kind": "tests",
                        "via": "asserted_call",
                        "where": f"{path}:{sub.lineno}",
                        "confidence": "exact",
                    })


def _is_test_path_py(path: str) -> bool:
    """True if path matches test_*.py or *_test.py naming convention."""
    last = path.rsplit("/", 1)[-1]
    return last.startswith("test_") or last.endswith("_test.py")


def _is_test_function_py(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if function name starts with test_ or has pytest decorator."""
    if fn_node.name.startswith("test_"):
        return True
    for d in fn_node.decorator_list:
        name = _decorator_name(d)
        if name.startswith("pytest."):
            return True
    return False


def _is_assertion_scoped_py(node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    """Walk up from node; return True if any ancestor is ast.Assert."""
    cur = parents.get(id(node))
    while cur is not None:
        if isinstance(cur, ast.Assert):
            return True
        cur = parents.get(id(cur))
    return False


def _callee_name_py(func: ast.expr) -> str | None:
    """Extract the bare function name from a call's func node, if resolvable."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        # e.g. obj.method — return just the method name for local lookup
        return func.attr
    return None


# ---------------------------------------------------------------------------
# L2 edge resolution — Task 3.8: SQLAlchemy ORM relationships + FK refs (#54)
# ---------------------------------------------------------------------------

def _attach_orm_edges(primitives: list[dict],
                      *, trees_by_path: dict[str, ast.Module],
                      imports_by_path: dict[str, dict[str, str]]) -> None:
    """For every class that transitively extends a SQLAlchemy ORM base,
    walk the class body and emit:

      * `references_orm` edges (via=relationship_call) for every
        `relationship(Target, ...)` or `relationship("Target", ...)` call
        — the target is the related ORM class.
      * `references_table` edges (via=foreign_key) for every
        `ForeignKey("table.col")` argument — the target is the class
        whose `__tablename__` matches the named table.

    Resolution policy:
      * Direct `relationship(Cls, ...)` — resolve via the file's
        top-level symbol table and imports map (the same indexes the
        inheritance / call passes use).
      * String `relationship("Cls", ...)` — look up against the
        corpus-wide `classname_to_id` index. On name collisions, prefer
        a class in the same package directory; otherwise pick the first
        deterministic match.
      * `ForeignKey("table.col")` — look up against
        `tablename_to_class_id` built once at pass start.

    Targets that don't resolve are skipped silently (not even an
    `external::unresolved::...` placeholder). Rationale: the ORM pass
    is an enrichment — missing edges fall back to the existing
    `extends` / `imports` story, and emitting a noisy placeholder for
    every ambiguous string would dilute the signal the pass is supposed
    to add.
    """
    # --- corpus-wide indexes -------------------------------------------------
    classes_by_id: dict[str, dict] = {p["id"]: p for p in primitives
                                       if p["primitive"] == "class"}
    extends_targets_by_id: dict[str, list[str]] = {
        p["id"]: [e["target"] for e in p.get("edges_out", [])
                  if e.get("kind") == "extends"]
        for p in primitives if p["primitive"] == "class"
    }
    # Top-level classes per file — used both for direct-name resolution
    # within a file and to build the global classname_to_id index. Nested
    # classes are intentionally excluded: SQLAlchemy models are always
    # module-level in practice, and including nested classes would
    # introduce false-positive collisions with project enum/helper names.
    top_classes_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] == "class" and p.get("owner") is None:
            top_classes_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    # classname_to_id: collisions are kept as a list so the resolver can
    # prefer same-package matches. Single-match names collapse to the
    # one id.
    classname_to_ids: dict[str, list[str]] = {}
    for path, names in top_classes_by_path.items():
        for name, cid in names.items():
            classname_to_ids.setdefault(name, []).append(cid)

    # tablename_to_class_id: read `__tablename__ = "..."` from each
    # class's member variables. `_variable_primitives` already stores
    # the RHS expression text on `signature.value_text`; we parse that
    # string literal back out. Non-literal RHS (computed names) is
    # skipped — the heuristic is "string literal or nothing".
    tablename_to_class_id: dict[str, str] = {}
    for p in primitives:
        if p["primitive"] != "variable":
            continue
        if not p["name"].endswith(".__tablename__"):
            continue
        owner = p.get("owner")
        if owner is None or owner not in classes_by_id:
            continue
        value_text = (p.get("signature") or {}).get("value_text")
        if not value_text:
            continue
        try:
            literal = ast.literal_eval(value_text)
        except (ValueError, SyntaxError):
            continue
        if isinstance(literal, str):
            # First definition wins — collisions are rare (two classes
            # sharing `__tablename__` is a SQLAlchemy mapping error) and
            # we don't want to emit ambiguous edges silently.
            tablename_to_class_id.setdefault(literal, owner)

    # Class ids that declare `__tablename__` as a string literal. The
    # ORM detector (#84) treats this body-level signal as a second
    # branch beyond inheritance, so frameworks that wire declarative
    # behavior through a custom metaclass (SQLModel etc.) still get
    # walked even when the inheritance chain never reaches a known
    # SQLAlchemy base name.
    tablename_class_ids: set[str] = set(tablename_to_class_id.values())

    # --- iterate ORM model classes ------------------------------------------
    # Lazy import to avoid circulars at module load (coverage_caveats has
    # no upward deps but the convention in this file is local-import for
    # cross-module helpers used in a single pass).
    from depgraph.lib.coverage_caveats import is_sqlalchemy_model

    for path, tree in trees_by_path.items():
        file_top_classes = top_classes_by_path.get(path, {})
        if not file_top_classes:
            continue
        file_imports = imports_by_path.get(path, {})

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            class_id = file_top_classes.get(node.name)
            if class_id is None:
                continue
            cls_prim = classes_by_id.get(class_id)
            if cls_prim is None:
                continue
            if not is_sqlalchemy_model(cls_prim, extends_targets_by_id,
                                        tablename_class_ids=tablename_class_ids):
                continue

            # First pass — class-body `AnnAssign` nodes where the
            # value is a `Relationship(...)` / `relationship(...)` call
            # WITHOUT a positional class argument. SQLModel (issue #84)
            # uses the shape `team: Team | None = Relationship(back_populates=...)`,
            # encoding the related class only in the annotation. The
            # canonical `_resolve_orm_relationship` resolver expects a
            # positional arg, so for these annotation-only calls we
            # mine the target from the annotation expression instead.
            for stmt in node.body:
                if not isinstance(stmt, ast.AnnAssign):
                    continue
                if not (isinstance(stmt.value, ast.Call)
                        and _orm_callee_last_name(stmt.value.func)
                            in ("relationship", "Relationship")):
                    continue
                if stmt.value.args:
                    # Positional arg present — handled by the generic
                    # walk below; skip to avoid emitting duplicate edges.
                    continue
                edge = _resolve_orm_relationship_from_annotation(
                    stmt.annotation, stmt.value,
                    path=path, source_class_id=class_id,
                    file_top_classes=file_top_classes,
                    file_imports=file_imports,
                    classname_to_ids=classname_to_ids,
                    classes_by_id=classes_by_id,
                )
                if edge is not None:
                    cls_prim["edges_out"].append(edge)

            # Walk every Call descendant of the class body. Class-level
            # variable assignments and `mapped_column(..., ForeignKey(...))`
            # nestings both surface here. Both `relationship` (SQLAlchemy
            # core) and `Relationship` (SQLModel re-exports it under the
            # capital-R name, issue #84) name the same edge shape.
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Call):
                    continue
                callee = _orm_callee_last_name(sub.func)
                if callee in ("relationship", "Relationship"):
                    edge = _resolve_orm_relationship(
                        sub, path=path, source_class_id=class_id,
                        file_top_classes=file_top_classes,
                        file_imports=file_imports,
                        classname_to_ids=classname_to_ids,
                        classes_by_id=classes_by_id,
                    )
                    if edge is not None:
                        cls_prim["edges_out"].append(edge)
                elif callee == "ForeignKey":
                    edge = _resolve_orm_foreign_key(
                        sub, path=path,
                        tablename_to_class_id=tablename_to_class_id,
                    )
                    if edge is not None:
                        cls_prim["edges_out"].append(edge)


def _orm_callee_last_name(func: ast.expr) -> str | None:
    """Return the rightmost name of a Call's callee — covers
    `relationship`, `orm.relationship`, `sqlalchemy.orm.relationship`,
    and the same dotted-attribute shapes for `ForeignKey`. Returns None
    for shapes that don't bottom out in a name (e.g. `f()()`)."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _resolve_orm_relationship(call: ast.Call, *, path: str,
                               source_class_id: str,
                               file_top_classes: dict[str, str],
                               file_imports: dict[str, str],
                               classname_to_ids: dict[str, list[str]],
                               classes_by_id: dict[str, dict]) -> dict | None:
    """Resolve a `relationship(...)` call's first positional arg to a
    target class id and return the edge dict — or None if nothing
    class-shaped resolves."""
    if not call.args:
        return None
    first = call.args[0]
    target_id: str | None = None

    if isinstance(first, ast.Name):
        # `relationship(Boat, ...)` — Name in-scope.
        candidate = file_top_classes.get(first.id) or file_imports.get(first.id)
        if candidate and candidate in classes_by_id:
            target_id = candidate
    elif isinstance(first, ast.Constant) and isinstance(first.value, str):
        # `relationship("Boat", ...)` — corpus-wide classname lookup.
        target_id = _resolve_classname_string(
            first.value,
            source_path=path,
            classname_to_ids=classname_to_ids,
        )

    if target_id is None or target_id == source_class_id:
        return None
    return {
        "target": target_id, "kind": "references_orm",
        "via": "relationship_call",
        "where": f"{path}:{call.lineno}", "confidence": "exact",
    }


def _resolve_orm_relationship_from_annotation(
    annotation: ast.expr,
    call: ast.Call,
    *,
    path: str,
    source_class_id: str,
    file_top_classes: dict[str, str],
    file_imports: dict[str, str],
    classname_to_ids: dict[str, list[str]],
    classes_by_id: dict[str, dict],
) -> dict | None:
    """Resolve an annotation-encoded relationship target (#84).

    SQLModel encodes the related class in the annotation rather than
    in the call: `heroes: list["Hero"] = Relationship(back_populates=...)`.
    The annotation can wrap the class name in `list[...]`, `Optional[...]`,
    `T | None`, `Mapped[...]`, etc. We walk the annotation tree and
    collect every name candidate, then resolve the first one that
    matches an in-corpus class (via the file's top-level symbol table,
    its imports map, or the corpus-wide classname index).

    Returns a single edge dict for the first resolved candidate, or
    None if nothing resolves — keeps the policy consistent with
    `_resolve_orm_relationship` (one edge per call, no placeholders)."""
    for candidate in _annotation_class_candidates(annotation):
        target_id: str | None = None
        if candidate.startswith('"') or candidate.startswith("'"):
            # Forward-ref string literal: `"Hero"` after stripping quotes.
            stripped = candidate.strip("\"'")
            target_id = _resolve_classname_string(
                stripped,
                source_path=path,
                classname_to_ids=classname_to_ids,
            )
        else:
            in_file = file_top_classes.get(candidate)
            imported = file_imports.get(candidate)
            if in_file and in_file in classes_by_id:
                target_id = in_file
            elif imported and imported in classes_by_id:
                target_id = imported
            else:
                target_id = _resolve_classname_string(
                    candidate,
                    source_path=path,
                    classname_to_ids=classname_to_ids,
                )
        if target_id is None or target_id == source_class_id:
            continue
        return {
            "target": target_id, "kind": "references_orm",
            "via": "relationship_call",
            "where": f"{path}:{call.lineno}", "confidence": "exact",
        }
    return None


# Typing-helper / container names that the annotation walker must NOT
# treat as candidate ORM classes. The list covers stdlib `typing`
# helpers, builtin collection generics, SQLAlchemy 2.x `Mapped[...]`
# wrappers, and `None` / `NoneType` (which surface inside `T | None`).
_ANNOTATION_SKIP_NAMES = frozenset({
    "list", "List", "tuple", "Tuple", "set", "Set", "dict", "Dict",
    "frozenset", "FrozenSet", "type", "Type",
    "Optional", "Union", "Annotated", "ClassVar", "Final", "Literal",
    "Mapped", "MappedColumn",
    "None", "NoneType",
})


def _annotation_class_candidates(node: ast.expr) -> list[str]:
    """Yield class-name candidates extracted from a type annotation.

    Walks into Subscripts (`list[Hero]`, `Mapped[Hero]`, `Optional[Hero]`),
    BinOps (`Hero | None`), and Tuples (`Union[Hero, Team]`), and
    surfaces:
      * `ast.Name.id` (e.g. `Hero`)
      * `ast.Constant` string values (e.g. `"Hero"`) — forward refs;
        the caller distinguishes them by the surrounding quote chars.

    Skips names in `_ANNOTATION_SKIP_NAMES` so we don't pick up
    `list`, `Optional`, `Mapped`, etc. as candidate classes. Returns
    candidates in lexical (left-to-right) order — the caller stops at
    the first one that resolves to an in-corpus class id."""
    out: list[str] = []

    def visit(n: ast.expr) -> None:
        if isinstance(n, ast.Name):
            if n.id not in _ANNOTATION_SKIP_NAMES:
                out.append(n.id)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            # Quote the literal so the caller can detect forward refs.
            out.append(f'"{n.value}"')
        elif isinstance(n, ast.Subscript):
            visit(n.value)
            visit(n.slice)
        elif isinstance(n, ast.BinOp):
            # `X | Y` — both sides may carry candidate names.
            visit(n.left)
            visit(n.right)
        elif isinstance(n, ast.Tuple):
            for elt in n.elts:
                visit(elt)
        elif isinstance(n, ast.Attribute):
            # `module.Class` — use the rightmost attribute name.
            if n.attr not in _ANNOTATION_SKIP_NAMES:
                out.append(n.attr)

    visit(node)
    return out


def _resolve_orm_foreign_key(call: ast.Call, *, path: str,
                              tablename_to_class_id: dict[str, str]) -> dict | None:
    """Resolve a `ForeignKey("table.col")` call's first arg to the
    class id that owns `__tablename__ == "table"`. Returns None for
    non-literal args, malformed strings, or unknown tables."""
    if not call.args:
        return None
    first = call.args[0]
    if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
        return None
    parts = first.value.split(".", 1)
    if len(parts) < 1 or not parts[0]:
        return None
    table_name = parts[0]
    target_id = tablename_to_class_id.get(table_name)
    if target_id is None:
        return None
    return {
        "target": target_id, "kind": "references_table",
        "via": "foreign_key",
        "where": f"{path}:{call.lineno}", "confidence": "exact",
    }


def _resolve_classname_string(name: str, *, source_path: str,
                                classname_to_ids: dict[str, list[str]]) -> str | None:
    """Resolve a string class name (`relationship("Boat", ...)`) to a
    class id. On collisions prefer a class in the same package
    directory as the source; fall back to the first id in the list
    (deterministic — `classname_to_ids` is populated in primitive-
    emission order, which is path-sorted)."""
    ids = classname_to_ids.get(name) or []
    if not ids:
        return None
    if len(ids) == 1:
        return ids[0]
    # Collision: prefer same-package directory.
    src_dir = source_path.rsplit("/", 1)[0] if "/" in source_path else ""
    for cid in ids:
        # id shape: repo::path::Symbol — extract path segment.
        parts = cid.split("::")
        if len(parts) < 3:
            continue
        cand_path = parts[1]
        cand_dir = cand_path.rsplit("/", 1)[0] if "/" in cand_path else ""
        if cand_dir == src_dir:
            return cid
    return ids[0]
