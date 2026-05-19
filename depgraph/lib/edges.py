"""Edge taxonomy for the layered depgraph (schema v2).

Edges live embedded on each primitive's `edges_out`. Reconcile builds
the reverse index (`by_target.json`).
"""
from __future__ import annotations

from enum import Enum
from typing import Any


# Filenames for the two indexes written under `nodes/_index/`. The reverse
# index used to drift from its readers (closed #12 fixed that round of drift)
# and #66 turns the literal into a single source so a future rename is atomic.
# Read sites build paths like `nodes / "_index" / REVERSE_INDEX_FILENAME`
# instead of repeating the literal string.
#
# Docstrings/prose that name the file to the reader may still spell it out;
# the rule is for code that builds the path, not for documentation.
REVERSE_INDEX_FILENAME = "by_target.json"
FORWARD_INDEX_FILENAME = "by_source.json"

# Telemetry log filenames written under `<data_dir>/telemetry/`. Same shape
# as the index filenames above — writers (pre_edit_inject, post_edit_telemetry)
# and readers (Context, stats, graphui loader) used to spell the literals
# independently across depgraph and logigraph (#76). Both subsystems write
# identically-named files under their respective telemetry/ dirs, so a single
# constant is correct for both.
INJECTIONS_LOG_FILENAME = "injections.jsonl"
ACKNOWLEDGMENTS_LOG_FILENAME = "acknowledgments.jsonl"


# Valid confidence values (issue #53 Option A). The old ternary
# `exact / fuzzy / unresolved` collapsed four very different situations
# into one bucket; the taxonomy below subdivides the previously-unresolved
# bucket by *cause* so a maintainer asking "which class of gap should I
# chase first?" can answer from the data alone. `dynamic` is enumerated
# but not yet populated by any extractor pass — see the follow-up issue.
VALID_CONFIDENCES = frozenset({
    "exact",
    "fuzzy",
    "external",
    "unresolved_internal",
    "unresolved_receiver",
    "dynamic",
})


def confidence_for_external_target(target_id: str) -> str:
    """Return the appropriate non-exact/fuzzy confidence value for an
    external-shaped target id.

    This is the deterministic mapping that issue #53 Option A locks down.
    Every place where an extractor used to stamp `confidence="unresolved"`
    routes through this helper so the bucket assignment is uniform across
    Python, TypeScript, and the SQL/db_access side passes.

    Mapping:
      - `external::npm::unknown::*` / `external::pypi::unknown::*` (3- or
        4-segment, `unknown` package slot) — target should be in-corpus
        but the resolver couldn't reach it. Bug-signal bucket. Returns
        `"unresolved_internal"`.
      - `external::unresolved::<corpus-id>::...` — method-call shape
        where the extractor located the receiver class in-corpus but the
        method lookup missed (e.g. inherited method whose base class
        lives outside the corpus; resolver bug; MRO walk not yet
        implemented — see #91 (b4)). The `::` in the body after the
        `external::unresolved::` prefix is the corpus-prefix delimiter,
        so its presence is the structural signal that the receiver was
        already classified. Returns `"unresolved_internal"`.
      - `external::unresolved::<recv>.<method>` (no `::` in the body) —
        bare method-call shape where the receiver type couldn't be
        inferred (e.g. `db.query`, `conn.execute`). Returns
        `"unresolved_receiver"`.
      - `external::dynamic::<shape>::<callsite>` — runtime-only callee
        shapes (`getattr(obj, name)(...)`, `obj[key](...)`,
        `Reflect.get(...)(...)`, etc.) detected at the AST/CST level.
        Distinct from `unresolved_receiver` because the gap is
        irreducible: no static pass can close it (#90). Returns
        `"dynamic"`.
      - Everything else under `external::*` (`external::npm::<pkg>::*`,
        `external::pypi::<pkg>::*`, `external::builtins::*`, the
        synthetic `external::python-dbapi::*`, etc.) — known external
        terminal; deliberately not indexed. Returns `"external"`.

    Pass a string that does NOT start with `external::` and this helper
    returns `"external"` defensively — that input is malformed and the
    caller should never reach this branch.
    """
    if target_id.startswith("external::pypi::unknown") or target_id.startswith(
        "external::npm::unknown"
    ):
        return "unresolved_internal"
    if target_id.startswith("external::dynamic::"):
        return "dynamic"
    if target_id.startswith("external::unresolved::"):
        # #91 cheap reclassification: when the body after the prefix
        # contains `::`, the receiver was already located to an in-corpus
        # primitive id (`<repo>::<path>::<Class>.<method>` shape). Only
        # the method lookup missed — that's a resolver gap, not an
        # ambiguous-receiver gap. Route to unresolved_internal so the
        # maintainer sees the bug signal instead of it hiding in the
        # typed-receiver bucket.
        body = target_id[len("external::unresolved::"):]
        if "::" in body:
            return "unresolved_internal"
        return "unresolved_receiver"
    return "external"


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
#
# instantiates.target: same posture as extends/implements. `new ZodObject()`
# where `ZodObject` is `export const ZodObject = $constructor(...)` resolves
# to a `variable` primitive; some codebases also declare a function and
# `new` it. The extractor downgrades these to fuzzy; exact `instantiates ->
# variable` is still a taxonomy error (#88).
EDGE_KIND_RULES: dict[str, dict[str, list[str]]] = {
    "defines":      {"source": ["module", "class", "package"], "target": ["any"]},
    "extends":      {"source": ["class"], "target": ["class", "variable", "function"]},
    "implements":   {"source": ["class"], "target": ["class", "variable", "function"]},
    "calls":        {"source": ["function"], "target": ["function"]},
    "instantiates": {"source": ["function"], "target": ["class", "variable", "function"]},
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
#
# `instantiates` to a `variable` / `function` is the symmetric case (#88) —
# `new SomeConst(...)` where SomeConst is a `$constructor`-style factory
# binding. Same posture: real arrow, fuzzy confidence, exact still a bug.
_TARGET_KIND_CONFIDENCE_GATES: dict[tuple[str, str], set[str]] = {
    ("extends", "variable"): {"fuzzy"},
    ("extends", "function"): {"fuzzy"},
    ("implements", "variable"): {"fuzzy"},
    ("implements", "function"): {"fuzzy"},
    ("instantiates", "variable"): {"fuzzy"},
    ("instantiates", "function"): {"fuzzy"},
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
    if confidence not in VALID_CONFIDENCES:
        errors.append(
            f"confidence must be one of {sorted(VALID_CONFIDENCES)}, "
            f"got {confidence!r}"
        )
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
