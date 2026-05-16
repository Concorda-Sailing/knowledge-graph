"""depgraph health subcommand handler.

Compact graph-health report. Bundles validate + orphans + stale-dossier
detection + tier-A coverage shortfall into one summary suitable for
SessionStart injection. Exits non-zero if anything is wrong.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .context import Context
from ._shared import load_dependents_index

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from depgraph.lib.config import basename_path_map  # noqa: E402


def _dossier_state(node: dict, depgraph: Path) -> str:
    """Return one of: 'current', 'unreviewed', 'stale', 'missing'.

    This is a local copy of the same logic in bin/depgraph._dossier_state
    translated to accept a ctx.DEPGRAPH path instead of reading the global.
    """
    rel = node.get("dossier")
    if not rel:
        return "missing"
    full = depgraph / rel
    if not full.exists():
        return "missing"
    text = full.read_text()
    pinned = None
    status = "current"
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("status:"):
            status = s.split(":", 1)[1].strip()
        if s.startswith("last_reviewed_against_hash:"):
            pinned = s.split(":", 1)[1].strip().strip('"').strip("'")
        if s == "---" and pinned is not None:
            break
    if pinned and pinned != node.get("structural_hash"):
        return "stale"
    if status == "unreviewed":
        return "unreviewed"
    return "current"


def cmd_health(args: argparse.Namespace, ctx: Context) -> int:
    """Compact graph-health report. Bundles validate + orphans + stale-dossier
    detection + tier-A coverage shortfall into one summary suitable for
    SessionStart injection. Exits non-zero if anything is wrong."""
    problems: list[str] = []
    summary: list[str] = []

    # ---- validate (schema) ----------------------------------------------
    try:
        import jsonschema  # type: ignore[import-untyped]
        schema = json.loads((ctx.tool_root / "schema" / "node.schema.json").read_text())
        invalid = 0
        for node_file in ctx.NODES.rglob("*.json"):
            if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
                continue
            try:
                data = json.loads(node_file.read_text())
                jsonschema.validate(data, schema)
            except (json.JSONDecodeError, jsonschema.ValidationError):
                invalid += 1
        if invalid:
            problems.append(f"{invalid} invalid node(s) — run `depgraph validate`")
    except ImportError:
        summary.append("validate: skipped (jsonschema not installed)")

    # ---- orphans (node points at missing source file) -------------------
    orphan_n = 0
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
        if not repo or not rel:
            continue
        repo_path = basename_to_path.get(repo)
        if repo_path is None:
            continue
        if not (repo_path / rel).exists():
            orphan_n += 1
    if orphan_n:
        problems.append(f"{orphan_n} orphan node(s) (source file gone) — run `depgraph orphans`")

    # ---- stale dossiers (hash drift) ------------------------------------
    stale_n = 0
    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if _dossier_state(data, ctx.DEPGRAPH) == "stale":
            stale_n += 1
    if stale_n:
        problems.append(f"{stale_n} stale dossier(s) (structural_hash drifted) — run `depgraph dossier-rank --only-stale`")

    # ---- tier-A coverage shortfall --------------------------------------
    a_total = 0
    a_covered = 0
    dependents = load_dependents_index(ctx)
    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = data.get("id")
        if not nid:
            continue
        kind = data.get("kind", "")
        if kind == "test":
            continue
        fan_out = len(dependents.get(nid) or [])
        if fan_out < 10:
            continue
        a_total += 1
        if _dossier_state(data, ctx.DEPGRAPH) == "current":
            a_covered += 1
    a_pct = int(round(100 * a_covered / a_total)) if a_total else 100
    if a_pct < 80 and a_total > 0:
        problems.append(f"Tier-A dossier coverage at {a_pct}% ({a_covered}/{a_total}) — run `depgraph dossier-rank --tier A`")
    else:
        summary.append(f"tier-A coverage: {a_pct}% ({a_covered}/{a_total})")

    # ---- output ---------------------------------------------------------
    print("# Depgraph health")
    if problems:
        print()
        for p in problems:
            print(f"  ⚠ {p}")
    else:
        print()
        print("  ✓ clean")
    if summary:
        print()
        for s in summary:
            print(f"  {s}")
    return 1 if problems else 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "health",
        help="One-shot graph health summary (validate + orphans + stale + tier-A coverage). Exit 1 if anything wrong.",
    )
    p.set_defaults(func=cmd_health)
