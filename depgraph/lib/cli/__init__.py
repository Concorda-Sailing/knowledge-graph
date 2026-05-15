"""depgraph CLI — modular subcommand layout.

Each subcommand has its own module exposing `cmd_<name>(args, ctx)` and
`register(sub)`. The dispatcher (`build_parser`) imports each module and
registers it; both `bin/depgraph` and `kg.cli.depgraph` call into the
same handlers.
"""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Construct the depgraph CLI's argparse tree."""
    parser = argparse.ArgumentParser(prog="depgraph")
    sub = parser.add_subparsers(dest="cmd", required=True)
    from . import (
        regen, context_cmd, dependents, orphans, validate,
        self_check, health, stats, commit_summary, memory_sync,
        dossier, flag, repo,
    )
    # Order matches legacy bin/depgraph to keep --help output consistent.
    for mod in (
        regen, context_cmd, dependents, orphans, validate,
        self_check, health, stats, commit_summary, memory_sync,
        dossier, flag, repo,
    ):
        mod.register(sub)
    return parser
