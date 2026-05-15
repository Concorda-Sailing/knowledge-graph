"""depgraph commit-summary subcommand handler.

Outputs a compact summary of touched tracked nodes for a commit body
trailer. Format is intentionally machine-greppable so blind spots can be
found later: any bug in a node that doesn't appear in any commit's
`Depgraph:` trailer is by definition unsurfaced.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .context import Context
from ._shared import load_dependents_index

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from config import project_repos, path_to_repo_relative  # noqa: E402


def cmd_commit_summary(args: argparse.Namespace, ctx: Context) -> int:
    """Output a compact summary of touched tracked nodes for a commit body
    trailer. Format is intentionally machine-greppable so blind spots can be
    found later: any bug in a node that doesn't appear in any commit's
    `Depgraph:` trailer is by definition unsurfaced.

    No args → reads `git diff --name-only` (staged + unstaged).
    With args → uses the given paths.
    """
    files: list[str] = list(args.files or [])
    if not files:
        try:
            staged = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, check=False,
            ).stdout.splitlines()
            unstaged = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True, text=True, check=False,
            ).stdout.splitlines()
            files = sorted(set(staged + unstaged))
        except FileNotFoundError:
            print("git not available", file=sys.stderr)
            return 1
    if not files:
        print("Depgraph: no files in diff (or none changed).")
        return 0

    # Resolve paths to absolute, then to (repo, rel) per project.toml repos.
    by_id: dict[str, dict] = {}
    by_source: dict[tuple[str, str], list[str]] = {}
    for nf in ctx.NODES.rglob("*.json"):
        if nf.name.startswith("_") or any(p.startswith("_") for p in nf.parts):
            continue
        try:
            data = json.loads(nf.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = data.get("id")
        if not nid:
            continue
        by_id[nid] = data
        src = data.get("source") or {}
        repo, p = src.get("repo"), src.get("path")
        if repo and p:
            by_source.setdefault((repo, p), []).append(nid)

    deps_index = load_dependents_index(ctx)

    repos = list(project_repos(ctx.DEPGRAPH).values())

    def _repo_relative(p: str) -> tuple[str, str] | None:
        """Path → (basename, rel) by consulting [repos.*].path. Works for both
        absolute paths and already-repo-relative paths regardless of layout."""
        # If `p` is already a repo-relative path like "models/foo.py", probe
        # each configured checkout for the file.
        if not Path(p).is_absolute():
            for info in repos:
                if (info["path"] / p).exists():
                    return info["basename"], p
            # Also tolerate "<basename>/<rel>" style by checking the prefix.
            for info in repos:
                bn = info["basename"]
                if p == bn or p.startswith(bn + "/"):
                    return bn, p[len(bn) + 1:] if p != bn else ""
            return None
        rr = path_to_repo_relative(p, ctx.DEPGRAPH)
        return rr

    # Group nodes by source file so a 274-method api.ts shows once, not 274 times.
    by_file: dict[str, list[str]] = {}
    untracked_files: list[str] = []
    for f in files:
        rr = _repo_relative(f)
        if not rr:
            untracked_files.append(f)
            continue
        ids = by_source.get(rr) or []
        if not ids:
            untracked_files.append(f)
            continue
        by_file[f"{rr[0]}/{rr[1]}"] = ids

    def _check_dossier(node: dict) -> str | None:
        rel = node.get("dossier")
        if not rel:
            return None
        dpath = ctx.DEPGRAPH / rel
        if not dpath.exists():
            return "missing-dossier"
        text = dpath.read_text()
        pinned = None
        status = "current"
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("last_reviewed_against_hash:"):
                pinned = s.split(":", 1)[1].strip().strip('"').strip("'")
            if s.startswith("status:"):
                status = s.split(":", 1)[1].strip()
            if s == "---" and pinned is not None:
                break
        if pinned and pinned != node.get("structural_hash"):
            return "stale-dossier"
        if status == "unreviewed":
            return "unreviewed-dossier"
        return None

    total_node_ids = sum(len(v) for v in by_file.values())
    lines = ["Depgraph:"]
    lines.append(
        f"  changed: {len(files)} file(s), {total_node_ids} tracked node(s)"
        + (f", {len(untracked_files)} untracked" if untracked_files else "")
    )

    high_impact: list[tuple[str, dict]] = []  # (id, node) for direct >= 5
    all_warnings: set[str] = set()
    grand_total_direct = 0
    grand_total_fuzzy = 0

    for fpath, ids in sorted(by_file.items()):
        per_file_direct = 0
        per_file_fuzzy = 0
        per_file_warnings: set[str] = set()
        for nid in ids:
            node = by_id.get(nid, {})
            direct = deps_index.get(nid) or []
            fuzzy = sum(1 for d in direct if d.get("via") == "string_url" or d.get("confidence") in ("fuzzy", "inferred"))
            per_file_direct += len(direct)
            per_file_fuzzy += fuzzy
            grand_total_direct += len(direct)
            grand_total_fuzzy += fuzzy
            for w in (node.get("warnings") or []):
                code = w.get("code") or "?"
                per_file_warnings.add(code)
                all_warnings.add(code)
            dossier_warn = _check_dossier(node)
            if dossier_warn:
                per_file_warnings.add(dossier_warn)
                all_warnings.add(dossier_warn)
            if len(direct) >= 5:
                high_impact.append((nid, node))

        # Per-file line: file path, node count, kind summary, direct deps
        kinds = {by_id.get(nid, {}).get("kind", "?") for nid in ids}
        kind_summary = ",".join(sorted(kinds))
        warn_str = f", warnings={','.join(sorted(per_file_warnings))}" if per_file_warnings else ""
        lines.append(
            f"  - {fpath}: {len(ids)} {kind_summary} node(s)"
            f", direct-deps={per_file_direct} (fuzzy={per_file_fuzzy})"
            f"{warn_str}"
        )

    if high_impact:
        lines.append("  high-impact (>=5 direct deps):")
        # Sort by direct desc, top 10
        scored = [(len(deps_index.get(nid) or []), nid) for nid, _ in high_impact]
        scored.sort(reverse=True)
        for n_direct, nid in scored[:10]:
            lines.append(f"    {n_direct:>4}  {nid}")
        if len(scored) > 10:
            lines.append(f"    ... +{len(scored) - 10} more")

    if untracked_files:
        sample = ",".join(untracked_files[:5])
        more = f" (+{len(untracked_files) - 5} more)" if len(untracked_files) > 5 else ""
        lines.append(f"  untracked: {sample}{more}")

    lines.append(
        f"  totals: direct-deps={grand_total_direct} (fuzzy={grand_total_fuzzy}), "
        f"warnings={','.join(sorted(all_warnings)) or 'none'}"
    )

    print("\n".join(lines))
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("commit-summary", help="Compact summary for commit body trailer")
    p.add_argument("files", nargs="*", help="Files to summarize; empty = git diff --name-only")
    p.set_defaults(func=cmd_commit_summary)
