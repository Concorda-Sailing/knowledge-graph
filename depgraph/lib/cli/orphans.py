"""depgraph orphans subcommand handler.

Walks nodes/ to find nodes whose source path no longer exists on disk.
Optionally archives them with --purge.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from depgraph.lib.config import basename_path_map  # noqa: E402

from .context import Context


def _archive_path(archive_dir: Path, source_name: str, when: str) -> Path:
    """Pick a unique destination under `archive_dir` for `source_name`.

    First-time archival lands at <archive>/<name>. Repeat archival (same
    node re-extracted then archived again) stamps the prior archival's
    timestamp into the filename so postmortems retain both."""
    target = archive_dir / source_name
    if not target.exists():
        return target
    stem = Path(source_name).stem
    suffix = Path(source_name).suffix or ".json"
    stamp = when.replace(":", "").replace("-", "").replace(".", "")
    return archive_dir / f"{stem}.archived-{stamp}{suffix}"


def archive_node_file(path: Path, archive_dir: Path, reason: str) -> Path:
    """Move `path` to `archive_dir`, stamping `_archived_at` and `_archive_reason`
    into the JSON body so the archived file is self-describing. Returns the
    destination path. Collision-safe across reruns."""
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    data["_archived_at"] = now
    data["_archive_reason"] = reason
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = _archive_path(archive_dir, path.name, now)
    target.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")
    path.unlink()
    return target


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
        for path, _ in orphans:
            target = archive_node_file(path, archive, reason="source_path_missing")
            print(f"  archived → {target.relative_to(ctx.DEPGRAPH)}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("orphans")
    p.add_argument("--purge", action="store_true")
    p.set_defaults(func=cmd_orphans)
