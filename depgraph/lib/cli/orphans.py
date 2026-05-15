"""depgraph orphans subcommand handler.

Walks nodes/ to find nodes whose source path no longer exists on disk.
Optionally archives them with --purge.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from config import basename_path_map  # noqa: E402

from .context import Context


def cmd_orphans(args: argparse.Namespace, ctx: Context) -> int:
    orphans = []
    basename_to_path = basename_path_map(ctx.DEPGRAPH)
    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        src = data.get("source") or {}
        repo, rel = src.get("repo"), src.get("path")
        # No source path at all → not an orphan, just an abstract node (rare).
        if not repo or not rel:
            continue
        repo_path = basename_to_path.get(repo)
        if repo_path is None:
            continue  # Unknown repo — don't claim it's orphan.
        if not (repo_path / rel).exists():
            orphans.append((node_file, data["id"]))
    if not orphans:
        print("no orphans")
        return 0
    for path, nid in orphans:
        print(f"orphan: {nid}  ({path.relative_to(ctx.DEPGRAPH)})")
    if args.purge:
        archive = ctx.NODES / "_archive"
        archive.mkdir(exist_ok=True)
        for path, _ in orphans:
            target = archive / path.name
            path.rename(target)
            print(f"  archived → {target.relative_to(ctx.DEPGRAPH)}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("orphans")
    p.add_argument("--purge", action="store_true")
    p.set_defaults(func=cmd_orphans)
