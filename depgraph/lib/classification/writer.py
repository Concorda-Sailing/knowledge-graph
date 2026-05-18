"""Classification writer — persists classified primitives to kind-dirs.

After `classify_corpus` runs, each primitive lands in one of two buckets:
  - kind was assigned: written to `nodes/<kind_dir>/<slug>.json` with `kind`
    and `classification` fields filled in.
  - no kind assigned: written to `nodes/<primitive_type_dir>/<slug>.json`
    unchanged (kind field left as-is from the primitive dict).

Output is bit-stable: json.dumps with indent=2 and sort_keys=True.
The Phase-6 determinism gate hashes these files and compares across runs.
"""
from __future__ import annotations

import json
from pathlib import Path

from depgraph.lib.primitives import slugify_id_for_filename


_KIND_DIRS: dict[str, str] = {
    "component": "components",
    "hook": "hooks",
    "endpoint": "endpoints",
    "service": "services",
    "model": "models",
    "schema": "schemas",
    "test": "tests",
    "util": "utils",
    "route_call": "route_calls",
}

_PRIMITIVE_DIRS: dict[str, str] = {
    "module": "modules",
    "package": "packages",
    "class": "classes",
    "function": "functions",
    "variable": "variables",
}


def _kind_dir_for(primitive: dict, decision_kind: str | None) -> str:
    """Return the bucket directory name a primitive lands in: classified kind
    takes precedence, else falls back to the primitive type."""
    if decision_kind is not None:
        return _KIND_DIRS[decision_kind]
    return _PRIMITIVE_DIRS[primitive["primitive"]]


def dossier_rel_path_for(primitive: dict, decision_kind: str | None = None) -> str:
    """Canonical relative dossier path for a primitive.

    Mirrors the node-file layout: a primitive that lands at
    `nodes/<dir>/<slug>.json` carries a dossier at `dossiers/<dir>/<slug>.md`."""
    bucket = _kind_dir_for(primitive, decision_kind)
    slug = slugify_id_for_filename(primitive["id"])
    return f"dossiers/{bucket}/{slug}.md"


def write_classified(primitives: list[dict], decisions: dict, *, data_dir: Path) -> None:
    """Write each primitive to the appropriate kind or primitive-type directory.

    `kind` is the unified taxonomy slot — for classified nodes it's the
    classifier's verdict (component / hook / endpoint / service / model /
    schema / test / util); for nodes no classifier touched, it defaults to
    the primitive type (module / package / class / function / variable).
    Consumers can always read `node["kind"]`; `primitive` stays on the
    record as the AST-shape source of truth that classified kinds layer
    on top of.

    Args:
        primitives: list of primitive dicts (schema v2).
        decisions: dict[str, Decision] returned by classify_corpus.
        data_dir: root output directory (e.g. the project's data/ folder).
    """
    for p in primitives:
        decision = decisions.get(p["id"])
        if decision and decision.kind is not None:
            kind_dir = _KIND_DIRS[decision.kind]
            p_out = dict(p,
                         kind=decision.kind,
                         classification={
                             "rule": decision.rule,
                             "evidence": decision.evidence,
                             "conflicts": decision.conflicts,
                         })
        else:
            kind_dir = _PRIMITIVE_DIRS[p["primitive"]]
            # Default unclassified nodes' kind to their primitive type so
            # every node carries a non-null kind. Preserve any kind the
            # extractor set directly (e.g. SQL schema primitives).
            p_out = p if p.get("kind") else dict(p, kind=p["primitive"])

        slug = slugify_id_for_filename(p["id"])
        target = data_dir / "nodes" / kind_dir / f"{slug}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(p_out, indent=2, sort_keys=True))
