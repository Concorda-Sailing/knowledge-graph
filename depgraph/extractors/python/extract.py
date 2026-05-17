"""Python primitive extractor — schema v2 layered substrate.

Walks every .py under repo_path, emits module / package / class / function /
variable primitives. No kind decisions; classification is a later step.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, Sequence

from depgraph.lib.path_filters import included

from .canonical import canonical_id, structural_hash


EXTRACTOR_TAG = "depgraph/extractors/python/extract.py@2026-05-16"
SCHEMA_VERSION = 2


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
    _attach_inheritance_edges(primitives, trees_by_path=trees_by_path)
    _attach_imports_edges(primitives, trees_by_path=trees_by_path, repo_key=repo_key,
                          repo_path=repo_path)
    _attach_call_edges(primitives, trees_by_path=trees_by_path)
    _attach_var_access_edges(primitives, trees_by_path=trees_by_path)

    imports_by_path = _build_imports_by_path(primitives)
    _attach_decorator_edges(primitives, trees_by_path=trees_by_path,
                             imports_by_path=imports_by_path)
    _attach_tests_edges(primitives, trees_by_path=trees_by_path)

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
                               *, trees_by_path: dict[str, ast.Module]) -> None:
    """Walk each class's bases AST, resolve base names to local class ids,
    append `extends` edges in-place."""
    # top-level class name -> id, per file
    by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] == "class" and p["owner"] is None:
            by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    classes_by_id = {p["id"]: p for p in primitives if p["primitive"] == "class"}

    for path, tree in trees_by_path.items():
        local_names = by_path.get(path, {})
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            class_id = local_names.get(node.name)
            if not class_id:
                continue
            target_class = classes_by_id[class_id]
            for base in node.bases:
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
                else:
                    target_class["edges_out"].append({
                        "target": f"external::pypi::unknown::{base_name}",
                        "kind": "extends",
                        "via": "class_decl",
                        "where": f"{path}:{node.lineno}",
                        "confidence": "unresolved",
                    })


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
                            confidence = "unresolved"
                        mod_prim["edges_out"].append({
                            "target": target,
                            "kind": "imports",
                            "via": "import_from",
                            "where": f"{path}:{node.lineno}",
                            "confidence": confidence,
                            "local_binding": local_binding,
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
                                mod_prim["edges_out"].append({
                                    "target": f"external::pypi::{root_pkg}",
                                    "kind": "imports", "via": "wildcard_import",
                                    "where": f"{path}:{node.lineno}",
                                    "confidence": "unresolved",
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
                            confidence = "unresolved"
                        mod_prim["edges_out"].append({
                            "target": target,
                            "kind": "imports",
                            "via": "import_from",
                            "where": f"{path}:{node.lineno}",
                            "confidence": confidence,
                            "local_binding": local_binding,
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
                        confidence = "unresolved"
                    mod_prim["edges_out"].append({
                        "target": target,
                        "kind": "imports",
                        "via": "import",
                        "where": f"{path}:{node.lineno}",
                        "confidence": confidence,
                        "local_binding": local_binding,
                    })


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

            # Seed type binding from parameter annotations
            var_types: dict[str, str] = {}  # local_name -> class_id
            for arg in fn_node.args.args + fn_node.args.kwonlyargs:
                if arg.annotation is None:
                    continue
                ann_text = ast.unparse(arg.annotation).split("[")[0].strip()
                target_id = local_names.get(ann_text) or imports.get(ann_text)
                if target_id and target_id in classes_by_id:
                    var_types[arg.arg] = target_id

            # Walk body in source order; update var_types on assignments,
            # emit edges for each Call node
            for sub in ast.walk(fn_node):
                # Pattern 1: x: SomeClass = ...
                if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                    ann_text = ast.unparse(sub.annotation).split("[")[0].strip()
                    cid = local_names.get(ann_text) or imports.get(ann_text)
                    if cid and cid in classes_by_id:
                        var_types[sub.target.id] = cid

                # Pattern 2: x = SomeClass(...)
                if (isinstance(sub, ast.Assign)
                        and len(sub.targets) == 1
                        and isinstance(sub.targets[0], ast.Name)
                        and isinstance(sub.value, ast.Call)
                        and isinstance(sub.value.func, ast.Name)):
                    cname = sub.value.func.id
                    cid = local_names.get(cname) or imports.get(cname)
                    if cid and cid in classes_by_id:
                        var_types[sub.targets[0].id] = cid

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
                        path=path,
                    )
                    fn_prim["edges_out"].extend(edges)


def _resolve_call_edge(call: ast.Call, *, local_names: dict, imports: dict,
                        classes_by_id: dict, functions_by_id: set,
                        methods_by_class: dict,
                        var_types: dict, path: str) -> list[dict]:
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
            recv_class_id = var_types.get(recv)
            if recv_class_id is None:
                return [{"target": f"external::unresolved::{recv}.{method}",
                          "kind": "calls", "via": "method_call",
                          "where": f"{path}:{call.lineno}",
                          "confidence": "unresolved"}]
            method_id = methods_by_class.get(recv_class_id, {}).get(method)
            if method_id:
                return [{"target": method_id, "kind": "calls",
                          "via": "method_call",
                          "where": f"{path}:{call.lineno}",
                          "confidence": "exact"}]
            return [{"target": f"external::unresolved::{recv_class_id}.{method}",
                      "kind": "calls", "via": "method_call",
                      "where": f"{path}:{call.lineno}",
                      "confidence": "unresolved"}]
        # Chained attribute (a.b.c()) — unresolved for v0
        return []

    # Computed callee (getattr, call[0](), etc.) — emit unresolved rather than
    # silently dropping, so the call site is preserved in the corpus.
    return [{"target": "external::unresolved::computed_callee",
              "kind": "calls", "via": "computed_callee",
              "where": f"{path}:{call.lineno}",
              "confidence": "unresolved"}]


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
    function, emit a `decorates` edge from that decorator function to the
    decorated primitive.

    External decorators (e.g. @functools.lru_cache, @pytest.fixture) do NOT
    produce edges — the edge taxonomy disallows external terminals as edge
    sources. Those are captured in `signature.decorators` only.
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
