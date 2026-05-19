"""Coverage caveats — first-class data for graph blind spots.

Extractors stamp `coverage_caveats: list[str]` on nodes where they know
they're missing a class of edges relevant to that node's shape. The
dossier renderer surfaces them; the dossier-draft prompt feeds them to
the LLM so drafted prose can name the gap honestly.

This module owns:
- The enum string registry (`CAVEAT_REGISTRY`) — stable, machine-
  readable identifiers with human-readable descriptions.
- The detector helpers that run during extraction.

When a future extractor closes one of these gaps (e.g., the SQLAlchemy
ORM extractor in #54), it removes the corresponding caveat from the
stamping rules; existing dossiers that mention the caveat get re-drafted
on the next dossier-rank cycle.
"""
from __future__ import annotations

from typing import Iterable


# Enum string → (short title, long description). The long description is
# what gets rendered into dossiers. Keep descriptions tight and concrete
# — they get baked into LLM prompts.
CAVEAT_REGISTRY: dict[str, tuple[str, str]] = {
    "orm_relationships_not_extracted": (
        "ORM relationships not extracted",
        "This node looks like a SQLAlchemy ORM model. `relationship(...)` "
        "calls referencing other model classes are not currently captured "
        "by the Python extractor, so semantic ORM dependencies (e.g. "
        "back-populates, lazy-loaded joins) are invisible in the graph. "
        "See issue #54.",
    ),
    "fk_references_not_extracted": (
        "Foreign-key references not extracted",
        "This node looks like a SQLAlchemy ORM model. `ForeignKey(\"table.col\")` "
        "arguments on `mapped_column` / `Column` are not currently captured by "
        "the Python extractor, so FK-based dependencies to other tables/models "
        "are invisible in the graph. See issue #54.",
    ),
    "pydantic_refs_not_extracted": (
        "Pydantic field references not extracted",
        "This node looks like a Pydantic model. Field type annotations that "
        "reference other Pydantic models (e.g. `field: OtherSchema`) are not "
        "currently emitted as graph edges, so model-to-model dependencies "
        "through the schema layer are invisible.",
    ),
    "fastapi_depends_chain_not_traced": (
        "FastAPI Depends() chain not traced",
        "This node looks like a FastAPI endpoint. `Depends(...)` arguments "
        "drive runtime dependency injection but are not currently traced as "
        "graph edges, so the dependency chain a request actually traverses "
        "is partly invisible.",
    ),
    "typed_receiver_unresolved": (
        "Method-call receiver types not inferred",
        "Many outgoing `calls` edges from this node target "
        "`external::unresolved::<receiver>.<method>` — the call's receiver "
        "type couldn't be inferred at extraction time, so the actual target "
        "method is invisible. See issue #51.",
    ),
    "test_coverage_not_modeled": (
        "Test coverage not modeled in this corpus",
        "Test files are excluded from extraction by project.toml. This "
        "node has no visible test-coverage edges; the graph cannot answer "
        "\"is this tested\" or \"which tests exercise this\". See issue #52.",
    ),
}


def caveat_description(name: str) -> str | None:
    """Return the long description for a caveat enum, or None if unknown."""
    entry = CAVEAT_REGISTRY.get(name)
    return entry[1] if entry else None


def caveat_title(name: str) -> str:
    """Return the short title for a caveat enum (falls back to the enum
    itself when unknown — keeps rendering robust if an extractor stamps
    an unregistered value)."""
    entry = CAVEAT_REGISTRY.get(name)
    return entry[0] if entry else name


# ---------------------------------------------------------------------------
# Detectors — pure functions over the primitive dict shape.
# ---------------------------------------------------------------------------

# SQLAlchemy ORM base-class names that, when extended (directly or through
# the imports table), mark a class as an ORM model. The list intentionally
# covers both the canonical 2.x form (`DeclarativeBase` / `MappedAsDataclass`)
# and the SQLAlchemy 1.x convention (`Base`, declared via `declarative_base()`).
_SQLA_BASE_NAMES = frozenset({
    "DeclarativeBase",
    "DeclarativeBaseNoMeta",
    "MappedAsDataclass",
    "Base",  # project-specific convention from `declarative_base()`
})

# Pydantic base class names.
_PYDANTIC_BASE_NAMES = frozenset({"BaseModel", "RootModel"})


def _extends_targets(primitive: dict) -> list[str]:
    """Return all `extends` edge targets for a primitive. Empty if none."""
    return [
        e.get("target") or ""
        for e in (primitive.get("edges_out") or [])
        if e.get("kind") == "extends"
    ]


def _last_segment(target: str) -> str:
    """Last `::`-separated segment of an edge target (the symbol name)."""
    return target.rsplit("::", 1)[-1] if target else ""


def _is_sqlalchemy_model(primitive: dict, all_targets_by_id: dict[str, list[str]]) -> bool:
    """A class is an ORM model if it `extends` a SQLAlchemy base directly
    or transitively. Walks the in-corpus inheritance chain by following
    `extends` edges through the primitives map; bottoms out either at a
    SQLAlchemy base name or at a chain step the resolver couldn't follow
    (in which case we say no — false-positives are worse than misses
    when a caveat would mislead the reader)."""
    if primitive.get("primitive") != "class":
        return False
    visited: set[str] = set()
    frontier = list(_extends_targets(primitive))
    while frontier:
        target = frontier.pop()
        if target in visited:
            continue
        visited.add(target)
        if _last_segment(target) in _SQLA_BASE_NAMES:
            return True
        # In-corpus extension — follow further extends.
        next_targets = all_targets_by_id.get(target)
        if next_targets:
            frontier.extend(next_targets)
    return False


def _is_pydantic_model(primitive: dict, all_targets_by_id: dict[str, list[str]]) -> bool:
    if primitive.get("primitive") != "class":
        return False
    visited: set[str] = set()
    frontier = list(_extends_targets(primitive))
    while frontier:
        target = frontier.pop()
        if target in visited:
            continue
        visited.add(target)
        if _last_segment(target) in _PYDANTIC_BASE_NAMES:
            return True
        next_targets = all_targets_by_id.get(target)
        if next_targets:
            frontier.extend(next_targets)
    return False


def _is_fastapi_endpoint(primitive: dict) -> bool:
    """A function with a route shape on its signature is a FastAPI / Flask
    endpoint (the Python extractor stamps `method`/`path` on functions
    whose decorator matches `<x>.<verb>(<path>)`)."""
    if primitive.get("primitive") != "function":
        return False
    sig = primitive.get("signature") or {}
    return bool(sig.get("method") and sig.get("path"))


def stamp_caveats(primitives: list[dict]) -> int:
    """Run all detector predicates over `primitives` and mutate each node
    by setting `coverage_caveats: list[str]` where any caveat applies.

    Idempotent: re-running on a corpus that already has caveats stamped
    produces the same list (sorted, deduplicated).

    Returns: the number of primitives that ended up with at least one
    caveat. Used by regen to report a one-line summary.
    """
    # Build an `extends`-targets lookup once so each detector can chase
    # the inheritance chain without rescanning.
    by_id: dict[str, list[str]] = {
        p["id"]: _extends_targets(p) for p in primitives if "id" in p
    }

    stamped_count = 0
    for p in primitives:
        caveats: set[str] = set(p.get("coverage_caveats") or [])
        if _is_sqlalchemy_model(p, by_id):
            caveats.add("orm_relationships_not_extracted")
            caveats.add("fk_references_not_extracted")
        if _is_pydantic_model(p, by_id):
            caveats.add("pydantic_refs_not_extracted")
        if _is_fastapi_endpoint(p):
            caveats.add("fastapi_depends_chain_not_traced")
        if caveats:
            p["coverage_caveats"] = sorted(caveats)
            stamped_count += 1
    return stamped_count


def aggregate_caveat_counts(primitives: Iterable[dict]) -> dict[str, int]:
    """Corpus-wide histogram of caveat enum → node count. Used by
    `depgraph health` to surface the "what is this graph blind to" view."""
    counts: dict[str, int] = {}
    for p in primitives:
        for c in p.get("coverage_caveats") or []:
            counts[c] = counts.get(c, 0) + 1
    return counts
