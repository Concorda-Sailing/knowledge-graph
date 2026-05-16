"""logigraph dossiers subcommand — backwards-compat alias for `stats` with no flags."""
from __future__ import annotations

import argparse

from .context import Context
from .stats import cmd_stats


def cmd_dossiers(args: argparse.Namespace, ctx: Context) -> int:
    """Backwards-compat alias for `stats` with no flags."""
    args.telemetry = False
    return cmd_stats(args, ctx)


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("dossiers")
    p.add_argument("--status", action="store_true")
    p.set_defaults(func=cmd_dossiers)
