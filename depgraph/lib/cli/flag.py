"""depgraph flag / unflag subcommand handlers.

flag  <id> [--reason TEXT] [--actor TEXT]   Set flagged=true on a node; commits.
unflag <id> [--actor TEXT]                  Clear the flag; commits.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from .context import Context
from ._shared import find_nodes_for_target, _depgraph_commit_if_changed


def _default_actor() -> str:
    r = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    return os.environ.get("USER", "unknown")


def cmd_flag(args: argparse.Namespace, ctx: Context) -> int:
    """Set flagged=true on a depgraph node and commit."""
    import datetime as _dt

    matches = find_nodes_for_target(ctx, args.id)
    if not matches:
        print(f"no depgraph node with id: {args.id}", file=sys.stderr)
        return 1
    if len(matches) > 1:
        print(f"ambiguous id (matched {len(matches)} nodes): {args.id}", file=sys.stderr)
        return 1
    node_path = matches[0]
    node = json.loads(node_path.read_text())
    actor = args.actor or _default_actor()
    today = _dt.date.today().isoformat()
    if (node.get("flagged") and node.get("flagged_by") == actor
            and node.get("flagged_reason") == args.reason):
        print(f"already flagged by {actor} with same reason — no change")
        return 0
    node["flagged"] = True
    node["flagged_by"] = actor
    node["flagged_at"] = today
    if args.reason:
        node["flagged_reason"] = args.reason
    else:
        node.pop("flagged_reason", None)
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    msg = f"flag: {args.id}"
    if args.reason:
        msg += f"\n\n{args.reason}"
    _depgraph_commit_if_changed(ctx, [node_path], msg)
    print(f"flagged {args.id} by {actor}")
    return 0


def cmd_unflag(args: argparse.Namespace, ctx: Context) -> int:
    """Clear the flagged marker from a depgraph node and commit."""
    matches = find_nodes_for_target(ctx, args.id)
    if not matches:
        print(f"no depgraph node with id: {args.id}", file=sys.stderr)
        return 1
    if len(matches) > 1:
        print(f"ambiguous id: {args.id}", file=sys.stderr)
        return 1
    node_path = matches[0]
    node = json.loads(node_path.read_text())
    if not node.get("flagged"):
        print(f"{args.id} is not flagged — no change")
        return 0
    for key in ("flagged", "flagged_by", "flagged_at", "flagged_reason"):
        node.pop(key, None)
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    _depgraph_commit_if_changed(ctx, [node_path], f"unflag: {args.id}")
    print(f"unflagged {args.id}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p_flag = sub.add_parser("flag", help="Set flagged=true on a node")
    p_flag.add_argument("id", help="Depgraph node id (contains :: separators)")
    p_flag.add_argument("--reason", default=None)
    p_flag.add_argument("--actor", default=None)
    p_flag.set_defaults(func=cmd_flag)

    p_unflag = sub.add_parser("unflag", help="Clear flagged")
    p_unflag.add_argument("id")
    p_unflag.add_argument("--actor", default=None)
    p_unflag.set_defaults(func=cmd_unflag)
