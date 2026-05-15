"""Rust language extractor via tree-sitter."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
# Allow direct script invocation: insert depgraph/ on path so
# `from extractors.X import ...` resolves.
_DEPGRAPH_ROOT = _Path(__file__).resolve().parents[3]
if str(_DEPGRAPH_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_DEPGRAPH_ROOT))

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import tree_sitter_rust
from tree_sitter import Language, Parser, Tree, Node

from extractors.generic.rust.detector_api import (
    Detector, DetectorContext, Mutation, RelabelNode, AddEdge, AddNode,
)

RUST_LANG = Language(tree_sitter_rust.language())
DEFAULT_EXCLUDES = (".git", "target", "node_modules", "dist", "build")
FRAMEWORK_DETECTOR_DIR = Path(__file__).parent / "detectors"


def discover_files(root: Path, extra_excludes: list[str] | None = None) -> Iterable[Path]:
    excludes = set(DEFAULT_EXCLUDES) | set(extra_excludes or ())
    for path in sorted(root.rglob("*.rs")):
        if any(part in excludes for part in path.relative_to(root).parts):
            continue
        yield path


def parse_file(path: Path) -> tuple[Tree | None, str | None]:
    parser = Parser(RUST_LANG)
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

    walk(tree.root_node, None)
    return nodes


def _load_detector_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"rust_detector_{path.stem}", path)
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
