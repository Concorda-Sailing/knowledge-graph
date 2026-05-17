"""Endpoint classifier — functions decorated by a known route decorator."""
from __future__ import annotations

KIND = "endpoint"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        decs = p["signature"].get("decorators", [])
        for d in decs:
            # Extractors emit clean decorator names (args already stripped),
            # so exact-match against config.route_decorators is sufficient.
            if d in config.route_decorators:
                decisions[p["id"]] = {
                    "rule": "route_decorator",
                    "evidence": [{"decorator": d,
                                  "where": f"{p['source']['path']}:{p['source']['line']}"}],
                }
                break
    return decisions
