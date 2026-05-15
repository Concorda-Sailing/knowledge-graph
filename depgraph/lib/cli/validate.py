"""depgraph validate subcommand handler.

JSON-Schema validates every node file under nodes/, with a --strict flag
(reserved for future use; currently has no effect beyond the base validation).
"""
from __future__ import annotations

import argparse
import json
import sys

from .context import Context


def cmd_validate(args: argparse.Namespace, ctx: Context) -> int:
    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:
        print("jsonschema not installed; install with: pip install jsonschema", file=sys.stderr)
        return 1
    # Schema travels with the tool framework; node data lives in DEPGRAPH.
    schema = json.loads((ctx.tool_root / "schema" / "node.schema.json").read_text())
    bad = 0
    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        try:
            data = json.loads(node_file.read_text())
            jsonschema.validate(data, schema)
        except (json.JSONDecodeError, jsonschema.ValidationError) as e:
            print(f"INVALID {node_file}: {e}", file=sys.stderr)
            bad += 1
    if bad:
        return 1
    print("all nodes valid")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("validate")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_validate)
