"""Python language extractor.

Five-stage contract: discover -> parse -> emit primitives -> run
detectors -> write. This file lands in stages across tasks 3, 4, 5.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
# Allow direct script invocation: insert depgraph/ on path so
# `from extractors.X import ...` resolves.
_DEPGRAPH_ROOT = _Path(__file__).resolve().parents[3]
if str(_DEPGRAPH_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_DEPGRAPH_ROOT))

import ast
from pathlib import Path, PurePosixPath
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

        def visit_Name(self, node: ast.Name):
            # Only emit name_ref_edges inside a function body, not at
            # module scope (where imports and class/function defs live).
            origin = current_fn_id[0]
            if origin is None:
                return
            nodes.append({
                "id": f"{origin}#nameref:{node.id}:{node.lineno}",
                "kind": "name_ref_edge", "from_id": origin,
                "target": node.id, "line": node.lineno,
            })

    Visitor().visit(tree)
    return nodes


import argparse
import importlib.util
import json
import sys
from typing import Iterable

from extractors.generic.python.detector_api import (
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
    # Canonical kinds — plural dirs to match pre-flip layout.
    "endpoint": "endpoints", "model": "models",
    "schema": "schemas", "service": "services",
    "test": "tests",
}


_MAX_FILENAME = 200  # bytes; ext4/xfs allow 255; leave headroom for ".json"


def _safe_filename(node_id: str) -> str:
    # Canonical IDs (post-canonicalize) use `::` as separator. Route them
    # through slugify_id_py so the on-disk filename matches pre-flip.
    if "::" in node_id:
        stem = slugify_id_py(node_id)
    else:
        stem = node_id.replace("/", "__").replace(":", "__")
    if len(stem) > _MAX_FILENAME:
        import hashlib
        digest = hashlib.sha1(stem.encode()).hexdigest()[:12]
        stem = stem[:_MAX_FILENAME] + "__" + digest
    return stem + ".json"


def write_nodes(nodes: list[dict], data_dir: Path) -> None:
    for n in nodes:
        kind = n["kind"]
        sub = _KIND_DIR.get(kind, kind + "s")
        out_dir = data_dir / "nodes" / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / _safe_filename(n["id"])
        path.write_text(json.dumps(n, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# Canonicalize stage: convert primitives + detector metadata into the
# pre-flip-shape canonical node set. See § Canonical Node Contracts in
# docs/superpowers/plans/2026-05-15-framework-canonicalization.md.
# --------------------------------------------------------------------------- #

from extractors.generic.python.canonical import (
    slugify_id_py, structural_hash, canonical_path,
    canonical_id_for_endpoint, canonical_id_for_repo_symbol,
    build_symbol_index, resolve_endpoint_depends_on,
)


CANONICAL_KINDS = {"endpoint", "model", "schema", "service", "test"}
PRIMITIVE_KINDS_TO_DROP = {
    "module", "class", "function", "import_edge", "call_edge", "name_ref_edge",
}


_EXTRACTOR_STAMP = "extract_api.py"


def _canonicalize_endpoint(n, *, primitives, sym_idx, repo_key):
    method = n["method"]
    path = n["path"]
    auth = n.get("auth", "none")
    request_type_name = n.get("request_type_name")
    response_type_name = n.get("response_type_name")
    cid = canonical_id_for_endpoint(method, path)
    sig = {
        "method": method,
        "path": path,
        "auth": auth,
        "request_schema_ref": n.get("request_schema_ref"),
        "response_schema_ref": n.get("response_schema_ref"),
    }
    hpayload = {
        "method": method,
        "path": canonical_path(path),
        "auth": auth,
        "request": request_type_name,
        "response": response_type_name,
    }
    out = {
        "schema_version": 1,
        "id": cid,
        "kind": "endpoint",
        "title": f"{method} {path}",
        "feature": None,
        "source": {
            "repo": repo_key,
            "path": n["file"],
            "symbol": n["name"],
            "line": n["line"],
        },
        "signature": sig,
        "structural_hash": structural_hash(hpayload),
        "depends_on": resolve_endpoint_depends_on(
            host_id=n["id"], host_file=n["file"],
            primitives=primitives, symbol_index=sym_idx,
            repo_key=repo_key,
        ),
        "external_consumers": [],
        "tests": [],
        "dossier": f"dossiers/endpoints/{slugify_id_py(cid)}.md",
        "extractor": _EXTRACTOR_STAMP,
        "warnings": [],
    }
    if response_type_name is None and method != "DELETE":
        out["warnings"].append({
            "code": "weakly_typed_response",
            "message": (
                "Handler has no declared response_model; structural hash "
                "cannot detect response shape changes. See DRIFT.md "
                "scenario 3."
            ),
            "where": f"{n['file']}:{n['line']}",
        })
    return out


def _canonicalize_model(n, *, repo_key):
    cid = canonical_id_for_repo_symbol(repo_key, n["file"], n["name"])
    payload = {
        "name": n["name"],
        "kind": "model",
        "tablename": n.get("tablename"),
    }
    return {
        "schema_version": 1,
        "id": cid,
        "kind": "model",
        "title": n["name"],
        "feature": None,
        "source": {
            "repo": repo_key,
            "path": n["file"],
            "symbol": n["name"],
            "line": n["line"],
        },
        "signature": payload,
        "structural_hash": structural_hash(payload),
        "depends_on": [],
        "external_consumers": [],
        "tests": [],
        "dossier": f"dossiers/models/{slugify_id_py(cid)}.md",
        "extractor": _EXTRACTOR_STAMP,
        "warnings": [],
    }


def _canonicalize_schema(n, *, repo_key):
    cid = canonical_id_for_repo_symbol(repo_key, n["file"], n["name"])
    payload = {
        "name": n["name"],
        "kind": "schema",
        "fields": n.get("fields", []),
    }
    return {
        "schema_version": 1,
        "id": cid,
        "kind": "schema",
        "title": n["name"],
        "feature": None,
        "source": {
            "repo": repo_key,
            "path": n["file"],
            "symbol": n["name"],
            "line": n["line"],
        },
        "signature": payload,
        "structural_hash": structural_hash(payload),
        "depends_on": [],
        "external_consumers": [],
        "tests": [],
        "dossier": f"dossiers/schemas/{slugify_id_py(cid)}.md",
        "extractor": _EXTRACTOR_STAMP,
        "warnings": [],
    }


def _canonicalize_service(n, *, repo_key):
    cid = canonical_id_for_repo_symbol(repo_key, n["file"], n["name"])
    payload = {
        "name": n["name"],
        "kind": "service",
        "args": n.get("args", []),
    }
    return {
        "schema_version": 1,
        "id": cid,
        "kind": "service",
        "title": n["name"],
        "feature": None,
        "source": {
            "repo": repo_key,
            "path": n["file"],
            "symbol": n["name"],
            "line": n["line"],
        },
        "signature": payload,
        "structural_hash": structural_hash(payload),
        "depends_on": [],
        "external_consumers": [],
        "tests": [],
        "dossier": f"dossiers/services/{slugify_id_py(cid)}.md",
        "extractor": _EXTRACTOR_STAMP,
        "warnings": [],
    }


def _accept_model(n: dict) -> bool:
    """Pre-flip extract_model_nodes only scans <repo>/models/**, skipping
    __init__.py and base.py. Mirror that here so detector emissions from
    elsewhere don't leak through."""
    parts = PurePosixPath(n["file"]).parts
    if not parts or parts[0] != "models":
        return False
    fname = parts[-1]
    if fname in ("__init__.py", "base.py"):
        return False
    return True


def _accept_schema(n: dict) -> bool:
    parts = PurePosixPath(n["file"]).parts
    if not parts or parts[0] != "schemas":
        return False
    if parts[-1] == "__init__.py":
        return False
    return True


def _accept_service(n: dict) -> bool:
    parts = PurePosixPath(n["file"]).parts
    if not parts or parts[0] not in ("services", "utils"):
        return False
    if parts[-1] == "__init__.py":
        return False
    return True


def canonicalize(primitives: list[dict], *, repo_key: str) -> list[dict]:
    """Convert detector-relabeled primitives into pre-flip-shape nodes.

    Primitive kinds (module/class/function/import_edge/call_edge) are
    dropped — they're tool-internal, not part of the depgraph node set.
    """
    sym_idx = build_symbol_index(primitives, repo_key=repo_key)
    out: list[dict] = []
    for n in primitives:
        k = n["kind"]
        if k in PRIMITIVE_KINDS_TO_DROP or k not in CANONICAL_KINDS:
            continue
        if k == "endpoint":
            out.append(_canonicalize_endpoint(
                n, primitives=primitives, sym_idx=sym_idx, repo_key=repo_key,
            ))
        elif k == "model":
            if not _accept_model(n):
                continue
            out.append(_canonicalize_model(n, repo_key=repo_key))
        elif k == "schema":
            if not _accept_schema(n):
                continue
            out.append(_canonicalize_schema(n, repo_key=repo_key))
        elif k == "service":
            if not _accept_service(n):
                continue
            out.append(_canonicalize_service(n, repo_key=repo_key))
    return out


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
            repo_path=str(args.repo_path),
        )
        muts = _run_detectors(detectors, tree, prims, ctx)
        labeled += sum(1 for m in muts if isinstance(m, RelabelNode))
        nodes = apply_mutations(prims, muts)
        all_nodes.extend(nodes)
        total_nodes += len(nodes)

    canonical = canonicalize(all_nodes, repo_key=args.repo_key)
    write_nodes(canonical, args.data_dir)
    print(f"wrote {len(canonical)} canonical nodes "
          f"({labeled} labeled by detectors, {total_nodes} primitives), "
          f"skipped {skipped} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
