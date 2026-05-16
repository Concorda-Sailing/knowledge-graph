"""logigraph flag / unflag subcommand handlers.

flag   <id> [--reason TEXT] [--actor TEXT]  Set flagged=true on a node; commits.
unflag <id> [--actor TEXT]                  Clear the flag; commits.
"""
from __future__ import annotations

import argparse
import json
import sys

from .context import Context
from ._shared import (
    resolve_node_path,
    git_commit_if_changed,
    default_actor,
)


def cmd_flag(args: argparse.Namespace, ctx: Context) -> int:
    """Set flagged=true on a logigraph node. Writes flagged_by + flagged_at
    (and flagged_reason if --reason given) to the node JSON and commits.
    Idempotent: if already flagged with same actor+reason, exit 0 without
    committing."""
    import datetime as _dt
    node_path = resolve_node_path(ctx, args.id)
    if node_path is None or not node_path.exists():
        print(f"no logigraph node with id: {args.id}", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())
    actor = args.actor or default_actor()
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
    git_commit_if_changed(ctx, [node_path], msg)
    print(f"flagged {args.id} by {actor}")
    return 0


def cmd_unflag(args: argparse.Namespace, ctx: Context) -> int:
    """Clear flagged + flagged_by + flagged_at + flagged_reason and commit.
    Idempotent: if not flagged, exit 0 without committing."""
    node_path = resolve_node_path(ctx, args.id)
    if node_path is None or not node_path.exists():
        print(f"no logigraph node with id: {args.id}", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())
    if not node.get("flagged"):
        print(f"{args.id} is not flagged — no change")
        return 0
    for key in ("flagged", "flagged_by", "flagged_at", "flagged_reason"):
        node.pop(key, None)
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    actor = args.actor or default_actor()
    git_commit_if_changed(ctx, [node_path], f"unflag: {args.id}")
    print(f"unflagged {args.id} by {actor}")
    return 0


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_flag = sub.add_parser("flag", help="Set flagged=true on a node")
    p_flag.add_argument("id", help="Logigraph node id (rule::*, resource::*, role::*, attribute::*, relationship::*, process::*)")
    p_flag.add_argument("--reason", default=None, help="One-line reason (recorded in commit message and JSON)")
    p_flag.add_argument("--actor", default=None, help="Actor name (default: git config user.name)")
    p_flag.set_defaults(func=cmd_flag)

    p_unflag = sub.add_parser("unflag", help="Clear flagged from a node")
    p_unflag.add_argument("id", help="Logigraph node id")
    p_unflag.add_argument("--actor", default=None, help="Actor name (default: git config user.name)")
    p_unflag.set_defaults(func=cmd_unflag)
