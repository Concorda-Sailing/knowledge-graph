"""Defines `echo`, which the package __init__ re-exports as a top-level
attribute (the barrel pattern that's load-bearing for the b2 fix —
`<imported-pkg>.<re-exported-name>` must still resolve)."""
from __future__ import annotations


def echo(value: str) -> str:
    return value
