"""Rollup computation: given a logigraph domain node, find the depgraph
nodes that operate on it.

Reads the existing reverse-dependents index at
`<data_dir>/nodes/_index/dependents.json` (built by `bin/depgraph regen`).
Pure functions; no I/O except reading already-loaded indexes.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class AnchorResult:
    model_id: str | None
    reason: str  # "table_match" | "class_name_match" | "defined_in" | "via_mediated_by" | "not_found"


def resolve_anchor(
    domain_node: dict,
    depgraph_index: dict[str, dict],
    logigraph_index: dict[str, dict] | None = None,
) -> AnchorResult:
    """Resolve the canonical depgraph model node for a logigraph domain node.

    Per spec § "Approach: pure graph derivation" step 1.

    Args:
        domain_node: a logigraph domain node dict (must have `subkind`, `source`).
        depgraph_index: { node_id: depgraph_node_dict } for fast lookup.
        logigraph_index: { node_id: domain_node_dict } for relationship
            recursion. REQUIRED when `subkind == "relationship"`; raises
            ValueError if omitted. Optional otherwise.

    Returns:
        AnchorResult.model_id is None when no anchor can be resolved.
    """
    subkind = domain_node.get("subkind")
    source = domain_node.get("source") or {}

    if subkind == "relationship":
        if logigraph_index is None:
            raise ValueError(
                "logigraph_index is required when resolving anchor for a "
                "relationship subkind (mediated_by recursion needs it)"
            )
        mediated_by = domain_node.get("mediated_by")
        if not mediated_by:
            return AnchorResult(None, "not_found")
        target = logigraph_index.get(mediated_by)
        if not target:
            return AnchorResult(None, "not_found")
        inner = resolve_anchor(target, depgraph_index, logigraph_index)
        if inner.model_id:
            return AnchorResult(inner.model_id, "via_mediated_by")
        return AnchorResult(None, "not_found")

    # For resource / role / attribute the consistent signal is `defined_in`.
    defined_in = source.get("defined_in")
    table = source.get("table")
    candidates: list[dict] = []
    if defined_in:
        # defined_in format: "<repo-basename>/<repo-relative-path>".
        # depgraph model node has source.repo + source.path that combine to the same.
        for node in depgraph_index.values():
            if node.get("kind") != "model":
                continue
            n_source = node.get("source") or {}
            n_repo = n_source.get("repo", "")
            n_path = n_source.get("path", "")
            if f"{n_repo}/{n_path}" == defined_in:
                candidates.append(node)

    if subkind == "resource" and table:
        # Prefer a candidate whose tablename also matches.
        for node in candidates:
            if (node.get("signature") or {}).get("tablename") == table:
                return AnchorResult(node["id"], "table_match")
        # No tablename match in `defined_in` candidates — scan the rest of
        # the corpus by tablename. Skip the candidates we just rejected.
        rejected_ids = {n["id"] for n in candidates}
        for node in depgraph_index.values():
            if node.get("kind") != "model" or node["id"] in rejected_ids:
                continue
            if (node.get("signature") or {}).get("tablename") == table:
                return AnchorResult(node["id"], "table_match")

    if subkind == "role" and table:
        # Roles store the PascalCase class name in `source.table`, NOT the
        # SQL tablename. Disambiguate among candidates by signature.name.
        for node in candidates:
            if (node.get("signature") or {}).get("name") == table:
                return AnchorResult(node["id"], "class_name_match")

    if candidates:
        # First candidate by stable order (defined_in match alone).
        candidates.sort(key=lambda n: n["id"])
        return AnchorResult(candidates[0]["id"], "defined_in")

    return AnchorResult(None, "not_found")
