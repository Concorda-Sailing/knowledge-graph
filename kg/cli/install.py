"""kg install — stub for Task 13. Real subprocess shim arrives there."""
from __future__ import annotations

import argparse


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("install", help="Machine setup (tools, hooks, systemd, etc.).")
    p.set_defaults(func=lambda args, extra: 1, wants_extra=True)
