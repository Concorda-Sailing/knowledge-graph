"""kg logigraph — native subcommand registration via logigraph.lib.cli.

Phase 3 replaces the Phase-1 subprocess shim. kg now owns argparse
end-to-end; --help reaches the real subcommand help surface; handlers
run in-process.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kg.cli import resolve

_LOGIGRAPH_ROOT = Path(__file__).resolve().parents[2] / "logigraph"

# Modules that both depgraph and logigraph ship under the same dotted names.
# We evict these inside _run() before importing logigraph's copies so that
# a kg depgraph X; kg logigraph Y sequence in the same process resolves
# correctly regardless of import order.
_SHARED_LIB_MODULES = (
    "lib",
    "lib.cli",
    "lib.config",
    "lib.cli.context",
    "lib.cli._shared",
    "lib.cli.regen",
    "lib.cli.validate",
    "lib.cli.health",
    "lib.cli.self_check",
    "lib.cli.stats",
    "lib.cli.context_cmd",
    "lib.cli.flag",
)


def _run(args: argparse.Namespace, extra: list[str]) -> int:
    try:
        proj = resolve.resolve_project(
            project_name=getattr(args, "project", None),
            data_dir=Path(args.data_dir).expanduser() if getattr(args, "data_dir", None) else None,
        )
    except resolve.ProjectResolutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Logigraph and depgraph both ship a `lib.cli` package; evict any
    # depgraph entries from sys.modules before importing logigraph's.
    for name in list(sys.modules):
        if name in _SHARED_LIB_MODULES:
            del sys.modules[name]

    # Ensure logigraph/ is at the front of sys.path.
    if sys.path[0] != str(_LOGIGRAPH_ROOT):
        sys.path.insert(0, str(_LOGIGRAPH_ROOT))

    from lib.cli import build_parser
    from lib.cli.context import Context as LogigraphContext

    sub_parser = build_parser()
    if extra and extra[0] in ("-h", "--help"):
        sub_parser.print_help()
        return 0
    sub_args = sub_parser.parse_args(extra)
    import os
    os.environ["DEPGRAPH_DATA_DIR"] = str(proj.depgraph_dir)
    ctx = LogigraphContext.from_data_dir(proj.logigraph_dir)
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
