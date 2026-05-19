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


class EdgeKind(str, Enum):
    DEFINES = "defines"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    INSTANTIATES = "instantiates"
    REFERENCES = "references"
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
EDGE_KIND_RULES: dict[str, dict[str, list[str]]] = {
    "defines":      {"source": ["module", "class", "package"], "target": ["any"]},
    "extends":      {"source": ["class"], "target": ["class"]},
    "implements":   {"source": ["class"], "target": ["class"]},
    "calls":        {"source": ["function"], "target": ["function"]},
    "instantiates": {"source": ["function"], "target": ["class"]},
    "references":   {"source": ["any"], "target": ["any"]},
    "reads":        {"source": ["function"], "target": ["variable", "class"]},
    "assigns":      {"source": ["function"], "target": ["variable"]},
    "decorates":    {"source": ["function", "class", "variable"],
                     "target": ["function", "class"]},
    "includes":     {"source": ["module"], "target": ["module"]},
    "imports":      {"source": ["module"], "target": ["module", "class", "function", "variable"]},
    "tests":        {"source": ["function"], "target": ["function", "class", "variable"]},
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
    if (tk := edge.get("target_kind")) and "any" not in rules["target"] and tk not in rules["target"]:
        errors.append(f"edge {kind!r} disallows target kind {tk!r}; allowed: {rules['target']}")
    if edge.get("confidence") not in {"exact", "fuzzy", "unresolved"}:
        errors.append(f"confidence must be exact|fuzzy|unresolved, got {edge.get('confidence')!r}")
    return errors
