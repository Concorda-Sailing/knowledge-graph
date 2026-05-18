"""Rollup computation: given a logigraph domain node, find the depgraph
nodes that operate on it.

Reads the existing reverse-dependents index at
`<data_dir>/nodes/_index/by_target.json` (built by `kg depgraph regen`).
Pure functions; no I/O except reading already-loaded indexes.
"""
from __future__ import annotations

from collections import deque
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class AnchorResult:
    model_id: str | None
    reason: str  # "table_match" | "class_name_match" | "defined_in" | "via_mediated_by" | "unresolved" | "not_found"


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


@dataclass(frozen=True)
class Entry:
    id: str
    title: str
    path: str         # "<repo>/<repo-relative-path>"
    repo: str
    kind: str         # depgraph kind: model | service | endpoint | component | test | hook | schema
    direct: bool
    via: tuple[str, ...]  # bridge chain from anchor to this node (empty for direct)


@dataclass(frozen=True)
class Rollup:
    anchor: AnchorResult
    by_kind: dict[str, list[Entry]]
    total: int


# Stable ordering for rendering.
_KIND_ORDER = ("model", "service", "endpoint", "component", "test", "hook", "schema")


def compute_rollup(
    anchor_id: str,
    depgraph_index: dict[str, dict],
    dependents_index: dict[str, list[dict]],
    depth: int = 3,
    anchor_result: AnchorResult | None = None,
) -> Rollup:
    """BFS over reverse-dependents from `anchor_id`, grouped by depgraph kind.

    Args:
        anchor_id: the depgraph model node id to root the BFS at.
        depgraph_index: { id: node } for kind/title/path lookups.
        dependents_index: { target_id: [{source, via, where}, ...] } —
            same shape as `nodes/_index/by_target.json`.
        depth: max BFS depth. 1 = direct dependents only. Spec default: 3.
        anchor_result: optional. If supplied, attached to the returned Rollup.
            When None, a placeholder AnchorResult is built from `anchor_id`.

    Returns:
        Rollup. The anchor node itself is included under `by_kind["<anchor's kind>"]`
        as a direct entry (so the "Model (1)" row in the rendered output is
        populated for resources/roles whose anchor IS the model).
    """
    by_kind: dict[str, list[Entry]] = {k: [] for k in _KIND_ORDER}
    seen: dict[str, Entry] = {}

    # Place the anchor itself first.
    anchor_node = depgraph_index.get(anchor_id)
    if anchor_node:
        entry = _entry_from_node(anchor_node, direct=True, via=())
        by_kind.setdefault(entry.kind, []).append(entry)
        seen[anchor_id] = entry

    # BFS. Queue items: (node_id, current_depth, via_chain).
    queue: deque[tuple[str, int, tuple[str, ...]]] = deque()
    queue.append((anchor_id, 0, ()))
    while queue:
        node_id, d, via_chain = queue.popleft()
        if d >= depth:
            continue
        for dep in dependents_index.get(node_id) or []:
            dep_id = dep.get("source")
            if not dep_id or dep_id in seen:
                continue
            dep_node = depgraph_index.get(dep_id)
            if not dep_node:
                # Edge points at an unknown node — skip silently. Reconcile
                # surfaces these as warnings; rollup doesn't duplicate the alarm.
                continue
            is_direct = (d == 0)
            entry = _entry_from_node(dep_node, direct=is_direct, via=via_chain)
            by_kind.setdefault(entry.kind, []).append(entry)
            seen[dep_id] = entry
            # Extend the chain with this node before recursing.
            queue.append((dep_id, d + 1, via_chain + (dep_id,)))

    # Sort within each kind: direct first, then transitive; alpha by title secondary.
    for k in by_kind:
        by_kind[k].sort(key=lambda e: (0 if e.direct else 1, e.title.lower()))

    return Rollup(
        anchor=anchor_result or AnchorResult(anchor_id if anchor_node else None,
                                             "unresolved" if anchor_node else "not_found"),
        by_kind=by_kind,
        total=sum(len(v) for v in by_kind.values()),
    )


# Tunables matching spec § "CLI surface":
#   summary cap = 3 per kind (CLI density)
#   max total summary lines = ~20 per entity
_SUMMARY_CAP_PER_KIND = 3


def format_rollup_text(rollup: Rollup, summary: bool = False) -> str:
    """Render a rollup as plain text. Used by `bin/logigraph context`
    (summary=True, inline in context output) and `bin/logigraph rollup`
    (summary=False, full output)."""
    if rollup.anchor.model_id is None:
        return f"Rollup: ⚠ no anchor model found ({rollup.anchor.reason})"

    lines: list[str] = []
    lines.append(f"Rollup: anchor {rollup.anchor.model_id}")
    for kind in _KIND_ORDER:
        entries = rollup.by_kind.get(kind) or []
        if not entries:
            continue
        total = len(entries)
        # Column alignment: kind name left-padded to 9 chars (longest is "Endpoint").
        label = kind.capitalize().ljust(9)
        if summary and total > _SUMMARY_CAP_PER_KIND:
            lines.append(
                f"  {label} ({total})              top {_SUMMARY_CAP_PER_KIND} of {total} — "
                f"see `logigraph rollup <entity-id>`"
            )
            show = entries[:_SUMMARY_CAP_PER_KIND]
        else:
            lines.append(f"  {label} ({total})")
            show = entries
        for e in show:
            marker = "direct" if e.direct else f"via {' → '.join(e.via)}"
            lines.append(f"    {e.id}              {marker}")
    return "\n".join(lines)


def format_rollup_json(rollup: Rollup) -> dict:
    """Render a rollup as a JSON-serializable dict. Schema is the durable
    contract for `bin/logigraph rollup --format json` consumers."""
    return {
        "anchor": {
            "model_id": rollup.anchor.model_id,
            "reason": rollup.anchor.reason,
        },
        "by_kind": {
            kind: [
                {
                    "id": e.id,
                    "title": e.title,
                    "path": e.path,
                    "repo": e.repo,
                    "kind": e.kind,
                    "direct": e.direct,
                    "via": list(e.via),
                }
                for e in entries
            ]
            for kind, entries in rollup.by_kind.items()
            if entries  # drop empty kinds for cleaner output
        },
        "total": rollup.total,
    }


@dataclass(frozen=True)
class RollupInputs:
    depgraph_index: dict[str, dict]
    dependents_index: dict[str, list[dict]]


def load_rollup_inputs(depgraph_data_dir) -> RollupInputs:
    """Read both indexes from disk. Used by CLI + graphui consumers so
    each doesn't reimplement the read.

    Raises FileNotFoundError with a clear regen pointer when the
    reverse-dependents index hasn't been built. Returning empty would
    silently produce false-empty rollups (anti-pattern from feedback_knowledge_graph_zero_defects).
    """
    root = Path(depgraph_data_dir)
    nodes_dir = root / "nodes"
    deps_path = nodes_dir / "_index" / "by_target.json"
    if not deps_path.exists():
        raise FileNotFoundError(
            f"reverse-dependents index missing: {deps_path}. "
            f"Run `kg depgraph regen` to rebuild it."
        )
    try:
        deps_raw = json.loads(deps_path.read_text())
    except json.JSONDecodeError as e:
        raise FileNotFoundError(
            f"reverse-dependents index unreadable: {deps_path}: {e}. "
            f"Run `kg depgraph regen` to rebuild it."
        )
    # v2: flat {target_id: [...]} dict. v1 (legacy) wrapped {"by_target": {...}}.
    if isinstance(deps_raw, dict) and "by_target" in deps_raw and "schema_version" in deps_raw:
        dependents = deps_raw.get("by_target") or {}
    else:
        dependents = deps_raw if isinstance(deps_raw, dict) else {}

    depgraph_index: dict[str, dict] = {}
    for nf in nodes_dir.rglob("*.json"):
        if nf.name.startswith("_") or any(p.startswith("_") for p in nf.parts):
            continue
        try:
            d = json.loads(nf.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = d.get("id")
        if nid:
            depgraph_index[nid] = d

    return RollupInputs(depgraph_index=depgraph_index, dependents_index=dependents)


def _entry_from_node(node: dict, *, direct: bool, via: tuple[str, ...]) -> Entry:
    src = node.get("source") or {}
    repo = src.get("repo", "")
    rel = src.get("path", "")
    kind = node.get("kind", "")
    # Pretty title per spec § "Row anatomy":
    #   endpoint  → "METHOD /path"
    #   default   → signature.name or node title
    if kind == "endpoint":
        sig = node.get("signature") or {}
        method = sig.get("method", "")
        path = sig.get("path", "")
        title = f"{method} {path}".strip() or node.get("title", node["id"])
    else:
        title = node.get("title") or (node.get("signature") or {}).get("name") or node["id"]
    return Entry(
        id=node["id"],
        title=title,
        path=f"{repo}/{rel}" if rel else repo,
        repo=repo,
        kind=kind,
        direct=direct,
        via=via,
    )
