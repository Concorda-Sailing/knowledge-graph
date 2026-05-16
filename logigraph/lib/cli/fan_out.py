"""logigraph fan-out subcommand — rank rules by claim count (refactor signal)."""
from __future__ import annotations

import argparse

from .context import Context
from ._shared import load_all_nodes


def cmd_fan_out(args: argparse.Namespace, ctx: Context) -> int:
    nodes = load_all_nodes(ctx)
    rules = [(nid, data) for nid, (_, data) in nodes.items() if data.get("kind") == "rule"]
    rules.sort(key=lambda x: -(x[1].get("fan_out") or len(x[1].get("claims_code") or [])))
    threshold = args.threshold
    print(f"{'fan-out':<8} rule")
    print(f"{'-'*8} {'-'*60}")
    for nid, data in rules:
        fan_out = data.get("fan_out") or len(data.get("claims_code") or [])
        if fan_out < threshold:
            continue
        print(f"{fan_out:<8} {nid}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("fan-out")
    p.add_argument("--threshold", type=int, default=1)
    p.set_defaults(func=cmd_fan_out)
