"""kg install — subprocess shim into install.sh.

Phase 1: forwards argv to install.sh (which lives next to the kg/
package). install.sh handles --project / --apply / --target itself,
so kg.cli.install does no project resolution — it's a transparent
wrapper that unifies the help surface.

Phase 4 ports install.sh's logic to Python under this module.
Subcommands with native Python handlers are dispatched directly;
everything else still subprocesses into install.sh (replaced P4T3-P4T8).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from kg.cli.install import init as _init_mod
from kg.cli.install import tools as _tools_mod


def _run_installer(args: argparse.Namespace, extra: list[str]) -> int:
    # Subcommands that have native Python handlers dispatch directly.
    if extra and extra[0] == "init":
        init_parser = argparse.ArgumentParser(prog="kg install init")
        init_parser.add_argument("path")
        init_args = init_parser.parse_args(extra[1:])
        return _init_mod.cmd_init(init_args)
    if extra and extra[0] in ("tools", "install"):
        tools_parser = argparse.ArgumentParser(prog="kg install tools")
        tools_parser.add_argument("--target", default=str(Path.home() / "tools"))
        tools_parser.add_argument("--data", action="append", default=[])
        tools_args = tools_parser.parse_args(extra[1:])
        return _tools_mod.cmd_tools(tools_args)
    # Fall through: subprocess shim for everything else.
    tool_root = Path(__file__).resolve().parents[3]
    installer = tool_root / "install.sh"
    os.execvpe(str(installer), [str(installer), *extra], os.environ.copy())


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "install",
        help="Machine setup: tools, hooks, systemd, PATH, cascade, bootstrap.",
        add_help=False,
    )
    p.set_defaults(func=_run_installer, wants_extra=True)
