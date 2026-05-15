"""depgraph context subcommand handler.

Module is named context_cmd (not context) to avoid collision with the
Context dataclass module at lib/cli/context.py.
"""
from __future__ import annotations

import argparse
import json
import sys

from .context import Context
from ._shared import find_nodes_for_target, load_dependents_index


def cmd_context(args: argparse.Namespace, ctx: Context) -> int:
    matches = find_nodes_for_target(ctx, args.target)
    if not matches:
        print(f"no nodes match: {args.target}", file=sys.stderr)
        return 1
    dependents_index = load_dependents_index(ctx)
    for path in matches:
        data = json.loads(path.read_text())
        print(f"# {data.get('title', data['id'])}")
        print(f"id: {data['id']}  ·  kind: {data['kind']}  ·  hash: {data['structural_hash'][:12]}")
        print(f"source: {data['source']['repo']}/{data['source']['path']}:{data['source'].get('line')}")
        print()
        print("## Direct dependents")
        for d in dependents_index.get(data["id"]) or []:
            print(f"  - {d['source']} (via {d.get('via','?')}, {d.get('confidence', 'exact')}, {d.get('where', '?')})")
        if not dependents_index.get(data["id"]):
            print("  _none_")
        print()
        dossier_rel = data.get("dossier")
        if dossier_rel and (ctx.DEPGRAPH / dossier_rel).exists():
            print("## Dossier")
            print((ctx.DEPGRAPH / dossier_rel).read_text())
        else:
            print("## Dossier\n_missing_")
        print()
        warns = data.get("warnings") or []
        if warns:
            print("## Warnings")
            for w in warns:
                print(f"  - [{w['code']}] {w['message']}")
            print()
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("context")
    p.add_argument("target")
    p.set_defaults(func=cmd_context)
