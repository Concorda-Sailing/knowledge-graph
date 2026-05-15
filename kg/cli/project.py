"""kg project — stub for Task 5. Real implementation arrives in Task 5."""
from __future__ import annotations

import argparse


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("project", help="Per-project config and registry.")
    p.set_defaults(func=lambda args: (print("kg project — not implemented yet"), 1)[1])
