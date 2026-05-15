"""kg logigraph — subprocess shim into the logigraph CLI.

Phase 1: resolves a project, exports LOGIGRAPH_DATA_DIR, then execs the
existing logigraph binary with the remaining argv.

Phase 3 replaces this with native subcommand registration that imports
from logigraph.lib.cli.* modules.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from kg.cli import resolve


def _run_logigraph(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    tool_root = Path(__file__).resolve().parents[2]
    logi_bin = tool_root / "logigraph" / "bin" / "logigraph"
    env = {
        **os.environ,
        "LOGIGRAPH_DATA_DIR": str(proj.logigraph_dir),
        "DEPGRAPH_DATA_DIR": str(proj.depgraph_dir),
    }
    os.execvpe(str(logi_bin), [str(logi_bin), *extra], env)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "logigraph",
        help="Rules-graph operations (regen, rules-for, rule/process/domain lifecycle, ...).",
        add_help=False,
    )
    p.add_argument("--project")
    p.add_argument("--data-dir")
    p.set_defaults(func=_run_logigraph, wants_extra=True)
