"""logigraph CLI — modular subcommand layout.

Each subcommand has its own module exposing cmd_<name>(args, ctx) and
register(sub). build_parser() imports each module and registers it.
Both bin/logigraph and kg.cli.logigraph call into the same handlers.
"""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Construct the logigraph CLI's argparse tree.

    Modules will be added in subsequent Phase-3 tasks. Until then this
    returns a parser with no subcommands.
    """
    parser = argparse.ArgumentParser(prog="logigraph")
    sub = parser.add_subparsers(dest="cmd", required=True)
    return parser
