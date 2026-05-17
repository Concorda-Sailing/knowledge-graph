"""Classification engine — runs per-kind rules over (primitives + edges).

Each classifier module exports `classify(primitives, *, by_source, by_target,
config, decisions_so_far) -> dict[str, dict]`. Engine merges decisions;
conflicts are recorded but not silently resolved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import component, hook, endpoint, service, model, util, test_kind
from .config import default_config, ClassificationConfig


@dataclass
class Decision:
    kind: str | None
    rule: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


_CLASSIFIERS = [
    test_kind,        # run first; tests rarely conflict
    hook,             # hook before component (use<Cap> overlaps with PascalCase aliases)
    component,
    endpoint,
    model,
    service,          # service requires endpoint set computed first
    util,             # util is last; relies on other classifications
]


def _build_edge_indexes(primitives: list[dict]) -> tuple[dict, dict]:
    by_source: dict[str, list[dict]] = {}
    by_target: dict[str, list[dict]] = {}
    for p in primitives:
        for e in p.get("edges_out", []):
            by_source.setdefault(p["id"], []).append(e)
            by_target.setdefault(e["target"], []).append({**e, "source": p["id"]})
    return by_source, by_target


def classify_corpus(primitives: list[dict],
                    config: ClassificationConfig | None = None) -> dict[str, Decision]:
    config = config or default_config()
    by_source, by_target = _build_edge_indexes(primitives)
    # Initialize from any kind already set by the extractor (e.g. SQL
    # extractor sets kind: "schema" on table primitives — that's not a
    # derived decision, it's intrinsic to the source language).
    decisions: dict[str, Decision] = {}
    for p in primitives:
        if p.get("kind"):
            decisions[p["id"]] = Decision(kind=p["kind"], rule="extractor_set",
                                           evidence=[{"reason": "kind set by extractor"}])
        else:
            decisions[p["id"]] = Decision(kind=None, rule="unclassified")

    for classifier in _CLASSIFIERS:
        kind_name = classifier.KIND
        classifier_decisions = classifier.classify(
            primitives, by_source=by_source, by_target=by_target,
            config=config, decisions_so_far=decisions,
        )
        for prim_id, ev in classifier_decisions.items():
            prior = decisions[prim_id]
            if prior.kind and prior.kind != kind_name:
                prior.conflicts.append(kind_name)
            else:
                decisions[prim_id] = Decision(kind=kind_name, rule=ev["rule"],
                                              evidence=ev.get("evidence", []))
    return decisions
