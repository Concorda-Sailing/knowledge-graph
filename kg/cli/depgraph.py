"""kg depgraph — subprocess shim into the depgraph CLI.

Phase 1: resolves a project, exports DEPGRAPH_DATA_DIR, then execs
the existing depgraph binary with the remaining argv. The user sees
identical output and signals.

Phase 2 replaces this with native subcommand registration that imports
from depgraph.lib.cli.* modules.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from kg.cli import resolve


def _run_depgraph(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    tool_root = Path(__file__).resolve().parents[2]
    depgraph_bin = tool_root / "depgraph" / "bin" / "depgraph"
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(proj.depgraph_dir)}
    # Use os.execvpe so signals (Ctrl-C, etc.) and exit codes are transparent.
    os.execvpe(str(depgraph_bin), [str(depgraph_bin), *extra], env)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "depgraph",
        help="Code-graph operations (regen, dependents, dossiers, ...).",
        add_help=False,  # let depgraph CLI handle --help so it reaches the actual command tree
    )
    p.add_argument("--project", help="Project name (overrides env/cwd/default).")
    p.add_argument("--data-dir", help="Depgraph data dir path.")
    p.set_defaults(func=_run_depgraph, wants_extra=True)
