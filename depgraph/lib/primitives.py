"""Primitive dataclass + id helpers for the layered depgraph (schema v2).

Five primitives (module, package, class, function, variable) carry uniform
metadata. Kind decisions happen elsewhere (lib/classification/).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


SCHEMA_VERSION = 2


class PrimitiveKind(str, Enum):
    MODULE = "module"
    PACKAGE = "package"
    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"


@dataclass
class Source:
    repo: str
    path: str
    language: str
    line: int
    end_line: int


@dataclass
class SignatureParameter:
    name: str
    type_annotation: str | None = None
    default: str | None = None


@dataclass
class Signature:
    """Shape of a primitive's "callable surface" — what hashing should
    treat as identity-defining beyond name + body. Fields are optional
    so different primitive kinds use the relevant subset:

    Functions: parameters, return_type, is_async, decorators
    Variables: type_annotation, value_text
    Classes (host language): decorators, bases
    Schema (SQL-sourced) classes additionally: primary_key, foreign_keys,
      indexes — structurally identity-defining for a table.
    """
    parameters: list[SignatureParameter] = field(default_factory=list)
    return_type: str | None = None
    is_async: bool = False
    decorators: list[str] = field(default_factory=list)
    # Variable-specific
    type_annotation: str | None = None
    value_text: str | None = None
    # Class-specific
    bases: list[str] = field(default_factory=list)
    # Schema-class-specific (SQL extractor)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[dict] = field(default_factory=list)
    indexes: list[dict] = field(default_factory=list)


@dataclass
class Attributes:
    """Boolean / metadata flags that don't define identity. Extra
    schema-specific fields (nullable, default, primary_key on column
    variables; defined_by on table classes) are allowed at runtime — the
    dataclass enumerates the canonical fields only."""
    abstract: bool = False
    generated: bool = False
    external: bool = False
    template_parameters: list[str] = field(default_factory=list)
    macro: bool = False
    mutable: bool = True
    instantiable: bool = True
    inheritable: bool = True
    # Variable-specific extensions on column primitives:
    #   nullable: bool
    #   default: str | None
    #   primary_key: bool
    # Table-specific:
    #   defined_by: list[str]


@dataclass
class Edge:
    target: str
    kind: str
    via: str
    where: str
    # See depgraph.lib.edges.VALID_CONFIDENCES for the full enum. Issue
    # #53 Option A subdivided the previously-ternary value into
    # `exact / fuzzy / external / unresolved_internal / unresolved_receiver / dynamic`.
    confidence: str


# NOTE on dataclasses vs dicts:
# The dataclasses above document the wire-format shape. At runtime,
# extractors emit *dicts*, not dataclass instances — JSON serialization
# and language-bridge compatibility stay simple that way. The dataclasses
# are consumed by validate_primitive / validate_edge (which operate on
# dicts), and by human readers who want a single place to see the schema.


@dataclass
class Primitive:
    id: str
    primitive: PrimitiveKind
    name: str
    owner: str | None
    source: Source
    signature: Signature
    attributes: Attributes
    edges_out: list[Edge]
    structural_hash: str
    kind: str | None
    extractor: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = SCHEMA_VERSION
        d["primitive"] = self.primitive.value
        return d


def canonical_id(repo: str, path: str, symbol: str) -> str:
    """`<repo>::<path>::<symbol>`. Methods use `Class.method` for symbol."""
    return f"{repo}::{path}::{symbol}"


def external_terminal(*, ecosystem: str, package: str | None = None, symbol: str) -> str:
    """Canonical external-terminal id.

    Format: `external::<ecosystem>::[<package>::]<symbol>`. The package
    segment is omitted when None or empty — for ecosystems that aren't
    package-organized (Python DB-API; the synthetic "unresolved"
    ecosystem; vendored code) the 3-segment form is canonical.

    Examples:
      external::pypi::sqlalchemy::DeclarativeBase    (4-segment)
      external::npm::react::useState                  (4-segment)
      external::python-dbapi::Cursor.execute          (3-segment, no package)
      external::unresolved::Foo                       (3-segment, no package)

    Use the `unresolved` ecosystem when import resolution failed and you
    know only the surface name.
    """
    if package:
        return f"external::{ecosystem}::{package}::{symbol}"
    return f"external::{ecosystem}::{symbol}"


def is_external_terminal(node_id: str) -> bool:
    return node_id.startswith("external::")


def slugify_id_for_filename(node_id: str) -> str:
    """Filename-safe slug. Mirrors the per-language slugify so reconcile
    can detect cross-language collisions without coupling to extractor code.

    The bare slug normalizes `::` to `__` and rewrites any other
    non-`[a-zA-Z0-9_]` char to `_`. That's lossy: distinct ids like
    `r::v4-mini` vs `r::v4/mini`, or `pkg/m.ts` vs `pkg/m.ts::$`, all
    collapse to the same on-disk filename (#87).

    The fix: when the id contains characters outside the
    structurally-safe set `[a-zA-Z0-9_/.]` (where `::` is treated as the
    canonical id separator and pre-normalized to `__`), append a short
    stable hash of the original id. The hash is deterministic in the id
    alone (so the same id always maps to the same on-disk filename across
    regens and across writer/reader call sites), and it makes the slug
    injective by construction for any id containing `-`, `$`, space, or
    other "lossy" characters. Ids whose only special characters are `/`,
    `.`, and `::` (the overwhelming majority — a canonical
    `<repo>::<path>::<symbol>` for a Python module is `r::a/b.py::Foo`)
    keep their bare slug, so existing filenames remain unchanged for the
    common case."""
    out = node_id.replace("::", "__")
    out = "".join(c if c.isalnum() or c == "_" else "_" for c in out)
    bare = out.strip("_")
    if _slug_is_lossy(node_id):
        h = hashlib.sha1(node_id.encode("utf-8")).hexdigest()[:8]
        return f"{bare}_{h}" if bare else h
    return bare


# Chars that survive slugification without ambiguity:
#   - `a-zA-Z0-9_` pass through as themselves
#   - `:` only appears as the `::` separator (canonical id grammar);
#      pre-normalized to `__` before any other replacement
#   - `/` and `.` are structural path separators; rewriting them to `_`
#      is lossy only when *another* id reaches the same shape, which in
#      practice only happens when a sibling id uses `-` / `$` / etc. (those
#      already get a hash suffix below, so no collision can occur)
_SAFE_SLUG_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.:"
)


def _slug_is_lossy(node_id: str) -> bool:
    """True if `node_id` contains any char that would force a non-trivial
    rewrite (anything outside the safe set). Such ids get a hash suffix in
    their slug to keep the slug injective."""
    return any(c not in _SAFE_SLUG_CHARS for c in node_id)


def check_slug_collisions(primitives: list[dict]) -> list[str]:
    """Return error strings for primitives whose slugified ids collide.

    Two distinct ids that slugify to the same filename would silently
    overwrite each other on disk. Reconcile calls this once per regen
    over the full primitive list; corpora with paths containing spaces
    or unicode are the most likely to trigger.

    Duplicate ids (same id twice) are NOT flagged here — that's a
    different problem (duplicate primitives), surfaced by reconcile's
    by-id index build.
    """
    by_slug: dict[str, set[str]] = {}
    for p in primitives:
        by_slug.setdefault(slugify_id_for_filename(p["id"]), set()).add(p["id"])
    return [
        f"slug collision: ids {sorted(ids)} all slugify to {slug!r}"
        for slug, ids in by_slug.items() if len(ids) > 1
    ]


def structural_hash_payload(*, primitive: str, name: str,
                              signature: dict, body_text: str = "") -> dict:
    """Canonical structural-hash payload per spec:
      sha256 of canonicalized name + signature + scope body.

    `body_text` is the raw source text of the symbol's body — for functions
    this is the function body, for classes the class body, for variables
    the initializer expression. Including body_text means semantic changes
    (different implementation) shift the hash; pure layout / line-number
    changes also shift it, which is acceptable for v0 (the spec says scope
    body verbatim, not normalized-AST).

    The payload *shape* is identical across languages (same field names,
    same nesting). The *values* are language-specific: Python's body_text
    comes from `ast.unparse(node)` (full def + body), TS's comes from
    `getBodyText()` (just the body braces). So two equivalent functions
    in different languages produce different hashes — fine because
    primitive ids are namespaced by repo + path, so cross-language hash
    collision can't occur. The shape consistency just lets one set of
    tooling (reconcile, the auto-migration script) reason about hashes
    uniformly without per-language branches.

    Returns a dict; callers pass it to `compute_hash`.
    """
    return {"primitive": primitive, "name": name,
            "signature": signature, "body_text": body_text}


def compute_hash(payload: dict) -> str:
    import hashlib
    import json
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


_REQUIRED_FIELDS = {
    "schema_version", "id", "primitive", "name", "owner",
    "source", "signature", "attributes", "edges_out",
    "structural_hash", "kind", "extractor",
}
_VALID_PRIMITIVES = {k.value for k in PrimitiveKind}
from .edges import VALID_CONFIDENCES as _VALID_CONFIDENCES  # noqa: E402


def validate_primitive(d: dict[str, Any]) -> list[str]:
    """Return a list of validation errors. Empty = valid."""
    errors: list[str] = []
    missing = _REQUIRED_FIELDS - set(d.keys())
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
        return errors  # short-circuit; rest of validation assumes presence

    if d["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}, got {d['schema_version']!r}")
    if d["primitive"] not in _VALID_PRIMITIVES:
        errors.append(f"primitive must be one of {sorted(_VALID_PRIMITIVES)}, got {d['primitive']!r}")
    if d["primitive"] == "function" and "." in d["name"] and d["owner"] is None:
        errors.append(f"function with `.` in name must have owner set: {d['name']!r}")
    for e in d.get("edges_out", []):
        if e.get("confidence") not in _VALID_CONFIDENCES:
            errors.append(f"edge confidence must be one of {sorted(_VALID_CONFIDENCES)}, got {e.get('confidence')!r}")
    return errors
