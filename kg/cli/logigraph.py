"""kg logigraph — stub for Task 12. Real subprocess shim arrives there."""
from __future__ import annotations

import argparse


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("logigraph", help="Rules-graph operations.")
    p.set_defaults(func=lambda args, extra: 1, wants_extra=True)
