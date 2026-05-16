"""logigraph rollup subcommand — full code rollup for a domain entity.

Module name uses _cmd suffix to avoid shadowing lib/rollup.py (which lives
in depgraph's lib/ and is imported cross-graph).
"""
from __future__ import annotations

import argparse
import json
import sys

from .context import Context
from ._shared import load_all_nodes


def cmd_rollup(args: argparse.Namespace, ctx: Context) -> int:
    """Emit the full code rollup for a logigraph domain entity.

    Resolves the entity's anchor model in depgraph, then BFS over the
    reverse-dependents index to gather every code symbol that operates
    on the entity. Output respects --kind / --depth / --format flags.

    Cross-graph: depgraph.lib.rollup is importable because the framework
    root is on sys.path (added by bin/kg or bin/logigraph at startup).
    """
    from depgraph.lib.rollup import (  # noqa: PLC0415
        compute_rollup,
        format_rollup_text,
        format_rollup_json,
        load_rollup_inputs,
        resolve_anchor,
        Rollup,
    )

    inputs = load_rollup_inputs(ctx.depgraph_dir)

    nodes = load_all_nodes(ctx)
    if args.entity_id not in nodes:
        print(f"no logigraph node with id: {args.entity_id}", file=sys.stderr)
        return 1
    _, domain_node = nodes[args.entity_id]
    logigraph_index = {nid: data for nid, (_, data) in nodes.items()}

    anchor = resolve_anchor(domain_node, inputs.depgraph_index, logigraph_index=logigraph_index)
    rollup = compute_rollup(
        anchor_id=anchor.model_id or "",
        depgraph_index=inputs.depgraph_index,
        dependents_index=inputs.dependents_index,
        depth=args.depth,
        anchor_result=anchor,
    )

    # --kind filter (post-compute so via-chains stay coherent).
    if args.kind:
        wanted = set(args.kind.split(","))
        rollup = Rollup(
            anchor=rollup.anchor,
            by_kind={k: v for k, v in rollup.by_kind.items() if k in wanted},
            total=sum(len(v) for k, v in rollup.by_kind.items() if k in wanted),
        )

    if args.format == "json":
        print(json.dumps(format_rollup_json(rollup), indent=2))
    else:
        print(format_rollup_text(rollup, summary=False))
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("rollup", help="Emit code rollup for a domain entity")
    p.add_argument("entity_id", help="Logigraph domain node id (e.g. resource::concorda::boat_crew)")
    p.add_argument("--kind", default=None, help="Comma-separated kinds (model,service,endpoint,component,test,hook,schema)")
    p.add_argument("--depth", type=int, default=3, choices=[1, 2, 3], help="BFS depth (1=direct only)")
    p.add_argument("--direct-only", action="store_true", help="Equivalent to --depth 1")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_rollup)
