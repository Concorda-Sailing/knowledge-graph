"""depgraph validate subcommand handler.

Runs two passes over the node corpus:
  1. JSON-Schema (shape) — validates each node file against node.schema.json.
  2. Corpus coherence    — runs validate_corpus from depgraph.extractors.reconcile
     to surface primitive_errors, edge_errors, slug_collisions, orphan_edges.

Output is summarized; the first 20 failures of each class are shown by default.
Pass --verbose to print full details (e.g., jsonschema's expected-shape dump),
and --all to remove the per-class cap.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import Context


_DEFAULT_CAP = 20


def _iter_node_files(ctx: Context):
    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        yield node_file


def _print_section(title: str, items: list[str], *, cap: int, full: bool) -> None:
    if not items:
        return
    print(f"\n{title}: {len(items)}", file=sys.stderr)
    show = items if full else items[:cap]
    for line in show:
        print(f"  {line}", file=sys.stderr)
    if not full and len(items) > cap:
        print(f"  … +{len(items) - cap} more (pass --all to print every entry)",
              file=sys.stderr)


def cmd_validate(args: argparse.Namespace, ctx: Context) -> int:
    # Liveness gate (#72): empty corpus + no _meta.json means regen has
    # never run for this project. Returning 0 would let `validate &&
    # next-step` scripts proceed as if the corpus was clean. Refuse.
    if not ctx.CORPUS_META.exists():
        print("validate: no extraction has run yet — run `depgraph regen`",
              file=sys.stderr)
        return 1

    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:
        print("jsonschema not installed; install with: pip install jsonschema",
              file=sys.stderr)
        return 1

    schema = json.loads((ctx.tool_root / "schema" / "node.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)

    cap = _DEFAULT_CAP
    full = bool(getattr(args, "all", False))
    verbose = bool(getattr(args, "verbose", False))

    shape_failures: list[str] = []   # jsonschema invalid nodes
    parse_failures: list[str] = []   # JSON decode errors
    total_files = 0
    primitives: list[dict] = []

    for node_file in _iter_node_files(ctx):
        total_files += 1
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError) as e:
            parse_failures.append(f"{node_file}: {e}")
            continue
        primitives.append(data)
        try:
            validator.validate(data)
        except jsonschema.ValidationError as e:
            # By default, print the short path + message. With --verbose, include
            # jsonschema's full context (the v1 behavior — useful for schema
            # debugging, ruinous for the unwary).
            msg = e.message if not verbose else str(e)
            loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
            shape_failures.append(f"{node_file.relative_to(ctx.NODES)} at {loc}: {msg}")

    # Corpus coherence pass (v2 graph-level validation).
    try:
        from depgraph.extractors.reconcile import validate_corpus
    except ImportError as e:  # pragma: no cover — defensive
        print(f"WARN: validate_corpus unavailable ({e}); skipping coherence pass",
              file=sys.stderr)
        report: dict = {"primitive_errors": [], "edge_errors": [],
                        "slug_collisions": [], "orphan_edges": []}
    else:
        report = validate_corpus(primitives)

    prim_errors = [f"{e['id']}: {e['error']}" for e in report["primitive_errors"]]
    edge_errors = [f"{e['source']} → {e['target']}: {e['error']}"
                   for e in report["edge_errors"]]
    orphans = [f"{e['source']} → {e['target']} ({e['kind']})"
               for e in report["orphan_edges"]]
    slug_collisions = list(report.get("slug_collisions") or [])

    total_problems = (len(parse_failures) + len(shape_failures) + len(prim_errors)
                      + len(edge_errors) + len(orphans) + len(slug_collisions))

    # One-line summary always.
    print(f"validate: {total_files} nodes, {total_problems} problems "
          f"(shape={len(shape_failures)} parse={len(parse_failures)} "
          f"primitive={len(prim_errors)} edge={len(edge_errors)} "
          f"orphan={len(orphans)} slug={len(slug_collisions)})")

    _print_section("parse failures", parse_failures, cap=cap, full=full)
    _print_section("shape (jsonschema) failures", shape_failures, cap=cap, full=full)
    _print_section("primitive errors", prim_errors, cap=cap, full=full)
    _print_section("edge errors", edge_errors, cap=cap, full=full)
    _print_section("orphan edges", orphans, cap=cap, full=full)
    _print_section("slug collisions", slug_collisions, cap=cap, full=full)

    return 1 if total_problems else 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("validate")
    p.add_argument("--verbose", action="store_true",
                   help="Print jsonschema's full failure context (long output).")
    p.add_argument("--all", action="store_true",
                   help="Remove the per-class display cap (default 20).")
    p.set_defaults(func=cmd_validate)
