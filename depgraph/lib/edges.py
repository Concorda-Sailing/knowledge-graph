"""Edge taxonomy for the layered depgraph (schema v2).

Edges live embedded on each primitive's `edges_out`. Reconcile builds
the reverse index (`by_target.json`).
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class EdgeKind(str, Enum):
    DEFINES = "defines"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    INSTANTIATES = "instantiates"
    REFERENCES = "references"
    # SQLAlchemy ORM seams (#54). `references_orm` is the
    # `relationship(...)` edge; `references_table` is the
    # `ForeignKey("table.col")` edge whose target is the class that
    # owns the named `__tablename__`. Both run class -> class because
    # the relevant target in the corpus is the model class, not the
    # raw table primitive (which doesn't exist in v2 yet).
    REFERENCES_ORM = "references_orm"
    REFERENCES_TABLE = "references_table"
    READS = "reads"
    ASSIGNS = "assigns"
    DECORATES = "decorates"
    INCLUDES = "includes"
    IMPORTS = "imports"
    TESTS = "tests"


ALL_EDGE_KINDS = {k.value for k in EdgeKind}

# Per spec table at line 213+. {kind: {source: [allowed], target: [allowed]}}.
# Allowed values: module / package / class / function / variable / any.
#
# decorates.source includes `variable` because the framework-style
# decorator-method-call pattern is extremely common in real codebases:
# `@router.get("/x")` (FastAPI), `@app.route("/x")` (Flask), `@admin.register(X)`
# (Django), `@click.command()` — the syntactic source is a module-level
# variable, and the actual decorator is the method-call result. Extractors
# anchor the edge to the variable because the call-expression itself has no
# node. See #30.
#
# reads.target includes `class` because in JS/TS (and Python to a lesser
# extent) a class binding is a runtime value — React Context objects
# (`createContext()`), Symbol-like sentinels, and bare class references
# passed to `useContext` / `getattr` / etc. show up as reads of a value
# whose primitive happens to be `class`. The structural-primitive
# distinction (class declaration vs const binding) doesn't constrain
# runtime usage.
#
# extends.target / implements.target: structurally a `class`, but real TS
# codebases routinely bind classes as const factories (`const ZodType =
# createZodType(...)`, Vue's `defineComponent`, mixins, etc.). The TS
# extractor classifies these as `variable` primitives — correctly, from a
# static-binding view. When the inheritance arrow resolves to such a
# binding, the extractor downgrades the edge to `confidence: "fuzzy"`. We
# permit `variable` / `function` targets ONLY at fuzzy confidence; exact
# `extends -> variable` is still a taxonomy error (#86).
EDGE_KIND_RULES: dict[str, dict[str, list[str]]] = {
    "defines":      {"source": ["module", "class", "package"], "target": ["any"]},
    "extends":      {"source": ["class"], "target": ["class", "variable", "function"]},
    "implements":   {"source": ["class"], "target": ["class", "variable", "function"]},
    "calls":        {"source": ["function"], "target": ["function"]},
    "instantiates": {"source": ["function"], "target": ["class"]},
    "references":   {"source": ["any"], "target": ["any"]},
    "references_orm":   {"source": ["class"], "target": ["class"]},
    "references_table": {"source": ["class"], "target": ["class"]},
    "reads":        {"source": ["function"], "target": ["variable", "class"]},
    "assigns":      {"source": ["function"], "target": ["variable"]},
    "decorates":    {"source": ["function", "class", "variable"],
                     "target": ["function", "class"]},
    "includes":     {"source": ["module"], "target": ["module"]},
    "imports":      {"source": ["module"], "target": ["module", "class", "function", "variable"]},
    "tests":        {"source": ["function"], "target": ["function", "class", "variable"]},
}


# Edge kind/target combinations only permitted at confidence != "exact". Maps
# (kind, target_kind) -> set of confidences under which the combination is
# allowed. Anything not listed is governed solely by EDGE_KIND_RULES.
#
# `extends`/`implements` to a `variable` or `function` primitive models the
# const-factory base-class pattern (#86). The arrow is real but the
# extractor can't structurally prove it without dataflow, so we require the
# extractor to emit it as fuzzy. Exact `extends -> variable` is still a bug.
_TARGET_KIND_CONFIDENCE_GATES: dict[tuple[str, str], set[str]] = {
    ("extends", "variable"): {"fuzzy"},
    ("extends", "function"): {"fuzzy"},
    ("implements", "variable"): {"fuzzy"},
    ("implements", "function"): {"fuzzy"},
}


def validate_edge(edge: dict[str, Any]) -> list[str]:
    """Validate edge structure including source/target-kind compatibility.

    `edge` should include `source_kind` / `target_kind` (caller-supplied;
    edges on disk don't carry them since the source is known from context).
    """
    errors: list[str] = []
    kind = edge.get("kind")
    if kind not in ALL_EDGE_KINDS:
        errors.append(f"unknown edge kind: {kind!r}")
        return errors
    rules = EDGE_KIND_RULES[kind]
    if (sk := edge.get("source_kind")) and "any" not in rules["source"] and sk not in rules["source"]:
        errors.append(f"edge {kind!r} disallows source kind {sk!r}; allowed: {rules['source']}")
    tk = edge.get("target_kind")
    if tk and "any" not in rules["target"] and tk not in rules["target"]:
        errors.append(f"edge {kind!r} disallows target kind {tk!r}; allowed: {rules['target']}")
    confidence = edge.get("confidence")
    if confidence not in {"exact", "fuzzy", "unresolved"}:
        errors.append(f"confidence must be exact|fuzzy|unresolved, got {confidence!r}")
    # Confidence gate for kind/target combos that are only allowed under
    # weaker confidence — e.g. `extends -> variable` MUST be fuzzy (#86).
    if tk and isinstance(kind, str):
        allowed_confs = _TARGET_KIND_CONFIDENCE_GATES.get((kind, tk))
        if allowed_confs is not None and confidence not in allowed_confs:
            errors.append(
                f"edge {kind!r} with target kind {tk!r} requires "
                f"confidence in {sorted(allowed_confs)}, got {confidence!r}"
            )
    return errors
