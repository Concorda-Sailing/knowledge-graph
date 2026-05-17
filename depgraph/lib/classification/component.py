"""Component classifier — JSX-returning PascalCase functions."""
from __future__ import annotations

KIND = "component"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        # Strip Class.method prefix before checking case
        name = p["name"].split(".")[-1]
        if not name or not name[0].isupper():
            continue
        if p["signature"].get("returns_jsx"):
            decisions[p["id"]] = {
                "rule": "returns_jsx",
                "evidence": [{"kind": "jsx_return", "where": f"{p['source']['path']}:{p['source']['line']}"}],
            }
    return decisions
