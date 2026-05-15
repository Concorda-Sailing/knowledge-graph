"""kg depgraph — native subcommand registration via depgraph.lib.cli.

Phase 2 replaces the Phase-1 subprocess shim. kg now owns argparse
end-to-end; --help reaches the real subcommand help surface; handlers
run in-process. Exit codes and signals pass through naturally.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kg.cli import resolve

_DEPGRAPH_ROOT = Path(__file__).resolve().parents[2] / "depgraph"
if str(_DEPGRAPH_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_ROOT))
from lib.cli import build_parser as _depgraph_build_parser  # noqa: E402
from lib.cli.context import Context as _DepgraphContext  # noqa: E402


def _run(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    sub_parser = _depgraph_build_parser()
    if extra and extra[0] in ("-h", "--help"):
        sub_parser.print_help()
        return 0
    sub_args = sub_parser.parse_args(extra)
    ctx = _DepgraphContext.from_data_dir(proj.depgraph_dir)
    return sub_args.func(sub_args, ctx)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "depgraph",
        help="Code-graph operations (regen, dependents, dossiers, ...).",
        add_help=False,
    )
    p.add_argument("--project")
    p.add_argument("--data-dir")
    p.set_defaults(func=_run, wants_extra=True)
