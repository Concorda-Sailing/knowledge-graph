"""Util classifier — function transitively reachable from a classified kind.

Rule: a function F is util iff
  (a) F is not yet classified, AND
  (b) there is a `calls`-edge path from at least one classified function
      *into* F (i.e., classified ─calls→ … ─calls→ F).

Computed by forward BFS starting from the classified set, expanding through
`calls` edges. Single pass; visited-set prevents cycling. Util-of-util chains
are handled because newly-reached util nodes are added to the frontier.
"""
from __future__ import annotations

KIND = "util"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    classified_ids = {pid for pid, dec in decisions_so_far.items() if dec.kind}
    if not classified_ids:
        return {}

    # Build caller -> [callees] map restricted to `calls` edges
    callees_of: dict[str, list[str]] = {}
    for src_id, edges in by_source.items():
        for e in edges:
            if e["kind"] == "calls":
                callees_of.setdefault(src_id, []).append(e["target"])

    # Forward BFS: classified nodes expand to everything they (transitively) call.
    # Anything reached that isn't already classified is util.
    reachable: set[str] = set()
    frontier = list(classified_ids)
    while frontier:
        cur = frontier.pop()
        for callee in callees_of.get(cur, []):
            if callee in classified_ids or callee in reachable:
                continue
            reachable.add(callee)
            frontier.append(callee)  # expand through util-of-util chains

    primitives_by_id = {p["id"]: p for p in primitives}
    decisions = {}
    for util_id in reachable:
        p = primitives_by_id.get(util_id)
        if p is None or p["primitive"] != "function":
            continue
        # Collect direct callers for evidence (useful for graphui traversal)
        direct_callers = [
            src_id for src_id, edges in by_source.items()
            for e in edges
            if e["kind"] == "calls" and e["target"] == util_id
        ]
        decisions[util_id] = {
            "rule": "transitive_call_target_of_classified",
            "evidence": [{"caller": c} for c in direct_callers],
        }
    return decisions
