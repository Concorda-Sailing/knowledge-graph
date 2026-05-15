"""Shared utilities used by multiple depgraph subcommand handlers.

Every function takes `ctx: Context` as its first parameter so handlers
don't reach for module globals. This is the refactor that unblocks
native import-and-register from kg.cli.depgraph.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Make depgraph/lib/config.py importable so _shared can use project_repos.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from config import project_repos  # noqa: E402

from .context import Context


def mark_regen_in_progress(ctx: Context) -> None:
    """Defect #2: write a regen marker so the hook can surface 'graph being
    rebuilt' when an edit happens mid-regen, and so a crashed extractor leaves
    a visible signal rather than a silently-torn graph. Reconcile rewrites
    _meta.json with regen_status='complete' on success — if anything fails
    between mark_regen_in_progress and reconcile finishing, the file stays at
    'in_progress'."""
    import datetime as _dt

    ctx.NODES.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "regen_status": "in_progress",
        "started_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
    # Don't clobber the prior `complete` payload if it has more info — preserve
    # what's there and override only the status fields.
    if ctx.CORPUS_META.exists():
        try:
            existing = json.loads(ctx.CORPUS_META.read_text())
            payload = {**existing, **payload}
        except (OSError, json.JSONDecodeError):
            pass
    tmp = ctx.CORPUS_META.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    tmp.replace(ctx.CORPUS_META)


def load_dependents_index(ctx: Context) -> dict[str, list[dict]]:
    """Read the reverse-edge index. Empty dict if not yet built."""
    if not ctx.DEPENDENTS_INDEX.exists():
        return {}
    try:
        idx = json.loads(ctx.DEPENDENTS_INDEX.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if idx.get("schema_version") != 1:
        print("WARN: dependents index schema_version mismatch", file=sys.stderr)
        return {}
    return idx.get("by_target") or {}


def find_nodes_for_target(ctx: Context, target: str) -> list[Path]:
    """If `target` is a file path, return nodes whose source.path matches.
    Otherwise treat it as a node id. Node ids contain `::` separators
    (e.g. `<repo>::models/foo.py::Bar` or `GET::/api/x`); a `/` in
    the target alone isn't enough to treat it as a path.

    Path matching looks up each repo's actual checkout from project.toml
    rather than assuming ~/<basename>/ — projects with non-flat layouts
    (e.g. ~/projects/<group>/<repo>/) need the config-driven lookup."""
    out: list[Path] = []
    is_id = "::" in target
    abs_path = Path(target).expanduser().resolve() if "/" in target and not is_id else None
    basename_to_path = {info["basename"]: info["path"] for info in project_repos(ctx.DEPGRAPH).values()}
    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if abs_path:
            src_repo = data.get("source", {}).get("repo", "")
            src_rel = data.get("source", {}).get("path", "") or ""
            repo_path = basename_to_path.get(src_repo)
            if repo_path is None:
                continue
            cand = (repo_path / src_rel).resolve()
            if cand == abs_path:
                out.append(node_file)
        else:
            if data.get("id") == target:
                out.append(node_file)
    return out


def _depgraph_commit_if_changed(ctx: Context, paths: list[Path], message: str) -> bool:
    rel = [str(p.relative_to(ctx.DEPGRAPH)) for p in paths]
    subprocess.run(["git", "-C", str(ctx.DEPGRAPH), "add", *rel], check=True)
    diff = subprocess.run(
        ["git", "-C", str(ctx.DEPGRAPH), "diff", "--cached", "--name-only"],
        capture_output=True, text=True,
    )
    if not diff.stdout.strip():
        return False
    subprocess.run(["git", "-C", str(ctx.DEPGRAPH), "commit", "-q", "-m", message], check=True)
    return True
