"""depgraph repo-add / repo-list / repo-remove subcommand handlers.

repo-add <key> <path> [options]   Write a [repos.<key>] table to project.toml.
repo-list                         Print all configured repos.
repo-remove <key>                 Strip a [repos.<key>] block from project.toml.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .context import Context
from depgraph.lib.config import (
    project_repos,
    project_primary_repo,
    project_primary_repo_explicit,
)


# ── private helpers ──────────────────────────────────────────────────────────

def _format_repo_table(key: str, path: str, extractor, detectors, files_arg) -> str:
    """Render a [repos.<key>] TOML block. Uses TOML basic-string quoting."""
    lines = [f"[repos.{key}]", f'path = "{path}"']
    if extractor:
        lines.append("extractor = [" + ", ".join(f'"{t}"' for t in extractor) + "]")
    if detectors:
        lines.append("detectors = [" + ", ".join(f'"{d}"' for d in detectors) + "]")
    if files_arg:
        lines.append(f'files_arg = "{files_arg}"')
    return "\n".join(lines) + "\n"


def _strip_existing_repo_block(text: str, key: str) -> str:
    """Remove a `[repos.<key>]` block (header + body up to next top-level table
    or EOF). Returns text unchanged if the block is absent."""
    pattern = re.compile(
        r"(?ms)^\[repos\." + re.escape(key) + r"\][^\n]*\n(?:(?!^\[).*\n?)*"
    )
    return pattern.sub("", text)


def _normalize_repo_path(p: str) -> str:
    """Rewrite absolute paths under $HOME to ~/... so project.toml stays
    portable across users. Pass relative/other paths through verbatim."""
    home = str(Path.home())
    abs_p = str(Path(p).expanduser())
    if abs_p.startswith(home + "/"):
        return "~" + abs_p[len(home):]
    return p


# ── subcommand handlers ──────────────────────────────────────────────────────

def cmd_repo_add(args: argparse.Namespace, ctx: Context) -> int:
    cfg_path = ctx.DEPGRAPH / "project.toml"
    if not cfg_path.exists():
        print(f"no project.toml at {cfg_path}", file=sys.stderr)
        return 1
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.key):
        print(f"invalid repo key: {args.key!r} "
              f"(allowed: alnum, -, _; must start with alnum)", file=sys.stderr)
        return 1

    repos = project_repos(ctx.DEPGRAPH)
    existed = args.key in repos
    if existed and not args.force:
        print(f"[repos.{args.key}] already exists in {cfg_path}; "
              f"pass --force to replace", file=sys.stderr)
        return 1

    stored_path = _normalize_repo_path(args.path)
    resolved = Path(stored_path).expanduser()
    if not resolved.exists():
        print(f"warning: {resolved} does not exist on disk yet — adding anyway",
              file=sys.stderr)

    block = _format_repo_table(
        args.key, stored_path,
        extractor=args.extractor,
        detectors=args.detector,
        files_arg=args.files_arg,
    )

    text = cfg_path.read_text()
    if existed:
        text = _strip_existing_repo_block(text, args.key).rstrip() + "\n"
    if not text.endswith("\n"):
        text += "\n"
    if not text.endswith("\n\n"):
        text += "\n"
    text += block
    cfg_path.write_text(text)
    print(f"{'replaced' if existed else 'added'} [repos.{args.key}] in {cfg_path}")
    return 0


def cmd_repo_list(args: argparse.Namespace, ctx: Context) -> int:
    repos = project_repos(ctx.DEPGRAPH)
    if not repos:
        print("no repos configured")
        return 0
    explicit_primary = project_primary_repo_explicit(ctx.DEPGRAPH)
    resolved_primary = project_primary_repo(ctx.DEPGRAPH)
    for key, r in repos.items():
        if explicit_primary and key == explicit_primary:
            marker = " (primary)"
        elif explicit_primary is None and key == resolved_primary:
            # No [project].primary_repo set; we fall back to first-by-order.
            # Mark it as a default so the user can tell the difference.
            marker = " (primary, default)"
        else:
            marker = ""
        print(f"{key}{marker}")
        print(f"  path:       {r['path']}")
        if r.get("extractor"):
            print(f"  extractor:  {' '.join(r['extractor'])}")
        if r.get("detectors"):
            print(f"  detectors:  {', '.join(r['detectors'])}")
        if r.get("files_arg"):
            print(f"  files_arg:  {r['files_arg']}")
    if explicit_primary is None:
        print("\n(no primary_repo set; first listed repo used as default — "
              "`kg project set primary_repo <key>` to make it explicit)")
    return 0


def cmd_repo_remove(args: argparse.Namespace, ctx: Context) -> int:
    cfg_path = ctx.DEPGRAPH / "project.toml"
    if not cfg_path.exists():
        print(f"no project.toml at {cfg_path}", file=sys.stderr)
        return 1
    repos = project_repos(ctx.DEPGRAPH)
    if args.key not in repos:
        print(f"[repos.{args.key}] not found in {cfg_path}", file=sys.stderr)
        return 1
    text = cfg_path.read_text()
    text = _strip_existing_repo_block(text, args.key).rstrip() + "\n"
    cfg_path.write_text(text)
    print(f"removed [repos.{args.key}] from {cfg_path}")
    return 0


# ── subparser registration ────────────────────────────────────────────────────

def register(sub: argparse._SubParsersAction) -> None:
    p_radd = sub.add_parser(
        "repo-add",
        help="Add a [repos.<key>] entry to project.toml (writes the sub-table form the loaders require)",
    )
    p_radd.add_argument("key", help="Repo key — canonical node ids are <key>::<rel-path>::<symbol>")
    p_radd.add_argument("path", help="Path to the repo checkout (~/... or absolute)")
    p_radd.add_argument("--extractor", nargs="+",
                        help="Extractor argv tokens (first is the program). Supports {kg_dir}/{data_dir}/{path} substitutions.")
    p_radd.add_argument("--detector", action="append", default=[],
                        help="Detector to layer on AST primitives; repeat for multiple")
    p_radd.add_argument("--files-arg", default=None,
                        help="Flag the extractor uses to receive a file list "
                             "(use = syntax for dash-leading values, e.g. --files-arg=--only)")
    p_radd.add_argument("--force", action="store_true",
                        help="Replace an existing entry with the same key")
    p_radd.set_defaults(func=cmd_repo_add)

    p_rlist = sub.add_parser("repo-list", help="List configured [repos.*] entries")
    p_rlist.set_defaults(func=cmd_repo_list)

    p_rrm = sub.add_parser("repo-remove", help="Remove a [repos.<key>] entry from project.toml")
    p_rrm.add_argument("key", help="Repo key to remove")
    p_rrm.set_defaults(func=cmd_repo_remove)
