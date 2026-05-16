"""logigraph rules-for subcommand — list rules that claim a depgraph node."""
from __future__ import annotations

import argparse
import json
import sys

from .context import Context
from ._shared import load_all_nodes


def cmd_rules_for(args: argparse.Namespace, ctx: Context) -> int:
    by_code_index = ctx.NODES / "_index" / "by_code.json"
    if not by_code_index.exists():
        print("by_code index not built — run `bin/logigraph regen`", file=sys.stderr)
        return 1
    idx = json.loads(by_code_index.read_text())
    rule_ids = idx.get("by_target", {}).get(args.depgraph_id, [])
    if not rule_ids:
        print(f"no rules claim {args.depgraph_id}")
        return 0
    nodes = load_all_nodes(ctx)
    for rid in rule_ids:
        node = nodes.get(rid, (None, {}))[1]
        title = node.get("title", rid)
        statement = node.get("statement", "")
        print(f"- {rid}")
        print(f"  {title}")
        if statement:
            print(f"  → {statement}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("rules-for")
    p.add_argument("depgraph_id")
    p.set_defaults(func=cmd_rules_for)
