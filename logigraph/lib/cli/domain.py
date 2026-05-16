"""logigraph domain-bump subcommand handler.

Subcommand: domain-bump
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import Context
from ._shared import (
    _domain_node_path,
    git_commit_if_changed,
    default_actor,
    rewrite_dossier_frontmatter,
)


# ---------------------------------------------------------------------------
# Domain-only path helpers
# ---------------------------------------------------------------------------

def _domain_dossier_path(ctx: Context, domain_id: str) -> Path:
    parts = domain_id.split("::")
    return ctx.LOGIGRAPH / "dossiers" / "domain" / f"{parts[0]}__{parts[1]}__{parts[2]}.md"


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def cmd_domain_bump(args: argparse.Namespace, ctx: Context) -> int:
    """Promote a domain node's definition_status (default: → human_reviewed).
    Updates both the JSON node and the dossier frontmatter."""
    domain_id = args.id
    try:
        node_path = _domain_node_path(ctx, domain_id)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    if not node_path.exists():
        print(f"no domain node: {node_path.relative_to(ctx.LOGIGRAPH)}", file=sys.stderr)
        return 1
    node = json.loads(node_path.read_text())
    new_status = args.status
    node["definition_status"] = new_status
    node_path.write_text(json.dumps(node, indent=2) + "\n")
    print(f"bumped {node_path.relative_to(ctx.LOGIGRAPH)} → definition_status: {new_status}")

    dossier_path = _domain_dossier_path(ctx, domain_id)
    actor = args.actor or default_actor()
    paths = [node_path]
    if dossier_path.exists():
        rewrite_dossier_frontmatter(dossier_path, node.get("structural_hash", ""), new_status, actor)
        print(f"updated {dossier_path.relative_to(ctx.LOGIGRAPH)} frontmatter")
        paths.append(dossier_path)

    prefix = "review" if new_status == "human_reviewed" else "chore(bump)"
    git_commit_if_changed(ctx, paths, f"{prefix}: {domain_id}")
    return 0


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_db = sub.add_parser("domain-bump", help="Promote a domain node's definition_status (default → human_reviewed)")
    p_db.add_argument("id")
    p_db.add_argument("--status", default="human_reviewed", choices=["stub", "llm_drafted", "human_reviewed"])
    p_db.add_argument("--actor", default=None, help="Reviewer (default: git config user.name)")
    p_db.set_defaults(func=cmd_domain_bump)
