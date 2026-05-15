"""kg install — subprocess shim into install.sh.

Phase 1: forwards argv to install.sh (which lives next to the kg/
package). install.sh handles --project / --apply / --target itself,
so kg.cli.install does no project resolution — it's a transparent
wrapper that unifies the help surface.

Phase 4 ports install.sh's logic to Python under this module.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def _run_installer(args: argparse.Namespace, extra: list[str]) -> int:
    tool_root = Path(__file__).resolve().parents[2]
    installer = tool_root / "install.sh"
    os.execvpe(str(installer), [str(installer), *extra], os.environ.copy())


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "install",
        help="Machine setup: tools, hooks, systemd, PATH, cascade, bootstrap.",
        add_help=False,
    )
    p.set_defaults(func=_run_installer, wants_extra=True)
