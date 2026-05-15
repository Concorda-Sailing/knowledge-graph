"""depgraph dependents subcommand handler.

Walks the reverse-edge index breadth-first up to --depth hops,
printing each reachable dependent node id with indentation.
"""
from __future__ import annotations

import argparse
import sys

from .context import Context
from ._shared import load_dependents_index


def cmd_dependents(args: argparse.Namespace, ctx: Context) -> int:
    dependents_index = load_dependents_index(ctx)
    if not dependents_index:
        print("dependents index not built — run `bin/depgraph regen`", file=sys.stderr)
        return 1

    # Validate that the requested id exists in the index (has at least an
    # entry as a target or as a source in some entry).  An id that appears
    # nowhere is almost certainly a typo.
    all_ids: set[str] = set(dependents_index.keys())
    for entries in dependents_index.values():
        for entry in entries:
            all_ids.add(entry["source"])

    if args.id not in all_ids:
        print(f"no nodes match: {args.id}", file=sys.stderr)
        return 1

    seen: set[str] = set()
    frontier = [(args.id, 0)]
    while frontier:
        nid, depth = frontier.pop(0)
        if nid in seen or depth > args.depth:
            continue
        seen.add(nid)
        prefix = "  " * depth + ("→ " if depth else "")
        print(f"{prefix}{nid}")
        for d in dependents_index.get(nid) or []:
            frontier.append((d["source"], depth + 1))
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dependents")
    p.add_argument("id")
    p.add_argument("--depth", type=int, default=2)
    p.set_defaults(func=cmd_dependents)
