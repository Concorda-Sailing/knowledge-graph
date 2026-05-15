"""depgraph CLI — modular subcommand layout.

Each subcommand has its own module exposing `cmd_<name>(args, ctx)` and
`register(sub)`. The dispatcher (`build_parser`) imports each module and
registers it; both `bin/depgraph` and `kg.cli.depgraph` call into the
same handlers.
"""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Construct the depgraph CLI's argparse tree.

    Modules will be added in subsequent Phase-2 tasks. Until then this
    returns a parser with no subcommands — useful only as scaffolding.
    """
    parser = argparse.ArgumentParser(prog="depgraph")
    sub = parser.add_subparsers(dest="cmd", required=True)
    # Modules wired in subsequent tasks (Tasks 2-14):
    #   regen, context_cmd, dependents, orphans, validate, self_check,
    #   health, stats, commit_summary, memory_sync, dossier, flag, repo
    return parser
