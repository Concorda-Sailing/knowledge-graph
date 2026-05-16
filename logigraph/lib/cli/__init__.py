"""logigraph CLI — modular subcommand layout.

Each subcommand has its own module exposing cmd_<name>(args, ctx) and
register(sub). build_parser() imports each module and registers it.
Both bin/logigraph and kg.cli.logigraph call into the same handlers.
"""
from __future__ import annotations

import argparse

from . import regen
from . import validate
from . import context_cmd
from . import rules_for
from . import fan_out
from . import gaps
from . import dossiers
from . import stats
from . import self_check
from . import health
from . import rule
from . import process
from . import domain
from . import rollup_cmd
from . import flag


def build_parser() -> argparse.ArgumentParser:
    """Construct the logigraph CLI's argparse tree.

    Modules are registered in legacy subcommand order so --help output
    is unchanged from the original monolithic bin/logigraph.
    """
    parser = argparse.ArgumentParser(prog="logigraph")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Legacy order: regen, validate, context, rules-for, fan-out, gaps,
    # dossiers, stats, self-check, health,
    # rule-rank, rule-stub, rule-draft, rule-finalize, rule-bump,
    # domain-bump,
    # process-rank, process-stub, process-draft, process-finalize, process-bump,
    # rollup,
    # flag, unflag
    regen.register(sub)
    validate.register(sub)
    context_cmd.register(sub)
    rules_for.register(sub)
    fan_out.register(sub)
    gaps.register(sub)
    dossiers.register(sub)
    stats.register(sub)
    self_check.register(sub)
    health.register(sub)
    rule.register(sub)
    domain.register(sub)
    process.register(sub)
    rollup_cmd.register(sub)
    flag.register(sub)

    return parser
