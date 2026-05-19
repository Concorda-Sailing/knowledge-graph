"""kg logigraph — native subcommand registration via logigraph.lib.cli.

Phase 3 replaces the Phase-1 subprocess shim. kg now owns argparse
end-to-end; --help reaches the real subcommand help surface; handlers
run in-process.

The lib-namespace collision that previously required a sys.modules eviction
block inside _run() is gone: fully-qualified imports (logigraph.lib.X vs
depgraph.lib.X) are distinct sys.modules keys and never collide.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from kg.cli import resolve
from kg.shared.env import DEPGRAPH_DATA_DIR

# bin/kg already adds the framework root to sys.path, so fully-qualified
# logigraph.lib.* imports resolve without any additional sys.path mutation.
from logigraph.lib.cli import build_parser as _logigraph_build_parser
from logigraph.lib.cli.context import Context as _LogigraphContext


def _run(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    sub_parser = _logigraph_build_parser()
    if extra and extra[0] in ("-h", "--help"):
        sub_parser.print_help()
        return 0
    sub_args = sub_parser.parse_args(extra)
    os.environ[DEPGRAPH_DATA_DIR] = str(proj.depgraph_dir)
    ctx = _LogigraphContext.from_data_dir(proj.logigraph_dir)
    return sub_args.func(sub_args, ctx)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "logigraph",
        help="Rules-graph operations (regen, rules-for, rule/process/domain lifecycle, ...).",
        add_help=False,
    )
    p.add_argument("--project")
    p.add_argument("--data-dir")
    p.set_defaults(func=_run, wants_extra=True)
