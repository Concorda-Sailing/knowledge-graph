"""kg depgraph — stub for Task 11. Real subprocess shim arrives there."""
from __future__ import annotations

import argparse


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("depgraph", help="Code-graph operations.")
    p.set_defaults(func=lambda args, extra: 1, wants_extra=True)
