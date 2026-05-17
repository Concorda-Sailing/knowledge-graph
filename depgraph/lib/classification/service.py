"""Service classifier — function with side-effect edges AND reachable from endpoint."""
from __future__ import annotations

KIND = "service"
_SIDE_EFFECT_KINDS = {
    "db_access", "queue_produce", "webhook_publish",
    "notification_send", "file_storage_access",
}


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    # Endpoints are already classified by the endpoint classifier upstream.
    # If service ever runs first, decisions_so_far is empty and no service
    # classifies — that's a correct safety property, not a bug.
    endpoints = {pid for pid, dec in decisions_so_far.items() if dec.kind == "endpoint"}

    # BFS reachability from endpoints over `calls` edges
    reachable: set[str] = set()
    frontier = list(endpoints)
    while frontier:
        cur = frontier.pop()
        if cur in reachable:
            continue
        reachable.add(cur)
        for e in by_source.get(cur, []):
            if e["kind"] == "calls":
                frontier.append(e["target"])

    # Functions with side-effect edges that are reachable but not themselves endpoints
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        if p["id"] not in reachable:
            continue
        if p["id"] in endpoints:
            # Endpoint stays endpoint; service must not double-classify it
            continue
        side_effects = [e for e in by_source.get(p["id"], []) if e["kind"] in _SIDE_EFFECT_KINDS]
        if side_effects:
            decisions[p["id"]] = {
                "rule": "side_effect_reachable_from_endpoint",
                "evidence": side_effects,
            }
    return decisions
