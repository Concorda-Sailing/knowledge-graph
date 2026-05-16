# Depgraph Extractor Rewrite — Layered Substrate (JS/TS/Python)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the kind-aware extractors in `depgraph/extractors/generic/{typescript,python}/` with the layered substrate from `docs/superpowers/specs/2026-05-15-layered-substrate-design.md`. JS/TS and Python only. No backward compatibility. Concorda's depgraph corpus regenerates from scratch when done.

**Architecture:** Each language extractor emits the five primitives (module / package / class / function / variable) with full attribute set, no kind decisions. A separate edge layer resolves call / extends / imports / etc. A thin Layer-3 stub recognizes the SDK call patterns the classifier needs. A classification engine over (primitives + edges) writes the kind-dirs (component / hook / endpoint / service / model / util / test) the rest of the system already reads.

**Tech Stack:** ts-morph 22 (TS AST), Python stdlib `ast` (Python AST), pytest (Python tests), vitest (TS tests), TOML (language registry).

---

## Background

### Why we're doing this

The current extractors decide a node's kind during AST extraction using lexical regex (`detectors/react.ts`) and path filters (`detectors/service.ts`). The spec calls this "lexical, not structural" and lists three concrete defects: kind decisions ignore behavior, class methods/fields are invisible in TS, and third-party code is conflated with first-party code.

The layered substrate fixes all three by:

1. Making extraction emit only structural primitives, with no kind decisions.
2. Adding a documented edge taxonomy as a first-class layer.
3. Adding a system-evidence layer between code and rules.
4. Moving classification to a derived step over primitives + edges.

This plan implements layers 1–2 in full, a minimal stub of layer 3 (just what classification needs), and the classifier itself, all for TypeScript / JavaScript and Python. Other languages and the full layer-3 taxonomy stay in the spec but ship later.

### Spec resolutions baked in

- **No backward compatibility.** The pre-flip parity gate and its fixtures are deleted. Concorda's corpus regenerates from scratch when this lands.
- **Persistence:** option (a) — derived nodes (kind-dirs) are written to disk by the classifier. Primitives that don't classify into a derived kind go to `nodes/<primitive_type>/`.
- **Scope:** JS/TS/Python only. Go/Rust/C/C++/SQL/Prisma/OpenAPI/GraphQL/Protobuf and the full L3 extractor taxonomy stay deferred.

### File structure (target)

```
depgraph/
  languages.toml                                  NEW   language registry
  lib/
    primitives.py                                 NEW   dataclass + id rules
    edges.py                                      NEW   edge taxonomy + dataclass
    schema.py                                     MOD   v2 node + edge schemas
    classification/
      __init__.py                                 NEW
      engine.py                                   NEW   classifier driver
      component.py                                NEW   classifier rule
      hook.py                                     NEW
      endpoint.py                                 NEW
      service.py                                  NEW
      model.py                                    NEW
      util.py                                     NEW
      test_kind.py                                NEW   (avoids pytest name clash)
    sql/
      __init__.py                                 NEW
      parser.py                                   NEW   sqlglot wrapper → Operations
      migration.py                                NEW   Python migration file recognition + SQL string extraction
      reconcile.py                                NEW   replay ordered ops → final schema primitives
      cross_ref.py                                NEW   ORM model → schema reference post-pass
    system_stub/
      __init__.py                                 NEW
      db_access.py                                NEW   db_access edges target schema primitives
    reconcile.py                                  REW   rewritten for v2 schema
  extractors/
    typescript/                                   NEW   replaces generic/typescript
      extract.ts                                  NEW   primitives only
      edges.ts                                    NEW   edge resolution
      canonical.ts                                NEW   id + hash rules
      package.json                                MOV   from generic/typescript
      tsconfig.json                               NEW
      vitest.config.ts                            MOV
    python/                                       NEW   replaces generic/python
      __init__.py                                 NEW
      extract.py                                  NEW   primitives only
      edges.py                                    NEW   edge resolution
      canonical.py                                NEW   id + hash rules
    sql/                                          NEW   language-registry entry for standalone .sql files
      __init__.py                                 NEW
      extract.py                                  NEW   walks .sql files (no-op for Concorda; framework-correct)
    generic/                                      DEL   delete in Phase 6 cutover
  tests/
    extractors/
      test_typescript_primitives.py               NEW   shells out to ts extract
      test_python_primitives.py                   NEW   in-process
      test_typescript_edges.py                    NEW
      test_python_edges.py                        NEW
      test_pre_flip_parity.py                     DEL   Phase 0
      fixtures/
        primitives_ts/                            NEW
        primitives_py/                            NEW
        edges_ts/                                 NEW
        edges_py/                                 NEW
        pre_flip_nodes/                           DEL   Phase 0
    lib/
      test_primitives.py                          NEW
      test_edges.py                               NEW
      test_classification_engine.py               NEW
      test_classifier_component.py                NEW
      test_classifier_hook.py                     NEW
      test_classifier_endpoint.py                 NEW
      test_classifier_service.py                  NEW
      test_classifier_model.py                    NEW
      test_classifier_util.py                     NEW
      test_classifier_test_kind.py                NEW
      test_db_access.py                           NEW
      test_reconcile_v2.py                        NEW
      sql/
        test_parser.py                            NEW
        test_migration.py                         NEW
        test_reconcile.py                         NEW
        test_cross_ref.py                         NEW
        fixtures/
          migrations/                             NEW   small synthetic migrations
          orm_models/                             NEW
          schemas/                                NEW   standalone .sql fixtures (optional)
```

### Output format (target — v2 schema)

A primitive on disk:

```json
{
  "schema_version": 2,
  "id": "concorda-api::routers/events.py::create_event",
  "primitive": "function",
  "name": "create_event",
  "owner": null,
  "source": {
    "repo": "concorda-api",
    "path": "routers/events.py",
    "language": "python",
    "line": 142,
    "end_line": 178
  },
  "signature": {
    "parameters": [
      {"name": "payload", "type_annotation": "EventCreate"},
      {"name": "user", "type_annotation": "User"}
    ],
    "return_type": "Event",
    "is_async": true,
    "decorators": ["router.post"]
  },
  "attributes": {
    "abstract": false,
    "generated": false,
    "external": false,
    "template_parameters": [],
    "macro": false
  },
  "edges_out": [
    {"target": "concorda-api::routers/events.py::EventCreate", "kind": "references", "via": "type_annotation", "where": "routers/events.py:142", "confidence": "exact"},
    {"target": "concorda-api::services/events.py::create_event_service", "kind": "calls", "via": "function_call", "where": "routers/events.py:155", "confidence": "exact"}
  ],
  "structural_hash": "<sha256 of canonicalized name + signature + body>",
  "kind": null,
  "extractor": "depgraph/extractors/python/extract.py@2026-05-16"
}
```

After classification, the file moves to `nodes/endpoints/<slug>.json` and `kind` is filled in.

A classified file is identical to the primitive file plus a filled `kind` and a `classification` block:

```json
{
  "schema_version": 2,
  "id": "concorda-api::routers/events.py::create_event",
  "primitive": "function",
  "name": "create_event",
  "owner": null,
  "source": {"repo": "concorda-api", "path": "routers/events.py",
             "language": "python", "line": 142, "end_line": 178},
  "signature": {"parameters": [...], "return_type": "Event", "is_async": true,
                "decorators": ["router.post"]},
  "attributes": {...},
  "edges_out": [...],
  "structural_hash": "<sha>",
  "extractor": "depgraph/extractors/python/extract.py@2026-05-16",
  "kind": "endpoint",
  "classification": {
    "rule": "route_decorator",
    "evidence": [{"decorator": "router.post", "where": "routers/events.py:141"}],
    "conflicts": []
  }
}
```

The `...` above stands for fields shown in the prior example; they're identical between primitive and classified files.

Edges are stored embedded on each primitive's `edges_out`. Reverse index (`by_target.json`) is built by reconcile. Total source-of-truth is the per-primitive files.

**`schema_version: 2` discriminator note.** Logigraph also uses `schema_version: 2` for its own node files. The two systems disambiguate by *directory*, not by version: depgraph nodes live under `<data_dir>/depgraph/nodes/`, logigraph nodes under `<data_dir>/logigraph/nodes/`. Each tool refuses to load files outside its own root. If we ever co-locate them, the discriminator becomes a `kind_namespace` field (`"depgraph"` / `"logigraph"`); not needed for this pass.

### Phasing summary

| Phase | Goal | Tests | Wild gate | Cutover safe? |
|---|---|---|---|---|
| 0 | Foundation: schema, language registry, retire pre-flip gate, freeze legacy extractors, wild-corpus scaffold | Schema validation | 5 deterministic-component verification logs (canonical / hash / validators / collisions / registry) | Yes (legacy still works) |
| 1 | TS primitives extractor | Primitive coverage | 8 TS pathological fixtures + Claude review | Legacy still works for Python |
| 2 | Python primitives extractor | Primitive coverage | 8 Python pathological fixtures + Claude review | Legacy still works for TS until cutover |
| 3 | L2 edge resolution (TS + Python) | Per-edge-kind | 8 edge-resolution fixtures + Claude review | Phases 1+2 run together if both done |
| 4 | Schema extraction (SQL parser + migration recognition + reconciliation + ORM↔schema cross-ref + db_access targeting schemas) | Parser ops + reconciliation + cross-ref + db_access | 8 SQL/schema fixtures + Claude review | n/a |
| 5 | Classification engine | Per-kind classifier | 8 classification fixtures + Claude review | n/a |
| 6 | Cutover: graphui-compat check, reconcile + CLI wiring, kitchen-sink E2E, project.toml migration, regen Concorda, determinism, logigraph claim auto-migration | Integration + determinism + logigraph migration | Kitchen-sink (~30-file mini-project) + Claude end-to-end review | Final |

Phases 0–5 can land independently. The world only flips in Phase 6.

### Verification protocol — automated tests + Claude-reviewed wild corpus

Every phase ends with two gates, both required:

1. **Automated gate.** All unit + integration tests green (already in each task).
2. **Claude gate.** Claude (or a human reviewer) reads each fixture under `depgraph/tests/fixtures/wild/<phase>/`, predicts the expected output *before* looking at `expected.json`, then diffs prediction vs expected vs actual. Each fixture carries a `verification.md` that captures the review. A phase isn't done until every fixture's `verification.md` is current and signed `✓ verified`.

The Claude gate exists because automated tests assert "code does what the test expects" — they don't catch the case where the test contract itself was wrong from the start. Reading source + expected + actual together catches that.

#### Wild corpus layout

```
depgraph/tests/fixtures/wild/
  README.md                      # index — one line per fixture
  primitives_ts/<scenario>/
    README.md                    # 5-10 lines: what's tricky here
    src/...                      # the source files
    expected.json                # ground truth: primitives + edges + classifications
    verification.md              # reviewer's log — see template below
  primitives_py/<scenario>/...
  edges/<scenario>/...
  sql/<scenario>/...
  classification/<scenario>/...
  kitchen_sink/                  # one assembled multi-language mini-project
    README.md
    api/                         # Python + SQL migrations
    web/                         # TypeScript
    db/                          # standalone SQL
    expected.json
    verification.md
```

Each fixture is small and focused (one concern, typically <60 lines of source). Total inventory: ~5–10 fixtures per phase, ~40 across the framework plus the kitchen-sink.

#### `verification.md` template

```markdown
# Verification log: <fixture-name>

**Last reviewed:** YYYY-MM-DD by <reviewer>
**Status:** ✓ verified | ⚠ has issues: <list>

## Pre-read prediction
*Written before looking at expected.json.* What I expect this fixture to produce:

- Primitives: <list with id + kind + owner>
- Edges: <list of (source, kind, target)>
- Classifications: <list of (id, kind)>

## Prediction vs expected.json
- Matches: <count>
- Discrepancies: <list with resolution>

## Expected vs actual (from last regen)
- Matches: <count>
- Discrepancies: <list with root cause: framework bug? expected stale?>

## Notes
<anything subtle worth recording for the next reviewer>
```

#### Deterministic-component verification

Components with deterministic behavior (parsers, validators, hash functions) get an independent verification log under `depgraph/tests/verification_logs/<component>.md` — Claude exercises the component with hand-crafted boundary inputs and records what it observed. See Task 0.6 for the full list.

---

## Phase 0 — Foundation

**Goal:** Define the v2 data shapes, the language registry, and clear the deck of pre-flip artifacts so future work isn't held to retired contracts.

**Files:**
- Create: `depgraph/lib/primitives.py`
- Create: `depgraph/lib/edges.py`
- Create: `depgraph/lib/schema.py` (overwrites existing if any)
- Create: `depgraph/languages.toml`
- Delete: `depgraph/tests/extractors/test_pre_flip_parity.py`
- Delete: `depgraph/tests/extractors/fixtures/pre_flip_nodes/` (whole dir)
- Test: `depgraph/tests/lib/test_primitives.py`
- Test: `depgraph/tests/lib/test_edges.py`

### Task 0.1: Delete pre-flip parity gate

- [ ] **Step 1: Confirm the files exist before deleting**

Run: `ls depgraph/tests/extractors/test_pre_flip_parity.py depgraph/tests/extractors/fixtures/pre_flip_nodes/`
Expected: both paths listed.

- [ ] **Step 2: Delete**

```bash
git rm depgraph/tests/extractors/test_pre_flip_parity.py
git rm -r depgraph/tests/extractors/fixtures/pre_flip_nodes/
```

- [ ] **Step 3: Confirm pytest still discovers (it should — only one test file removed)**

Run: `pytest depgraph/tests --collect-only -q 2>&1 | tail -5`
Expected: collection succeeds; pre-flip tests no longer listed.

- [ ] **Step 4: Commit**

```bash
git commit -m "depgraph: retire pre-flip parity gate

Resolved 2026-05-16: no backward-compat constraint for the layered
substrate transition. Pre-flip fixtures were locking the prior
flat-extraction contract; the new model rewrites the contract.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task 0.2: Define primitive dataclass

**Files:**
- Create: `depgraph/lib/primitives.py`
- Test: `depgraph/tests/lib/test_primitives.py`

- [ ] **Step 1: Write the failing test**

```python
# depgraph/tests/lib/test_primitives.py
from depgraph.lib.primitives import (
    Primitive, PrimitiveKind, Source, Signature, Attributes,
    canonical_id, validate_primitive,
)


def test_canonical_id_top_level_function():
    assert canonical_id("concorda-api", "routers/events.py", "create_event") == \
        "concorda-api::routers/events.py::create_event"


def test_canonical_id_class_method_uses_dot():
    assert canonical_id("concorda-api", "services/users.py", "UserService.fetch") == \
        "concorda-api::services/users.py::UserService.fetch"


def test_primitive_kind_enum_values():
    assert {k.value for k in PrimitiveKind} == {"module", "package", "class", "function", "variable"}


def test_validate_primitive_accepts_minimal_function():
    p = Primitive(
        id="concorda-api::routers/events.py::create_event",
        primitive=PrimitiveKind.FUNCTION,
        name="create_event",
        owner=None,
        source=Source(repo="concorda-api", path="routers/events.py", language="python", line=10, end_line=20),
        signature=Signature(parameters=[], return_type=None, is_async=False, decorators=[]),
        attributes=Attributes(),
        edges_out=[],
        structural_hash="0" * 64,
        kind=None,
        extractor="test",
    )
    errors = validate_primitive(p.to_dict())
    assert errors == [], errors


def test_external_terminal_format():
    from depgraph.lib.primitives import external_terminal, is_external_terminal
    tid = external_terminal(ecosystem="pypi", package="sqlalchemy",
                              symbol="DeclarativeBase")
    assert tid == "external::pypi::sqlalchemy::DeclarativeBase"
    assert is_external_terminal(tid)
    assert not is_external_terminal("concorda-api::routers/events.py::create_event")


def test_structural_hash_payload_includes_body():
    from depgraph.lib.primitives import structural_hash_payload, compute_hash
    a = compute_hash(structural_hash_payload(
        primitive="function", name="f", signature={}, body_text="return 1"))
    b = compute_hash(structural_hash_payload(
        primitive="function", name="f", signature={}, body_text="return 2"))
    assert a != b, "body change must shift hash per spec"


def test_validate_primitive_rejects_method_without_owner():
    """A function with a `.` in its symbol must have owner set."""
    p_dict = {
        "schema_version": 2,
        "id": "concorda-api::services/users.py::UserService.fetch",
        "primitive": "function",
        "name": "UserService.fetch",
        "owner": None,
        "source": {"repo": "concorda-api", "path": "services/users.py", "language": "python", "line": 10, "end_line": 20},
        "signature": {"parameters": [], "return_type": None, "is_async": False, "decorators": []},
        "attributes": {},
        "edges_out": [],
        "structural_hash": "0" * 64,
        "kind": None,
        "extractor": "test",
    }
    errors = validate_primitive(p_dict)
    assert any("owner" in e for e in errors), f"expected owner-missing error, got: {errors}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest depgraph/tests/lib/test_primitives.py -v`
Expected: ImportError or collection failure (module doesn't exist).

- [ ] **Step 3: Write `depgraph/lib/primitives.py`**

```python
"""Primitive dataclass + id helpers for the layered depgraph (schema v2).

Five primitives (module, package, class, function, variable) carry uniform
metadata. Kind decisions happen elsewhere (lib/classification/).
"""
from __future__ import annotations

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


# NOTE on dataclasses vs dicts:
# The dataclasses below (Source, Signature, Attributes, Edge, Primitive)
# document the wire-format shape. At runtime, extractors emit *dicts*, not
# dataclass instances — this keeps JSON serialization and language-bridge
# (TS extractor) compatibility simple. The dataclasses are consumed by:
#   - `validate_primitive()` / `validate_edge()` (operate on dicts)
#   - human readers who want a single place to see the schema
#   - type checkers when in-process tooling (reconcile, classification)
#     wraps a dict in `Primitive(**d)` for typed access — done sparingly.
# If you find yourself reaching for `Primitive(...)` everywhere, that's a
# signal to make extractors emit instances directly and add `to_dict()`
# at serialization boundaries instead.


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
      indexes — these are in signature because they're structurally
      identity-defining for a table (two tables with the same columns but
      different FKs are not the same schema).
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
    mutable: bool = True               # for variables
    instantiable: bool = True          # for classes
    inheritable: bool = True           # for classes
    # Variable-specific (column primitives extend with these):
    #   nullable: bool
    #   default: str | None
    #   primary_key: bool
    # Table-specific:
    #   defined_by: list[str]  (paths of migrations that touched this table)


@dataclass
class Edge:
    target: str
    kind: str
    via: str
    where: str
    confidence: str   # "exact" | "fuzzy" | "unresolved"


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


def external_terminal(*, ecosystem: str, package: str, symbol: str) -> str:
    """Canonical external-terminal id.

    Format: `external::<ecosystem>::<package>::<symbol>`. Examples:
      external::pypi::sqlalchemy::DeclarativeBase
      external::npm::react::useState
      external::python-dbapi::Cursor.execute

    Use `unresolved` ecosystem when import resolution failed and we don't
    know what the target is, just its surface name:
      external::unresolved::<symbol>
    """
    return f"external::{ecosystem}::{package}::{symbol}"


def is_external_terminal(node_id: str) -> bool:
    return node_id.startswith("external::")


def slugify_id_for_filename(node_id: str) -> str:
    """Filename-safe slug. Mirrors the per-language slugify so reconcile
    can detect cross-language collisions without coupling to extractor code."""
    out = node_id.replace("::", "__")
    out = "".join(c if c.isalnum() or c == "_" else "_" for c in out)
    return out.strip("_")


def check_slug_collisions(primitives: list[dict]) -> list[str]:
    """Return error strings for primitives whose slugified ids collide.

    Two distinct ids that slugify to the same filename would silently
    overwrite each other on disk. Reconcile calls this once per regen
    over the full primitive list; corpora with paths containing spaces
    or unicode are the most likely to trigger.
    """
    by_slug: dict[str, list[str]] = {}
    for p in primitives:
        by_slug.setdefault(slugify_id_for_filename(p["id"]), []).append(p["id"])
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
    in different languages produce different hashes — that's fine because
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
_VALID_CONFIDENCES = {"exact", "fuzzy", "unresolved"}


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest depgraph/tests/lib/test_primitives.py -v`
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add depgraph/lib/primitives.py depgraph/tests/lib/test_primitives.py
git commit -m "depgraph: v2 primitive dataclass + id helpers + validator"
```

### Task 0.3: Define edge taxonomy

**Files:**
- Create: `depgraph/lib/edges.py`
- Test: `depgraph/tests/lib/test_edges.py`

- [ ] **Step 1: Write the failing test**

```python
# depgraph/tests/lib/test_edges.py
from depgraph.lib.edges import (
    EdgeKind, validate_edge, ALL_EDGE_KINDS, EDGE_KIND_RULES,
)


def test_edge_kinds_taxonomy_complete():
    expected = {
        "defines", "extends", "implements", "calls", "instantiates",
        "references", "reads", "assigns", "decorates", "includes",
        "imports", "tests",
    }
    assert {k.value for k in EdgeKind} == expected


def test_validate_edge_calls_function_to_function_ok():
    edge = {"source_kind": "function", "target_kind": "function",
            "kind": "calls", "via": "function_call",
            "where": "foo.py:1", "confidence": "exact"}
    errors = validate_edge(edge)
    assert errors == [], errors


def test_validate_edge_extends_rejects_function_source():
    edge = {"source_kind": "function", "target_kind": "class",
            "kind": "extends", "via": "class_decl",
            "where": "foo.py:1", "confidence": "exact"}
    errors = validate_edge(edge)
    assert any("source" in e for e in errors), errors


def test_edge_kind_rules_documented_for_every_kind():
    """Every EdgeKind has explicit source-kind and target-kind rules."""
    for k in EdgeKind:
        assert k.value in EDGE_KIND_RULES, f"missing rules for {k.value}"
        rules = EDGE_KIND_RULES[k.value]
        assert "source" in rules and "target" in rules
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest depgraph/tests/lib/test_edges.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `depgraph/lib/edges.py`**

```python
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
    READS = "reads"
    ASSIGNS = "assigns"
    DECORATES = "decorates"
    INCLUDES = "includes"
    IMPORTS = "imports"
    TESTS = "tests"


ALL_EDGE_KINDS = {k.value for k in EdgeKind}

# Per spec table at line 213+. {kind: {source: [allowed], target: [allowed]}}.
# Allowed values: module / package / class / function / variable / any.
EDGE_KIND_RULES: dict[str, dict[str, list[str]]] = {
    "defines":      {"source": ["module", "class", "package"], "target": ["any"]},
    "extends":      {"source": ["class"], "target": ["class"]},
    "implements":   {"source": ["class"], "target": ["class"]},
    "calls":        {"source": ["function"], "target": ["function"]},
    "instantiates": {"source": ["function"], "target": ["class"]},
    "references":   {"source": ["any"], "target": ["any"]},
    "reads":        {"source": ["function"], "target": ["variable"]},
    "assigns":      {"source": ["function"], "target": ["variable"]},
    "decorates":    {"source": ["function", "class"], "target": ["function", "class"]},
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest depgraph/tests/lib/test_edges.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add depgraph/lib/edges.py depgraph/tests/lib/test_edges.py
git commit -m "depgraph: edge taxonomy + per-kind source/target rules"
```

### Task 0.4: Define language registry

**Files:**
- Create: `depgraph/languages.toml`
- Test: `depgraph/tests/lib/test_language_registry.py`
- Create: `depgraph/lib/language_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# depgraph/tests/lib/test_language_registry.py
from pathlib import Path
from depgraph.lib.language_registry import (
    load_languages, Language,
)

FRAMEWORK_TOML = Path(__file__).resolve().parents[2] / "languages.toml"


def test_load_shipped_languages_includes_ts_py_sql():
    langs = load_languages(FRAMEWORK_TOML)
    names = {l.name for l in langs}
    assert "typescript" in names
    assert "python" in names
    assert "sql" in names


def test_typescript_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    ts = langs["typescript"]
    assert ts.extensions == [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]


def test_python_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    py = langs["python"]
    assert py.extensions == [".py"]


def test_sql_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    s = langs["sql"]
    assert s.extensions == [".sql"]


def test_extractor_path_resolves_under_framework_root():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    for name in ("typescript", "python", "sql"):
        l = langs[name]
        assert l.extractor.exists(), f"{name} extractor missing: {l.extractor}"


def test_per_project_language_adds_new_language(tmp_path):
    """A project.toml can register an entirely new language extractor."""
    project_toml = tmp_path / "project.toml"
    (tmp_path / "extract_yaml.py").touch()
    project_toml.write_text("""
[languages.yaml]
extensions = [".yaml", ".yml"]
extractor = "extract_yaml.py"
runtime = "python"
""")
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML, project_toml)}
    assert "yaml" in langs
    assert "typescript" in langs  # framework langs still present
    assert langs["yaml"].extensions == [".yaml", ".yml"]


def test_per_project_language_overrides_framework_by_name(tmp_path):
    """Project entry with the same name as a framework one replaces it."""
    project_toml = tmp_path / "project.toml"
    (tmp_path / "custom_python.py").touch()
    project_toml.write_text("""
[languages.python]
extensions = [".py", ".pyi"]
extractor = "custom_python.py"
runtime = "python"
""")
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML, project_toml)}
    py = langs["python"]
    assert py.extensions == [".py", ".pyi"]   # overridden
    assert py.extractor.name == "custom_python.py"
```

- [ ] **Step 2: Write `depgraph/languages.toml`**

```toml
# Language registry — what extractor runs against which file types.
# Per-project project.toml may add or override entries.

[languages.typescript]
extensions = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
extractor = "depgraph/extractors/typescript/extract.ts"
runtime = "node"

[languages.python]
extensions = [".py"]
extractor = "depgraph/extractors/python/extract.py"
runtime = "python"

[languages.sql]
extensions = [".sql"]
extractor = "depgraph/extractors/sql/extract.py"
runtime = "python"
```

- [ ] **Step 3: Write `depgraph/lib/language_registry.py`**

```python
"""Language registry loader. Reads languages.toml from framework + optionally
a per-project `[languages.*]` block in project.toml. Per-project entries
override framework entries by name; entirely-new languages get added."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Language:
    name: str
    extensions: list[str]
    extractor: Path
    runtime: str


def _read_languages_section(toml_path: Path, *, base_dir: Path) -> dict[str, Language]:
    data = tomllib.loads(toml_path.read_text())
    out: dict[str, Language] = {}
    for name, spec in data.get("languages", {}).items():
        out[name] = Language(
            name=name,
            extensions=list(spec["extensions"]),
            extractor=(base_dir / spec["extractor"]).resolve(),
            runtime=spec["runtime"],
        )
    return out


def load_languages(framework_toml: Path,
                    project_toml: Path | None = None) -> list[Language]:
    """Load framework languages, then merge any per-project overrides /
    additions from project_toml's `[languages.*]` section.

    `extractor` paths in framework_toml resolve relative to the framework
    root (parent of `depgraph/`). Paths in project_toml resolve relative
    to project_toml's parent.
    """
    framework_root = framework_toml.parent.parent
    merged = _read_languages_section(framework_toml, base_dir=framework_root)
    if project_toml is not None and project_toml.exists():
        project_root = project_toml.parent
        for name, lang in _read_languages_section(project_toml,
                                                    base_dir=project_root).items():
            merged[name] = lang  # project overrides framework on name collision
    return list(merged.values())
```

- [ ] **Step 4: Create extractor stubs so registry tests pass**

The registry test asserts the extractor files exist. Phase 1 / 2 fill these with real code; for now they're empty placeholders.

```bash
mkdir -p depgraph/extractors/typescript depgraph/extractors/python depgraph/extractors/sql
touch depgraph/extractors/typescript/extract.ts
touch depgraph/extractors/python/extract.py
touch depgraph/extractors/sql/extract.py
echo '"""Python extractor — implemented in Phase 2."""' > depgraph/extractors/python/__init__.py
echo '"""SQL extractor — implemented in Phase 4 (standalone .sql files; migration-embedded SQL is in depgraph/lib/sql/)."""' > depgraph/extractors/sql/__init__.py
```

- [ ] **Step 5: Run tests**

Run: `pytest depgraph/tests/lib/test_language_registry.py -v`
Expected: 5 tests pass.

- [ ] **Step 6: Commit**

```bash
git add depgraph/languages.toml depgraph/lib/language_registry.py \
        depgraph/tests/lib/test_language_registry.py \
        depgraph/extractors/typescript/extract.ts \
        depgraph/extractors/python/ depgraph/extractors/sql/
git commit -m "depgraph: v2 language registry (typescript + python + sql)"
```

### Task 0.5: Mark legacy extractors as frozen

Legacy extractors stay on disk until Phase 6 so old corpus regen still works; we just add a banner so nobody edits them by mistake.

**Files:**
- Modify: `depgraph/extractors/generic/typescript/extract.ts` (top of file)
- Modify: `depgraph/extractors/generic/python/extract.py` (top of file)

- [ ] **Step 1: Prepend freeze banner to TS extractor**

Read the first 5 lines of `depgraph/extractors/generic/typescript/extract.ts`, then add this comment block immediately after the existing copyright/imports:

```typescript
/**
 * !!! FROZEN — pending replacement by depgraph/extractors/typescript/extract.ts
 * (layered substrate, schema v2). Do not extend. See docs/superpowers/plans/
 * 2026-05-16-depgraph-extractor-rewrite.md.
 */
```

- [ ] **Step 2: Prepend freeze banner to Python extractor**

```python
# !!! FROZEN — pending replacement by depgraph/extractors/python/extract.py
# (layered substrate, schema v2). Do not extend. See
# docs/superpowers/plans/2026-05-16-depgraph-extractor-rewrite.md.
```

- [ ] **Step 3: Commit**

```bash
git add depgraph/extractors/generic/typescript/extract.ts depgraph/extractors/generic/python/extract.py
git commit -m "depgraph: freeze legacy extractors pending layered rewrite"
```

### Task 0.6: Deterministic-component verification

The deterministic helpers from Tasks 0.2–0.4 (id helpers, hash functions, validators, registry loader) have unit tests; this task adds a Claude-reviewed verification log per component that catches "the test was wrong from the start" — the reviewer (Claude) exercises each component with hand-crafted boundary inputs and writes down what it observed.

**Files:**
- Create: `depgraph/tests/verification_logs/canonical_helpers.md`
- Create: `depgraph/tests/verification_logs/structural_hash.md`
- Create: `depgraph/tests/verification_logs/validators.md`
- Create: `depgraph/tests/verification_logs/slug_collisions.md`
- Create: `depgraph/tests/verification_logs/language_registry.md`

- [ ] **Step 1: Write verification log for canonical helpers**

```markdown
# Verification log: canonical helpers
# depgraph/tests/verification_logs/canonical_helpers.md

**Last reviewed:** YYYY-MM-DD by Claude
**Components:** canonical_id, slugify_id, external_terminal, is_external_terminal

## Inputs exercised
| Input | Expected | Observed |
|---|---|---|
| canonical_id("a", "b.py", "C") | "a::b.py::C" | (fill in) |
| canonical_id("a", "b.py", "C.m") | "a::b.py::C.m" | (fill in) |
| canonical_id("repo with space", "b.py", "C") | "repo with space::b.py::C" | (fill in) |
| slugify_id("a::b/c.py::D.m") | "a__b_c_py__D_m" | (fill in) |
| slugify_id("__leading::trailing__") | "leading__trailing" | (fill in) |
| slugify_id("unicode_é_in_path") | "unicode___in_path" | (fill in — confirm '_' replacement) |
| external_terminal("pypi", "sqlalchemy", "Base") | "external::pypi::sqlalchemy::Base" | (fill in) |
| is_external_terminal("external::npm::react::useState") | True | (fill in) |
| is_external_terminal("concorda-api::routers/x.py::y") | False | (fill in) |

## Observations
- (fill in: anything surprising; e.g., does slugify collapse consecutive non-alphanumerics into a single underscore, or preserve them?)

## Status
✓ verified | ⚠ has issues: <list>
```

Run the helpers in a Python REPL (or a small scratch script) against each input row; record the observed output; mark `✓` once all match.

- [ ] **Step 2: Write verification log for structural_hash**

Exercise: same payload with different key insertion order → same hash; same name+signature with different body_text → different hash; same name+signature+body_text → same hash; nested dict with reordered inner keys → same hash. Record in `verification_logs/structural_hash.md`.

- [ ] **Step 3: Write verification log for validators**

Exercise `validate_primitive` and `validate_edge` with: minimal valid sample (no errors); each invalid variant (missing required field, wrong primitive kind, function-with-dot-no-owner, bad edge confidence, source/target kind mismatch). For each invalid case, confirm the error message names the actual problem. Record in `verification_logs/validators.md`.

- [ ] **Step 4: Write verification log for slug_collisions**

Construct two distinct ids that slugify identically (e.g., `r::a.b::x` and `r::a-b::x` both slugify to `r__a_b__x`); pass to `check_slug_collisions`; confirm flagged. Pass non-colliding set; confirm empty result. Record in `verification_logs/slug_collisions.md`.

- [ ] **Step 5: Write verification log for language_registry**

Load framework-only; load framework + per-project that adds a new language; load framework + per-project that overrides an existing language by name. For each, confirm the merged result is what would actually run when extracting. Record in `verification_logs/language_registry.md`.

- [ ] **Step 6: Commit**

```bash
git add depgraph/tests/verification_logs/
git commit -m "depgraph: Phase 0 deterministic-component verification logs"
```

### Task 0.7: Scaffold the wild corpus directory

Create the directory structure and the master index so subsequent phases can drop fixtures in without re-arguing the layout.

**Files:**
- Create: `depgraph/tests/fixtures/wild/README.md`
- Create: `depgraph/tests/fixtures/wild/{primitives_ts,primitives_py,edges,sql,classification,kitchen_sink}/.gitkeep`

- [ ] **Step 1: Write the master index**

```markdown
# Wild corpus — synthetic-pathological test fixtures

These fixtures aren't representative of any specific project. They're hand-crafted to exercise the corners of the framework — patterns that would break a naive extractor. Concorda is the framework's *first consumer*, not its test case; the wild corpus is what proves the framework correct.

## Layout

Each fixture directory contains:
- `README.md` — what's tested + why this pattern is tricky
- `src/` — source file(s); typically small (one file, <60 lines)
- `expected.json` — ground truth: primitive ids + edges + classification decisions
- `verification.md` — reviewer's log (see template in plan)

**`repo-path` convention.** The test harness passes the *fixture root* (NOT `fixture/src`) as `--repo-path`. The extractor walks recursively, so source files at `<fixture>/src/foo.ts` are emitted with path `src/foo.ts` and ids like `fixture::src/foo.ts::Bar`. This convention is identical across all phases (TS, Python, SQL). Fixture authors: write your `expected.json` ids with the `src/` prefix.

## Inventory

### Phase 1 — TS primitives (primitives_ts/)
- anonymous_zoo — default-exported anonymous functions + named function expressions
- overload_storm — function with 5 overload declarations + 1 impl; class with same
- name_collisions — same name as instance method, static method, class field, type alias
- decorator_stack — 3+ stacked decorators incl. parameterized
- generics_constraints — generic class with constrained type params + generic methods
- jsx_corners — memo + forwardRef wrapping, conditional null returns, JSX never returned
- tsconfig_paths_complex — overlapping path aliases, nested aliases
- re_export_chain — barrel → barrel → impl, 3 hops

### Phase 2 — Python primitives (primitives_py/)
- dunder_zoo — __init_subclass__, __set_name__, __class_getitem__, properties
- metaclasses — metaclass=ABCMeta, class Bar(type), dynamic __new__
- dataclass_pydantic_namedtuple — three coexisting with overlapping fields
- nested_everything — class-in-class-in-function, function-in-class-in-function
- decorator_factories — @functools.wraps-decorated, parameterized, stacked
- walrus_match_pep695 — walrus + match/case + PEP 695 generics
- if_name_main — module-level state inside if __name__ == "__main__" (should NOT extract); dynamic class via type()
- relative_dots — `from ...pkg.sub import X` (multi-level relative)

### Phase 3 — L2 edges (edges/) — 9 fixtures
- method_call_chains — client.users.get().filter().first() chained calls
- instance_passing — function takes typed param, calls method on it
- dynamic_dispatch — getattr/setattr-style calls, computed callees → unresolved
- monkey_patch — SomeClass.method = lambda — patched method exists at runtime
- circular_imports_py — A imports B imports A
- circular_imports_ts — same shape, TS
- conditional_rebinding — `if x: s = A() else: s = B(); s.do_work()` — v0 walk-order semantics produce last-assign-wins; fixture pins this (wrong-but-deterministic) behavior so a future flow-sensitive pass has a target
- decorator_target_resolution — decorator from external lib vs local
- read_assign_global — module-scope variable read in fn-A, assigned in fn-B

### Phase 4 — SQL + schema (sql/)
- multi_dialect_create — postgres SERIAL, mysql AUTO_INCREMENT, sqlite AUTOINCREMENT
- alembic_op_style — uses op.create_table instead of text()
- bare_sql_file — standalone .sql with multiple CREATE TABLE
- self_referential_fk — node.parent_id REFERENCES node(id)
- circular_fk — A → B → A
- mixed_text_and_op — migration using both text() and op.* calls
- dynamic_sql_warning — only f-string interpolated SQL → warnings, no schema
- alter_replay_chain — CREATE → ALTER ADD → ALTER TYPE → RENAME → DROP COLUMN; final state matters

### Phase 5 — Classification (classification/)
- endpoint_AND_service_conflict — route-decorated function that also does db_access
- hook_calling_hook_chain — useFoo → useBar → useState
- component_HOC_wrapped — memo(forwardRef(({...}) => <div/>))
- pseudo_test_not_test — function named test_thing outside test path + no asserts
- orphan_model — class extends Base but no __tablename__
- model_without_schema — class with __tablename__ but no matching schema primitive
- util_deep_transitive — endpoint → util A → util B → util C; all must classify
- classification_conflict_logged — function satisfying two kinds; conflict recorded

### Kitchen sink (kitchen_sink/) — structurally distinct

Unlike the per-phase fixtures above (each focused on one pattern), the kitchen-sink is a single assembled mini-project covering all kinds. It has its own internal structure (`api/`, `web/`, `db/` subdirs) instead of the standard `src/` layout, and a single `expected.json` capturing the corpus-wide kind distribution + invariants.

- ~30 files across api/, web/, db/. Distribution: 5 endpoints, 4 services, 6 utils, 2 hooks, 3 components, 8 schemas, 5 models, 4 tests. End-to-end gate before Concorda regen.
```

- [ ] **Step 2: Commit the scaffold**

```bash
mkdir -p depgraph/tests/fixtures/wild/{primitives_ts,primitives_py,edges,sql,classification}
mkdir -p depgraph/tests/fixtures/wild/kitchen_sink/{api,web,db}
for d in depgraph/tests/fixtures/wild/{primitives_ts,primitives_py,edges,sql,classification}/; do
  touch "$d.gitkeep"
done
# Kitchen-sink gets a placeholder README; Task 6.5 fills in the project.
echo "# Kitchen-sink mini-project — populated by Task 6.5" > depgraph/tests/fixtures/wild/kitchen_sink/README.md
git add depgraph/tests/fixtures/wild/
git commit -m "depgraph/tests: scaffold wild corpus directory + master index"
```

---

## Phase 1 — TypeScript Primitive Extractor

**Goal:** Walk every `.ts/.tsx/.js/.jsx/.mjs/.cjs` file in a repo and emit module / package / class / function / variable primitives. No kind decisions. Class methods and fields are first-class.

**Detection goals (each gets a test):**
1. Every source file emits a `module` primitive.
2. Every directory containing source files emits a `package` primitive.
3. `ClassDeclaration` → class primitive.
4. `InterfaceDeclaration` → class with `attributes.abstract = true` and `attributes.instantiable = false`.
5. `EnumDeclaration` → class.
6. `TypeAliasDeclaration` → class with `attributes.instantiable = false`.
7. Top-level `FunctionDeclaration` → function primitive.
8. Class `MethodDeclaration` → function primitive with `owner = <class_id>`.
9. Arrow function bound to top-level `VariableDeclaration` → function primitive.
10. Class `PropertyDeclaration` → variable primitive with `owner = <class_id>`.
11. Top-level `VariableDeclaration` (non-arrow-function) → variable primitive.
12. Object-literal API client (`export const fooApi = { method1(){}, method2: () => {} }`) → class primitive with method/variable members.
13. Generics `<T, U>` → `attributes.template_parameters = ["T", "U"]`.
14. `abstract class Foo` → `attributes.abstract = true` and `attributes.instantiable = false`.
15. `export const Foo = React.memo(...)` → primitive captured (component-classification happens later).

**Files:**
- Create: `depgraph/extractors/typescript/extract.ts`
- Create: `depgraph/extractors/typescript/canonical.ts`
- Create: `depgraph/extractors/typescript/package.json`
- Create: `depgraph/extractors/typescript/tsconfig.json`
- Move: `depgraph/extractors/typescript/vitest.config.ts` (from `generic/`)
- Test: `depgraph/tests/extractors/test_typescript_primitives.py`
- Test fixtures: `depgraph/tests/extractors/fixtures/primitives_ts/<scenario>/`

### Task 1.1: Bootstrap the new TS extractor package

- [ ] **Step 1: Write package.json**

```json
{
  "name": "@depgraph/extractor-typescript",
  "private": true,
  "type": "module",
  "scripts": {
    "extract": "tsx extract.ts",
    "test": "vitest run"
  },
  "dependencies": {
    "ts-morph": "^22.0.0"
  },
  "devDependencies": {
    "tsx": "^4.7.0",
    "typescript": "^5.3.0",
    "vitest": "^1.4.0",
    "@types/node": "^20.11.0"
  }
}
```

- [ ] **Step 2: Write tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "include": ["*.ts"]
}
```

- [ ] **Step 3: Install deps**

```bash
cd depgraph/extractors/typescript && npm install
```

Expected: `node_modules/` populated, no errors.

- [ ] **Step 4: Commit (with node_modules ignored by depgraph/.gitignore)**

```bash
git add depgraph/extractors/typescript/package.json depgraph/extractors/typescript/package-lock.json depgraph/extractors/typescript/tsconfig.json
git commit -m "depgraph/extractors/typescript: bootstrap package"
```

### Task 1.2: TS canonical helpers (id + hash)

**Files:**
- Create: `depgraph/extractors/typescript/canonical.ts`
- Test: `depgraph/extractors/typescript/canonical.test.ts`

- [ ] **Step 1: Write failing test**

```typescript
// depgraph/extractors/typescript/canonical.test.ts
import { describe, expect, it } from "vitest";
import { canonicalId, slugifyId, structuralHash } from "./canonical.js";

describe("canonical", () => {
  it("builds top-level id", () => {
    expect(canonicalId("concorda-web", "src/foo.ts", "Foo"))
      .toBe("concorda-web::src/foo.ts::Foo");
  });

  it("builds class member id with dot", () => {
    expect(canonicalId("concorda-web", "src/foo.ts", "Foo.bar"))
      .toBe("concorda-web::src/foo.ts::Foo.bar");
  });

  it("slugify replaces non-alphanumeric with underscore", () => {
    expect(slugifyId("concorda-web::src/foo.ts::Foo.bar"))
      .toBe("concorda_web__src_foo_ts__Foo_bar");
  });

  it("structuralHash is sha256 of canonical JSON", () => {
    const h = structuralHash({ name: "x", signature: { return_type: null } });
    expect(h).toMatch(/^[a-f0-9]{64}$/);
  });

  it("structuralHash is stable across key insertion order", () => {
    const a = structuralHash({ a: 1, b: 2 });
    const b = structuralHash({ b: 2, a: 1 });
    expect(a).toBe(b);
  });
});
```

- [ ] **Step 2: Run, verify fail**

Run: `cd depgraph/extractors/typescript && npx vitest run canonical.test.ts`
Expected: import resolution error or `canonical.js` not found.

- [ ] **Step 3: Write `canonical.ts`**

```typescript
import { createHash } from "node:crypto";

export function canonicalId(repo: string, path: string, symbol: string): string {
  return `${repo}::${path}::${symbol}`;
}

export function slugifyId(nodeId: string): string {
  return nodeId
    .replace(/::/g, "__")
    .replace(/[^a-zA-Z0-9_]/g, "_")
    .replace(/^_+|_+$/g, "");
}

/** sha256 of canonical-JSON (keys sorted recursively) of the payload. */
export function structuralHash(payload: unknown): string {
  return createHash("sha256").update(canonicalJSON(payload)).digest("hex");
}

function canonicalJSON(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJSON).join(",")}]`;
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalJSON(obj[k])}`).join(",")}}`;
}
```

- [ ] **Step 4: Run, verify pass**

Run: `cd depgraph/extractors/typescript && npx vitest run canonical.test.ts`
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/typescript/canonical.ts depgraph/extractors/typescript/canonical.test.ts
git commit -m "depgraph/extractors/typescript: canonical id + hash helpers"
```

### Task 1.3: First primitive — module primitive

A walk that emits one `module` primitive per source file with no other content. Lays the IO + CLI scaffold.

**Files:**
- Modify: `depgraph/extractors/typescript/extract.ts`
- Create: `depgraph/tests/extractors/test_typescript_primitives.py`
- Create: `depgraph/tests/extractors/fixtures/primitives_ts/module_only/src/hello.ts`

- [ ] **Step 1: Create fixture file**

```typescript
// depgraph/tests/extractors/fixtures/primitives_ts/module_only/src/hello.ts
// (empty content — just the file's existence)
```

The file is literally a comment. The test asserts the extractor emits one module primitive for it.

- [ ] **Step 2: Write failing Python test that shells out to the TS extractor**

```python
# depgraph/tests/extractors/test_typescript_primitives.py
"""TS primitive extractor end-to-end tests.

Each test runs the extractor against a small fixture project under
fixtures/primitives_ts/<scenario>/ and asserts on the primitive set
emitted.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "primitives_ts"
EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def run_extractor(fixture_name: str) -> list[dict]:
    """Run the extractor against the named fixture; return primitives list."""
    fixture_root = FIXTURE_DIR / fixture_name
    cmd = ["npx", "tsx", str(EXTRACTOR),
           "--repo-key", "fixture",
           "--repo-path", str(fixture_root),
           "--format", "ndjson"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=EXTRACTOR.parent, check=True)
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def test_module_primitive_for_each_source_file():
    prims = run_extractor("module_only")
    modules = [p for p in prims if p["primitive"] == "module"]
    assert len(modules) == 1
    m = modules[0]
    assert m["id"] == "fixture::src/hello.ts"
    assert m["source"]["language"] == "typescript"
    assert m["source"]["path"] == "src/hello.ts"
```

- [ ] **Step 3: Run, verify fail**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v`
Expected: extractor exits with error or produces nothing.

- [ ] **Step 4: Write minimal `extract.ts`**

```typescript
// depgraph/extractors/typescript/extract.ts
/**
 * Layered-substrate TS extractor — emits primitives only.
 * Schema v2; see docs/superpowers/specs/2026-05-15-layered-substrate-design.md.
 */
import { Project, SourceFile, SyntaxKind, Node } from "ts-morph";
import { parseArgs } from "node:util";
import { readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { canonicalId, structuralHash } from "./canonical.js";

interface Primitive {
  schema_version: 2;
  id: string;
  primitive: "module" | "package" | "class" | "function" | "variable";
  name: string;
  owner: string | null;
  source: { repo: string; path: string; language: string; line: number; end_line: number };
  signature: any;
  attributes: any;
  edges_out: any[];
  structural_hash: string;
  kind: null;
  extractor: string;
}

const EXTRACTOR_TAG = "depgraph/extractors/typescript/extract.ts@2026-05-16";
const EXTS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"];

function listSourceFiles(root: string): string[] {
  const out: string[] = [];
  function walk(dir: string) {
    for (const ent of readdirSync(dir)) {
      const p = join(dir, ent);
      const s = statSync(p);
      if (s.isDirectory()) {
        if (ent === "node_modules" || ent === ".git" || ent === "dist") continue;
        walk(p);
      } else if (EXTS.some((e) => p.endsWith(e))) {
        out.push(p);
      }
    }
  }
  walk(root);
  return out;
}

function emit(p: Primitive) {
  process.stdout.write(JSON.stringify(p) + "\n");
}

function moduleFor(sf: SourceFile, repoKey: string, repoPath: string): Primitive {
  const rel = relative(repoPath, sf.getFilePath());
  const id = `${repoKey}::${rel}`;
  return {
    schema_version: 2,
    id,
    primitive: "module",
    name: rel,
    owner: null,
    source: { repo: repoKey, path: rel, language: "typescript",
              line: 1, end_line: sf.getEndLineNumber() },
    signature: {},
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({ kind: "module", path: rel }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function main() {
  const { values } = parseArgs({
    options: {
      "repo-key": { type: "string" },
      "repo-path": { type: "string" },
      "format": { type: "string", default: "ndjson" },
    },
  });
  const repoKey = values["repo-key"];
  const repoPath = values["repo-path"];
  if (!repoKey || !repoPath) {
    console.error("Usage: extract.ts --repo-key <key> --repo-path <path>");
    process.exit(1);
  }

  const project = new Project({ skipAddingFilesFromTsConfig: true });
  for (const f of listSourceFiles(repoPath)) project.addSourceFileAtPath(f);

  for (const sf of project.getSourceFiles()) {
    emit(moduleFor(sf, repoKey, repoPath));
  }
}

main();
```

- [ ] **Step 5: Run, verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py::test_module_primitive_for_each_source_file -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/typescript/extract.ts \
        depgraph/tests/extractors/test_typescript_primitives.py \
        depgraph/tests/extractors/fixtures/primitives_ts/module_only/
git commit -m "depgraph/extractors/typescript: emit module primitives"
```

### Task 1.4: Class primitives (declaration, interface, enum, type alias)

- [ ] **Step 1: Create fixture**

```typescript
// depgraph/tests/extractors/fixtures/primitives_ts/classes/src/all.ts
export class Concrete {}
export abstract class AbstractC {}
export class Generic<T, U> {}
export interface IFoo { name: string; }
export enum Color { Red, Green, Blue }
export type Json = string | number;
```

- [ ] **Step 2: Add tests**

Append to `test_typescript_primitives.py`:

```python
def test_class_declaration():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "Concrete" in classes
    c = classes["Concrete"]
    assert c["attributes"]["abstract"] is False
    assert c["attributes"]["instantiable"] is True

def test_abstract_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    c = classes["AbstractC"]
    assert c["attributes"]["abstract"] is True
    assert c["attributes"]["instantiable"] is False

def test_class_with_generics():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert classes["Generic"]["attributes"]["template_parameters"] == ["T", "U"]

def test_interface_as_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    i = classes["IFoo"]
    assert i["attributes"]["abstract"] is True
    assert i["attributes"]["instantiable"] is False

def test_enum_as_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "Color" in classes

def test_type_alias_as_class():
    prims = run_extractor("classes")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert classes["Json"]["attributes"]["instantiable"] is False
```

- [ ] **Step 3: Run, verify failure (5 of 6 tests fail; extractor still only emits modules)**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v`
Expected: most class tests FAIL.

- [ ] **Step 4: Implement class extraction in `extract.ts`**

Add to `extract.ts` after the `moduleFor` function:

```typescript
function classPrimitive(
  node: Node,
  name: string,
  attrs: { abstract: boolean; instantiable: boolean; template_parameters: string[] },
  repoKey: string, relPath: string,
): Primitive {
  const id = canonicalId(repoKey, relPath, name);
  return {
    schema_version: 2,
    id,
    primitive: "class",
    name,
    owner: null,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature: { decorators: [] },
    attributes: { abstract: attrs.abstract, generated: false, external: false,
                  template_parameters: attrs.template_parameters, macro: false,
                  mutable: false, instantiable: attrs.instantiable, inheritable: true },
    edges_out: [],
    structural_hash: structuralHash({ kind: "class", name, attrs }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function extractClasses(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];
  for (const cls of sf.getClasses()) {
    out.push(classPrimitive(cls, cls.getName() ?? "<anonymous>", {
      abstract: cls.isAbstract(),
      instantiable: !cls.isAbstract(),
      template_parameters: cls.getTypeParameters().map((tp) => tp.getName()),
    }, repoKey, relPath));
  }
  for (const iface of sf.getInterfaces()) {
    out.push(classPrimitive(iface, iface.getName(), {
      abstract: true, instantiable: false,
      template_parameters: iface.getTypeParameters().map((tp) => tp.getName()),
    }, repoKey, relPath));
  }
  for (const en of sf.getEnums()) {
    out.push(classPrimitive(en, en.getName(), {
      abstract: false, instantiable: false, template_parameters: [],
    }, repoKey, relPath));
  }
  for (const alias of sf.getTypeAliases()) {
    out.push(classPrimitive(alias, alias.getName(), {
      abstract: false, instantiable: false,
      template_parameters: alias.getTypeParameters().map((tp) => tp.getName()),
    }, repoKey, relPath));
  }
  return out;
}
```

Then in `main()`, after `emit(moduleFor(...))`:

```typescript
for (const p of extractClasses(sf, repoKey, relative(repoPath, sf.getFilePath()))) emit(p);
```

- [ ] **Step 5: Run, verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v -k class`
Expected: all 6 class tests PASS.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/typescript/extract.ts \
        depgraph/tests/extractors/test_typescript_primitives.py \
        depgraph/tests/extractors/fixtures/primitives_ts/classes/
git commit -m "depgraph/extractors/typescript: emit class / interface / enum / type alias primitives"
```

### Task 1.5: Function primitives (top-level + method + arrow-bound + JSX detection)

Includes detection goals for: anonymous default exports (`export default function(){}`, `export default () => {}`), TS method overloads (keep only the implementation signature, not the overload stubs), and JSX-return marking for the classifier downstream.

- [ ] **Step 1: Create fixture**

```typescript
// depgraph/tests/extractors/fixtures/primitives_ts/functions/src/all.ts
export function topLevel(x: number): string { return String(x); }
export async function asyncFn() { return 1; }
export const arrow = (a: string) => a.length;
export const arrowConst: () => void = () => {};

export default function() { return 1; }   // anonymous default

export class Holder {
  method(x: number): string { return String(x); }
  async asyncMethod() {}
  static staticMethod() {}
  private privateMethod() {}

  // TS overloads: two declarations + one implementation. Only the
  // implementation should emit a primitive.
  format(x: number): string;
  format(x: string): string;
  format(x: any): string { return String(x); }

  // Same-name static + instance: must NOT collide on id.
  shared() { return "instance"; }
  static shared() { return "static"; }
}
```

```tsx
// depgraph/tests/extractors/fixtures/primitives_ts/functions/src/jsx.tsx
export function Header(): JSX.Element { return <h1>Title</h1>; }
export const Footer = () => <footer>©</footer>;
export function notAComponent(): string { return "no jsx here"; }
```

- [ ] **Step 2: Add tests**

```python
def test_top_level_function():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "topLevel" in fns
    f = fns["topLevel"]
    assert f["owner"] is None
    assert f["signature"]["is_async"] is False
    assert f["signature"]["return_type"] == "string"
    assert [p["name"] for p in f["signature"]["parameters"]] == ["x"]

def test_async_function():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert fns["asyncFn"]["signature"]["is_async"] is True

def test_arrow_function_bound_to_const():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "arrow" in fns
    assert fns["arrow"]["owner"] is None

def test_class_method_has_owner():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function" and "." in p["name"]}
    names = {p["name"] for p in fns}
    assert "Holder.method" in names
    m = next(p for p in fns if p["name"] == "Holder.method")
    assert m["owner"] == "fixture::src/all.ts::Holder"

def test_static_method_captured():
    prims = run_extractor("functions")
    names = {p["name"] for p in prims if p["primitive"] == "function"}
    assert "Holder.staticMethod" in names

def test_private_method_captured():
    prims = run_extractor("functions")
    names = {p["name"] for p in prims if p["primitive"] == "function"}
    assert "Holder.privateMethod" in names

def test_anonymous_default_export_gets_synthesized_name():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    # `export default function() {}` — no source-given name. Use module basename.
    assert "<default:all>" in fns
    assert fns["<default:all>"]["owner"] is None
    assert fns["<default:all>"]["signature"]["is_async"] is False

def test_ts_overload_stubs_skipped_only_impl_emitted():
    prims = run_extractor("functions")
    formats = [p for p in prims if p["primitive"] == "function"
               and p["name"] == "Holder.format"]
    assert len(formats) == 1, "overload stubs should be skipped; only impl emits"
    # The impl is the one with a body — return_type from the impl signature.
    assert formats[0]["signature"]["return_type"] == "string"

def test_jsx_returning_function_sets_attribute():
    prims = run_extractor("functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert fns["Header"]["signature"]["returns_jsx"] is True
    assert fns["Footer"]["signature"]["returns_jsx"] is True
    assert fns["notAComponent"]["signature"]["returns_jsx"] is False

def test_same_name_static_and_instance_method_disambiguate():
    """`shared()` and `static shared()` must produce distinct ids."""
    prims = run_extractor("functions")
    ids = {p["id"] for p in prims if p["primitive"] == "function"
           and p["owner"] == "fixture::src/all.ts::Holder"
           and p["name"].split(".")[-1].startswith("shared")}
    assert "fixture::src/all.ts::Holder.shared" in ids
    assert "fixture::src/all.ts::Holder.shared:static" in ids
    assert len(ids) == 2
```

- [ ] **Step 3: Run, verify fail**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v -k function or method`
Expected: all function/method tests FAIL.

- [ ] **Step 4: Implement function extraction**

Add to `extract.ts`:

```typescript
function bodyHasJsx(node: { getDescendantsOfKind: (k: SyntaxKind) => any[] }): boolean {
  return (
    node.getDescendantsOfKind(SyntaxKind.JsxElement).length > 0 ||
    node.getDescendantsOfKind(SyntaxKind.JsxFragment).length > 0 ||
    node.getDescendantsOfKind(SyntaxKind.JsxSelfClosingElement).length > 0
  );
}

function bodyText(node: { getBodyText?: () => string | undefined; getText: () => string }): string {
  // Functions/methods expose getBodyText(); arrow/expression bodies don't.
  return (node.getBodyText?.() ?? node.getText()) || "";
}

function functionPrimitive(
  node: { getStartLineNumber(): number; getEndLineNumber(): number },
  name: string,
  owner: string | null,
  signature: { parameters: { name: string; type_annotation: string | null }[];
               return_type: string | null;
               is_async: boolean;
               decorators: string[];
               returns_jsx: boolean },
  body: string,
  repoKey: string, relPath: string,
): Primitive {
  const symbol = owner ? `${owner.split("::").pop()}.${name}` : name;
  const id = canonicalId(repoKey, relPath, symbol);
  return {
    schema_version: 2, id, primitive: "function", name: symbol, owner,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature,
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    // Per spec: name + signature + scope body.
    structural_hash: structuralHash({ primitive: "function", name: symbol,
                                       signature, body_text: body }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function paramShape(p: any) {
  return { name: p.getName(), type_annotation: p.getTypeNode()?.getText() ?? null };
}

function moduleBasename(relPath: string): string {
  const last = relPath.split("/").pop() ?? relPath;
  const dot = last.lastIndexOf(".");
  return dot === -1 ? last : last.slice(0, dot);
}

function extractFunctions(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];

  for (const fn of sf.getFunctions()) {
    // Skip TS overload stubs (declarations without bodies). Only the
    // implementation signature gets a primitive.
    if (!fn.hasBody()) continue;
    const fnName = fn.getName() ?? `<default:${moduleBasename(relPath)}>`;
    out.push(functionPrimitive(fn, fnName, null, {
      parameters: fn.getParameters().map(paramShape),
      return_type: fn.getReturnTypeNode()?.getText() ?? null,
      is_async: fn.isAsync(),
      decorators: [],
      returns_jsx: bodyHasJsx(fn),
    }, bodyText(fn), repoKey, relPath));
  }

  for (const vs of sf.getVariableStatements()) {
    for (const decl of vs.getDeclarations()) {
      const init = decl.getInitializer();
      if (init && (Node.isArrowFunction(init) || Node.isFunctionExpression(init))) {
        out.push(functionPrimitive(decl, decl.getName(), null, {
          parameters: init.getParameters().map(paramShape),
          return_type: init.getReturnTypeNode()?.getText() ?? null,
          is_async: init.isAsync(),
          decorators: [],
          returns_jsx: bodyHasJsx(init),
        }, bodyText(init), repoKey, relPath));
      }
    }
  }

  // `export default function(){}` / `export default () => {}` are
  // ExportAssignment expressions whose expression is an anonymous fn.
  for (const ea of sf.getExportAssignments()) {
    if (ea.isExportEquals()) continue;
    const expr = ea.getExpression();
    if (Node.isFunctionExpression(expr) || Node.isArrowFunction(expr)) {
      // Already handled if its name was assigned via `export default function foo(){}`.
      if (Node.isFunctionExpression(expr) && expr.getName()) continue;
      const synthName = `<default:${moduleBasename(relPath)}>`;
      out.push(functionPrimitive(ea, synthName, null, {
        parameters: expr.getParameters().map(paramShape),
        return_type: expr.getReturnTypeNode()?.getText() ?? null,
        is_async: expr.isAsync(),
        decorators: [],
        returns_jsx: bodyHasJsx(expr),
      }, bodyText(expr), repoKey, relPath));
    }
  }

  for (const cls of sf.getClasses()) {
    const classId = canonicalId(repoKey, relPath, cls.getName() ?? "<anonymous>");
    for (const m of cls.getMethods()) {
      // Skip overload stubs on methods too.
      if (!m.hasBody()) continue;
      // TS allows same-name static + instance methods on one class. Append
      // a `:static` suffix to disambiguate ids.
      const methodLocalName = m.isStatic()
        ? `${m.getName()}:static`
        : m.getName();
      out.push(functionPrimitive(m, methodLocalName, classId, {
        parameters: m.getParameters().map(paramShape),
        return_type: m.getReturnTypeNode()?.getText() ?? null,
        is_async: m.isAsync(),
        decorators: m.getDecorators().map((d) => d.getName()),
        returns_jsx: bodyHasJsx(m),
      }, bodyText(m), repoKey, relPath));
    }
  }

  return out;
}
```

Wire it into `main()` alongside `extractClasses(...)`.

- [ ] **Step 5: Run, verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v`
Expected: all function/method tests PASS.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/typescript/extract.ts \
        depgraph/tests/extractors/test_typescript_primitives.py \
        depgraph/tests/extractors/fixtures/primitives_ts/functions/
git commit -m "depgraph/extractors/typescript: emit function primitives incl. methods + arrow-bound"
```

### Task 1.6: Variable primitives (top-level + class field)

- [ ] **Step 1: Create fixture**

```typescript
// depgraph/tests/extractors/fixtures/primitives_ts/variables/src/all.ts
export const PI = 3.14;
export let counter = 0;
export const config: Record<string, string> = {};

export class Settings {
  static readonly VERSION = "1.0";
  private debug: boolean = false;
  publicProp: string;
}
```

- [ ] **Step 2: Add tests**

```python
def test_top_level_const_variable():
    prims = run_extractor("variables")
    vars_ = {p["name"]: p for p in prims if p["primitive"] == "variable"}
    assert "PI" in vars_
    assert vars_["PI"]["attributes"]["mutable"] is False

def test_top_level_let_variable():
    prims = run_extractor("variables")
    vars_ = {p["name"]: p for p in prims if p["primitive"] == "variable"}
    assert vars_["counter"]["attributes"]["mutable"] is True

def test_arrow_function_const_is_function_not_variable():
    """`const x = () => 1` should be function, not variable."""
    prims = run_extractor("functions")
    primitives_by_name = {p["name"]: p["primitive"] for p in prims}
    assert primitives_by_name.get("arrow") == "function"

def test_class_field_has_owner():
    prims = run_extractor("variables")
    fields = [p for p in prims if p["primitive"] == "variable" and p["owner"] is not None]
    names = {p["name"] for p in fields}
    assert "Settings.VERSION" in names
    assert "Settings.debug" in names
    assert "Settings.publicProp" in names
```

- [ ] **Step 3: Run, verify fail**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v -k variable`
Expected: FAIL (extractor doesn't emit variables yet).

- [ ] **Step 4: Implement variable extraction**

Add to `extract.ts`:

```typescript
function variablePrimitive(
  node: { getStartLineNumber(): number; getEndLineNumber(): number },
  name: string, owner: string | null, mutable: boolean,
  type_annotation: string | null,
  value_text: string | null,
  repoKey: string, relPath: string,
): Primitive {
  const symbol = owner ? `${owner.split("::").pop()}.${name}` : name;
  const signature = { type_annotation, value_text };
  return {
    schema_version: 2, id: canonicalId(repoKey, relPath, symbol),
    primitive: "variable", name: symbol, owner,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature,
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable,
                  instantiable: false, inheritable: false },
    edges_out: [],
    // Per spec: name + signature + scope body. For a variable the "body"
    // is its initializer expression. Same payload shape as Python.
    structural_hash: structuralHash({
      primitive: "variable", name: symbol,
      signature, body_text: value_text ?? "",
    }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function extractVariables(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];

  for (const vs of sf.getVariableStatements()) {
    const declKind = vs.getDeclarationKind();  // "const" | "let" | "var"
    for (const decl of vs.getDeclarations()) {
      const init = decl.getInitializer();
      if (init && (Node.isArrowFunction(init) || Node.isFunctionExpression(init))) continue;
      out.push(variablePrimitive(decl, decl.getName(), null,
        declKind !== "const",
        decl.getTypeNode()?.getText() ?? null,
        init?.getText() ?? null,
        repoKey, relPath));
    }
  }

  for (const cls of sf.getClasses()) {
    const classId = canonicalId(repoKey, relPath, cls.getName() ?? "<anonymous>");
    for (const prop of cls.getProperties()) {
      out.push(variablePrimitive(prop, prop.getName(), classId,
        !prop.isReadonly(),
        prop.getTypeNode()?.getText() ?? null,
        prop.getInitializer()?.getText() ?? null,
        repoKey, relPath));
    }
  }

  return out;
}
```

Wire into `main()`.

- [ ] **Step 5: Run, verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v`
Expected: all variable tests PASS, prior tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/typescript/extract.ts \
        depgraph/tests/extractors/test_typescript_primitives.py \
        depgraph/tests/extractors/fixtures/primitives_ts/variables/
git commit -m "depgraph/extractors/typescript: emit variable primitives incl. class fields"
```

### Task 1.7: Package primitives + object-literal API client classes

- [ ] **Step 1: Create fixture**

```typescript
// depgraph/tests/extractors/fixtures/primitives_ts/object_api_client/src/lib/users-api.ts
export const usersApi = {
  fetch(id: string) { return id; },
  create: (name: string) => ({ name }),
  endpoint: "/users",
};
```

- [ ] **Step 2: Add tests**

```python
def test_package_primitive_per_dir_with_sources():
    prims = run_extractor("object_api_client")
    pkgs = {p["name"]: p for p in prims if p["primitive"] == "package"}
    # Expect packages for "src" and "src/lib"
    assert "src" in pkgs
    assert "src/lib" in pkgs

def test_object_literal_api_client_emits_class_and_members():
    prims = run_extractor("object_api_client")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "usersApi" in classes
    fns = {p["name"] for p in prims if p["primitive"] == "function" and p["owner"]}
    assert "usersApi.fetch" in fns
    assert "usersApi.create" in fns
    vars_ = {p["name"] for p in prims if p["primitive"] == "variable" and p["owner"]}
    assert "usersApi.endpoint" in vars_
```

- [ ] **Step 3: Run, verify fail**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v -k package or api_client`
Expected: FAIL.

- [ ] **Step 4: Implement package + object-literal handling**

Add to `extract.ts`:

```typescript
function packagePrimitives(sourceFiles: SourceFile[], repoKey: string, repoPath: string): Primitive[] {
  const dirs = new Set<string>();
  for (const sf of sourceFiles) {
    let rel = relative(repoPath, sf.getFilePath());
    let dir = rel.includes("/") ? rel.substring(0, rel.lastIndexOf("/")) : "";
    while (dir) {
      dirs.add(dir);
      dir = dir.includes("/") ? dir.substring(0, dir.lastIndexOf("/")) : "";
    }
    if (dirs.has("")) dirs.delete("");
  }
  return [...dirs].sort().map((d) => ({
    schema_version: 2 as const,
    id: `${repoKey}::${d}`,
    primitive: "package",
    name: d,
    owner: null,
    source: { repo: repoKey, path: d, language: "typescript", line: 0, end_line: 0 },
    signature: {},
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({ kind: "package", path: d }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  }));
}

function extractObjectLiteralApiClients(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];
  for (const vs of sf.getVariableStatements()) {
    for (const decl of vs.getDeclarations()) {
      const init = decl.getInitializer();
      if (!init || !Node.isObjectLiteralExpression(init)) continue;
      const className = decl.getName();
      const classId = canonicalId(repoKey, relPath, className);
      out.push({
        schema_version: 2, id: classId, primitive: "class",
        name: className, owner: null,
        source: { repo: repoKey, path: relPath, language: "typescript",
                  line: decl.getStartLineNumber(), end_line: decl.getEndLineNumber() },
        signature: {},
        attributes: { abstract: false, generated: false, external: false,
                      template_parameters: [], macro: false, mutable: false,
                      instantiable: true, inheritable: false },
        edges_out: [],
        structural_hash: structuralHash({ kind: "class", name: className, object_literal: true }),
        kind: null,
        extractor: EXTRACTOR_TAG,
      });

      for (const prop of init.getProperties()) {
        if (Node.isMethodDeclaration(prop) || (Node.isPropertyAssignment(prop) &&
            (Node.isArrowFunction(prop.getInitializer()!) || Node.isFunctionExpression(prop.getInitializer()!)))) {
          const isMethod = Node.isMethodDeclaration(prop);
          const memberName = isMethod ? prop.getName() : (prop as any).getName();
          const fnNode: any = isMethod ? prop : (prop as any).getInitializer()!;
          out.push(functionPrimitive(fnNode, memberName, classId, {
            parameters: fnNode.getParameters().map(paramShape),
            return_type: fnNode.getReturnTypeNode?.()?.getText() ?? null,
            is_async: fnNode.isAsync?.() ?? false,
            decorators: [],
            returns_jsx: bodyHasJsx(fnNode),
          }, bodyText(fnNode), repoKey, relPath));
        } else if (Node.isPropertyAssignment(prop)) {
          // Plain property: `endpoint: "/users"` etc. Capture the RHS
          // text so cross-language clients of structural_hash see the
          // value, matching Python's value_text convention.
          const initText = (prop as any).getInitializer()?.getText() ?? null;
          out.push(variablePrimitive(prop, prop.getName(), classId, true,
            null, initText, repoKey, relPath));
        }
      }
    }
  }
  return out;
}
```

Wire into `main()`.

- [ ] **Step 5: Run, verify pass**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/typescript/extract.ts \
        depgraph/tests/extractors/test_typescript_primitives.py \
        depgraph/tests/extractors/fixtures/primitives_ts/object_api_client/
git commit -m "depgraph/extractors/typescript: emit package primitives + object-literal API client classes"
```

### Task 1.8: Sweep test — every primitive validates against the schema

- [ ] **Step 1: Add a final round-trip test**

```python
# in test_typescript_primitives.py
from depgraph.lib.primitives import validate_primitive

def test_all_emitted_primitives_validate():
    for scenario in ("module_only", "classes", "functions", "variables", "object_api_client"):
        prims = run_extractor(scenario)
        for p in prims:
            errors = validate_primitive(p)
            assert not errors, f"{scenario}/{p.get('id')}: {errors}"
```

- [ ] **Step 2: Run**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v`
Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add depgraph/tests/extractors/test_typescript_primitives.py
git commit -m "depgraph/extractors/typescript: schema validation gate for all emitted primitives"
```

### Task 1.9: Author wild fixtures + Claude verification

The 8 wild fixtures for Phase 1 land here, each authored as a deliberately-awkward minimal project. Each gets an `expected.json` and a `verification.md` that the reviewer fills in before the phase closes.

**Files:**
- Create: `depgraph/tests/fixtures/wild/primitives_ts/{anonymous_zoo,overload_storm,name_collisions,decorator_stack,generics_constraints,jsx_corners,tsconfig_paths_complex,re_export_chain}/`
  - Each with `README.md`, `src/`, `expected.json`, `verification.md`
- Create: `depgraph/tests/extractors/test_typescript_wild.py`

- [ ] **Step 1: Author the 8 fixtures**

For each fixture, write the README first (what's tricky), then craft `src/` to exercise exactly that, then hand-compute `expected.json`. Example for `anonymous_zoo`:

```markdown
<!-- depgraph/tests/fixtures/wild/primitives_ts/anonymous_zoo/README.md -->
# anonymous_zoo

Default-exported anonymous functions, named function expressions, and
arrow-vs-function distinction. Naive extractors that filter on
`fn.getName()` drop these silently; the extractor must synthesize a
stable name (`<default:<modulebasename>>`) or use the surrounding
binding.
```

```typescript
// depgraph/tests/fixtures/wild/primitives_ts/anonymous_zoo/src/a.ts
export default function() { return 1; }   // anonymous default

// named function expression — `inner` visible inside the body only
export const aliased = function inner(n: number): number {
  return n > 0 ? inner(n - 1) : 0;
};

// arrow expression
export const arrow = (s: string) => s.length;
```

```json
// depgraph/tests/fixtures/wild/primitives_ts/anonymous_zoo/expected.json
{
  "primitives": [
    {"id": "fixture::src/a.ts", "primitive": "module", "name": "src/a.ts", "owner": null},
    {"id": "fixture::src/a.ts::<default:a>", "primitive": "function",
     "name": "<default:a>", "owner": null},
    {"id": "fixture::src/a.ts::aliased", "primitive": "function",
     "name": "aliased", "owner": null},
    {"id": "fixture::src/a.ts::arrow", "primitive": "function",
     "name": "arrow", "owner": null}
  ],
  "edges": [
    {"source": "fixture::src/a.ts", "kind": "defines",
     "target": "fixture::src/a.ts::<default:a>"},
    {"source": "fixture::src/a.ts", "kind": "defines",
     "target": "fixture::src/a.ts::aliased"},
    {"source": "fixture::src/a.ts", "kind": "defines",
     "target": "fixture::src/a.ts::arrow"}
  ]
}
```

```markdown
<!-- depgraph/tests/fixtures/wild/primitives_ts/anonymous_zoo/verification.md -->
# Verification log: anonymous_zoo

**Last reviewed:** (fill in)
**Status:** ⚠ pending review

## Pre-read prediction
*Written before looking at expected.json. List every primitive + edge
you expect this fixture to produce. Don't cheat by peeking.*

## Prediction vs expected.json
- (fill in)

## Expected vs actual (from last regen)
- (fill in)

## Notes
```

Repeat the same pattern for the remaining 7 fixtures. Each one focuses on the specific pattern named in `wild/README.md`.

- [ ] **Step 2: Write the wild-corpus test harness**

```python
# depgraph/tests/extractors/test_typescript_wild.py
"""Wild-corpus runner for Phase 1.

For each fixture dir under wild/primitives_ts/, run the extractor and
compare emitted primitives + edges against expected.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "primitives_ts"
EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


def _run_extractor(fixture_root: Path) -> list[dict]:
    proc = subprocess.run([
        "npx", "tsx", str(EXTRACTOR),
        "--repo-key", "fixture", "--repo-path", str(fixture_root),
        "--format", "ndjson",
    ], capture_output=True, text=True, check=True, cwd=EXTRACTOR.parent)
    return [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_fixture_primitives_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = _run_extractor(fixture)
    actual_ids = {p["id"] for p in actual}
    expected_ids = {p["id"] for p in expected["primitives"]}
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    assert not missing and not extra, (
        f"{fixture.name}: missing={missing}, extra={extra}")


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_fixture_edges_subset_of_actual(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = _run_extractor(fixture)
    actual_edges = {(p["id"], e["kind"], e["target"])
                    for p in actual for e in p.get("edges_out", [])}
    for e in expected.get("edges", []):
        triple = (e["source"], e["kind"], e["target"])
        assert triple in actual_edges, (
            f"{fixture.name}: expected edge {triple} missing from actual")
```

- [ ] **Step 3: Claude verification pass**

For each of the 8 fixtures, read `src/` end-to-end. Write the prediction section of `verification.md` *before* opening `expected.json`. Diff the prediction against expected, resolve disagreements (fix expected if it was wrong, or correct the prediction). Run the extractor; diff actual against expected. Sign `verification.md` ✓ when all three agree.

If automated tests fail: fix framework, re-run, re-verify. If automated tests pass but Claude review surfaces an issue (e.g., the expected.json said only 2 primitives but the source clearly contains 3, and the framework also only emits 2 — both test and framework are wrong): fix both, re-run.

- [ ] **Step 4: Commit**

```bash
git add depgraph/tests/fixtures/wild/primitives_ts/ \
        depgraph/tests/extractors/test_typescript_wild.py
git commit -m "depgraph: Phase 1 wild corpus (8 TS pathological fixtures + Claude review)"
```

---

## Phase 2 — Python Primitive Extractor

**Goal:** Same five primitives in Python via stdlib `ast`. Class methods, class fields, top-level constants, modules, packages.

**Detection goals:**
1. Every `.py` file → module primitive.
2. Every directory with an `__init__.py` → package primitive.
3. `ast.ClassDef` → class primitive (Pydantic / SQLAlchemy / Django base classes are *not* special-cased — base class names become `extends` edges in Phase 3).
4. `ast.FunctionDef` / `AsyncFunctionDef` at module scope → function with `owner=None`.
5. `ast.FunctionDef` inside a class → function with `owner=<class_id>`.
6. `ast.Assign` / `ast.AnnAssign` at module scope → variable.
7. `ast.Assign` / `ast.AnnAssign` inside class body → variable with owner.
8. Decorators on functions/classes → recorded in `signature.decorators` (list of dotted-name strings).
9. Generics via `ast.TypeVar` / PEP-695 syntax → `attributes.template_parameters`.
10. `@dataclass`, `@pytest.fixture`, etc. → decorator names recorded; no kind decision.

**Files:**
- Create: `depgraph/extractors/python/__init__.py`
- Create: `depgraph/extractors/python/extract.py`
- Create: `depgraph/extractors/python/canonical.py`
- Test: `depgraph/tests/extractors/test_python_primitives.py`
- Test fixtures: `depgraph/tests/extractors/fixtures/primitives_py/<scenario>/`

### Task 2.1: Python canonical helpers

**Files:** `depgraph/extractors/python/canonical.py`, `depgraph/tests/extractors/test_python_canonical.py`

- [ ] **Step 1: Write failing test**

```python
# depgraph/tests/extractors/test_python_canonical.py
from depgraph.extractors.python.canonical import (
    canonical_id, slugify_id, structural_hash,
)


def test_canonical_id_top_level():
    assert canonical_id("concorda-api", "routers/events.py", "create_event") == \
        "concorda-api::routers/events.py::create_event"


def test_canonical_id_method():
    assert canonical_id("concorda-api", "services/users.py", "UserService.fetch") == \
        "concorda-api::services/users.py::UserService.fetch"


def test_slugify():
    assert slugify_id("concorda-api::routers/events.py::create_event") == \
        "concorda_api__routers_events_py__create_event"


def test_structural_hash_stable_on_dict_key_order():
    a = structural_hash({"a": 1, "b": 2})
    b = structural_hash({"b": 2, "a": 1})
    assert a == b
    assert len(a) == 64
```

- [ ] **Step 2: Run, verify fail.**

Run: `pytest depgraph/tests/extractors/test_python_canonical.py -v`

- [ ] **Step 3: Write `canonical.py`**

```python
"""Canonical id / slug / hash helpers for the v2 Python extractor."""
from __future__ import annotations

import hashlib
import json


def canonical_id(repo: str, path: str, symbol: str) -> str:
    return f"{repo}::{path}::{symbol}"


def slugify_id(node_id: str) -> str:
    out = node_id.replace("::", "__")
    out = "".join(c if c.isalnum() or c == "_" else "_" for c in out)
    return out.strip("_")

# Note: corpus-wide slug-collision detection lives in depgraph/lib/primitives.py
# as `check_slug_collisions()` — reconcile invokes it during regen so two
# distinct primitive ids that slugify to the same filename get flagged
# (e.g., when a repo path contains spaces or unusual chars).


def structural_hash(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()
```

- [ ] **Step 4: Run, verify pass + commit**

```bash
pytest depgraph/tests/extractors/test_python_canonical.py -v
git add depgraph/extractors/python/canonical.py depgraph/tests/extractors/test_python_canonical.py
git commit -m "depgraph/extractors/python: canonical id + slug + hash helpers"
```

### Task 2.2: Module + package primitives

**Files:** `depgraph/extractors/python/extract.py`, `depgraph/tests/extractors/test_python_primitives.py`, `depgraph/tests/extractors/fixtures/primitives_py/modules_only/pkg/__init__.py`, `.../pkg/mod.py`

- [ ] **Step 1: Create fixture**

```python
# fixtures/primitives_py/modules_only/pkg/__init__.py
# (empty)
```

```python
# fixtures/primitives_py/modules_only/pkg/mod.py
# (empty)
```

- [ ] **Step 2: Write failing test**

```python
# depgraph/tests/extractors/test_python_primitives.py
from pathlib import Path
import json
import pytest
from depgraph.extractors.python.extract import extract_repo

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "primitives_py"


def extract(scenario: str) -> list[dict]:
    return list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / scenario))


def test_module_per_py_file():
    prims = extract("modules_only")
    modules = [p for p in prims if p["primitive"] == "module"]
    paths = {m["source"]["path"] for m in modules}
    assert paths == {"pkg/__init__.py", "pkg/mod.py"}


def test_package_for_dir_with_init():
    prims = extract("modules_only")
    packages = [p for p in prims if p["primitive"] == "package"]
    names = {p["name"] for p in packages}
    assert "pkg" in names
```

- [ ] **Step 3: Run, verify fail.**

- [ ] **Step 4: Write `extract.py`**

```python
"""Python primitive extractor — schema v2 layered substrate.

Walks every .py under repo_path, emits module / package / class / function /
variable primitives. No kind decisions; classification is a later step.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator

from .canonical import canonical_id, structural_hash


EXTRACTOR_TAG = "depgraph/extractors/python/extract.py@2026-05-16"
SCHEMA_VERSION = 2


def _base_primitive(*, schema_id: str, primitive: str, name: str,
                    owner: str | None, repo: str, path: str,
                    line: int, end_line: int, signature: dict,
                    attributes_overrides: dict | None = None,
                    structural_payload: dict) -> dict:
    attrs = {"abstract": False, "generated": False, "external": False,
             "template_parameters": [], "macro": False, "mutable": True,
             "instantiable": True, "inheritable": True}
    attrs.update(attributes_overrides or {})
    return {
        "schema_version": SCHEMA_VERSION,
        "id": schema_id,
        "primitive": primitive,
        "name": name,
        "owner": owner,
        "source": {"repo": repo, "path": path, "language": "python",
                   "line": line, "end_line": end_line},
        "signature": signature,
        "attributes": attrs,
        "edges_out": [],
        "structural_hash": structural_hash(structural_payload),
        "kind": None,
        "extractor": EXTRACTOR_TAG,
    }


def _iter_py_files(repo_path: Path) -> Iterator[Path]:
    for p in repo_path.rglob("*.py"):
        if any(part in {"__pycache__", ".venv", "venv", "node_modules"} for part in p.parts):
            continue
        yield p


def extract_repo(*, repo_key: str, repo_path: Path) -> Iterator[dict]:
    files = sorted(_iter_py_files(repo_path))

    # packages: dirs that contain __init__.py
    package_dirs = set()
    for f in files:
        rel = f.relative_to(repo_path)
        if rel.name == "__init__.py":
            package_dirs.add(str(rel.parent))
    for pkg_path in sorted(package_dirs):
        yield _base_primitive(
            schema_id=f"{repo_key}::{pkg_path}",
            primitive="package", name=pkg_path, owner=None,
            repo=repo_key, path=pkg_path, line=0, end_line=0,
            signature={}, structural_payload={"kind": "package", "path": pkg_path},
        )

    # modules
    for f in files:
        rel = str(f.relative_to(repo_path))
        text = f.read_text()
        tree = ast.parse(text)
        end_line = len(text.splitlines())
        yield _base_primitive(
            schema_id=f"{repo_key}::{rel}",
            primitive="module", name=rel, owner=None,
            repo=repo_key, path=rel, line=1, end_line=end_line,
            signature={}, structural_payload={"kind": "module", "path": rel},
        )
        # class / function / variable extraction comes in subsequent tasks
```

- [ ] **Step 5: Run, verify pass + commit**

```bash
pytest depgraph/tests/extractors/test_python_primitives.py -v
git add depgraph/extractors/python/extract.py \
        depgraph/tests/extractors/test_python_primitives.py \
        depgraph/tests/extractors/fixtures/primitives_py/modules_only/
git commit -m "depgraph/extractors/python: emit module + package primitives"
```

### Task 2.3: Class + function primitives (Python)

**Fixture:** `fixtures/primitives_py/classes_and_functions/src.py`

```python
# fixtures/primitives_py/classes_and_functions/src.py
def top_level(x: int) -> str:
    return str(x)

async def async_fn():
    pass

class Foo:
    field: int = 0
    CONST = "hi"

    def method(self, x: int) -> str:
        return str(x)

    async def async_method(self):
        pass

    @staticmethod
    def static_m(): pass

class GenericFoo[T, U]:
    pass

class Abstract(metaclass=ABCMeta):
    pass

class Outer:
    """Nested classes must produce primitives with dotted qualnames and
    owner pointing at the parent class id."""
    class Inner:
        def inner_method(self) -> int:
            return 1
```

- [ ] **Step 1: Add tests**

```python
def test_class_and_function():
    prims = extract("classes_and_functions")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}

    assert "Foo" in classes
    assert "top_level" in fns
    assert fns["top_level"]["signature"]["return_type"] == "str"
    assert [p["name"] for p in fns["top_level"]["signature"]["parameters"]] == ["x"]


def test_async_function():
    prims = extract("classes_and_functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert fns["async_fn"]["signature"]["is_async"] is True


def test_method_has_owner():
    prims = extract("classes_and_functions")
    methods = {p["name"]: p for p in prims if p["primitive"] == "function" and p["owner"]}
    assert "Foo.method" in methods
    assert methods["Foo.method"]["owner"] == "fixture::src.py::Foo"


def test_static_method_recorded():
    prims = extract("classes_and_functions")
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "Foo.static_m" in fns
    assert "staticmethod" in fns["Foo.static_m"]["signature"]["decorators"]


def test_pep695_type_parameters():
    prims = extract("classes_and_functions")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert classes["GenericFoo"]["attributes"]["template_parameters"] == ["T", "U"]


def test_nested_class_extracted_with_dotted_qualname():
    prims = extract("classes_and_functions")
    classes = {p["name"]: p for p in prims if p["primitive"] == "class"}
    assert "Outer" in classes
    assert "Outer.Inner" in classes, f"missing nested class; got: {list(classes)}"
    inner = classes["Outer.Inner"]
    assert inner["owner"] == "fixture::src.py::Outer"
    fns = {p["name"]: p for p in prims if p["primitive"] == "function"}
    assert "Outer.Inner.inner_method" in fns
    assert fns["Outer.Inner.inner_method"]["owner"] == "fixture::src.py::Outer.Inner"
```

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Extend `extract.py`**

Below the existing module emit, add a walker. Replace the trailing comment "# class / function / variable extraction comes in subsequent tasks" with:

```python
        yield from _walk_module_body(tree, repo_key=repo_key, rel_path=rel)


def _decorator_name(dec: ast.expr) -> str:
    if isinstance(dec, ast.Name):
        return dec.id
    if isinstance(dec, ast.Attribute):
        return f"{_decorator_name(dec.value)}.{dec.attr}"
    if isinstance(dec, ast.Call):
        return _decorator_name(dec.func)
    return ast.unparse(dec)


def _annotation_text(ann: ast.expr | None) -> str | None:
    return ast.unparse(ann) if ann is not None else None


def _walk_module_body(tree: ast.Module, *, repo_key: str, rel_path: str) -> Iterator[dict]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            yield from _emit_class(node, repo_key=repo_key, rel_path=rel_path)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield _function_primitive(node, owner=None,
                                       repo_key=repo_key, rel_path=rel_path)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            yield from _variable_primitives(node, owner=None,
                                             repo_key=repo_key, rel_path=rel_path)


def _emit_class(node: ast.ClassDef, *, repo_key: str, rel_path: str,
                 parent_qualname: str | None = None) -> Iterator[dict]:
    """Emit a class primitive plus its members. Recurses into nested classes.

    `parent_qualname` is the dotted name of the enclosing class chain, used
    to build nested ids like `Outer.Inner` and `Outer.Inner.method`.
    """
    qualname = f"{parent_qualname}.{node.name}" if parent_qualname else node.name
    class_id = canonical_id(repo_key, rel_path, qualname)
    owner = canonical_id(repo_key, rel_path, parent_qualname) if parent_qualname else None
    tparams = [tp.name for tp in getattr(node, "type_params", [])]
    yield _base_primitive(
        schema_id=class_id, primitive="class", name=qualname, owner=owner,
        repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
        signature={"decorators": [_decorator_name(d) for d in node.decorator_list]},
        attributes_overrides={"abstract": False, "instantiable": True,
                              "template_parameters": tparams},
        structural_payload={"primitive": "class", "name": qualname,
                            "signature": {"decorators": [_decorator_name(d) for d in node.decorator_list],
                                            "bases": [ast.unparse(b) for b in node.bases]},
                            "body_text": ast.unparse(node)},
    )
    for child in node.body:
        if isinstance(child, ast.ClassDef):
            # Nested class — recurse with this class as parent. The
            # recursive call builds the dotted qualname (Outer.Inner) and
            # sets `owner` to the enclosing class id.
            yield from _emit_class(child, repo_key=repo_key, rel_path=rel_path,
                                     parent_qualname=qualname)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # `owner` carries the parent's full canonical id; the function
            # primitive derives its symbol as `<owner-qualname>.<name>`,
            # which works for nested classes since the owner's id ends
            # with the dotted qualname (Outer.Inner).
            yield _function_primitive(child, owner=class_id, repo_key=repo_key,
                                         rel_path=rel_path)
        elif isinstance(child, (ast.Assign, ast.AnnAssign)):
            yield from _variable_primitives(child, owner=class_id, repo_key=repo_key,
                                             rel_path=rel_path)


def _function_primitive(node: ast.FunctionDef | ast.AsyncFunctionDef,
                        *, owner: str | None, repo_key: str, rel_path: str) -> dict:
    symbol = f"{owner.split('::')[-1]}.{node.name}" if owner else node.name
    params = [{"name": a.arg, "type_annotation": _annotation_text(a.annotation),
               "default": None}
              for a in node.args.args + node.args.kwonlyargs]
    tparams = [tp.name for tp in getattr(node, "type_params", [])]
    body_text = ast.unparse(node)  # full def + body, canonicalized by ast.unparse
    signature = {
        "parameters": params,
        "return_type": _annotation_text(node.returns),
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "decorators": [_decorator_name(d) for d in node.decorator_list],
    }
    return _base_primitive(
        schema_id=canonical_id(repo_key, rel_path, symbol),
        primitive="function", name=symbol, owner=owner,
        repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
        signature=signature,
        attributes_overrides={"template_parameters": tparams,
                              "instantiable": False, "inheritable": False},
        # Per spec: name + signature + scope body. Include body so two
        # functions with the same signature but different bodies hash
        # differently.
        structural_payload={"primitive": "function", "name": symbol,
                            "signature": signature, "body_text": body_text},
    )


def _variable_primitives(node: ast.Assign | ast.AnnAssign,
                          *, owner: str | None, repo_key: str, rel_path: str) -> Iterator[dict]:
    if isinstance(node, ast.AnnAssign):
        targets = [node.target]
        type_ann = _annotation_text(node.annotation)
    else:
        targets = node.targets
        type_ann = None
    # RHS value text — needed by the SQL cross-ref pass to read
    # `__tablename__ = "users"`. For AnnAssign the value may be absent
    # (`x: int` with no initializer); record None in that case.
    value_text = ast.unparse(node.value) if node.value is not None else None
    for tgt in targets:
        if not isinstance(tgt, ast.Name):
            continue
        symbol = f"{owner.split('::')[-1]}.{tgt.id}" if owner else tgt.id
        yield _base_primitive(
            schema_id=canonical_id(repo_key, rel_path, symbol),
            primitive="variable", name=symbol, owner=owner,
            repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
            signature={"type_annotation": type_ann, "value_text": value_text},
            attributes_overrides={"mutable": tgt.id != tgt.id.upper(),
                                  "instantiable": False, "inheritable": False},
            # Per spec: hash includes name + signature + body. For a
            # variable the "body" is its initializer expression.
            structural_payload={"primitive": "variable", "name": symbol,
                                  "signature": {"type_annotation": type_ann,
                                                  "value_text": value_text},
                                  "body_text": value_text or ""},
        )
```

> Note: `signature.value_text` is the canonical place for the RHS expression text. The SQL cross-reference pass (Task 4.5) reads it to recover `__tablename__ = "users"` → the string `"users"`. Future passes can use it for similar literal-extraction needs (e.g., enum value sets).

- [ ] **Step 4: Run, verify pass.**

```bash
pytest depgraph/tests/extractors/test_python_primitives.py -v
```

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/python/extract.py \
        depgraph/tests/extractors/test_python_primitives.py \
        depgraph/tests/extractors/fixtures/primitives_py/classes_and_functions/
git commit -m "depgraph/extractors/python: emit class / function / variable primitives incl. methods + fields"
```

### Task 2.4: Schema validation sweep

- [ ] **Step 1: Add sweep test**

```python
# in test_python_primitives.py
from depgraph.lib.primitives import validate_primitive

def test_all_python_primitives_validate():
    for scenario in ("modules_only", "classes_and_functions"):
        for p in extract(scenario):
            errors = validate_primitive(p)
            assert not errors, f"{scenario}/{p.get('id')}: {errors}"
```

- [ ] **Step 2: Run, verify pass + commit**

```bash
pytest depgraph/tests/extractors/test_python_primitives.py -v
git add depgraph/tests/extractors/test_python_primitives.py
git commit -m "depgraph/extractors/python: schema validation gate"
```

### Task 2.5: Author wild fixtures + Claude verification

Same protocol as Task 1.9, applied to Phase 2's Python pathological patterns.

**Files:**
- Create: `depgraph/tests/fixtures/wild/primitives_py/{dunder_zoo,metaclasses,dataclass_pydantic_namedtuple,nested_everything,decorator_factories,walrus_match_pep695,if_name_main,relative_dots}/`
- Create: `depgraph/tests/extractors/test_python_wild.py`

- [ ] **Step 1: Author the 8 fixtures**

Follow the layout from `wild/README.md`. Each fixture: `README.md` (5–10 lines: what's tricky), `src/` (the awkward Python), `expected.json` (hand-computed primitives + edges), `verification.md` (template, status `⚠ pending review`). Example tricky case for `if_name_main`: assignments inside the `__main__` guard MUST NOT become primitives even though they're "top-level" syntactically — the test gates this.

- [ ] **Step 2: Test harness**

```python
# depgraph/tests/extractors/test_python_wild.py
import json
from pathlib import Path
import pytest
from depgraph.extractors.python.extract import extract_repo

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "primitives_py"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_primitives_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = list(extract_repo(repo_key="fixture", repo_path=fixture))
    actual_ids = {p["id"] for p in actual}
    expected_ids = {p["id"] for p in expected["primitives"]}
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    assert not missing and not extra, f"{fixture.name}: missing={missing}, extra={extra}"


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_edges_subset_of_actual(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = list(extract_repo(repo_key="fixture", repo_path=fixture))
    actual_edges = {(p["id"], e["kind"], e["target"])
                    for p in actual for e in p.get("edges_out", [])}
    for e in expected.get("edges", []):
        triple = (e["source"], e["kind"], e["target"])
        assert triple in actual_edges, f"{fixture.name}: expected edge {triple} missing"
```

- [ ] **Step 3: Claude verification**

For each fixture: read `src/` end-to-end; write the prediction section of `verification.md` *before* opening `expected.json`; diff; resolve disagreements; run extractor; diff actual; sign `✓`.

- [ ] **Step 4: Commit**

```bash
git add depgraph/tests/fixtures/wild/primitives_py/ \
        depgraph/tests/extractors/test_python_wild.py
git commit -m "depgraph: Phase 2 wild corpus (8 Python pathological fixtures + Claude review)"
```

---

## Phase 3 — L2 Edge Resolution

**Goal:** Both extractors emit `edges_out` on each primitive covering: `defines`, `extends`, `implements`, `calls`, `instantiates`, `references`, `reads`, `assigns`, `decorates`, `imports`, `tests`. Resolution is `exact` only at launch; `fuzzy` and `unresolved` come later behind a confidence threshold.

Each edge kind has at least one fixture + test in each language.

**Files:**
- Modify: `depgraph/extractors/typescript/extract.ts` (add edge resolution pass)
- Modify: `depgraph/extractors/python/extract.py` (add edge resolution pass)
- Test: `depgraph/tests/extractors/test_typescript_edges.py`
- Test: `depgraph/tests/extractors/test_python_edges.py`
- Test fixtures: `depgraph/tests/extractors/fixtures/edges_ts/<scenario>/`
- Test fixtures: `depgraph/tests/extractors/fixtures/edges_py/<scenario>/`

### Task 3.1: `defines` (implicit from extraction)

Every class → defines its methods/fields. Every module → defines its top-level classes/functions/variables. Every package → defines its modules.

- [ ] **Step 1: TS fixture + test**

Fixture: `fixtures/edges_ts/defines/src/file.ts`

```typescript
export class Foo { bar(): void {} }
```

Test:

```python
# test_typescript_edges.py
def test_defines_class_method():
    prims = run_extractor("defines", which="edges")  # shells out as before
    cls = next(p for p in prims if p["name"] == "Foo")
    targets = {e["target"] for e in cls["edges_out"] if e["kind"] == "defines"}
    assert "fixture::src/file.ts::Foo.bar" in targets

def test_defines_module_top_level():
    prims = run_extractor("defines", which="edges")
    mod = next(p for p in prims if p["primitive"] == "module")
    targets = {e["target"] for e in mod["edges_out"] if e["kind"] == "defines"}
    assert "fixture::src/file.ts::Foo" in targets
```

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Implement — add a finalization pass in both extractors that builds `defines` edges from the primitive set**

In `extract.ts`, before emitting, run a pass that for each module, attaches `defines` edges to every primitive whose `source.path` matches and `owner` is null; for each class, attaches `defines` to every primitive whose `owner` matches.

Sketch:

```typescript
function attachDefinesEdges(prims: Primitive[]): Primitive[] {
  const byId = new Map(prims.map((p) => [p.id, p]));
  for (const p of prims) {
    if (p.primitive === "module") {
      for (const child of prims) {
        if (child.id === p.id) continue;
        if (child.source.path === p.source.path && child.owner === null
            && (child.primitive === "class" || child.primitive === "function" || child.primitive === "variable")) {
          p.edges_out.push({
            target: child.id, kind: "defines", via: "lexical_scope",
            where: `${p.source.path}:${child.source.line}`, confidence: "exact",
          });
        }
      }
    } else if (p.primitive === "class") {
      for (const child of prims) {
        if (child.owner === p.id) {
          p.edges_out.push({
            target: child.id, kind: "defines", via: "class_body",
            where: `${p.source.path}:${child.source.line}`, confidence: "exact",
          });
        }
      }
    } else if (p.primitive === "package") {
      // child modules whose path is directly inside this package
      for (const child of prims) {
        if (child.primitive !== "module") continue;
        const dir = child.source.path.includes("/") ? child.source.path.substring(0, child.source.path.lastIndexOf("/")) : "";
        if (dir === p.source.path) {
          p.edges_out.push({
            target: child.id, kind: "defines", via: "package_member",
            where: `${p.source.path}/`, confidence: "exact",
          });
        }
      }
    }
  }
  return prims;
}
```

In Python, do the equivalent in a finalization function in `extract.py`. Apply to both extractors.

- [ ] **Step 4: Same fixture + test for Python**

Fixture: `fixtures/edges_py/defines/src.py`

```python
class Foo:
    def bar(self): pass
```

Test (in `test_python_edges.py`):

```python
def test_defines_class_method_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "defines"))
    cls = next(p for p in prims if p["name"] == "Foo")
    targets = {e["target"] for e in cls["edges_out"] if e["kind"] == "defines"}
    assert "fixture::src.py::Foo.bar" in targets
```

- [ ] **Step 5: Run all, verify pass.**

```bash
pytest depgraph/tests/extractors/test_typescript_edges.py depgraph/tests/extractors/test_python_edges.py -v
```

- [ ] **Step 6: Commit**

```bash
git commit -m "depgraph/extractors: emit defines edges (module/class/package → child)"
```

### Task 3.2: `extends` / `implements`

- [ ] **Step 1: TS fixture**

```typescript
// fixtures/edges_ts/inheritance/src/file.ts
export class Base {}
export interface ISpeaker { speak(): void; }
export class Child extends Base implements ISpeaker { speak() {} }
```

Test:

```python
def test_extends_and_implements_ts():
    prims = run_extractor("inheritance", which="edges")
    child = next(p for p in prims if p["name"] == "Child")
    ex = [e for e in child["edges_out"] if e["kind"] == "extends"]
    impls = [e for e in child["edges_out"] if e["kind"] == "implements"]
    assert any(e["target"] == "fixture::src/file.ts::Base" for e in ex)
    assert any(e["target"] == "fixture::src/file.ts::ISpeaker" for e in impls)
```

- [ ] **Step 2: Python fixture**

```python
# fixtures/edges_py/inheritance/src.py
class Base: pass
class Child(Base): pass
```

Test:

```python
def test_extends_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "inheritance"))
    child = next(p for p in prims if p["name"] == "Child")
    ex = [e for e in child["edges_out"] if e["kind"] == "extends"]
    assert any(e["target"] == "fixture::src.py::Base" for e in ex)
```

- [ ] **Step 3: Run, verify fail.**

- [ ] **Step 4: Implement**

TS (in `extract.ts`'s `attachDefinesEdges` sibling — call it `attachInheritanceEdges`):

```typescript
function attachInheritanceEdges(prims: Primitive[], sourceFiles: SourceFile[],
                                  repoKey: string, repoPath: string): Primitive[] {
  const symbolIndex = buildLocalSymbolIndex(prims);
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    for (const cls of sf.getClasses()) {
      const myId = canonicalId(repoKey, rel, cls.getName() ?? "<anonymous>");
      const myPrim = prims.find((p) => p.id === myId);
      if (!myPrim) continue;
      for (const ex of cls.getExtends() ? [cls.getExtends()!] : []) {
        const targetName = ex.getExpression().getText();
        const targetId = symbolIndex.get(targetName);
        if (targetId) {
          myPrim.edges_out.push({ target: targetId, kind: "extends", via: "class_decl",
            where: `${rel}:${ex.getStartLineNumber()}`, confidence: "exact" });
        }
      }
      for (const impl of cls.getImplements()) {
        const targetName = impl.getExpression().getText();
        const targetId = symbolIndex.get(targetName);
        if (targetId) {
          myPrim.edges_out.push({ target: targetId, kind: "implements", via: "class_decl",
            where: `${rel}:${impl.getStartLineNumber()}`, confidence: "exact" });
        }
      }
    }
  }
  return prims;
}

function buildLocalSymbolIndex(prims: Primitive[]): Map<string, string> {
  // Top-level symbol name -> id. For exact intra-file resolution; later passes
  // handle cross-file via import edges.
  const idx = new Map<string, string>();
  for (const p of prims) {
    if (p.owner === null && (p.primitive === "class" || p.primitive === "function" || p.primitive === "variable")) {
      idx.set(p.name, p.id);
    }
  }
  return idx;
}
```

Python (in `extract.py`). The cleanest path is to cache parsed ASTs from the module pass and feed them to the edge pass:

```python
# Module pass (extend extract_repo to keep parsed trees):
def extract_repo(*, repo_key: str, repo_path: Path) -> Iterator[dict]:
    primitives: list[dict] = []
    trees_by_path: dict[str, ast.Module] = {}
    files = sorted(_iter_py_files(repo_path))
    # ... existing module / class / function / variable emission, but
    # accumulate into `primitives` instead of yielding incrementally,
    # and stash `trees_by_path[rel] = tree` after each ast.parse.
    _attach_inheritance_edges(primitives, trees_by_path=trees_by_path)
    yield from primitives


def _attach_inheritance_edges(primitives: list[dict],
                                *, trees_by_path: dict[str, ast.Module]) -> None:
    """Walk each class's bases AST, resolve base names to local class ids,
    append `extends` edges in-place."""
    by_path: dict[str, dict[str, str]] = {}  # path -> { local_name -> id }
    for p in primitives:
        if p["primitive"] == "class" and p["owner"] is None:
            by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    classes_by_id = {p["id"]: p for p in primitives if p["primitive"] == "class"}

    for path, tree in trees_by_path.items():
        local_names = by_path.get(path, {})
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            class_id = local_names.get(node.name)
            if not class_id:
                continue
            target_class = classes_by_id[class_id]
            for base in node.bases:
                base_name = _name_from_base(base)
                if base_name is None:
                    continue
                target_id = local_names.get(base_name)
                if target_id:
                    target_class["edges_out"].append({
                        "target": target_id, "kind": "extends",
                        "via": "class_decl",
                        "where": f"{path}:{node.lineno}",
                        "confidence": "exact",
                    })
                else:
                    # Unresolved local name -> external terminal target
                    target_class["edges_out"].append({
                        "target": f"external::pypi::unknown::{base_name}",
                        "kind": "extends", "via": "class_decl",
                        "where": f"{path}:{node.lineno}",
                        "confidence": "unresolved",
                    })


def _name_from_base(base: ast.expr) -> str | None:
    """Recover the rightmost name from a base class expression.
    e.g. `Base` -> 'Base', `pkg.Base` -> 'Base', `Generic[T]` -> 'Generic'."""
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    if isinstance(base, ast.Subscript):
        return _name_from_base(base.value)
    return None
```

Python has no `implements` clause; the spec says interface conformance manifests as `extends` to a class with `attributes.abstract: true` (Protocols, ABCs). For this pass we treat all Python base classes as `extends` and let the classifier inspect target attributes if it cares.

- [ ] **Step 5: Run, verify pass + commit**

### Task 3.3: `imports`

- [ ] **Step 1: TS fixture**

```typescript
// fixtures/edges_ts/imports/src/a.ts
import { foo } from "./b.js";
```

```typescript
// fixtures/edges_ts/imports/src/b.ts
export function foo() {}
```

Test:

```python
def test_import_resolves_to_exporting_module():
    prims = run_extractor("imports", which="edges")
    mod_a = next(p for p in prims if p["source"]["path"] == "src/a.ts" and p["primitive"] == "module")
    imports = [e for e in mod_a["edges_out"] if e["kind"] == "imports"]
    targets = {e["target"] for e in imports}
    assert "fixture::src/b.ts::foo" in targets or "fixture::src/b.ts" in targets
```

- [ ] **Step 2: Python fixture + test**

```python
# fixtures/edges_py/imports/a.py
from .b import foo
```

```python
# fixtures/edges_py/imports/b.py
def foo(): pass
```

```python
def test_python_imports():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "imports"))
    mod_a = next(p for p in prims if p["source"]["path"] == "a.py" and p["primitive"] == "module")
    imports = [e for e in mod_a["edges_out"] if e["kind"] == "imports"]
    assert any(e["target"] == "fixture::b.py::foo" for e in imports)
```

- [ ] **Step 3: TS path-mapping fixture (tsconfig `paths`)**

Concorda-web uses Next.js / TS path mappings like `@/components/*`. The extractor must read `tsconfig.json` to resolve these.

```json
// fixtures/edges_ts/imports_with_paths/tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

```typescript
// fixtures/edges_ts/imports_with_paths/src/app.ts
import { greet } from "@/utils/greet.js";
```

```typescript
// fixtures/edges_ts/imports_with_paths/src/utils/greet.ts
export function greet() {}
```

Test:

```python
def test_tsconfig_path_alias_resolves():
    prims = run_extractor("imports_with_paths", which="edges")
    mod = next(p for p in prims if p["source"]["path"] == "src/app.ts"
               and p["primitive"] == "module")
    imports = [e for e in mod["edges_out"] if e["kind"] == "imports"]
    assert any(e["target"].startswith("fixture::src/utils/greet.ts")
               and e["confidence"] == "exact"
               for e in imports), imports
```

- [ ] **Step 4: Re-export fixture + test (TS)**

```typescript
// fixtures/edges_ts/imports_reexport/src/barrel.ts
export { foo } from "./impl.js";
```

```typescript
// fixtures/edges_ts/imports_reexport/src/impl.ts
export function foo() {}
```

```typescript
// fixtures/edges_ts/imports_reexport/src/consumer.ts
import { foo } from "./barrel.js";
```

Test:

```python
def test_reexport_resolves_to_origin_with_fuzzy_confidence():
    """consumer imports foo via barrel; the imports edge from consumer to
    impl::foo should be emitted with confidence=fuzzy (v1 doesn't follow
    re-export chains transitively for exact resolution)."""
    prims = run_extractor("imports_reexport", which="edges")
    consumer = next(p for p in prims if p["source"]["path"] == "src/consumer.ts"
                    and p["primitive"] == "module")
    imports = [e for e in consumer["edges_out"] if e["kind"] == "imports"]
    foo_imports = [e for e in imports if "foo" in e["target"]]
    assert foo_imports, "expected at least one imports edge mentioning foo"
    # Either fuzzy-resolved to impl, or exact to the barrel — both acceptable
    # for v0; the gate is that we emit *something*, not nothing.
    assert any(e["target"].endswith("::foo") for e in foo_imports), foo_imports
```

- [ ] **Step 5: Convention — import edges carry `local_binding`**

Every `imports` edge **must** include a `local_binding` field — the name the imported symbol is bound to in the importing module. Downstream passes (intra-function type binding in Phase 3.4; db_access in Phase 4.6) read this to resolve identifiers in source bodies to imported class ids.

Concretely:

| Source | Edge fields |
|---|---|
| `from .models import User` | `target: "<repo>::models.py::User"`, `local_binding: "User"` |
| `from .models import User as TheUser` | `target: "<repo>::models.py::User"`, `local_binding: "TheUser"` |
| `import requests` | `target: "external::pypi::requests"`, `local_binding: "requests"` |
| `import requests as r` | `target: "external::pypi::requests"`, `local_binding: "r"` |
| TS `import { foo } from "./b"` | `target: "<repo>::b.ts::foo"`, `local_binding: "foo"` |
| TS `import { foo as bar } from "./b"` | `target: "<repo>::b.ts::foo"`, `local_binding: "bar"` |
| TS `import * as Mod from "./b"` | `target: "<repo>::b.ts"`, `local_binding: "Mod"` |
| TS `import Default from "./b"` | `target: "<repo>::b.ts::default"`, `local_binding: "Default"` |

Test gate:

```python
def test_aliased_import_records_local_binding():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "imports_aliased"))
    mod = next(p for p in prims if p["source"]["path"] == "a.py" and p["primitive"] == "module")
    edge = next(e for e in mod["edges_out"] if e["kind"] == "imports" and "foo" in e["target"])
    assert edge["local_binding"] == "bar"
```

Required fixture for the test (create alongside the other imports fixtures):

```python
# depgraph/tests/extractors/fixtures/edges_py/imports_aliased/a.py
from .b import foo as bar
```

```python
# depgraph/tests/extractors/fixtures/edges_py/imports_aliased/b.py
def foo(): pass
```

A parallel TS fixture lives under `depgraph/tests/extractors/fixtures/edges_ts/imports_aliased/`:

```typescript
// src/a.ts
import { foo as bar } from "./b.js";
```

```typescript
// src/b.ts
export function foo() {}
```

With a TS test mirroring the Python one (asserts `edge.local_binding === "bar"`).

- [ ] **Step 6: Run, verify fail. Implement. Verify pass.**

TS: walk `sf.getImportDeclarations()`. For each named import, resolve the module specifier through ts-morph's `Project` initialized with the fixture's `tsconfig.json` (so its `compilerOptions.paths` apply); use `imp.getModuleSpecifierSourceFile()` which honors path aliases. For each import specifier, the local binding is `specifier.getAliasNode()?.getText() ?? specifier.getName()`. Non-resolved imports emit `confidence: "unresolved"` and target `external::npm::<package>::<symbol>`.

Re-exports: walk `sf.getExportDeclarations()` separately. For `export { foo } from "./b"`, emit an `imports` edge from the re-exporting module to `<target-module>::foo` with `confidence: "fuzzy"` and `local_binding: "foo"` (or the alias). A consumer's `import { foo } from "./barrel"` looks up the resolved target via the same module-specifier path; if barrel re-exports foo, the resolution chases one hop. Deeper chains stay `fuzzy` for v0.

Python: walk `ast.Import` and `ast.ImportFrom`. For `ImportFrom` with `level > 0` (relative), resolve from the module's directory + N parents per the `level`. For each `alias` node in `node.names`, `local_binding = alias.asname or alias.name`. For absolute imports, match the dot-joined name against the corpus's module index (paths converted to dotted form: `concorda_api/routers/events.py` → `concorda_api.routers.events`). For unresolved targets, emit `external::pypi::<root-package>::<symbol>` where root-package is the first dotted segment.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/typescript/extract.ts \
        depgraph/extractors/python/extract.py \
        depgraph/tests/extractors/test_typescript_edges.py \
        depgraph/tests/extractors/test_python_edges.py \
        depgraph/tests/extractors/fixtures/edges_ts/imports/ \
        depgraph/tests/extractors/fixtures/edges_ts/imports_with_paths/ \
        depgraph/tests/extractors/fixtures/edges_ts/imports_reexport/ \
        depgraph/tests/extractors/fixtures/edges_py/imports/
git commit -m "depgraph/extractors: imports edges (incl. tsconfig path aliases, re-exports, Python relative+absolute)"
```

### Task 3.4: `calls` + `instantiates` (with intra-function type binding)

This task **must** include intra-function type binding — without it, the common Python pattern `svc = UserService(session); svc.create_user(...)` produces no `calls` edge from the host function into `UserService.create_user`, and the service classifier downstream can't reach service-shaped functions. Full whole-program type inference is out of scope; what's in scope: track `x = SomeClass(...)` and `x: SomeClass = ...` within a single function body and resolve subsequent `x.method(...)` calls.

- [ ] **Step 1: TS fixture (with method-call resolution)**

```typescript
// fixtures/edges_ts/calls/src/file.ts
function helper(): string { return "ok"; }

export class Service {
  doWork(): string { return "done"; }
}

export function root() {
  helper();
  const s = new Service();
  s.doWork();             // intra-fn binding: s -> Service
  const t: Service = new Service();
  t.doWork();             // annotation also binds
}
```

Test:

```python
def test_calls_resolves_local_function():
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src/file.ts::helper" for e in calls)

def test_instantiates_resolves_local_class():
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    insts = [e for e in root["edges_out"] if e["kind"] == "instantiates"]
    assert any(e["target"] == "fixture::src/file.ts::Service" for e in insts)

def test_method_call_on_instantiated_local_resolves():
    """s = new Service(); s.doWork() — should emit a calls edge to Service.doWork."""
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src/file.ts::Service.doWork" for e in calls)

def test_method_call_on_annotated_local_resolves():
    """t: Service = new Service(); t.doWork() — annotation provides the bind."""
    prims = run_extractor("calls", which="edges")
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    # Two doWork call sites — both should resolve
    do_work_calls = [e for e in calls
                     if e["target"] == "fixture::src/file.ts::Service.doWork"]
    assert len(do_work_calls) >= 2
```

- [ ] **Step 2: Python fixture (with method-call resolution)**

```python
# fixtures/edges_py/calls/src.py
def helper(): return "ok"

class Service:
    def do_work(self):
        return "done"

def root():
    helper()
    s = Service()
    s.do_work()             # intra-fn binding: s -> Service
    t: Service = Service()
    t.do_work()             # annotation also binds

def handler(svc: Service):
    svc.do_work()           # parameter annotation binds
```

Test:

```python
def test_calls_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src.py::helper" for e in calls)

def test_instantiates_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    root = next(p for p in prims if p["name"] == "root")
    insts = [e for e in root["edges_out"] if e["kind"] == "instantiates"]
    assert any(e["target"] == "fixture::src.py::Service" for e in insts)

def test_method_call_on_local_instance_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    root = next(p for p in prims if p["name"] == "root")
    calls = [e for e in root["edges_out"] if e["kind"] == "calls"]
    do_works = [e for e in calls if e["target"] == "fixture::src.py::Service.do_work"]
    assert len(do_works) >= 2, f"expected 2 do_work calls from root, got {do_works}"

def test_method_call_on_parameter_annotation_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "calls"))
    handler = next(p for p in prims if p["name"] == "handler")
    calls = [e for e in handler["edges_out"] if e["kind"] == "calls"]
    assert any(e["target"] == "fixture::src.py::Service.do_work" for e in calls)
```

- [ ] **Step 3: Implement type binding + call resolution (Python)**

```python
# depgraph/extractors/python/extract.py — add a body-edges pass

def _attach_call_edges(primitives: list[dict],
                        *, trees_by_path: dict[str, ast.Module]) -> None:
    """For each function primitive, walk its body and emit calls /
    instantiates edges. Resolves method calls on local variables when the
    variable's type is known from (a) `x = SomeClass(...)` assignment,
    (b) `x: SomeClass = ...` annotated assignment, (c) parameter
    annotations on the enclosing function."""
    # Index local symbols and imports per file
    local_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p.get("owner") is not None:
            continue
        if p["primitive"] not in {"class", "function", "variable"}:
            continue
        local_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    classes_by_id = {p["id"]: p for p in primitives if p["primitive"] == "class"}
    fn_by_id = {p["id"]: p for p in primitives if p["primitive"] == "function"}

    # Index methods: for each class, map method name -> primitive id
    methods_by_class: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] == "function" and p.get("owner") in classes_by_id:
            methods_by_class.setdefault(p["owner"], {})[p["name"].split(".")[-1]] = p["id"]

    # Imports: from each module primitive's edges_out, build local-binding -> target-id.
    # Phase 3.3 records the local-binding name on each import edge as
    # `local_binding` (handles aliased imports correctly).
    imports_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] != "module":
            continue
        for e in p["edges_out"]:
            if e["kind"] != "imports":
                continue
            local_binding = e.get("local_binding")
            if local_binding:
                imports_by_path.setdefault(p["source"]["path"], {})[local_binding] = e["target"]

    for path, tree in trees_by_path.items():
        local_names = local_by_path.get(path, {})
        imports = imports_by_path.get(path, {})

        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Resolve the function primitive by source line
            fn_prim = next(
                (p for p in primitives
                 if p["primitive"] == "function"
                    and p["source"]["path"] == path
                    and p["source"]["line"] == fn_node.lineno),
                None,
            )
            if fn_prim is None:
                continue

            # Build initial type binding from parameter annotations
            var_types: dict[str, str] = {}  # local_name -> class_id
            for arg in fn_node.args.args + fn_node.args.kwonlyargs:
                if arg.annotation is None:
                    continue
                ann_text = ast.unparse(arg.annotation).split("[")[0].strip()
                target_id = local_names.get(ann_text) or imports.get(ann_text)
                if target_id and target_id in classes_by_id:
                    var_types[arg.arg] = target_id

            # Walk body in source order; update var_types on assignments
            for sub in ast.walk(fn_node):
                # Pattern 1: x: SomeClass = ...
                if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                    ann_text = ast.unparse(sub.annotation).split("[")[0].strip()
                    cid = local_names.get(ann_text) or imports.get(ann_text)
                    if cid and cid in classes_by_id:
                        var_types[sub.target.id] = cid

                # Pattern 2: x = SomeClass(...)
                if (isinstance(sub, ast.Assign)
                        and len(sub.targets) == 1
                        and isinstance(sub.targets[0], ast.Name)
                        and isinstance(sub.value, ast.Call)
                        and isinstance(sub.value.func, ast.Name)):
                    cname = sub.value.func.id
                    cid = local_names.get(cname) or imports.get(cname)
                    if cid and cid in classes_by_id:
                        var_types[sub.targets[0].id] = cid

                # Emit edges for each call
                if isinstance(sub, ast.Call):
                    edges = _resolve_call_edge(sub, local_names=local_names,
                                                 imports=imports,
                                                 classes_by_id=classes_by_id,
                                                 methods_by_class=methods_by_class,
                                                 var_types=var_types,
                                                 path=path)
                    fn_prim["edges_out"].extend(edges)


def _resolve_call_edge(call: ast.Call, *, local_names, imports,
                        classes_by_id, methods_by_class, var_types, path):
    """Return [edge] or [] for a single Call node."""
    if isinstance(call.func, ast.Name):
        # Bare name: helper() or Service()
        name = call.func.id
        target = local_names.get(name) or imports.get(name)
        if target is None:
            return []
        kind = "instantiates" if target in classes_by_id else "calls"
        return [{"target": target, "kind": kind, "via": "function_call",
                  "where": f"{path}:{call.lineno}", "confidence": "exact"}]

    if isinstance(call.func, ast.Attribute):
        # Method call: receiver.method
        if isinstance(call.func.value, ast.Name):
            recv = call.func.value.id
            method = call.func.attr
            recv_class_id = var_types.get(recv)
            if recv_class_id is None:
                # Receiver type unknown — leave unresolved
                return [{"target": f"external::unresolved::{recv}.{method}",
                          "kind": "calls", "via": "method_call",
                          "where": f"{path}:{call.lineno}",
                          "confidence": "unresolved"}]
            method_id = methods_by_class.get(recv_class_id, {}).get(method)
            if method_id:
                return [{"target": method_id, "kind": "calls",
                          "via": "method_call",
                          "where": f"{path}:{call.lineno}",
                          "confidence": "exact"}]
            return [{"target": f"external::unresolved::{recv_class_id}.{method}",
                      "kind": "calls", "via": "method_call",
                      "where": f"{path}:{call.lineno}",
                      "confidence": "unresolved"}]

        # Chained attribute (a.b.c()) — unresolved for v0
        return []

    # Computed callee (call[0](), call.func()()) — unresolved
    return []
```

TypeScript implementation mirrors the same algorithm against ts-morph. Key ts-morph types: walk `fn.getDescendants()` filtering for `Node.isCallExpression` and `Node.isNewExpression`. For type binding, use `VariableDeclaration.getTypeNode()` (annotated case) and `Node.isNewExpression(decl.getInitializer())` to detect `new SomeClass(...)`. For TS, ts-morph's `Symbol`/`Type` APIs (`callExpr.getExpression().getType().getSymbol()`) can fully resolve typed receivers — use that when available for `exact` confidence, fall back to local-binding heuristics otherwise.

- [ ] **Step 4: Run, verify pass + commit**

```bash
pytest depgraph/tests/extractors/test_python_edges.py -v -k call
pytest depgraph/tests/extractors/test_typescript_edges.py -v -k call
git add depgraph/extractors/typescript/extract.ts \
        depgraph/extractors/python/extract.py \
        depgraph/tests/extractors/test_python_edges.py \
        depgraph/tests/extractors/test_typescript_edges.py \
        depgraph/tests/extractors/fixtures/edges_ts/calls/ \
        depgraph/tests/extractors/fixtures/edges_py/calls/
git commit -m "depgraph/extractors: calls/instantiates edges with intra-function type binding"
```

### Task 3.5: `references` + `reads` + `assigns` + `decorates`

`reads` and `assigns` distinguish read vs write access to module-scope variables (immutability rules anchor on this). `decorates` connects each decorator-source to its decorated target. `references` is the catch-all for any "this primitive names that one" relationship not already covered by a more specific edge kind.

- [ ] **Step 1: Python fixture**

```python
# fixtures/edges_py/references/src.py
GLOBAL = 0

def reader():
    return GLOBAL

def writer():
    global GLOBAL
    GLOBAL = 1

import functools
@functools.lru_cache()
def decorated():
    pass

def local_dec(fn):
    return fn

@local_dec
def locally_decorated():
    pass
```

- [ ] **Step 2: Failing tests**

```python
def test_reads_edge_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    reader = next(p for p in prims if p["name"] == "reader")
    reads = [e for e in reader["edges_out"] if e["kind"] == "reads"]
    assert any(e["target"] == "fixture::src.py::GLOBAL" for e in reads)

def test_assigns_edge_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    writer = next(p for p in prims if p["name"] == "writer")
    assigns = [e for e in writer["edges_out"] if e["kind"] == "assigns"]
    assert any(e["target"] == "fixture::src.py::GLOBAL" for e in assigns)

def test_decorates_edge_local_decorator_py():
    """A local decorator (`@local_dec`) produces a `decorates` edge from
    the decorator function primitive to the decorated function. External
    decorators (`@functools.lru_cache`) do NOT produce an edge — they're
    captured in `signature.decorators` instead, since the edge taxonomy
    disallows external terminals as edge sources."""
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    locally_decorated = next(p for p in prims if p["name"] == "locally_decorated")
    local_dec = next(p for p in prims if p["name"] == "local_dec")

    # Local decorator → edge present, source is local_dec
    incoming = [
        e for src_p in prims for e in src_p["edges_out"]
        if e["kind"] == "decorates" and e["target"] == locally_decorated["id"]
    ]
    assert incoming, "expected a decorates edge into `locally_decorated`"
    src_ids = {p["id"] for p in prims for e in p["edges_out"]
               if e["kind"] == "decorates" and e["target"] == locally_decorated["id"]}
    assert local_dec["id"] in src_ids


def test_external_decorator_not_an_edge_py():
    """`@functools.lru_cache()` records in signature.decorators but does
    not produce a decorates edge (no external-as-source edges)."""
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "references"))
    decorated = next(p for p in prims if p["name"] == "decorated")

    # Captured in signature
    assert any("functools" in d or "lru_cache" in d
               for d in decorated["signature"]["decorators"])
    # No incoming decorates edge
    incoming = [
        e for src_p in prims for e in src_p["edges_out"]
        if e["kind"] == "decorates" and e["target"] == decorated["id"]
    ]
    assert incoming == [], (
        f"external decorator should not emit a decorates edge; got: {incoming}"
    )
```

- [ ] **Step 3: TS fixture + tests**

```typescript
// fixtures/edges_ts/references/src/file.ts
let globalCount = 0;
export function reader(): number {
  return globalCount;
}
export function writer() {
  globalCount = 1;
}
```

Test:

```python
def test_reads_edge_ts():
    prims = run_extractor("references", which="edges")
    reader = next(p for p in prims if p["name"] == "reader")
    reads = [e for e in reader["edges_out"] if e["kind"] == "reads"]
    assert any(e["target"] == "fixture::src/file.ts::globalCount" for e in reads)

def test_assigns_edge_ts():
    prims = run_extractor("references", which="edges")
    writer = next(p for p in prims if p["name"] == "writer")
    assigns = [e for e in writer["edges_out"] if e["kind"] == "assigns"]
    assert any(e["target"] == "fixture::src/file.ts::globalCount" for e in assigns)
```

- [ ] **Step 4: Implement (Python)**

Add to `depgraph/extractors/python/extract.py`:

```python
def _attach_var_access_edges(primitives, *, trees_by_path):
    """For each function, walk body and emit `reads` / `assigns` edges to
    module-scope variables defined in the same file (or imported)."""
    by_path: dict[str, dict[str, str]] = {}  # path -> { var_name -> var_id }
    for p in primitives:
        if (p["primitive"] == "variable" and p.get("owner") is None):
            by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    for path, tree in trees_by_path.items():
        local_vars = by_path.get(path, {})
        if not local_vars:
            continue
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fn_prim = next(
                (p for p in primitives
                 if p["primitive"] == "function"
                    and p["source"]["path"] == path
                    and p["source"]["line"] == fn_node.lineno),
                None,
            )
            if fn_prim is None:
                continue
            for sub in ast.walk(fn_node):
                if isinstance(sub, ast.Name) and sub.id in local_vars:
                    var_id = local_vars[sub.id]
                    if isinstance(sub.ctx, ast.Load):
                        fn_prim["edges_out"].append({
                            "target": var_id, "kind": "reads",
                            "via": "name_load", "where": f"{path}:{sub.lineno}",
                            "confidence": "exact",
                        })
                    elif isinstance(sub.ctx, ast.Store):
                        fn_prim["edges_out"].append({
                            "target": var_id, "kind": "assigns",
                            "via": "name_store", "where": f"{path}:{sub.lineno}",
                            "confidence": "exact",
                        })


def _attach_decorator_edges(primitives, *, trees_by_path, imports_by_path):
    """For each function/class with decorators in its signature, emit a
    `decorates` edge from the decorator source to the decorated primitive.
    The decorator source resolves via local names (for in-file definitions)
    or imports (for external decorators)."""
    local_by_path: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p.get("owner") is None and p["primitive"] in {"class", "function", "variable"}:
            local_by_path.setdefault(p["source"]["path"], {})[p["name"]] = p["id"]

    # The edge taxonomy disallows external terminals as edge sources, so
    # `decorates` edges are only emitted for **locally-defined** decorators.
    # External decorators (e.g., @functools.lru_cache, @pytest.fixture) are
    # captured in the function/class primitive's `signature.decorators`
    # name list — that's the canonical place for them. No separate edge.
    primitives_by_id = {q["id"]: q for q in primitives}
    for p in primitives:
        if p["primitive"] not in {"class", "function"}:
            continue
        decorators = p.get("signature", {}).get("decorators", [])
        if not decorators:
            continue
        path = p["source"]["path"]
        locals_ = local_by_path.get(path, {})
        imports = imports_by_path.get(path, {})
        for dec in decorators:
            head = dec.split(".")[0]
            source_id = locals_.get(head) or imports.get(head)
            if source_id is None:
                # External — no edge; presence already in signature.decorators
                continue
            if source_id.startswith("external::"):
                # Imported from external package — same rule: no edge.
                continue
            source_prim = primitives_by_id.get(source_id)
            if source_prim is None:
                continue
            source_prim["edges_out"].append({
                "target": p["id"], "kind": "decorates",
                "via": dec,
                "where": f"{path}:{p['source']['line']}",
                "confidence": "exact",
            })
```

- [ ] **Step 5: Implement (TS)**

TS uses ts-morph's `Identifier` walk. For each function/method's `getDescendantsOfKind(SyntaxKind.Identifier)`, check whether the parent is an assignment target (`BinaryExpression` with `=`) or a read. For decorators on functions/methods, the decorator's expression resolves via the symbol-table lookup the same way `imports` does.

- [ ] **Step 6: Run, verify pass + commit**

```bash
pytest depgraph/tests/extractors/test_python_edges.py -v -k 'reads or assigns or decorates'
pytest depgraph/tests/extractors/test_typescript_edges.py -v -k 'reads or assigns'
git add depgraph/extractors/python/extract.py \
        depgraph/extractors/typescript/extract.ts \
        depgraph/tests/extractors/test_python_edges.py \
        depgraph/tests/extractors/test_typescript_edges.py \
        depgraph/tests/extractors/fixtures/edges_py/references/ \
        depgraph/tests/extractors/fixtures/edges_ts/references/
git commit -m "depgraph/extractors: reads / assigns / decorates edges"
```

### Task 3.5b: Consolidate `extract_repo` final shape (checkpoint)

Phases 2 and 3 have incrementally extended `extract_repo`. This isn't a TDD task — it's a structural checkpoint. Before moving to Phase 4, the Python extractor's `extract_repo` should look exactly like the canonical shape below. The TS extractor's `main()` follows the same outline.

```python
# depgraph/extractors/python/extract.py — canonical final shape after Phase 3
def extract_repo(*, repo_key: str, repo_path: Path) -> Iterator[dict]:
    primitives: list[dict] = []
    trees_by_path: dict[str, ast.Module] = {}

    # 1. Walk files; emit module / package primitives + parse + accumulate trees
    files = sorted(_iter_py_files(repo_path))
    package_dirs = _discover_package_dirs(files)
    for pkg_path in sorted(package_dirs):
        primitives.append(_package_primitive(pkg_path, repo_key))
    for f in files:
        rel = str(f.relative_to(repo_path))
        text = f.read_text()
        tree = ast.parse(text)
        trees_by_path[rel] = tree
        primitives.append(_module_primitive(rel, text, tree, repo_key))
        primitives.extend(_walk_module_body(tree, repo_key=repo_key, rel_path=rel))

    # 2. L2 edge passes — order matters: each depends on indexes built by
    #    its predecessors (e.g., calls resolution uses imports edges).
    _attach_inheritance_edges(primitives, trees_by_path=trees_by_path)
    _attach_imports_edges(primitives, trees_by_path=trees_by_path,
                            repo_path=repo_path)  # populates module.edges_out
    # imports_by_path is built fresh by passes that need it; the imports
    # edges live on each module primitive's edges_out.
    _attach_call_edges(primitives, trees_by_path=trees_by_path)
    _attach_var_access_edges(primitives, trees_by_path=trees_by_path)

    # imports_by_path for decorator pass
    imports_by_path = _build_imports_by_path(primitives)
    _attach_decorator_edges(primitives, trees_by_path=trees_by_path,
                              imports_by_path=imports_by_path)
    _attach_tests_edges(primitives, trees_by_path=trees_by_path,
                         config=default_classification_config())

    yield from primitives


def _build_imports_by_path(primitives: list[dict]) -> dict[str, dict[str, str]]:
    """Helper used by passes that need {path -> {local_binding -> target_id}}.
    Reads imports edges from module primitives' edges_out."""
    out: dict[str, dict[str, str]] = {}
    for p in primitives:
        if p["primitive"] != "module":
            continue
        for e in p["edges_out"]:
            if e["kind"] != "imports":
                continue
            lb = e.get("local_binding")
            if lb:
                out.setdefault(p["source"]["path"], {})[lb] = e["target"]
    return out
```

Test: a smoke test that calls `extract_repo` against a fixture covering one primitive of each kind and one edge of each kind, asserts every attach pass ran (a non-empty `edges_out` of the expected kind on the expected primitives).

```python
# depgraph/tests/extractors/test_python_pipeline.py
def test_extract_repo_runs_all_edge_passes(tmp_path):
    """Sanity check: after extract_repo returns, every documented edge
    kind has at least one instance somewhere in the corpus. Catches the
    case where a future refactor forgets to wire in one of the attach
    passes."""
    repo = tmp_path / "fixture"
    repo.mkdir()
    (repo / "models.py").write_text("class Base: pass\n\n"
                                      "class User(Base):\n"
                                      "    __tablename__ = 'users'\n")
    (repo / "service.py").write_text("from .models import User\n"
                                       "import functools\n\n"
                                       "GLOBAL = 0\n\n"
                                       "def local_dec(fn): return fn\n\n"
                                       "@local_dec\n"
                                       "def read_global() -> int:\n"
                                       "    return GLOBAL\n\n"
                                       "def write_global():\n"
                                       "    global GLOBAL\n"
                                       "    GLOBAL = 1\n\n"
                                       "def make_user():\n"
                                       "    u = User()\n"
                                       "    return u\n")
    (repo / "test_service.py").write_text("from .service import read_global\n"
                                            "def test_read():\n"
                                            "    assert read_global() == 0\n")

    prims = list(extract_repo(repo_key="fixture", repo_path=repo))
    edge_kinds = {e["kind"] for p in prims for e in p["edges_out"]}
    expected_kinds = {"defines", "extends", "imports", "calls",
                      "instantiates", "reads", "assigns", "decorates",
                      "tests"}
    missing = expected_kinds - edge_kinds
    assert not missing, f"extract_repo missed edge passes: {missing}"
```

This test is the regression gate against L5/L6 (forgotten attach passes).

- [ ] **Step 1: Run the pipeline smoke test**

```bash
pytest depgraph/tests/extractors/test_python_pipeline.py -v
```

If any expected edge kind is missing, the corresponding attach pass isn't wired in. Trace back to the relevant Phase 3 task.

- [ ] **Step 2: Commit**

```bash
git add depgraph/extractors/python/extract.py \
        depgraph/tests/extractors/test_python_pipeline.py
git commit -m "depgraph/extractors/python: pipeline smoke test + consolidated extract_repo"
```

### Task 3.6: `tests` edges (assertion-scoped)

A test function is one whose body calls a known test framework primitive. The naive "edge from test to every imported function it calls" rule is overbroad (it edges to test helpers, framework primitives, parameter factories). Tighter rule: emit a `tests` edge only for call targets that appear **inside an assertion expression** (`expect(...).toBe(...)`, `assert <expr>`) — the function being passed to or called inside the assertion is the subject under test.

- [ ] **Step 1: TS fixture (vitest)**

```typescript
// fixtures/edges_ts/tests/src/example.test.ts
import { describe, it, expect } from "vitest";
import { add, normalize } from "./math.js";
import { makeFixture } from "./test_helpers.js";

describe("add", () => {
  it("adds", () => {
    const x = makeFixture();              // helper call — NOT a subject
    expect(add(1, 2)).toBe(3);            // subject: add
    expect(normalize("X")).toBe("x");     // subject: normalize
  });
});
```

```typescript
// fixtures/edges_ts/tests/src/math.ts
export function add(a: number, b: number): number { return a + b; }
export function normalize(s: string): string { return s.toLowerCase(); }
```

```typescript
// fixtures/edges_ts/tests/src/test_helpers.ts
export function makeFixture() { return 42; }
```

Test:

```python
def test_tests_edge_to_subject_only():
    prims = run_extractor("tests", which="edges")
    test_fn = next(p for p in prims if p["primitive"] == "function"
                   and p["source"]["path"].endswith(".test.ts"))
    tests = [e for e in test_fn["edges_out"] if e["kind"] == "tests"]
    targets = {e["target"] for e in tests}
    assert "fixture::src/math.ts::add" in targets
    assert "fixture::src/math.ts::normalize" in targets
    # helper called outside expect(...) — must NOT be a tests-edge target
    assert "fixture::src/test_helpers.ts::makeFixture" not in targets
    # framework primitives must NOT be targets either
    assert not any("vitest" in t for t in targets)
```

- [ ] **Step 2: Python fixture (pytest)**

```python
# fixtures/edges_py/tests/src/math.py
def add(a, b): return a + b
def normalize(s): return s.lower()
```

```python
# fixtures/edges_py/tests/src/test_helpers.py
def make_fixture(): return 42
```

```python
# fixtures/edges_py/tests/src/test_math.py
from .math import add, normalize
from .test_helpers import make_fixture

def test_add():
    x = make_fixture()           # helper call — NOT a subject
    assert add(1, 2) == 3        # subject: add
    assert normalize("X") == "x" # subject: normalize
```

Test:

```python
def test_tests_edge_py_assertion_scoped():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "tests"))
    tfn = next(p for p in prims if p["name"] == "test_add")
    tests = [e for e in tfn["edges_out"] if e["kind"] == "tests"]
    targets = {e["target"] for e in tests}
    assert "fixture::src/math.py::add" in targets
    assert "fixture::src/math.py::normalize" in targets
    # helper imported but called outside an assert — not a subject
    assert "fixture::src/test_helpers.py::make_fixture" not in targets
```

- [ ] **Step 3: Implement**

Tighter recognition:

- A function is a "test function" if it's inside a recognized test file (`*.test.ts`, `*.test.tsx`, `*.spec.ts`, `test_*.py`, `*_test.py`) **or** has a recognized test decorator (`@pytest.fixture`, `@pytest.mark.*`).
- For each call **inside the test function**, walk up the parent chain at the AST level. If any enclosing expression is recognized as an assertion (`Call` with `func.id in {"expect", "assert", ...}` for TS / `ast.Assert` ancestor for Python), the call's resolved target gets a `tests` edge.
- Framework primitives (`it`, `describe`, `expect`, `test`, `pytest.fixture`, etc.) and decorator targets never get `tests` edges. Filter at emit time by checking whether the call expression's resolved target id matches a framework-name set from `config.test_framework_primitives`.

Python implementation:

```python
def _attach_tests_edges(primitives, *, trees_by_path, config):
    framework_names = set(config.test_framework_primitives)
    for path, tree in trees_by_path.items():
        if not _is_test_path_py(path):
            continue
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _is_test_function_py(fn_node):
                continue
            fn_prim = _find_fn_primitive(primitives, path, fn_node.lineno)
            if fn_prim is None:
                continue
            # Build child->parent map once
            parents = {}
            for sub in ast.walk(fn_node):
                for child in ast.iter_child_nodes(sub):
                    parents[id(child)] = sub
            for sub in ast.walk(fn_node):
                if not isinstance(sub, ast.Call):
                    continue
                # Is this call inside an assert / inside an expect chain?
                if not _is_assertion_scoped(sub, parents):
                    continue
                callee_name = _callee_name(sub.func)
                if callee_name in framework_names:
                    continue
                target_id = _resolve_target_id(callee_name, path, primitives)
                if target_id:
                    fn_prim["edges_out"].append({
                        "target": target_id, "kind": "tests",
                        "via": "asserted_call",
                        "where": f"{path}:{sub.lineno}",
                        "confidence": "exact",
                    })


def _is_assertion_scoped(node, parents):
    """Walk up from node; True if any ancestor is ast.Assert."""
    cur = parents.get(id(node))
    while cur is not None:
        if isinstance(cur, ast.Assert):
            return True
        cur = parents.get(id(cur))
    return False


def _is_test_path_py(path: str) -> bool:
    last = path.rsplit("/", 1)[-1]
    return last.startswith("test_") or last.endswith("_test.py")


def _is_test_function_py(fn_node) -> bool:
    if fn_node.name.startswith("test_"):
        return True
    for d in fn_node.decorator_list:
        name = _decorator_name(d)
        if name.startswith("pytest."):
            return True
    return False
```

TS variant: walk for `CallExpression` nodes whose immediate-or-near-ancestor is a `CallExpression` with callee `expect`. Use ts-morph's `getAncestors()` and look for `Identifier` named `expect` or `assert`.

- [ ] **Step 4: Run, verify pass + commit.**

```bash
git commit -m "depgraph/extractors: tests edges scoped to assertion expressions only"
```

### Task 3.7: Schema validation sweep on edges

- [ ] **Step 1: Add a validation sweep test**

```python
# test_python_edges.py / test_typescript_edges.py
from depgraph.lib.edges import validate_edge

def test_all_emitted_edges_validate():
    primitives_by_id = {p["id"]: p for p in extract("calls") + extract("inheritance") + extract("imports") + extract("references") + extract("tests")}
    for p in primitives_by_id.values():
        for e in p["edges_out"]:
            # caller adds source_kind from primitive
            validation_input = {**e, "source_kind": p["primitive"]}
            # target_kind: resolve from primitives_by_id if internal
            tgt = primitives_by_id.get(e["target"])
            if tgt:
                validation_input["target_kind"] = tgt["primitive"]
            errors = validate_edge(validation_input)
            assert not errors, f"{p['id']} -> {e['target']}: {errors}"
```

- [ ] **Step 2: Run, verify pass + commit.**

```bash
git commit -m "depgraph/extractors: edge schema validation gate"
```

### Task 3.8: Author wild fixtures + Claude verification

The 8 Phase-3 wild fixtures stress edge resolution: method calls on instance variables, chained calls, dynamic dispatch (must not crash, must mark `unresolved`), monkey-patches, circular imports, decorator targets, module-scope read/assign distinction.

**Files:**
- Create: `depgraph/tests/fixtures/wild/edges/{method_call_chains,instance_passing,dynamic_dispatch,monkey_patch,circular_imports_py,circular_imports_ts,conditional_rebinding,decorator_target_resolution,read_assign_global}/`
- Create: `depgraph/tests/extractors/test_edges_wild.py`

- [ ] **Step 1: Author the 8 fixtures**

Each fixture pairs source files with hand-computed expected edges. Critical assertions per fixture:

- **method_call_chains**: `client.users.get().filter().first()` — first call resolves; subsequent chained calls land `fuzzy` or `unresolved` (acceptable for v0).
- **instance_passing**: function takes typed param, calls method on it → edge resolves via param annotation.
- **dynamic_dispatch**: `getattr(obj, name)()` — extractor produces a `calls` edge with `confidence: "unresolved"` and target `external::unresolved::*`, doesn't crash.
- **monkey_patch**: `SomeClass.method = lambda` — the lambda IS extracted as a function primitive, but the assignment doesn't redirect existing `calls` edges (out of scope; document).
- **circular_imports_py / circular_imports_ts**: A imports B imports A. Both modules' import edges resolve; the corpus walk doesn't deadlock.
- **conditional_rebinding**: `if x: s = A() else: s = B(); s.do_work()`. The v0 implementation walks the AST in `ast.walk` order (BFS-ish), not control-flow order. Both Assign nodes get processed before the outer Expr-Call, so `var_types["s"]` ends up bound to whichever branch was walked last. `expected.json` asserts the deterministic-but-wrong behavior so a future flow-sensitive pass has a regression target. The fixture's `verification.md` should clearly note this is *intentionally pinned wrong* — a reviewer who reads the fixture without context might "fix" the test.
- **decorator_target_resolution**: `@local_dec` (local function) produces a `decorates` edge from the decorator function to the target. `@functools.lru_cache` (external) produces *no* edge — external terminals can't be edge sources (decorator name is recorded in `signature.decorators` instead).
- **read_assign_global**: module-scope `GLOBAL = 0`; one function reads, one writes; distinct edges emitted.

- [ ] **Step 2: Test harness**

```python
# depgraph/tests/extractors/test_edges_wild.py
"""Wild edge-resolution gate. Runs each fixture's extractor (TS or Python
based on src/ contents), compares edges_out against expected.json."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "edges"
TS_EXTRACTOR = Path(__file__).resolve().parents[2] / "extractors" / "typescript" / "extract.ts"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


def _run(fixture):
    # Detect language from src/ contents
    if any(f.suffix in {".ts", ".tsx", ".js"} for f in (fixture / "src").iterdir()):
        proc = subprocess.run([
            "npx", "tsx", str(TS_EXTRACTOR),
            "--repo-key", "fixture", "--repo-path", str(fixture),
            "--format", "ndjson",
        ], capture_output=True, text=True, check=True, cwd=TS_EXTRACTOR.parent)
        return [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]
    else:
        from depgraph.extractors.python.extract import extract_repo
        return list(extract_repo(repo_key="fixture", repo_path=fixture / "src"))


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_edges_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    actual = _run(fixture)
    actual_edges = {(p["id"], e["kind"], e["target"], e.get("confidence"))
                    for p in actual for e in p.get("edges_out", [])}
    for e in expected.get("edges", []):
        triple = (e["source"], e["kind"], e["target"], e.get("confidence", "exact"))
        assert triple in actual_edges, f"{fixture.name}: expected edge {triple} missing"


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_unresolved_edges_present_where_expected(fixture):
    """Some fixtures (dynamic_dispatch) MUST emit unresolved edges; the
    expected.json marks these. This test ensures we're not silently
    dropping them."""
    expected = json.loads((fixture / "expected.json").read_text())
    if not expected.get("unresolved_edges_expected"):
        return  # nothing to assert
    actual = _run(fixture)
    unresolved = [e for p in actual for e in p.get("edges_out", [])
                  if e.get("confidence") == "unresolved"]
    assert unresolved, f"{fixture.name}: expected at least one unresolved edge"
```

- [ ] **Step 3: Claude verification**

Same protocol. For each fixture, especially focus on whether `dynamic_dispatch` produces an unresolved edge rather than crashing — that's a soundness-vs-completeness signal we want to preserve.

- [ ] **Step 4: Commit**

```bash
git add depgraph/tests/fixtures/wild/edges/ \
        depgraph/tests/extractors/test_edges_wild.py
git commit -m "depgraph: Phase 3 wild corpus (8 edge-resolution fixtures + Claude review)"
```

---

## Phase 4 — Schema Extraction from Actual Artifacts

**Goal:** Extract the database schema from where it actually lives. For Concorda that is 65+ `CREATE TABLE` statements inside Python migration files (plus `ALTER TABLE`, `CREATE INDEX`, `DROP TABLE`, etc.). The schema primitives become first-class corpus nodes. ORM mapper classes (SQLAlchemy `class User(Base)`) are downstream observers that `references → schema` after a cross-reference pass.

**Detection goals (each gets a test):**

1. `CREATE TABLE foo (...)` → class primitive `kind: "schema"`, columns → variable primitives owned by the table.
2. `CREATE TABLE IF NOT EXISTS foo (...)` → same shape (idempotent variant).
3. Column types resolve from SQL (`VARCHAR(128)` → type_annotation `"VARCHAR(128)"`, `INTEGER NOT NULL` → annotation `"INTEGER"`, attributes `{nullable: false}`).
4. `PRIMARY KEY` and `FOREIGN KEY` constraints → recorded on the table primitive's `signature` (`signature.primary_key: ["id"]`, `signature.foreign_keys: [{column: "user_id", references_table: "users", references_column: "id"}]`). Placed in `signature` rather than `attributes` so they participate in `structural_hash` — two tables with the same columns but different FKs are structurally distinct.
5. `CREATE INDEX foo ON bar(baz)` → `references` edge from index name to the column primitive; no primitive emitted for the index itself.
6. `ALTER TABLE foo ADD COLUMN bar TEXT` → after reconciliation, the `foo` table primitive includes `bar` in its columns.
7. `ALTER TABLE foo DROP COLUMN bar` → after reconciliation, `bar` is absent from `foo`.
8. `DROP TABLE foo` → after reconciliation, the `foo` table primitive is archived (not present in the live corpus).
9. Migration file ordinal prefix (`047_organization_region.py` → `migration_order: 47`).
10. Non-prefixed migration filename (`add_event_regatta_id.py`) → `migration_order: null` (excluded from ordered replay; documented limitation).
11. SQL extracted from `text("...")` inside `conn.execute(text(...))` → parsed and treated as an operation in the containing migration.
12. SQL extracted from f-strings inside `text(f"...")` → parsed if the f-string's interpolations resolve to literal values at the call site (string concat / .format with literal args also OK); skipped with a `warnings` entry on the migration module if interpolations are dynamic.
13. Python class with `__tablename__ = "X"` and `extends → Base` → emits a `references` edge to the schema-sourced class whose name matches `X`.
14. `session.query(User)` resolves `User` (Python class) → follows `references → User` (schema) → emits `db_access` edge targeting the schema primitive.
15. Raw `conn.execute(text("SELECT ... FROM users ..."))` outside migration files → parsed; `db_access` edges emitted to each referenced table primitive.

**Files:**
- Create: `depgraph/extractors/sql/extract.py` (language-registry entry for standalone `.sql` files; no-op for Concorda but framework-correct)
- Create: `depgraph/lib/sql/__init__.py`
- Create: `depgraph/lib/sql/parser.py` (sqlglot wrapper → structured operations)
- Create: `depgraph/lib/sql/migration.py` (Python migration recognition + SQL string extraction)
- Create: `depgraph/lib/sql/reconcile.py` (replay ordered operations → final schema primitives)
- Create: `depgraph/lib/sql/cross_ref.py` (ORM model → schema reference post-pass)
- Create: `depgraph/lib/system_stub/__init__.py`
- Create: `depgraph/lib/system_stub/db_access.py` (rewritten: resolves to schema primitives, not synthetic terminals)
- Test: `depgraph/tests/lib/sql/test_parser.py`
- Test: `depgraph/tests/lib/sql/test_migration.py`
- Test: `depgraph/tests/lib/sql/test_reconcile.py`
- Test: `depgraph/tests/lib/sql/test_cross_ref.py`
- Test: `depgraph/tests/lib/test_db_access.py`
- Test fixtures: `depgraph/tests/lib/sql/fixtures/migrations/{001..}_*.py`
- Test fixtures: `depgraph/tests/lib/sql/fixtures/schemas/*.sql`

### Task 4.1: SQL parser library (sqlglot wrapper)

The parser takes a SQL string and returns a list of structured operations. Operations carry enough metadata for downstream layers to build primitives and references.

- [ ] **Step 1: Add sqlglot to depgraph dependencies**

```bash
cd /home/lgreenlee/tools/knowledge-graph/depgraph
echo "sqlglot>=23.0.0" >> requirements.txt
pip install -r requirements.txt
```

- [ ] **Step 2: Write failing test**

```python
# depgraph/tests/lib/sql/test_parser.py
from depgraph.lib.sql.parser import parse_operations, Operation


def test_create_table_emits_create_op():
    sql = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    ops = parse_operations(sql)
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "create_table"
    assert op.table == "users"
    assert op.columns == [
        {"name": "id", "type": "INTEGER", "nullable": True,
         "default": None, "primary_key": True},
        {"name": "email", "type": "VARCHAR(255)", "nullable": False,
         "default": None, "primary_key": False},
        {"name": "created_at", "type": "TIMESTAMP", "nullable": True,
         "default": "CURRENT_TIMESTAMP", "primary_key": False},
    ]


def test_create_table_if_not_exists():
    ops = parse_operations("CREATE TABLE IF NOT EXISTS foo (id INTEGER)")
    assert ops[0].kind == "create_table"
    assert ops[0].table == "foo"
    assert ops[0].if_not_exists is True


def test_foreign_key_recorded():
    sql = """
    CREATE TABLE event_crew (
        id INTEGER PRIMARY KEY,
        event_id INTEGER NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id)
    )
    """
    op = parse_operations(sql)[0]
    assert op.foreign_keys == [
        {"column": "event_id", "references_table": "events", "references_column": "id"}
    ]


def test_alter_table_add_column():
    op = parse_operations("ALTER TABLE users ADD COLUMN role VARCHAR(50)")[0]
    assert op.kind == "alter_add_column"
    assert op.table == "users"
    assert op.column == {"name": "role", "type": "VARCHAR(50)", "nullable": True,
                          "default": None, "primary_key": False}


def test_alter_table_drop_column():
    op = parse_operations("ALTER TABLE users DROP COLUMN legacy_field")[0]
    assert op.kind == "alter_drop_column"
    assert op.table == "users"
    assert op.column_name == "legacy_field"


def test_alter_column_type():
    op = parse_operations(
        "ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(255)",
        dialect="postgres",
    )[0]
    assert op.kind == "alter_column_type"
    assert op.table == "users"
    assert op.column_name == "email"
    assert "VARCHAR" in op.new_type.upper()


def test_alter_column_default():
    op = parse_operations(
        "ALTER TABLE users ALTER COLUMN role SET DEFAULT 'member'",
        dialect="postgres",
    )[0]
    assert op.kind == "alter_column_default"
    assert op.column_name == "role"
    assert "member" in (op.new_default or "")


def test_alter_column_drop_not_null():
    op = parse_operations(
        "ALTER TABLE users ALTER COLUMN email DROP NOT NULL",
        dialect="postgres",
    )[0]
    assert op.kind == "alter_column_nullable"
    assert op.new_nullable is True


def test_rename_column():
    op = parse_operations(
        "ALTER TABLE users RENAME COLUMN email_addr TO email",
        dialect="postgres",
    )[0]
    assert op.kind == "rename_column"
    assert op.column_name == "email_addr"
    assert op.new_column_name == "email"


def test_drop_table():
    op = parse_operations("DROP TABLE old_audit_log")[0]
    assert op.kind == "drop_table"
    assert op.table == "old_audit_log"


def test_create_index():
    op = parse_operations("CREATE INDEX idx_users_email ON users(email)")[0]
    assert op.kind == "create_index"
    assert op.index_name == "idx_users_email"
    assert op.table == "users"
    assert op.columns_indexed == ["email"]


def test_multiple_statements_in_one_string():
    sql = """
    CREATE TABLE a (id INTEGER);
    CREATE TABLE b (id INTEGER);
    """
    ops = parse_operations(sql)
    assert [op.table for op in ops] == ["a", "b"]


def test_select_statement_returns_empty_for_ddl_parser():
    """Parser is DDL-focused; SELECTs return no operations.
    The db_access logic uses a different parse path for SELECT/UPDATE/etc."""
    ops = parse_operations("SELECT * FROM users")
    assert ops == []
```

- [ ] **Step 3: Run, verify fail**

Run: `pytest depgraph/tests/lib/sql/test_parser.py -v`
Expected: ImportError (module doesn't exist).

- [ ] **Step 4: Implement `depgraph/lib/sql/parser.py`**

```python
"""SQL DDL parser — extracts structured operations from SQL text.

Built on sqlglot for cross-dialect tolerance (sqlite, postgres, mysql).
Returns Operation dataclasses; downstream layers convert to primitives.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import sqlglot
from sqlglot import expressions as exp


@dataclass
class Operation:
    kind: str   # create_table | alter_add_column | alter_drop_column |
                # alter_column_type | alter_column_default | alter_column_nullable |
                # drop_table | create_index | create_view | rename_table |
                # rename_column
    table: str | None = None
    if_not_exists: bool = False
    columns: list[dict[str, Any]] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)
    column: dict[str, Any] | None = None
    column_name: str | None = None
    new_column_name: str | None = None  # rename_column
    new_type: str | None = None          # alter_column_type
    new_default: str | None = None       # alter_column_default
    new_nullable: bool | None = None     # alter_column_nullable
    index_name: str | None = None
    columns_indexed: list[str] = field(default_factory=list)
    new_name: str | None = None          # rename_table


def parse_operations(sql_text: str, *, dialect: str = "sqlite") -> list[Operation]:
    """Parse one or more SQL statements. Non-DDL statements are skipped."""
    ops: list[Operation] = []
    for parsed in sqlglot.parse(sql_text, dialect=dialect):
        if parsed is None:
            continue
        if isinstance(parsed, exp.Create):
            ops.append(_handle_create(parsed))
        elif isinstance(parsed, exp.AlterTable):
            ops.extend(_handle_alter(parsed))
        elif isinstance(parsed, exp.Drop):
            ops.append(_handle_drop(parsed))
        # SELECT / UPDATE / INSERT / DELETE handled by db_access path, not here.
    return [op for op in ops if op is not None]


def _column_dict(coldef: exp.ColumnDef) -> dict[str, Any]:
    name = coldef.name
    type_expr = coldef.args.get("kind")
    type_text = type_expr.sql() if type_expr else "UNKNOWN"
    constraints = coldef.args.get("constraints") or []
    nullable = True
    primary_key = False
    default = None
    for c in constraints:
        ck = c.kind if hasattr(c, "kind") else None
        if isinstance(ck, exp.NotNullColumnConstraint):
            nullable = False
        elif isinstance(ck, exp.PrimaryKeyColumnConstraint):
            primary_key = True
        elif isinstance(ck, exp.DefaultColumnConstraint):
            default = ck.this.sql() if ck.this else None
    return {"name": name, "type": type_text, "nullable": nullable,
            "default": default, "primary_key": primary_key}


def _handle_create(node: exp.Create) -> Operation:
    target = node.args.get("kind", "").upper()
    if target == "TABLE":
        schema = node.this
        table_name = schema.this.name if hasattr(schema.this, "name") else schema.name
        columns = []
        foreign_keys = []
        for col in schema.expressions:
            if isinstance(col, exp.ColumnDef):
                columns.append(_column_dict(col))
            elif isinstance(col, exp.PrimaryKey):
                # PRIMARY KEY (a, b) at table level
                pk_cols = [c.name for c in col.expressions]
                for cd in columns:
                    if cd["name"] in pk_cols:
                        cd["primary_key"] = True
            elif isinstance(col, exp.ForeignKey):
                local_cols = [c.name for c in col.expressions]
                ref = col.args.get("reference")
                if ref:
                    ref_table = ref.this.this.name if hasattr(ref.this, "this") else ""
                    ref_cols = [e.name for e in (ref.this.expressions or [])]
                    for lc, rc in zip(local_cols, ref_cols or [""]):
                        foreign_keys.append({"column": lc, "references_table": ref_table,
                                              "references_column": rc})
        return Operation(kind="create_table", table=table_name,
                          if_not_exists=bool(node.args.get("exists")),
                          columns=columns, foreign_keys=foreign_keys)
    if target == "INDEX":
        index_name = node.this.this.name if hasattr(node.this, "this") else ""
        params = node.args.get("params") or {}
        table = ""
        cols = []
        if hasattr(node, "args"):
            schema = node.args.get("this")
            if hasattr(schema, "args"):
                tbl = schema.args.get("table")
                if tbl:
                    table = tbl.name
                for e in (schema.expressions or []):
                    if hasattr(e, "name"):
                        cols.append(e.name)
        return Operation(kind="create_index", index_name=index_name,
                          table=table, columns_indexed=cols)
    if target == "VIEW":
        return Operation(kind="create_view", table=node.this.name)
    return Operation(kind="unsupported_create")


def _handle_alter(node: exp.AlterTable) -> list[Operation]:
    table = node.this.name
    ops: list[Operation] = []
    for action in (node.args.get("actions") or []):
        if isinstance(action, exp.ColumnDef):
            ops.append(Operation(kind="alter_add_column", table=table,
                                  column=_column_dict(action)))
        elif isinstance(action, exp.Drop):
            ops.append(Operation(kind="alter_drop_column", table=table,
                                  column_name=action.this.name if hasattr(action.this, "name") else str(action.this)))
        elif isinstance(action, exp.RenameTable):
            ops.append(Operation(kind="rename_table", table=table,
                                  new_name=action.this.name))
        elif isinstance(action, exp.RenameColumn):
            ops.append(Operation(
                kind="rename_column", table=table,
                column_name=action.this.name,
                new_column_name=action.args.get("to").name,
            ))
        elif isinstance(action, exp.AlterColumn):
            # ALTER COLUMN can change type, default, or nullability. Each
            # surfaces as a different arg on the action node. sqlglot's
            # exact representation varies — be defensive: check both
            # string-equality and isinstance for the NOT-NULL drop marker.
            col = action.this.name if hasattr(action.this, "name") else str(action.this)
            new_type = action.args.get("dtype")
            new_default = action.args.get("default")
            drop = action.args.get("drop")
            drops_not_null = drop is not None and (
                drop == "NOT NULL"
                or isinstance(drop, exp.NotNullColumnConstraint)
                or (hasattr(drop, "sql") and "NOT NULL" in drop.sql().upper())
            )
            allow_null = action.args.get("allow_null")
            if new_type is not None:
                ops.append(Operation(kind="alter_column_type", table=table,
                                       column_name=col, new_type=new_type.sql()))
            if new_default is not None:
                ops.append(Operation(kind="alter_column_default", table=table,
                                       column_name=col,
                                       new_default=new_default.sql() if hasattr(new_default, "sql") else str(new_default)))
            if drops_not_null:
                ops.append(Operation(kind="alter_column_nullable", table=table,
                                       column_name=col, new_nullable=True))
            if allow_null is not None:
                ops.append(Operation(kind="alter_column_nullable", table=table,
                                       column_name=col,
                                       new_nullable=bool(allow_null)))
    return ops


def _handle_drop(node: exp.Drop) -> Operation:
    target = node.args.get("kind", "").upper()
    if target == "TABLE":
        return Operation(kind="drop_table", table=node.this.name)
    return Operation(kind=f"drop_{target.lower()}", table=node.this.name)
```

> Note: sqlglot's AST shape varies by dialect and version. The implementation above tracks sqlglot 23.x. If a test fails on a particular construct, inspect the parsed tree with `print(parsed.dump())` and adjust the navigation. The Operation dataclass is the contract; how we get there is a sqlglot-version detail.

- [ ] **Step 5: Run, verify pass**

Run: `pytest depgraph/tests/lib/sql/test_parser.py -v`
Expected: 9 tests PASS. (If sqlglot's AST navigation differs from what's above, adjust `_handle_create` / `_handle_alter` until tests pass — the test assertions are the contract.)

- [ ] **Step 6: Commit**

```bash
git add depgraph/lib/sql/__init__.py depgraph/lib/sql/parser.py \
        depgraph/tests/lib/sql/test_parser.py depgraph/requirements.txt
git commit -m "depgraph/lib/sql: SQL DDL parser (sqlglot-backed, returns structured Operations)"
```

### Task 4.2: Migration file recognition + SQL string extraction

A migration is a Python file that performs schema changes. We recognize it by path (`migrations/*.py`) and content (contains at least one `text("...")` call passed to an `execute`-like callable). The extractor walks the AST, pulls each SQL string, runs it through `parse_operations`, and produces a list of `MigrationOperation` records attached to the migration module.

- [ ] **Step 1: Build fixture migrations**

```python
# depgraph/tests/lib/sql/fixtures/migrations/001_create_users.py
from sqlalchemy import text

def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email VARCHAR(255) NOT NULL
            )
        """))
```

```python
# depgraph/tests/lib/sql/fixtures/migrations/002_add_role.py
from sqlalchemy import text

def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50)"))
```

```python
# depgraph/tests/lib/sql/fixtures/migrations/003_drop_legacy_index.py
from sqlalchemy import text

def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX idx_users_email ON users(email)"))
```

```python
# depgraph/tests/lib/sql/fixtures/migrations/add_unnumbered_thing.py
from sqlalchemy import text

def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
```

```python
# depgraph/tests/lib/sql/fixtures/migrations/004_dynamic_sql.py
from sqlalchemy import text

def migrate(engine, cols):
    cols_sql = ", ".join(cols)
    # Dynamic interpolation — extractor should record a warning, not parse.
    with engine.connect() as conn:
        conn.execute(text(f"CREATE TABLE dynamic ({cols_sql})"))
```

- [ ] **Step 2: Write failing test**

```python
# depgraph/tests/lib/sql/test_migration.py
from pathlib import Path
from depgraph.lib.sql.migration import (
    is_migration_file, extract_migration, MigrationFile,
)

FIXTURES = Path(__file__).parent / "fixtures" / "migrations"


def test_recognizes_numbered_migration():
    assert is_migration_file(FIXTURES / "001_create_users.py") is True


def test_recognizes_unnumbered_migration_with_sql():
    assert is_migration_file(FIXTURES / "add_unnumbered_thing.py") is True


def test_rejects_non_migration_python():
    """A Python file outside a migrations/ directory or without text() calls."""
    p = FIXTURES.parent / "not_a_migration.py"
    p.write_text("def foo(): return 1\n")
    try:
        assert is_migration_file(p) is False
    finally:
        p.unlink()


def test_extract_migration_order_from_prefix():
    m = extract_migration(FIXTURES / "001_create_users.py")
    assert m.migration_order == 1
    assert m.operations[0].kind == "create_table"
    assert m.operations[0].table == "users"


def test_extract_migration_order_null_for_unnumbered():
    m = extract_migration(FIXTURES / "add_unnumbered_thing.py")
    assert m.migration_order is None
    assert m.operations[0].kind == "alter_add_column"


def test_extract_records_text_call_line():
    m = extract_migration(FIXTURES / "001_create_users.py")
    # The text(...) call is on line 5 in the fixture
    assert m.operations[0].source_line >= 5
    assert m.operations[0].source_line <= 12  # within the text(...) block


def test_dynamic_sql_recorded_as_warning_not_parsed():
    m = extract_migration(FIXTURES / "004_dynamic_sql.py")
    assert m.operations == []
    assert any("dynamic" in w.lower() or "interpolation" in w.lower()
               for w in m.warnings)
```

- [ ] **Step 3: Run, verify fail.**

- [ ] **Step 4: Implement `depgraph/lib/sql/migration.py`**

```python
"""Recognize Python migration files and extract embedded SQL.

Migration files are Python modules that execute SQL strings against a
database connection. Concorda's convention: `migrations/NNN_<slug>.py`
with a `migrate()` function that calls `conn.execute(text("..."))`.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from depgraph.lib.sql.parser import Operation, parse_operations


_ORDINAL_PREFIX = re.compile(r"^(\d+)_")


@dataclass
class MigrationOperation:
    """An Operation plus the source location it was extracted from."""
    operation: Operation
    source_line: int
    raw_sql: str

    # Convenience pass-throughs so tests can read `mo.kind` not `mo.operation.kind`
    @property
    def kind(self) -> str:
        return self.operation.kind

    @property
    def table(self) -> str | None:
        return self.operation.table


@dataclass
class MigrationFile:
    path: Path
    migration_order: int | None
    operations: list[MigrationOperation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def is_migration_file(path: Path) -> bool:
    """Path is in a migrations/ directory AND contains a text(...) call."""
    if "migrations" not in path.parts:
        return False
    if path.suffix != ".py":
        return False
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "text"):
            return True
    return False


def extract_migration(path: Path) -> MigrationFile:
    """Parse a migration file, extract every SQL string from text(...) calls,
    parse each into Operations, return MigrationFile with line metadata."""
    order = None
    m = _ORDINAL_PREFIX.match(path.name)
    if m:
        order = int(m.group(1))

    tree = ast.parse(path.read_text())
    result = MigrationFile(path=path, migration_order=order)

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "text"):
            continue
        arg = node.args[0] if node.args else None
        if arg is None:
            continue
        sql_text, dynamic_reason = _extract_string(arg)
        if dynamic_reason:
            result.warnings.append(
                f"line {node.lineno}: dynamic SQL skipped ({dynamic_reason})")
            continue
        ops = parse_operations(sql_text)
        for op in ops:
            result.operations.append(MigrationOperation(
                operation=op, source_line=node.lineno, raw_sql=sql_text,
            ))
    return result


def _extract_string(expr: ast.expr) -> tuple[str, str | None]:
    """Return (sql_text, dynamic_reason). dynamic_reason is non-None when
    the expression can't be reduced to a literal string at parse time."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value, None
    if isinstance(expr, ast.JoinedStr):  # f-string
        parts = []
        for v in expr.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                return "", "f-string interpolation"
        return "".join(parts), None
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        l, lr = _extract_string(expr.left)
        r, rr = _extract_string(expr.right)
        if lr or rr:
            return "", lr or rr
        return l + r, None
    return "", "non-literal SQL expression"
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest depgraph/tests/lib/sql/test_migration.py -v
```

- [ ] **Step 6: Commit**

```bash
git add depgraph/lib/sql/migration.py depgraph/tests/lib/sql/test_migration.py \
        depgraph/tests/lib/sql/fixtures/migrations/
git commit -m "depgraph/lib/sql: migration file recognition + embedded SQL extraction"
```

### Task 4.3: Schema reconciliation across ordered migrations

After all migration files are extracted, replay their operations in `migration_order` to produce the final-state schema primitives. Tables added by an early `CREATE TABLE` and modified by later `ALTER TABLE` end up with the union of columns. Columns dropped by `ALTER TABLE DROP COLUMN` disappear. Tables dropped by `DROP TABLE` are archived (not present in the live corpus). Unordered migrations (filename without ordinal prefix) replay after the ordered ones in filename order.

- [ ] **Step 1: Write failing test**

```python
# depgraph/tests/lib/sql/test_reconcile.py
from pathlib import Path
from depgraph.lib.sql.migration import extract_migration
from depgraph.lib.sql.reconcile import reconcile_schema, SchemaPrimitive

FIXTURES = Path(__file__).parent / "fixtures" / "migrations"


def _load_all():
    files = sorted(FIXTURES.glob("*.py"))
    return [extract_migration(f) for f in files]


def test_create_table_produces_schema_primitive():
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    assert "users" in tables
    user = tables["users"]
    assert user.kind == "schema"
    assert {col["name"] for col in user.columns} == {"id", "email", "role", "bio"}


def test_alter_add_column_extends_table():
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    user = tables["users"]
    role = next(c for c in user.columns if c["name"] == "role")
    assert role["type"] == "VARCHAR(50)"


def test_unnumbered_migration_runs_after_ordered():
    """add_unnumbered_thing.py adds `bio` to users. It has no ordinal,
    so it runs after the ordered migrations. The final `users` table
    must include `bio`."""
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    bio = next(c for c in tables["users"].columns if c["name"] == "bio")
    assert bio["type"] == "TEXT"


def test_schema_primitive_id_shape():
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    user = tables["users"]
    assert user.id == "fixture::schema::users"


def test_schema_primitive_source_points_at_creating_migration():
    """The schema primitive's source.path is the migration that CREATE'd it.
    Later ALTER migrations are recorded as additional `defines` edges, but
    the primitive's source field stays anchored to its origin."""
    migrations = _load_all()
    tables = {t.name: t for t in reconcile_schema(migrations, repo_key="fixture")}
    user = tables["users"]
    assert user.source["path"].endswith("001_create_users.py")


def test_alter_column_type_updates_in_place():
    """A migration that runs `ALTER TABLE users ALTER COLUMN email TYPE TEXT`
    should leave the final-state column with type TEXT."""
    from depgraph.lib.sql.migration import MigrationFile, MigrationOperation
    from depgraph.lib.sql.parser import Operation, parse_operations
    base = MigrationFile(
        path=Path("/fake/001_init.py"), migration_order=1,
        operations=[MigrationOperation(
            operation=parse_operations(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(64))"
            )[0],
            source_line=1, raw_sql="",
        )],
    )
    alter = MigrationFile(
        path=Path("/fake/002_widen.py"), migration_order=2,
        operations=[MigrationOperation(
            operation=Operation(kind="alter_column_type", table="users",
                                  column_name="email", new_type="VARCHAR(255)"),
            source_line=1, raw_sql="",
        )],
    )
    tables = {t.name: t for t in reconcile_schema([base, alter], repo_key="fixture")}
    email = next(c for c in tables["users"].columns if c["name"] == "email")
    assert email["type"] == "VARCHAR(255)"


def test_drop_column_garbage_collects_index_and_fk():
    """Dropping a column removes any index/FK that referenced it."""
    from depgraph.lib.sql.migration import MigrationFile, MigrationOperation
    from depgraph.lib.sql.parser import Operation
    create = MigrationFile(
        path=Path("/fake/001_init.py"), migration_order=1,
        operations=[MigrationOperation(
            operation=Operation(
                kind="create_table", table="users",
                columns=[{"name": "id", "type": "INTEGER", "nullable": False,
                            "default": None, "primary_key": True},
                          {"name": "team_id", "type": "INTEGER", "nullable": True,
                            "default": None, "primary_key": False}],
                foreign_keys=[{"column": "team_id", "references_table": "teams",
                                 "references_column": "id"}],
            ),
            source_line=1, raw_sql="",
        )],
    )
    add_idx = MigrationFile(
        path=Path("/fake/002_idx.py"), migration_order=2,
        operations=[MigrationOperation(
            operation=Operation(kind="create_index", index_name="idx_users_team",
                                  table="users", columns_indexed=["team_id"]),
            source_line=1, raw_sql="",
        )],
    )
    drop_col = MigrationFile(
        path=Path("/fake/003_drop.py"), migration_order=3,
        operations=[MigrationOperation(
            operation=Operation(kind="alter_drop_column", table="users",
                                  column_name="team_id"),
            source_line=1, raw_sql="",
        )],
    )
    tables = {t.name: t for t in reconcile_schema(
        [create, add_idx, drop_col], repo_key="fixture")}
    users = tables["users"]
    assert all(c["name"] != "team_id" for c in users.columns)
    assert users.indexes == [], f"orphan index left behind: {users.indexes}"
    assert users.foreign_keys == [], f"dangling FK left behind: {users.foreign_keys}"


def test_drop_table_clears_incoming_fks():
    """Dropping a referenced table removes FKs pointing at it from other tables."""
    from depgraph.lib.sql.migration import MigrationFile, MigrationOperation
    from depgraph.lib.sql.parser import Operation
    create_teams = MigrationFile(
        path=Path("/fake/001.py"), migration_order=1,
        operations=[MigrationOperation(
            operation=Operation(kind="create_table", table="teams",
                                  columns=[{"name": "id", "type": "INTEGER",
                                              "nullable": False, "default": None,
                                              "primary_key": True}]),
            source_line=1, raw_sql="",
        )],
    )
    create_users = MigrationFile(
        path=Path("/fake/002.py"), migration_order=2,
        operations=[MigrationOperation(
            operation=Operation(kind="create_table", table="users",
                                  columns=[{"name": "id", "type": "INTEGER",
                                              "nullable": False, "default": None,
                                              "primary_key": True},
                                            {"name": "team_id", "type": "INTEGER",
                                              "nullable": True, "default": None,
                                              "primary_key": False}],
                                  foreign_keys=[{"column": "team_id",
                                                   "references_table": "teams",
                                                   "references_column": "id"}]),
            source_line=1, raw_sql="",
        )],
    )
    drop_teams = MigrationFile(
        path=Path("/fake/003.py"), migration_order=3,
        operations=[MigrationOperation(
            operation=Operation(kind="drop_table", table="teams"),
            source_line=1, raw_sql="",
        )],
    )
    tables = {t.name: t for t in reconcile_schema(
        [create_teams, create_users, drop_teams], repo_key="fixture")}
    assert "teams" not in tables
    assert tables["users"].foreign_keys == []
```

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Implement `depgraph/lib/sql/reconcile.py`**

```python
"""Replay ordered migration operations to produce final-state schema primitives.

Input: list of MigrationFile (each with operations[] + migration_order).
Output: list of SchemaPrimitive (one per surviving table).

Ordering rules:
- Migrations with `migration_order != None` run first, sorted by that int.
- Migrations with `migration_order == None` run after, sorted by filename.
- Tables touched by later `ALTER TABLE` accumulate the column changes.
- Tables dropped by `DROP TABLE` are removed from the output set.
- `CREATE INDEX` emits a references edge from the table primitive to the
  indexed column (stored on the table's `attributes.indexes[]`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from depgraph.lib.sql.migration import MigrationFile


@dataclass
class SchemaPrimitive:
    """A reconciled table after replaying all migrations."""
    id: str
    name: str
    kind: str = "schema"
    primitive: str = "class"
    columns: list[dict[str, Any]] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)
    indexes: list[dict[str, Any]] = field(default_factory=list)
    source: dict[str, Any] = field(default_factory=dict)
    defined_by: list[str] = field(default_factory=list)  # migration paths
    schema_version: int = 2


def _ordered(migrations: list[MigrationFile]) -> list[MigrationFile]:
    numbered = sorted(
        [m for m in migrations if m.migration_order is not None],
        key=lambda m: m.migration_order,
    )
    unnumbered = sorted(
        [m for m in migrations if m.migration_order is None],
        key=lambda m: m.path.name,
    )
    return numbered + unnumbered


def reconcile_schema(migrations: list[MigrationFile], *, repo_key: str) -> list[SchemaPrimitive]:
    tables: dict[str, SchemaPrimitive] = {}

    for migration in _ordered(migrations):
        mig_path = str(migration.path)
        for mo in migration.operations:
            op = mo.operation
            if op.kind == "create_table":
                if op.table in tables:
                    # IF NOT EXISTS — silently skip; otherwise overwrite would
                    # be a data loss, so we log it as a defined_by event.
                    if op.if_not_exists:
                        tables[op.table].defined_by.append(mig_path)
                        continue
                tables[op.table] = SchemaPrimitive(
                    id=f"{repo_key}::schema::{op.table}",
                    name=op.table,
                    columns=list(op.columns),
                    foreign_keys=list(op.foreign_keys),
                    source={
                        "repo": repo_key,
                        "path": migration.path.relative_to(migration.path.parent.parent).as_posix(),
                        "language": "sql",
                        "line": mo.source_line,
                        "end_line": mo.source_line,
                    },
                    defined_by=[mig_path],
                )
            elif op.kind == "alter_add_column":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue  # ALTER on a table we never saw; treat as no-op
                tbl.columns.append(op.column)
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_drop_column":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                tbl.columns = [c for c in tbl.columns if c["name"] != op.column_name]
                # GC: drop any index that referenced this column; drop any
                # FK pointing at or originating from this column.
                tbl.indexes = [idx for idx in tbl.indexes
                               if op.column_name not in idx.get("columns", [])]
                tbl.foreign_keys = [fk for fk in tbl.foreign_keys
                                    if fk.get("column") != op.column_name]
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_column_type":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["type"] = op.new_type
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_column_default":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["default"] = op.new_default
                tbl.defined_by.append(mig_path)
            elif op.kind == "alter_column_nullable":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["nullable"] = bool(op.new_nullable)
                tbl.defined_by.append(mig_path)
            elif op.kind == "rename_column":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                for c in tbl.columns:
                    if c["name"] == op.column_name:
                        c["name"] = op.new_column_name
                # Rewrite references to the old column name in indexes / FKs
                for idx in tbl.indexes:
                    idx["columns"] = [op.new_column_name if n == op.column_name else n
                                       for n in idx.get("columns", [])]
                for fk in tbl.foreign_keys:
                    if fk.get("column") == op.column_name:
                        fk["column"] = op.new_column_name
                tbl.defined_by.append(mig_path)
            elif op.kind == "drop_table":
                tables.pop(op.table, None)
                # GC: any other table's FK pointing at this one is now dangling.
                for other in tables.values():
                    other.foreign_keys = [fk for fk in other.foreign_keys
                                           if fk.get("references_table") != op.table]
            elif op.kind == "rename_table":
                tbl = tables.pop(op.table, None)
                if tbl is None:
                    continue
                # Rewrite incoming FKs from any other table that referenced the old name
                for other in tables.values():
                    for fk in other.foreign_keys:
                        if fk.get("references_table") == op.table:
                            fk["references_table"] = op.new_name
                tbl.name = op.new_name
                tbl.id = f"{repo_key}::schema::{op.new_name}"
                tbl.defined_by.append(mig_path)
                tables[op.new_name] = tbl
            elif op.kind == "create_index":
                tbl = tables.get(op.table)
                if tbl is None:
                    continue
                tbl.indexes.append({"name": op.index_name, "columns": op.columns_indexed})
                tbl.defined_by.append(mig_path)

    return list(tables.values())
```

- [ ] **Step 4: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/sql/test_reconcile.py -v
git add depgraph/lib/sql/reconcile.py depgraph/tests/lib/sql/test_reconcile.py
git commit -m "depgraph/lib/sql: schema reconciliation over ordered migrations"
```

### Task 4.4: Emit schema primitives + per-statement primitive ids

The reconciled `SchemaPrimitive` dataclass needs to convert into the wire-format primitive shape that the rest of the pipeline reads. Plus each per-column primitive needs its own id so logigraph claims can target individual columns ("the email column is unique").

- [ ] **Step 1: Write failing test**

```python
# depgraph/tests/lib/sql/test_reconcile.py (append)
from depgraph.lib.sql.reconcile import schema_to_primitives

def test_schema_to_primitives_table_class_plus_column_variables():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    # One class per table
    classes = [p for p in prims if p["primitive"] == "class"]
    assert {p["name"] for p in classes} == {"users"}
    # One variable per column (id, email, role, bio)
    variables = [p for p in prims if p["primitive"] == "variable"]
    assert {p["name"] for p in variables} == {
        "users.id", "users.email", "users.role", "users.bio",
    }
    # Column variables owned by table class
    email = next(v for v in variables if v["name"] == "users.email")
    assert email["owner"] == "fixture::schema::users"
    assert email["signature"]["type_annotation"] == "VARCHAR(255)"
    assert email["attributes"]["nullable"] is False


def test_table_primitive_has_kind_schema():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    classes = [p for p in prims if p["primitive"] == "class"]
    assert all(p["kind"] == "schema" for p in classes)


def test_column_primitive_id_format():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    email = next(p for p in prims if p["name"] == "users.email")
    assert email["id"] == "fixture::schema::users.email"
```

- [ ] **Step 2: Run, verify fail.**

- [ ] **Step 3: Extend `depgraph/lib/sql/reconcile.py`**

Add to the bottom of the file:

```python
from depgraph.lib.primitives import compute_hash, structural_hash_payload

EXTRACTOR_TAG = "depgraph/lib/sql/reconcile.py@2026-05-16"


def schema_to_primitives(tables: list[SchemaPrimitive]) -> list[dict]:
    """Convert SchemaPrimitive dataclasses into wire-format primitive dicts.
    One class primitive per table; one variable primitive per column.

    Hash payloads use the spec-aligned shape (primitive / name / signature
    / body_text) via `structural_hash_payload` — same as Python and TS
    extractors. A schema-sourced `users` class and a Python `users` class
    hash differently because their `signature` differs, but the *payload
    shape* is identical across languages.
    """
    prims: list[dict] = []
    for t in tables:
        table_id = t.id
        table_signature = {
            "decorators": [],
            "primary_key": [c["name"] for c in t.columns if c.get("primary_key")],
            "foreign_keys": list(t.foreign_keys),
            "indexes": list(t.indexes),
        }
        table_body = repr([
            {"name": c["name"], "type": c["type"], "nullable": c["nullable"],
             "default": c.get("default")}
            for c in t.columns
        ])
        table_prim = {
            "schema_version": 2,
            "id": table_id,
            "primitive": "class",
            "name": t.name,
            "owner": None,
            "source": dict(t.source),
            "signature": table_signature,
            "attributes": {
                "abstract": False, "generated": False, "external": False,
                "template_parameters": [], "macro": False, "mutable": False,
                "instantiable": True, "inheritable": False,
                "defined_by": list(t.defined_by),
            },
            "edges_out": [],
            "structural_hash": compute_hash(structural_hash_payload(
                primitive="class", name=t.name,
                signature=table_signature, body_text=table_body,
            )),
            "kind": "schema",
            "extractor": EXTRACTOR_TAG,
        }
        prims.append(table_prim)

        for c in t.columns:
            col_id = f"{table_id}.{c['name']}"
            col_signature = {
                "type_annotation": c["type"],
                "value_text": c.get("default"),
            }
            col_body = c.get("default") or ""
            prims.append({
                "schema_version": 2,
                "id": col_id,
                "primitive": "variable",
                "name": f"{t.name}.{c['name']}",
                "owner": table_id,
                "source": dict(t.source),
                "signature": col_signature,
                "attributes": {
                    "abstract": False, "generated": False, "external": False,
                    "template_parameters": [], "macro": False,
                    "mutable": True, "instantiable": False, "inheritable": False,
                    "nullable": c["nullable"], "primary_key": c.get("primary_key", False),
                    "default": c.get("default"),
                },
                "edges_out": [],
                "structural_hash": compute_hash(structural_hash_payload(
                    primitive="variable", name=f"{t.name}.{c['name']}",
                    signature=col_signature, body_text=col_body,
                )),
                "kind": None,
                "extractor": EXTRACTOR_TAG,
            })
    return prims
```

Notes:
- Both `primary_key` and `foreign_keys` move from `attributes` into `signature` for the table primitive so they participate in hash. Two tables with the same columns but different FKs are structurally different.
- Column nullability lives in `attributes` (cross-language invariant) but also in `signature.value_text` if a default exists — same pattern as Python's class-scope variables.
- `_hash` private function removed; we use `compute_hash` from `depgraph/lib/primitives.py`. One implementation of the hash, period.

- [ ] **Step 4: Run, verify pass + commit**

### Task 4.5: ORM model → schema cross-reference

After the Python extractor has emitted ORM model classes (Python `class User(Base): __tablename__ = "users"`) and the SQL pipeline has emitted schema primitives, a post-pass connects them via `references` edges.

- [ ] **Step 1: Fixture**

```python
# depgraph/tests/lib/sql/fixtures/orm_models/models/user.py
from .base import Base

class User(Base):
    __tablename__ = "users"
    # In real ORM models columns are defined here too, but we only need
    # tablename for the cross-reference test.
```

```python
# depgraph/tests/lib/sql/fixtures/orm_models/models/base.py
class Base:
    pass
```

- [ ] **Step 2: Write failing test**

```python
# depgraph/tests/lib/sql/test_cross_ref.py
from pathlib import Path
from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.sql.cross_ref import attach_model_schema_references

FIXTURES = Path(__file__).parent / "fixtures"


def test_model_class_references_matching_schema():
    """User Python class with __tablename__='users' references the
    SQL-sourced users table."""
    py_prims = list(extract_repo(repo_key="fixture",
                                  repo_path=FIXTURES / "orm_models"))
    schema_prims = [{
        "id": "fixture::schema::users",
        "primitive": "class", "name": "users", "owner": None,
        "source": {"repo": "fixture", "path": "schema/users",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }]
    all_prims = py_prims + schema_prims
    attach_model_schema_references(all_prims)
    user_class = next(p for p in all_prims
                      if p["name"] == "User" and p["primitive"] == "class")
    refs = [e for e in user_class["edges_out"] if e["kind"] == "references"]
    assert any(e["target"] == "fixture::schema::users" for e in refs)


def test_model_with_no_tablename_no_reference():
    """A Python class without __tablename__ does not get a schema reference,
    even if a matching schema primitive exists by name."""
    py_prims = [{
        "id": "fixture::orm/other.py::Other",
        "primitive": "class", "name": "Other", "owner": None,
        "source": {"repo": "fixture", "path": "orm/other.py",
                   "language": "python", "line": 1, "end_line": 2},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": None,
        "extractor": "test", "schema_version": 2,
    }]
    schema_prims = [{
        "id": "fixture::schema::Other", "primitive": "class", "name": "Other",
        "owner": None,
        "source": {"repo": "fixture", "path": "schema/Other",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }]
    all_prims = py_prims + schema_prims
    attach_model_schema_references(all_prims)
    other = py_prims[0]
    refs = [e for e in other["edges_out"] if e["kind"] == "references"]
    assert refs == []
```

- [ ] **Step 3: Run, verify fail.**

- [ ] **Step 4: Implement `depgraph/lib/sql/cross_ref.py`**

```python
"""Cross-reference ORM mapper classes to their schema-sourced counterparts.

For each Python class that has a class-scoped variable `__tablename__`
bound to a string literal AND extends a known ORM base class, emit a
`references` edge to the schema primitive whose name matches.

The variable primitive for `__tablename__` is produced by Phase 2;
its RHS expression is recorded in `signature.value_text` (the canonical
field for raw initializer text, set by Task 2.3's `_variable_primitives`).
"""
from __future__ import annotations

import ast
from pathlib import Path


def attach_model_schema_references(primitives: list[dict]) -> list[dict]:
    """In-place: append `references` edges from each ORM model class to
    the schema-sourced class with matching name."""
    schema_by_name: dict[str, str] = {
        p["id"].split("::schema::", 1)[-1]: p["id"]
        for p in primitives
        if p.get("kind") == "schema" and "::schema::" in p["id"]
        and p["primitive"] == "class"
    }
    if not schema_by_name:
        return primitives

    # Index Python class primitives by their id and find their __tablename__
    classes_by_id = {
        p["id"]: p for p in primitives
        if p["primitive"] == "class" and p["source"]["language"] == "python"
    }
    tablename_by_class: dict[str, str] = {}
    for p in primitives:
        if (p["primitive"] == "variable"
                and p.get("owner") in classes_by_id
                and p["name"].endswith(".__tablename__")):
            # Task 2.3 records the RHS as signature.value_text. For
            # `__tablename__ = "users"`, value_text is `'"users"'` (the
            # string with quotes preserved by ast.unparse).
            tablename_value = _string_literal(p["signature"].get("value_text"))
            if tablename_value:
                tablename_by_class[p["owner"]] = tablename_value

    for class_id, tablename in tablename_by_class.items():
        schema_id = schema_by_name.get(tablename)
        if not schema_id:
            continue
        cls = classes_by_id[class_id]
        cls["edges_out"].append({
            "target": schema_id, "kind": "references",
            "via": "__tablename__",
            "where": f"{cls['source']['path']}:{cls['source']['line']}",
            "confidence": "exact",
        })
    return primitives


def _string_literal(value_text: str | None) -> str | None:
    """Unwrap a Python string literal expression to its content. Inputs come
    from `ast.unparse(node.value)`, so `"users"` → `users`. Non-literal
    expressions (concatenations, format strings) return None — we don't
    evaluate dynamic table names."""
    if not value_text:
        return None
    text = value_text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return None
```

- [ ] **Step 5: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/sql/test_cross_ref.py -v
git add depgraph/lib/sql/cross_ref.py depgraph/tests/lib/sql/test_cross_ref.py \
        depgraph/tests/lib/sql/fixtures/orm_models/
git commit -m "depgraph/lib/sql: ORM model → schema reference post-pass"
```

### Task 4.6: db_access edges target schema-sourced primitives

The final piece: when the recognizer sees `session.query(User)` in a Python function body, it resolves `User` to the local Python class primitive, follows the `references` edge to the schema primitive, and emits the `db_access` edge targeting the schema. This replaces the synthetic-terminal stub.

- [ ] **Step 1: Fixture**

```python
# depgraph/tests/lib/test_db_access_fixtures/src.py
from sqlalchemy.orm import Session
from .models import User  # ORM model class

def get_user(session: Session, user_id):
    return session.query(User).filter(User.id == user_id).first()

def save_user(session: Session, user):
    session.add(user)
    session.commit()
```

```python
# depgraph/tests/lib/test_db_access_fixtures/models.py
class Base: pass

class User(Base):
    __tablename__ = "users"
```

- [ ] **Step 2: Write failing test**

```python
# depgraph/tests/lib/test_db_access.py
from pathlib import Path
from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.sql.cross_ref import attach_model_schema_references
from depgraph.lib.system_stub.db_access import attach_db_access_edges

FIXTURE = Path(__file__).parent / "test_db_access_fixtures"


def _setup_corpus():
    """Extract Python primitives + add a schema primitive for the users table."""
    py_prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE))
    schema_prim = {
        "id": "fixture::schema::users", "primitive": "class", "name": "users",
        "owner": None,
        "source": {"repo": "fixture", "path": "schema/users",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }
    all_prims = py_prims + [schema_prim]
    attach_model_schema_references(all_prims)
    return all_prims


def test_session_query_targets_schema_primitive():
    prims = _setup_corpus()
    attach_db_access_edges(prims, repo_path=FIXTURE)
    fn = next(p for p in prims if p["name"] == "get_user")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    targets = {e["target"] for e in dba}
    assert "fixture::schema::users" in targets


def test_session_add_targets_schema_primitive_via_inferred_type():
    """`session.add(user)` — `user` is a function parameter typed `User`.
    Resolve via the parameter annotation if present; otherwise emit
    unresolved with the function name as `via`."""
    prims = _setup_corpus()
    attach_db_access_edges(prims, repo_path=FIXTURE)
    fn = next(p for p in prims if p["name"] == "save_user")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    # save_user's `user` param has no type annotation in the fixture, so
    # session.add(user) resolves as unresolved.
    add_edges = [e for e in dba if "add" in e["via"]]
    assert any(e["confidence"] == "unresolved" for e in add_edges)


def test_orphan_query_target_emits_unresolved(tmp_path):
    """session.query(NotInCorpus) — emit edge with confidence=unresolved.

    Uses pytest's tmp_path so the test doesn't mutate the committed fixture
    dir and can run concurrently with sibling tests."""
    # Copy the fixture into tmp_path and add a misc.py with an unknown query
    import shutil
    work = tmp_path / "fixture"
    shutil.copytree(FIXTURE, work)
    (work / "misc.py").write_text(
        "def strange_query(session):\n"
        "    return session.query(NoSuchClass).all()\n"
    )

    py_prims = list(extract_repo(repo_key="fixture", repo_path=work))
    schema_prim = {
        "id": "fixture::schema::users", "primitive": "class", "name": "users",
        "owner": None,
        "source": {"repo": "fixture", "path": "schema/users",
                   "language": "sql", "line": 1, "end_line": 1},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "test", "schema_version": 2,
    }
    all_prims = py_prims + [schema_prim]
    attach_model_schema_references(all_prims)
    attach_db_access_edges(all_prims, repo_path=work)

    fn = next(p for p in all_prims if p["name"] == "strange_query")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    assert any(e["confidence"] == "unresolved" for e in dba)
```

- [ ] **Step 3: Run, verify fail.**

- [ ] **Step 4: Implement `depgraph/lib/system_stub/db_access.py`** (rewrite — replaces the synthetic-terminal version)

```python
"""db_access edge recognition — targets schema-sourced primitives.

The pipeline:
  1. Recognize `session.query(X)`, `db.add(x)`, `cursor.execute(text("..."))`
     and similar SDK patterns inside Python function bodies.
  2. Resolve the argument to a Python class primitive (via local symbol
     index + import resolution).
  3. Follow the Python class's `references → schema` edge to find the
     schema primitive.
  4. Emit db_access edge from the calling function to the schema primitive
     with confidence=exact.

Fallbacks:
- If the argument doesn't resolve to a known class, emit confidence=unresolved
  with the function name as `via` and no target (or `external::unresolved::<symbol>` if a
  target field is required).
- If the argument resolves to a Python class with no schema reference, emit
  confidence=unresolved targeting the Python class.
- For `cursor.execute(text("SELECT ... FROM users ..."))` (raw SQL outside
  migrations), parse the SQL with sqlglot, identify each referenced table,
  emit one db_access edge per table.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import sqlglot
from sqlglot import expressions as exp


_SESSION_METHODS = {"query", "add", "commit", "execute", "scalars",
                     "scalar", "delete", "merge", "flush", "rollback"}
_CURSOR_METHODS = {"execute", "executemany", "fetchone", "fetchall", "fetchmany"}


def attach_db_access_edges(primitives: list[dict], *, repo_path: Path) -> list[dict]:
    schema_by_name = {
        p["name"]: p["id"] for p in primitives
        if p.get("kind") == "schema" and p["primitive"] == "class"
    }
    # Python class id -> schema id (via references edges)
    py_class_to_schema: dict[str, str] = {}
    py_classes_by_id: dict[str, dict] = {}
    for p in primitives:
        if p["primitive"] == "class" and p["source"]["language"] == "python":
            py_classes_by_id[p["id"]] = p
            for e in p["edges_out"]:
                if e["kind"] == "references" and e["target"] in schema_by_name.values():
                    py_class_to_schema[p["id"]] = e["target"]

    # Build a per-file local-name -> python-class-id index
    by_path: dict[str, list[dict]] = {}
    for p in primitives:
        if p["source"]["language"] != "python":
            continue
        by_path.setdefault(p["source"]["path"], []).append(p)

    for path, prims_in_file in by_path.items():
        local_names: dict[str, str] = {}
        for p in prims_in_file:
            if p["primitive"] == "class" and p.get("owner") is None:
                local_names[p["name"]] = p["id"]

        # Imported names: scan imports edges on the module primitive.
        # Per the import-edge convention (Phase 3.3), each import edge
        # carries `local_binding` = the name as bound in the importing
        # file. For `from X import User as TheUser`, local_binding =
        # "TheUser"; for unaliased imports, it equals the target symbol.
        module = next((p for p in prims_in_file if p["primitive"] == "module"), None)
        if module:
            for e in module["edges_out"]:
                if e["kind"] != "imports":
                    continue
                if e["target"] not in py_classes_by_id:
                    continue
                imported_cls = py_classes_by_id[e["target"]]
                local_binding = e.get("local_binding") or imported_cls["name"]
                local_names[local_binding] = e["target"]

        source_text = (repo_path / path).read_text()
        try:
            tree = ast.parse(source_text)
        except SyntaxError:
            continue
        fn_by_line = {p["source"]["line"]: p
                      for p in prims_in_file if p["primitive"] == "function"}

        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fn_prim = fn_by_line.get(fn_node.lineno)
            if not fn_prim:
                continue
            # Track local variable types from parameter annotations
            param_types: dict[str, str] = {}
            for arg in fn_node.args.args:
                if arg.annotation is not None:
                    ann = ast.unparse(arg.annotation)
                    param_types[arg.arg] = ann.split("[")[0].strip()

            for sub in ast.walk(fn_node):
                if not isinstance(sub, ast.Call):
                    continue
                if isinstance(sub.func, ast.Attribute):
                    method = sub.func.attr
                    receiver = ast.unparse(sub.func.value)
                    # Pattern A: session.<method>(...)
                    if method in _SESSION_METHODS:
                        _emit_session_edge(fn_prim, sub, method, receiver, path,
                                            local_names, py_class_to_schema, param_types)
                    # Pattern B: cursor.execute(text("..."))
                    if method in _CURSOR_METHODS:
                        _emit_cursor_edge(fn_prim, sub, method, receiver, path,
                                           schema_by_name)
    return primitives


def _emit_session_edge(fn_prim, call, method, receiver, path,
                       local_names, py_class_to_schema, param_types):
    """Resolve session.<method>(<arg>) target and emit edge."""
    arg = call.args[0] if call.args else None
    target_id, confidence = None, "unresolved"

    if isinstance(arg, ast.Name):
        # session.query(User) — resolve `User` via local names
        class_id = local_names.get(arg.id)
        if class_id and class_id in py_class_to_schema:
            target_id, confidence = py_class_to_schema[class_id], "exact"
        elif arg.id in param_types:
            # session.add(user) where user: User
            class_id = local_names.get(param_types[arg.id])
            if class_id and class_id in py_class_to_schema:
                target_id, confidence = py_class_to_schema[class_id], "exact"
    # else: text() call, attribute access, dynamic — unresolved

    fn_prim["edges_out"].append({
        "target": target_id or "external::unresolved::db_target",
        "kind": "db_access",
        "via": f"{receiver}.{method}",
        "where": f"{path}:{call.lineno}",
        "confidence": confidence,
    })


def _emit_cursor_edge(fn_prim, call, method, receiver, path, schema_by_name):
    """For cursor.execute(text("SELECT ... FROM <table>")), parse SQL and
    emit one edge per referenced table that resolves to a schema primitive."""
    arg = call.args[0] if call.args else None
    sql_text = None
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "text":
        if arg.args and isinstance(arg.args[0], ast.Constant) and isinstance(arg.args[0].value, str):
            sql_text = arg.args[0].value
    elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        sql_text = arg.value

    if not sql_text:
        fn_prim["edges_out"].append({
            "target": "external::unresolved::db_target", "kind": "db_access",
            "via": f"{receiver}.{method}", "where": f"{path}:{call.lineno}",
            "confidence": "unresolved",
        })
        return

    tables = _tables_referenced_by_sql(sql_text)
    if not tables:
        fn_prim["edges_out"].append({
            "target": "external::unresolved::db_target", "kind": "db_access",
            "via": f"{receiver}.{method}", "where": f"{path}:{call.lineno}",
            "confidence": "unresolved",
        })
        return

    for table_name in tables:
        target_id = schema_by_name.get(table_name)
        if target_id:
            fn_prim["edges_out"].append({
                "target": target_id, "kind": "db_access",
                "via": f"{receiver}.{method}(SQL)",
                "where": f"{path}:{call.lineno}",
                "confidence": "exact",
            })
        else:
            fn_prim["edges_out"].append({
                "target": f"external::unresolved::table::{table_name}",
                "kind": "db_access", "via": f"{receiver}.{method}(SQL)",
                "where": f"{path}:{call.lineno}", "confidence": "unresolved",
            })


def _tables_referenced_by_sql(sql_text: str) -> list[str]:
    """Return the list of table names that the SQL reads from or writes to."""
    try:
        parsed = sqlglot.parse(sql_text, dialect="sqlite")
    except sqlglot.errors.ParseError:
        return []
    names: list[str] = []
    for stmt in parsed:
        if stmt is None:
            continue
        for tbl in stmt.find_all(exp.Table):
            names.append(tbl.name)
    # Deduplicate while preserving order
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n); out.append(n)
    return out
```

- [ ] **Step 5: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/test_db_access.py -v
git add depgraph/lib/system_stub/ depgraph/tests/lib/test_db_access.py \
        depgraph/tests/lib/test_db_access_fixtures/
git commit -m "depgraph/system_stub: db_access edges target schema primitives via ORM model references"
```

### Task 4.7: Attach `up_operations[]` to migration module primitives

After extraction + reconciliation, each migration module primitive (emitted by the Python extractor as a regular `module` primitive at `concorda-api::migrations/047_organization_region.py`) gets an `attributes.migration_order` and an `attributes.up_operations` list containing the ids of the schema primitives it produced. Logigraph rules about migration discipline anchor on these.

- [ ] **Step 1: Failing test**

```python
# depgraph/tests/lib/sql/test_migration_attach.py
from pathlib import Path
from depgraph.lib.sql.migration import extract_migration
from depgraph.lib.sql.reconcile import reconcile_schema, schema_to_primitives
from depgraph.lib.sql.attach import attach_migration_attributes

FIXTURES = Path(__file__).parent / "fixtures" / "migrations"


def test_migration_module_gets_order_and_up_operations():
    # A synthetic module primitive as the Python extractor would emit
    module_prim = {
        "schema_version": 2,
        "id": "fixture::001_create_users.py",
        "primitive": "module",
        "name": "001_create_users.py",
        "owner": None,
        "source": {"repo": "fixture", "path": "001_create_users.py",
                   "language": "python", "line": 1, "end_line": 10},
        "signature": {}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None,
        "extractor": "test",
    }
    migrations = [extract_migration(FIXTURES / "001_create_users.py")]
    schemas = reconcile_schema(migrations, repo_key="fixture")
    schema_prims = schema_to_primitives(schemas)

    attach_migration_attributes(
        primitives=[module_prim] + schema_prims,
        migrations=migrations,
    )

    assert module_prim["attributes"].get("migration_order") == 1
    up_ops = module_prim["attributes"].get("up_operations", [])
    assert any("schema::users" in oid for oid in up_ops), up_ops
```

- [ ] **Step 2: Implement `depgraph/lib/sql/attach.py`**

```python
"""Attach migration metadata to module primitives.

Run after extraction + SQL reconciliation; mutates the matching module
primitive in place. Each migration file's `migration_order` becomes
`attributes.migration_order`; the ids of schema primitives it produced
become `attributes.up_operations`.
"""
from __future__ import annotations

from depgraph.lib.sql.migration import MigrationFile


def attach_migration_attributes(*, primitives: list[dict],
                                  migrations: list[MigrationFile]) -> None:
    # Build a map: filename -> migration_file
    by_filename = {m.path.name: m for m in migrations}

    # Build a map: table_name -> schema_primitive_id
    schema_by_name: dict[str, str] = {}
    for p in primitives:
        if p.get("kind") == "schema" and p["primitive"] == "class":
            schema_by_name[p["name"]] = p["id"]

    for p in primitives:
        if p["primitive"] != "module":
            continue
        # Path's basename is the migration filename
        path = p["source"]["path"]
        filename = path.rsplit("/", 1)[-1]
        mf = by_filename.get(filename)
        if mf is None:
            continue
        # Build up_operations: ids of schema primitives this migration
        # produced (one per CREATE TABLE / one per ALTER per column, etc.)
        up_op_ids: list[str] = []
        for mo in mf.operations:
            op = mo.operation
            if op.table and op.table in schema_by_name:
                # For CREATE/ALTER/DROP — point at the (current-state) schema id.
                # For a DROP that removed the table from the corpus, schema
                # won't exist; record as "external::dropped::<table>".
                up_op_ids.append(schema_by_name[op.table])
            elif op.table:
                up_op_ids.append(f"external::dropped::table::{op.table}")
        p["attributes"]["migration_order"] = mf.migration_order
        p["attributes"]["up_operations"] = up_op_ids
```

- [ ] **Step 3: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/sql/test_migration_attach.py -v
git add depgraph/lib/sql/attach.py depgraph/tests/lib/sql/test_migration_attach.py
git commit -m "depgraph/lib/sql: attach migration_order + up_operations[] to module primitives"
```

### Task 4.8: Schema validation sweep — emitted schema primitives validate

- [ ] **Step 1: Add sweep test**

```python
# depgraph/tests/lib/sql/test_reconcile.py (append)
from depgraph.lib.primitives import validate_primitive

def test_all_schema_primitives_validate():
    migrations = _load_all()
    tables = reconcile_schema(migrations, repo_key="fixture")
    prims = schema_to_primitives(tables)
    for p in prims:
        errors = validate_primitive(p)
        assert not errors, f"{p['id']}: {errors}"
```

- [ ] **Step 2: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/sql/test_reconcile.py::test_all_schema_primitives_validate -v
git commit -m "depgraph/lib/sql: schema validation gate for emitted schema primitives"
```

### Task 4.9: Author wild fixtures + Claude verification

The 8 Phase-4 wild fixtures exercise SQL extraction + reconciliation + cross-reference under pressure.

**Files:**
- Create: `depgraph/tests/fixtures/wild/sql/{multi_dialect_create,alembic_op_style,bare_sql_file,self_referential_fk,circular_fk,mixed_text_and_op,dynamic_sql_warning,alter_replay_chain}/`
- Create: `depgraph/tests/lib/sql/test_sql_wild.py`

- [ ] **Step 1: Author the 8 fixtures**

Critical assertions per fixture:

- **multi_dialect_create**: three migration files, one each in sqlite / postgres / mysql syntax, all logically equivalent (`id INTEGER PRIMARY KEY AUTOINCREMENT` vs `id SERIAL PRIMARY KEY` vs `id INT AUTO_INCREMENT PRIMARY KEY`). All three reconcile to a `users` table with identical column structure.
- **alembic_op_style**: a migration using `op.create_table("users", sa.Column("id", sa.Integer))`. The migration recognizer + SQL pipeline must produce a `users` schema primitive even though no `text(...)` call appears. *Note: if Alembic-style is out of v0 scope, document that explicitly in this fixture's README and mark expected.json with `unsupported: true`; the test asserts the warning instead.*
- **bare_sql_file**: a standalone `.sql` file with 3 CREATE TABLE statements. The SQL language extractor (from Task 0.4's language registry) must walk it; expected.json lists 3 schema primitives.
- **self_referential_fk**: `CREATE TABLE node (id INT, parent_id INT REFERENCES node(id))`. After reconciliation, the `node` schema's `foreign_keys` includes `parent_id → node.id`.
- **circular_fk**: tables A and B with FKs to each other (legal in postgres with deferred constraints; the parser must not crash).
- **mixed_text_and_op**: migration uses both `text("CREATE TABLE x ...")` and `op.add_column(...)`. Both paths fire; the resulting schema includes both shapes.
- **dynamic_sql_warning**: migration with `text(f"CREATE TABLE {table_name} (...)")` only. Expected: zero schema primitives, one warning entry on the migration module mentioning the line number.
- **alter_replay_chain**: a 6-migration sequence: CREATE → ALTER ADD col → ALTER TYPE col → RENAME col → DROP col → DROP TABLE. After replay, the table is absent (drop wins). A simpler control sequence ending without the final DROP confirms incremental reconciliation worked.

- [ ] **Step 2: Test harness**

```python
# depgraph/tests/lib/sql/test_sql_wild.py
import json
from pathlib import Path
import pytest

from depgraph.lib.sql.migration import extract_migration, is_migration_file
from depgraph.lib.sql.reconcile import reconcile_schema, schema_to_primitives

WILD_DIR = Path(__file__).parent.parent.parent / "fixtures" / "wild" / "sql"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_schema_matches_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    src = fixture / "src"
    migrations = [extract_migration(p) for p in sorted(src.rglob("*.py"))
                  if is_migration_file(p)]
    tables = reconcile_schema(migrations, repo_key="fixture")
    actual = {t.name: t for t in tables}
    expected_tables = {t["name"]: t for t in expected.get("tables", [])}
    assert set(actual) == set(expected_tables), (
        f"{fixture.name}: tables mismatch: actual={set(actual)} expected={set(expected_tables)}"
    )
    for name, t_actual in actual.items():
        t_expected = expected_tables[name]
        actual_cols = {c["name"] for c in t_actual.columns}
        expected_cols = set(t_expected["columns"])
        assert actual_cols == expected_cols, (
            f"{fixture.name}/{name}: columns mismatch: actual={actual_cols} expected={expected_cols}"
        )


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_warnings_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    expected_warnings = expected.get("expect_warnings", False)
    src = fixture / "src"
    migrations = [extract_migration(p) for p in sorted(src.rglob("*.py"))
                  if is_migration_file(p)]
    has_warnings = any(m.warnings for m in migrations)
    if expected_warnings:
        assert has_warnings, f"{fixture.name}: expected warnings but got none"
```

- [ ] **Step 3: Claude verification**

Especially scrutinize multi-dialect: it's the most likely to expose sqlglot version drift. Read each fixture's SQL, write down what columns each table should have, compare to expected.json, then to actual. Record the sqlglot version in `verification.md` so a future reviewer knows which version the gate was last sanity-checked against.

- [ ] **Step 4: Commit**

```bash
git add depgraph/tests/fixtures/wild/sql/ \
        depgraph/tests/lib/sql/test_sql_wild.py
git commit -m "depgraph: Phase 4 wild corpus (8 SQL pathological fixtures + Claude review)"
```

---

## Phase 5 — Classification Engine

**Goal:** Given a corpus of primitives + edges, decide a `kind` for each primitive that satisfies one of the kind rules. Write classified primitives to `nodes/<kind>/<slug>.json`. Write unclassified primitives to `nodes/<primitive_type>/<slug>.json`.

**Detection goals** (from spec table at line 296+):

| Kind | Rule |
|---|---|
| component | function/method whose body returns JSX OR PascalCase variable bound to an HOC call OR PascalCase alias of a known component |
| hook | function whose name matches `use<Capital>` AND calls another known hook or React built-in |
| endpoint | function decorated by a known route decorator (config-driven list of decorator names) |
| service | function with at least one `db_access` / `queue_produce` / `webhook_publish` / `notification_send` / `file_storage_access` edge AND transitively called from at least one endpoint |
| model | class with `extends` edge to a known ORM base class name (config-driven) |
| util | function called by at least one classified kind AND classifies as no other rule |
| test | function calling a known test framework primitive (config-driven list) |

Schema kind is deferred until schema-language extractors land. Controller is folded into endpoint for this pass.

**Files:**
- Create: `depgraph/lib/classification/engine.py`
- Create: `depgraph/lib/classification/{component,hook,endpoint,service,model,util,test_kind}.py`
- Create: `depgraph/lib/classification/config.py` (route decorators, ORM base names, test framework primitives)
- Test: `depgraph/tests/lib/test_classifier_*.py` (one file per classifier)
- Test: `depgraph/tests/lib/test_classification_engine.py`

### Task 5.1: Engine skeleton + config

- [ ] **Step 1: Test**

```python
# depgraph/tests/lib/test_classification_engine.py
from depgraph.lib.classification.engine import classify_corpus

def test_classify_corpus_returns_dict_id_to_decision():
    prims = [{
        "id": "x::y::Foo", "primitive": "function", "name": "Foo",
        "owner": None, "source": {"path": "y", "line": 1, "end_line": 1, "language": "typescript", "repo": "x"},
        "signature": {"decorators": []}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }]
    decisions = classify_corpus(prims)
    assert isinstance(decisions, dict)
    assert "x::y::Foo" in decisions
    # Decision is a dataclass; access by attribute. Default = unclassified.
    assert decisions["x::y::Foo"].kind is None
    assert decisions["x::y::Foo"].rule == "unclassified"
```

- [ ] **Step 2: Implement**

```python
# depgraph/lib/classification/engine.py
"""Classification engine — runs per-kind rules over (primitives + edges).

Each classifier module exports `classify(primitives, *, edges_by_source,
edges_by_target, config) -> dict[str, Decision]`. Engine merges decisions;
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
        for e in p["edges_out"]:
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
                                              evidence=ev["evidence"])
    return decisions
```

```python
# depgraph/lib/classification/config.py
"""Per-language cue maps for classification rules.

The classifier rule shapes are language-agnostic (e.g., "endpoint = function
decorated by a route registration"). The *cues* are per-language. This config
holds the cues so adding a new host language (Vue, Django, Yew, etc.) is a
matter of extending the maps, not editing classifier code.
"""
from dataclasses import dataclass, field

@dataclass
class LanguageCues:
    """Cues for one host language."""
    route_decorators: set[str] = field(default_factory=set)
    orm_base_classes: set[str] = field(default_factory=set)
    test_framework_primitives: set[str] = field(default_factory=set)
    hook_call_names: set[str] = field(default_factory=set)
    # Vias for cross-ref edges that mean "this class is the ORM mapper for
    # a schema." Used by the model classifier to distinguish mapper-style
    # references from incidental type references.
    orm_schema_link_vias: set[str] = field(default_factory=set)


@dataclass
class ClassificationConfig:
    """Aggregated cues across languages. Each classifier consumes the union
    or per-language subset as appropriate."""
    languages: dict[str, LanguageCues] = field(default_factory=dict)

    # Aggregated views, computed on access. Used by language-agnostic
    # classifiers (most of them).
    @property
    def route_decorators(self) -> set[str]:
        return {d for lang in self.languages.values() for d in lang.route_decorators}

    @property
    def orm_base_classes(self) -> set[str]:
        return {b for lang in self.languages.values() for b in lang.orm_base_classes}

    @property
    def test_framework_primitives(self) -> set[str]:
        return {p for lang in self.languages.values() for p in lang.test_framework_primitives}

    @property
    def hook_call_names(self) -> set[str]:
        return {h for lang in self.languages.values() for h in lang.hook_call_names}

    @property
    def orm_schema_link_vias(self) -> set[str]:
        return {v for lang in self.languages.values() for v in lang.orm_schema_link_vias}


def default_config() -> ClassificationConfig:
    """Cues that ship with the framework for JS/TS and Python.
    Per-project project.toml can extend this with custom cues."""
    return ClassificationConfig(languages={
        "python": LanguageCues(
            route_decorators={
                "router.get", "router.post", "router.put", "router.patch",
                "router.delete", "router.head", "router.options",
                "app.get", "app.post", "app.put", "app.patch", "app.delete",
            },
            orm_base_classes={
                "DeclarativeBase", "Base", "BaseModel",  # SQLAlchemy + project
            },
            test_framework_primitives={
                "pytest.fixture", "pytest.mark", "pytest.raises",
            },
            orm_schema_link_vias={"__tablename__"},
        ),
        "typescript": LanguageCues(
            # Express / Next.js API-route patterns are file-based for Next,
            # decorator-based for some Express-extension setups. Add as needed.
            route_decorators={
                "app.get", "app.post", "app.put", "app.patch", "app.delete",
                "router.get", "router.post", "router.put", "router.patch",
                "router.delete",
            },
            orm_base_classes={
                "Model", "BaseEntity",  # Prisma / TypeORM names
            },
            test_framework_primitives={"it", "test", "describe", "expect"},
            hook_call_names={
                "useState", "useEffect", "useMemo", "useCallback", "useRef",
                "useContext", "useReducer", "useLayoutEffect",
            },
            orm_schema_link_vias={"__tablename__"},
            # Future: add Prisma's "@@map" once a Prisma DSL extractor lands
        ),
    })
```

Plus seven stub modules in `lib/classification/`. Each is a one-line file at this stage; subsequent tasks (5.2–5.7) replace the no-op body. Run these as a single shell block:

```bash
mkdir -p depgraph/lib/classification
cat > depgraph/lib/classification/__init__.py <<'EOF'
EOF

for kind in component hook endpoint service model util test_kind; do
  cat > "depgraph/lib/classification/${kind}.py" <<EOF
"""${kind} classifier — stub. Filled in by Task 5.$([ "$kind" = "component" ] && echo 2 || ([ "$kind" = "hook" ] && echo 3 || ([ "$kind" = "endpoint" ] && echo 4 || ([ "$kind" = "service" ] && echo 5 || ([ "$kind" = "model" ] && echo 6 || echo 7))))).
"""
KIND = "${kind/test_kind/test}"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    return {}
EOF
done
```

(The `test_kind` module's `KIND` is `"test"` so it can't collide with pytest's discovery for a file literally named `test.py`.)

- [ ] **Step 3: Run, verify pass + commit**

### Task 5.2: Component classifier

- [ ] **Step 1: Test**

```python
# depgraph/tests/lib/test_classifier_component.py
from depgraph.lib.classification.component import classify
from depgraph.lib.classification.config import default_config


def _prim(id_, name, primitive="function", owner=None,
          returns_jsx=False, decorators=None):
    return {
        "id": id_, "primitive": primitive, "name": name, "owner": owner,
        "source": {"path": "p.tsx", "line": 1, "end_line": 1, "language": "typescript", "repo": "r"},
        "signature": {"decorators": decorators or [], "returns_jsx": returns_jsx},
        "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }


def test_function_returning_jsx_is_component():
    p = _prim("r::p.tsx::MyComponent", "MyComponent", returns_jsx=True)
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert decisions["r::p.tsx::MyComponent"]["rule"] == "returns_jsx"


def test_pascalcase_arrow_const_with_jsx_is_component():
    p = _prim("r::p.tsx::Header", "Header", returns_jsx=True)
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert "Header" in {p["name"] for pid in decisions for p in [_prim(pid, "Header")]}


def test_lowercase_function_returning_jsx_is_not_component():
    p = _prim("r::p.tsx::renderItem", "renderItem", returns_jsx=True)
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert decisions.get("r::p.tsx::renderItem", {}).get("rule") != "returns_jsx"
```

- [ ] **Step 2: Implement `lib/classification/component.py`**

```python
"""Component classifier — JSX-returning PascalCase functions."""
from __future__ import annotations

KIND = "component"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        # PascalCase first letter
        name = p["name"].split(".")[-1]  # strip Class.method prefix
        if not name or not name[0].isupper():
            continue
        if p["signature"].get("returns_jsx"):
            decisions[p["id"]] = {
                "rule": "returns_jsx",
                "evidence": [{"kind": "jsx_return", "where": f"{p['source']['path']}:{p['source']['line']}"}],
            }
    return decisions
```

> `signature.returns_jsx` is set by the TS extractor (Phase 1 Task 1.5, with its own test). No retro patching required.

- [ ] **Step 3: Run, verify pass + commit.**

### Task 5.3: Hook classifier

- [ ] **Step 1: Test**

```python
# test_classifier_hook.py
def test_use_prefix_calling_known_hook_is_hook():
    """Function named useFoo that has a calls-edge to a known hook (useState)
    classifies as hook."""
    p_user = {
        "id": "r::p.ts::useFoo", "primitive": "function", "name": "useFoo",
        "owner": None,
        "source": {"path": "p.ts", "line": 1, "end_line": 1, "language": "typescript", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "external::npm::react::useState", "kind": "calls",
                       "via": "fn", "where": "p.ts:2", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.hook import classify
    from depgraph.lib.classification.config import default_config
    decisions = classify([p_user], by_source={p_user["id"]: p_user["edges_out"]},
                         by_target={}, config=default_config(), decisions_so_far={})
    assert decisions[p_user["id"]]["rule"] == "use_prefix_calls_hook"
```

- [ ] **Step 2: Implement**

```python
# lib/classification/hook.py
import re

KIND = "hook"
_USE_PREFIX = re.compile(r"^use[A-Z]")


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    known_hook_externals = {f"external::npm::react::{n}" for n in config.hook_call_names}
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        name = p["name"].split(".")[-1]
        if not _USE_PREFIX.match(name):
            continue
        calls = [e for e in by_source.get(p["id"], []) if e["kind"] == "calls"]
        if any(c["target"] in known_hook_externals for c in calls):
            decisions[p["id"]] = {
                "rule": "use_prefix_calls_hook",
                "evidence": [c for c in calls if c["target"] in known_hook_externals],
            }
            continue
        # Or calls another user-defined hook (transitive — handled by second pass)
    return decisions
```

- [ ] **Step 3: Pass + commit.**

### Task 5.4: Endpoint classifier

- [ ] **Step 1: Test**

```python
# test_classifier_endpoint.py
def test_route_decorator_makes_endpoint():
    p = {
        "id": "r::routers/events.py::create_event", "primitive": "function",
        "name": "create_event", "owner": None,
        "source": {"path": "routers/events.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.post"]}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.endpoint import classify
    from depgraph.lib.classification.config import default_config
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert decisions[p["id"]]["rule"] == "route_decorator"


def test_no_route_decorator_no_endpoint():
    p = {
        "id": "r::routers/events.py::helper", "primitive": "function",
        "name": "helper", "owner": None,
        "source": {"path": "routers/events.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.endpoint import classify
    from depgraph.lib.classification.config import default_config
    decisions = classify([p], by_source={}, by_target={}, config=default_config(), decisions_so_far={})
    assert p["id"] not in decisions
```

- [ ] **Step 2: Implement**

```python
# lib/classification/endpoint.py
KIND = "endpoint"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        decs = p["signature"].get("decorators", [])
        for d in decs:
            if d in config.route_decorators or any(d.startswith(rd) for rd in config.route_decorators):
                decisions[p["id"]] = {
                    "rule": "route_decorator",
                    "evidence": [{"decorator": d, "where": f"{p['source']['path']}:{p['source']['line']}"}],
                }
                break
    return decisions
```

- [ ] **Step 3: Pass + commit.**

### Task 5.5: Service classifier

Two-stage rule: (a) function has at least one `db_access` / `queue_produce` / etc. edge; (b) function is transitively called from at least one endpoint.

- [ ] **Step 1: Test**

```python
# test_classifier_service.py
def test_function_with_db_access_and_called_by_endpoint_is_service():
    endpoint_fn = {
        "id": "r::routers/x.py::handler", "primitive": "function", "name": "handler",
        "owner": None,
        "source": {"path": "routers/x.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.get"]}, "attributes": {},
        "edges_out": [{"target": "r::services/x.py::do_work", "kind": "calls",
                       "via": "fn", "where": "routers/x.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    service_fn = {
        "id": "r::services/x.py::do_work", "primitive": "function", "name": "do_work",
        "owner": None,
        "source": {"path": "services/x.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "external::pypi::sqlalchemy::Session.query", "kind": "db_access",
                       "via": "session.query", "where": "services/x.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.engine import classify_corpus
    decisions = classify_corpus([endpoint_fn, service_fn])
    assert decisions["r::services/x.py::do_work"].kind == "service"


def test_function_with_db_access_not_reachable_from_endpoint_is_not_service():
    orphan = {
        "id": "r::lib/orphan.py::helper", "primitive": "function", "name": "helper",
        "owner": None,
        "source": {"path": "lib/orphan.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "external::pypi::sqlalchemy::Session.query", "kind": "db_access",
                       "via": "session.query", "where": "lib/orphan.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.engine import classify_corpus
    decisions = classify_corpus([orphan])
    assert decisions["r::lib/orphan.py::helper"].kind != "service"
```

- [ ] **Step 2: Implement**

```python
# lib/classification/service.py
"""Service classifier — function with side-effect edges AND reachable from endpoint."""
from __future__ import annotations

KIND = "service"
_SIDE_EFFECT_KINDS = {"db_access", "queue_produce", "webhook_publish",
                       "notification_send", "file_storage_access"}


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

    # Functions with side-effect edges that are reachable
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        if p["id"] not in reachable:
            continue
        side_effects = [e for e in by_source.get(p["id"], []) if e["kind"] in _SIDE_EFFECT_KINDS]
        if side_effects and p["id"] not in endpoints:
            decisions[p["id"]] = {
                "rule": "side_effect_reachable_from_endpoint",
                "evidence": side_effects,
            }
    return decisions
```

- [ ] **Step 3: Run, verify pass + commit.**

### Task 5.6: Model classifier — requires schema reference

Per the spec's resolved model/schema split (2026-05-16): a class is `model` only if it BOTH extends a known ORM base AND has a `references` edge to a `schema`-kind primitive. A class that extends Base but lacks a schema reference is an *orphan mapper* — surfaces as unclassified with a `warnings` entry (signal for "we have an ORM model for a table we never extracted"). A class with `kind: "schema"` set by the SQL extractor is NOT a model and is skipped by this classifier.

- [ ] **Step 1: Tests**

```python
# depgraph/tests/lib/test_classifier_model.py
from depgraph.lib.classification.engine import classify_corpus


def _user_class(edges_out):
    return {
        "id": "r::models/user.py::User", "primitive": "class", "name": "User",
        "owner": None,
        "source": {"path": "models/user.py", "line": 1, "end_line": 1,
                   "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": edges_out, "structural_hash": "0", "kind": None,
        "extractor": "t", "schema_version": 2,
    }


def _users_schema():
    return {
        "id": "r::schema::users", "primitive": "class", "name": "users",
        "owner": None,
        "source": {"path": "schema/users", "line": 1, "end_line": 1,
                   "language": "sql", "repo": "r"},
        "signature": {}, "attributes": {}, "edges_out": [],
        "structural_hash": "0", "kind": "schema",
        "extractor": "t", "schema_version": 2,
    }


def test_orm_class_with_schema_reference_is_model():
    user = _user_class([
        {"target": "external::pypi::sqlalchemy::Base", "kind": "extends",
         "via": "class_decl", "where": "models/user.py:1", "confidence": "exact"},
        {"target": "r::schema::users", "kind": "references",
         "via": "__tablename__", "where": "models/user.py:2", "confidence": "exact"},
    ])
    decisions = classify_corpus([user, _users_schema()])
    assert decisions[user["id"]].kind == "model"
    # schema primitive's kind was set by the extractor; classifier doesn't change it
    assert decisions["r::schema::users"].kind == "schema"


def test_orm_class_without_schema_reference_is_not_model():
    """Extends Base but no references → schema. Treated as orphan mapper."""
    user = _user_class([
        {"target": "external::pypi::sqlalchemy::Base", "kind": "extends",
         "via": "class_decl", "where": "models/user.py:1", "confidence": "exact"},
    ])
    decisions = classify_corpus([user])
    assert decisions[user["id"]].kind != "model"


def test_schema_primitive_not_classified_as_model():
    schema = _users_schema()
    decisions = classify_corpus([schema])
    assert decisions[schema["id"]].kind == "schema"


def test_class_with_schema_reference_but_no_orm_extends_is_not_model():
    """References → schema alone isn't enough; must also extend an ORM base.
    Otherwise any class that mentions a schema in a type hint would be a model."""
    cls = _user_class([
        {"target": "r::schema::users", "kind": "references",
         "via": "type_hint", "where": "models/user.py:1", "confidence": "exact"},
    ])
    decisions = classify_corpus([cls])
    assert decisions[cls["id"]].kind != "model"


def test_orm_class_with_typehint_only_reference_is_not_model():
    """Extends Base AND references schema, but `via` is a type hint — that's
    incidental, not an ORM mapping. Must not classify as model. The
    distinguishing marker is `via: "__tablename__"` (or another known
    orm_schema_link_vias entry)."""
    user = _user_class([
        {"target": "external::pypi::sqlalchemy::Base", "kind": "extends",
         "via": "class_decl", "where": "models/user.py:1", "confidence": "exact"},
        {"target": "r::schema::users", "kind": "references",
         "via": "return_type_annotation", "where": "models/user.py:5",
         "confidence": "exact"},
    ])
    decisions = classify_corpus([user, _users_schema()])
    assert decisions[user["id"]].kind != "model"
```

- [ ] **Step 2: Implement**

```python
# depgraph/lib/classification/model.py
"""Model classifier — ORM mapper class that observes a schema.

Requires BOTH:
  1. `extends` edge to a known ORM base class (config.orm_base_classes).
  2. `references` edge to a primitive whose kind == "schema".

Classes already classified as `schema` (by the SQL extractor) are skipped.
"""
from __future__ import annotations

KIND = "model"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    schema_ids = {p["id"] for p in primitives if p.get("kind") == "schema"}

    decisions = {}
    for p in primitives:
        if p["primitive"] != "class":
            continue
        if p.get("kind") == "schema":
            # Already labeled schema by extractor; not a model
            continue

        extends_orm = False
        orm_base_evidence = None
        schema_ref = None
        for e in by_source.get(p["id"], []):
            if e["kind"] == "extends":
                target_last = e["target"].split("::")[-1]
                if target_last in config.orm_base_classes:
                    extends_orm = True
                    orm_base_evidence = {"base": target_last, "via": e["via"]}
            elif (e["kind"] == "references"
                  and e["target"] in schema_ids
                  and e.get("via") in config.orm_schema_link_vias):
                # Only "ORM-mapper" style references count — `via` must come
                # from a known ORM-link marker like `__tablename__`. This
                # prevents type-hint references (`def f(u: UserSchema)`) from
                # turning every typed-arg class into a model.
                schema_ref = {"schema": e["target"], "via": e["via"]}

        if extends_orm and schema_ref is not None:
            decisions[p["id"]] = {
                "rule": "orm_mapper_with_schema_reference",
                "evidence": [orm_base_evidence, schema_ref],
            }
        # extends_orm without schema_ref: orphan mapper. We could surface
        # a warning here; engine writes that into Decision.conflicts if
        # we extend the API for it. Out of scope for this task — the
        # `kind` stays None and graphui can query "classes extending an
        # ORM base but unclassified" separately.
    return decisions
```

- [ ] **Step 3: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/test_classifier_model.py -v
git add depgraph/lib/classification/model.py depgraph/tests/lib/test_classifier_model.py
git commit -m "depgraph/classification: model requires both ORM base extends AND schema reference"
```

### Task 5.7: Util + Test classifiers

- [ ] **Step 1a: Test for util classifier**

Util's rule is "function called by at least one classified kind AND classifies as none of the above". This needs `decisions_so_far` from the engine, so the engine API grows a kwarg every classifier accepts (most ignore it).

Update the engine's call signature first:

```python
# lib/classification/engine.py — replace the classifier call
classifier_decisions = classifier.classify(
    primitives, by_source=by_source, by_target=by_target,
    config=config, decisions_so_far=decisions,
)
```

Then update every classifier from Tasks 5.2–5.6 to accept `decisions_so_far` (they ignore it):

```python
def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    ...
```

Test:

```python
# depgraph/tests/lib/test_classifier_util.py
from depgraph.lib.classification.engine import classify_corpus


def test_function_called_by_classified_endpoint_is_util():
    endpoint_fn = {
        "id": "r::routers/x.py::handler", "primitive": "function", "name": "handler",
        "owner": None,
        "source": {"path": "routers/x.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.get"]}, "attributes": {},
        "edges_out": [{"target": "r::utils/format.py::format_date", "kind": "calls",
                       "via": "fn", "where": "routers/x.py:5", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    util_fn = {
        "id": "r::utils/format.py::format_date", "primitive": "function", "name": "format_date",
        "owner": None,
        "source": {"path": "utils/format.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    decisions = classify_corpus([endpoint_fn, util_fn])
    assert decisions[endpoint_fn["id"]].kind == "endpoint"
    assert decisions[util_fn["id"]].kind == "util"


def test_function_called_only_by_unclassified_is_not_util():
    """If the only caller is itself unclassified, the callee isn't util."""
    a = {
        "id": "r::lib/a.py::a_fn", "primitive": "function", "name": "a_fn",
        "owner": None,
        "source": {"path": "lib/a.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "r::lib/b.py::b_fn", "kind": "calls",
                       "via": "fn", "where": "lib/a.py:2", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    b = {**a, "id": "r::lib/b.py::b_fn", "name": "b_fn",
         "source": {**a["source"], "path": "lib/b.py"}, "edges_out": []}
    decisions = classify_corpus([a, b])
    assert decisions[b["id"]].kind != "util"
```

- [ ] **Step 1b: Implement util (reachability-based, transitive)**

Single-pass "called by classified" misses the common case where A calls B calls endpoint — A is reachable through util B but a single pass doesn't yet know B is util. Reachability closure handles this in one go.

```python
# lib/classification/util.py
"""Util classifier — function transitively reachable into a classified kind.

Rule: a function F is util iff
  (a) F is not yet classified, AND
  (b) there is a `calls`-edge path from at least one classified function
      *into* F (i.e., classified ─calls→ … ─calls→ F).

Computed by forward BFS over reversed `calls` edges starting from the
classified set. Single pass; no fixed-point iteration needed because the
reachable set grows monotonically.
"""
from __future__ import annotations

KIND = "util"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    classified_ids = {pid for pid, dec in decisions_so_far.items() if dec.kind}
    if not classified_ids:
        return {}

    # Build callee->[callers] map (reverse of by_source for `calls` edges)
    callees_of: dict[str, list[str]] = {}  # caller -> [callees]
    for src_id, edges in by_source.items():
        for e in edges:
            if e["kind"] == "calls":
                callees_of.setdefault(src_id, []).append(e["target"])

    # BFS: starting from classified, expand to everything they call
    # transitively. Anything reachable that isn't already classified is util.
    reachable: set[str] = set()
    frontier = [pid for pid in classified_ids]
    while frontier:
        cur = frontier.pop()
        for callee in callees_of.get(cur, []):
            if callee in classified_ids or callee in reachable:
                continue
            reachable.add(callee)
            frontier.append(callee)  # expand through util-of-util chains

    # Look up evidence (direct classified callers) for each util
    primitives_by_id = {p["id"]: p for p in primitives}
    decisions = {}
    for util_id in reachable:
        p = primitives_by_id.get(util_id)
        if p is None or p["primitive"] != "function":
            continue
        # Find all direct callers (classified OR other utils — useful for graphui)
        direct_callers = [
            src for src, edges in by_source.items()
            for e in edges
            if e["kind"] == "calls" and e["target"] == util_id
        ]
        decisions[util_id] = {
            "rule": "transitive_call_target_of_classified",
            "evidence": [{"caller": c} for c in direct_callers],
        }
    return decisions
```

Add a third test case for the transitive scenario:

```python
# depgraph/tests/lib/test_classifier_util.py — append
def test_transitive_util_chain():
    """endpoint → util A → util B → util C. All three of A, B, C classify
    as util in a single pass (no fixed-point loop needed in the engine)."""
    endpoint = {
        "id": "r::p.py::handler", "primitive": "function", "name": "handler",
        "owner": None,
        "source": {"path": "p.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": ["router.get"]}, "attributes": {},
        "edges_out": [{"target": "r::a.py::a_fn", "kind": "calls",
                       "via": "fn", "where": "p.py:2", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    def util(id_, name, calls_target):
        return {
            "id": id_, "primitive": "function", "name": name, "owner": None,
            "source": {"path": f"{name}.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
            "signature": {"decorators": []}, "attributes": {},
            "edges_out": [{"target": calls_target, "kind": "calls",
                            "via": "fn", "where": f"{name}.py:1", "confidence": "exact"}],
            "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
        }
    a = util("r::a.py::a_fn", "a_fn", "r::b.py::b_fn")
    b = util("r::b.py::b_fn", "b_fn", "r::c.py::c_fn")
    c = util("r::c.py::c_fn", "c_fn", "r::leaf.py::leaf")
    leaf = util("r::leaf.py::leaf", "leaf", "r::a.py::a_fn")  # cycle: classifier must terminate
    leaf["edges_out"] = []  # no outbound; simplifies — drop the cycle for clarity
    decisions = classify_corpus([endpoint, a, b, c, leaf])
    assert decisions[endpoint["id"]].kind == "endpoint"
    assert decisions[a["id"]].kind == "util"
    assert decisions[b["id"]].kind == "util"
    assert decisions[c["id"]].kind == "util"
    assert decisions[leaf["id"]].kind == "util"
```

- [ ] **Step 2: Tests + implementation for `test_kind`**

```python
# lib/classification/test_kind.py
KIND = "test"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        # Has a `tests` edge OR has decorator like pytest.fixture OR is in a *.test.* file with a known framework call
        has_tests_edge = any(e["kind"] == "tests" for e in by_source.get(p["id"], []))
        decs = p["signature"].get("decorators", [])
        is_pytest_fixture = any(d.startswith("pytest.fixture") for d in decs)
        in_test_file = ".test." in p["source"]["path"] or p["source"]["path"].endswith("_test.py") \
                       or p["source"]["path"].split("/")[-1].startswith("test_")
        if has_tests_edge or is_pytest_fixture or (in_test_file and p["name"].startswith(("test_", "test"))):
            decisions[p["id"]] = {
                "rule": "test_framework_primitive",
                "evidence": [{"reason": ["has_tests_edge" if has_tests_edge else None,
                                          "pytest_fixture" if is_pytest_fixture else None,
                                          "test_filename" if in_test_file else None]}],
            }
    return decisions
```

- [ ] **Step 3: Run all classifier tests, verify pass + commit.**

```bash
pytest depgraph/tests/lib/test_classifier_*.py depgraph/tests/lib/test_classification_engine.py -v
git commit -m "depgraph/classification: util + test classifiers"
```

### Task 5.8: Classification writer — move primitives to kind-dirs

- [ ] **Step 1: Test**

```python
# test_classification_writer.py
import json
from pathlib import Path
from depgraph.lib.classification.engine import classify_corpus
from depgraph.lib.classification.writer import write_classified

def test_classified_primitive_lands_in_kind_dir(tmp_path):
    p = {"id": "r::p.py::create_event", "primitive": "function", "name": "create_event",
         "owner": None,
         "source": {"path": "p.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
         "signature": {"decorators": ["router.post"]}, "attributes": {},
         "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2}
    write_classified([p], classify_corpus([p]), data_dir=tmp_path)
    expected = tmp_path / "nodes/endpoints/r__p_py__create_event.json"
    assert expected.exists()
    written = json.loads(expected.read_text())
    assert written["kind"] == "endpoint"


def test_unclassified_primitive_lands_in_primitive_type_dir(tmp_path):
    p = {"id": "r::p.py::random_helper", "primitive": "function", "name": "random_helper",
         "owner": None,
         "source": {"path": "p.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
         "signature": {"decorators": []}, "attributes": {},
         "edges_out": [], "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2}
    write_classified([p], classify_corpus([p]), data_dir=tmp_path)
    expected = tmp_path / "nodes/functions/r__p_py__random_helper.json"
    assert expected.exists()
```

- [ ] **Step 2: Implement `lib/classification/writer.py`**

```python
import json
from pathlib import Path
from depgraph.extractors.python.canonical import slugify_id


_KIND_DIRS = {
    "component": "components", "hook": "hooks", "endpoint": "endpoints",
    "service": "services", "model": "models", "schema": "schemas",
    "test": "tests", "util": "utils",
}
_PRIMITIVE_DIRS = {
    "module": "modules", "package": "packages", "class": "classes",
    "function": "functions", "variable": "variables",
}


def write_classified(primitives, decisions, *, data_dir: Path) -> None:
    for p in primitives:
        decision = decisions.get(p["id"])
        if decision and decision.kind:
            kind_dir = _KIND_DIRS[decision.kind]
            p_out = dict(p, kind=decision.kind,
                          classification={"rule": decision.rule,
                                          "evidence": decision.evidence,
                                          "conflicts": decision.conflicts})
        else:
            kind_dir = _PRIMITIVE_DIRS[p["primitive"]]
            p_out = p
        target = data_dir / "nodes" / kind_dir / f"{slugify_id(p['id'])}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(p_out, indent=2, sort_keys=True))
```

- [ ] **Step 3: Run, verify pass + commit.**

### Task 5.9: Author wild fixtures + Claude verification

The 8 Phase-5 wild fixtures stress classification at the corners. These are also the *most* important to Claude-review by hand because classification is the most rule-shaped part of the system and the easiest place for "the test was wrong" to slip through.

**Files:**
- Create: `depgraph/tests/fixtures/wild/classification/{endpoint_AND_service_conflict,hook_calling_hook_chain,component_HOC_wrapped,pseudo_test_not_test,orphan_model,model_without_schema,util_deep_transitive,classification_conflict_logged}/`
- Create: `depgraph/tests/lib/test_classification_wild.py`

- [ ] **Step 1: Author the 8 fixtures**

Critical assertions per fixture:

- **endpoint_AND_service_conflict**: a function with `@router.get` decorator that *also* makes a `session.query(...)` call directly. Must classify as `endpoint`; `Decision.conflicts` must include `"service"`.
- **hook_calling_hook_chain**: `useFoo` → `useBar` → `useState`. All three classify as `hook`.
- **component_HOC_wrapped**: `const Card = memo(forwardRef(({...}, ref) => <div ref={ref}/>))`. The outer binding `Card` must classify as component. (Open question to surface in verification.md: which primitive carries `kind: component` — the top-level `Card` or the inner arrow? Document the decision.)
- **pseudo_test_not_test**: function named `test_calculate` inside `lib/calculations.py` (NOT a test path), no asserts in body. Must NOT classify as test.
- **orphan_model**: class extends `Base` but no `__tablename__`. Must NOT classify as model. (Surface in `verification.md`: did the framework log a warning? If yes, document where.)
- **model_without_schema**: class with `__tablename__ = "users"` but no `users` schema in corpus. References edge target is unresolved; class must NOT classify as model.
- **util_deep_transitive**: endpoint → A → B → C → D. All four interior functions classify as util via the reachability BFS in one pass.
- **classification_conflict_logged**: a hand-crafted edge case satisfying both `endpoint` and `model` predicates (extremely unusual but possible). Test asserts `Decision.conflicts` is populated; engine doesn't crash.

- [ ] **Step 2: Test harness**

```python
# depgraph/tests/lib/test_classification_wild.py
import json
from pathlib import Path
import pytest

from depgraph.lib.classification.engine import classify_corpus

WILD_DIR = Path(__file__).parent.parent / "fixtures" / "wild" / "classification"


def _fixtures():
    return sorted(d for d in WILD_DIR.iterdir() if d.is_dir() and (d / "src").exists())


def _build_corpus(fixture):
    """Each classification fixture pre-builds its corpus inline as a JSON
    file `corpus.json` (since we don't want to re-run extraction for every
    fixture). The corpus represents what Phases 1-4 would have produced."""
    return json.loads((fixture / "corpus.json").read_text())


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda f: f.name)
def test_wild_classifications_match_expected(fixture):
    expected = json.loads((fixture / "expected.json").read_text())
    corpus = _build_corpus(fixture)
    decisions = classify_corpus(corpus)
    expected_decisions = {e["id"]: e["kind"] for e in expected["classifications"]}
    for prim_id, expected_kind in expected_decisions.items():
        assert decisions[prim_id].kind == expected_kind, (
            f"{fixture.name}: {prim_id} expected {expected_kind} "
            f"got {decisions[prim_id].kind}"
        )
    for ec in expected.get("conflicts", []):
        assert ec["kind"] in decisions[ec["id"]].conflicts, (
            f"{fixture.name}: expected conflict {ec} not in "
            f"{decisions[ec['id']].conflicts}"
        )
```

- [ ] **Step 3: Claude verification**

For each fixture, *especially* `pseudo_test_not_test` and `orphan_model`: write the prediction in `verification.md` of what the classifier *should* decide based on the spec rule, then compare. These are the cases where a sloppy implementation would over-classify; the Claude review is the gate.

- [ ] **Step 4: Commit**

```bash
git add depgraph/tests/fixtures/wild/classification/ \
        depgraph/tests/lib/test_classification_wild.py
git commit -m "depgraph: Phase 5 wild corpus (8 classification edge fixtures + Claude review)"
```

---

## Phase 6 — Cutover

**Goal:** Wire the new pipeline into `kg depgraph regen` + `kg depgraph context` + the PreToolUse hook. Delete the frozen legacy extractors. Regen Concorda's corpus.

**Files:**
- Modify: `depgraph/extractors/reconcile.py` (rewrite for v2)
- Modify: `kg/cli/depgraph/regen.py` (or wherever regen lives) — invoke new extractors per language registry
- Delete: `depgraph/extractors/generic/` (whole subtree)
- Create: `kg/cli/depgraph/migrate_logigraph_claims.py` (one-shot script for Task 6.8)
- Test: `depgraph/tests/test_reconcile_v2.py` (full end-to-end against a tiny synthetic project)
- Test: `depgraph/tests/test_regen_determinism.py` (CI gate: regen twice → identical output)

### Task 6.0: Pre-cutover compatibility check (graphui kind dirs)

Before tearing out the legacy extractors, confirm graphui can read the new kind set including the new `schemas/` dir. graphui may hardcode a kind-dir whitelist somewhere; this task is to find it and update.

- [ ] **Step 1: Locate graphui's kind-dir reader**

Run: `grep -rn "components\|hooks\|endpoints\|services\|models" ~/tools/knowledge-graph/graphui/ --include="*.py" --include="*.ts" 2>/dev/null | head -20`

Document where the kind-dir list lives (file + line).

- [ ] **Step 2: Add `schemas` to the kind-dir list**

If hardcoded, append `"schemas"` (and any new primitive-type dirs: `modules`, `packages`, `classes`, `functions`, `variables`). If config-driven, update the config.

- [ ] **Step 3: Smoke-test graphui against a tiny v2 corpus**

Run graphui locally pointed at a synthetic tmp corpus containing one schema + one model + one endpoint. Verify all three appear in the relevant tabs.

- [ ] **Step 4: Commit**

```bash
git commit -m "graphui: surface schemas/ kind dir + v2 primitive-type dirs"
```

### Task 6.1: Rewrite reconcile for v2

- [ ] **Step 1: Test**

```python
# depgraph/tests/test_reconcile_v2.py
"""End-to-end: synthetic source → primitives + edges + classification → reconcile builds reverse index."""

import json
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture
def tiny_project(tmp_path):
    api = tmp_path / "api"
    api.mkdir()
    (api / "routers.py").write_text("""
def helper(): pass

def create_event():
    helper()
""")
    return tmp_path


def test_regen_end_to_end(tiny_project, tmp_path):
    out = tmp_path / "data"
    subprocess.run([
        sys.executable, "-m", "kg.cli", "depgraph", "regen",
        "--data-dir", str(out),
        "--repo-key", "api", "--repo-path", str(tiny_project / "api"),
    ], check=True)
    helper = out / "nodes/functions/api__routers_py__helper.json"
    assert helper.exists()
    # by_target index should include the calls edge
    idx = json.loads((out / "nodes/_index/by_target.json").read_text())
    assert "api::routers.py::helper" in idx
    incoming = idx["api::routers.py::helper"]
    assert any(e["kind"] == "calls" for e in incoming)
```

- [ ] **Step 2: Rewrite `reconcile.py` to build the v2 indexes**

The new reconcile:

1. Reads every `nodes/**/*.json` (any kind dir).
2. Validates each against `validate_primitive` — any failure aborts regen with a clear error pointing at the offending file.
3. Runs `check_slug_collisions(all_primitives)` from `depgraph/lib/primitives.py`; any collisions abort regen.
4. For every edge in `edges_out`: looks up `target` in the primitive set (or recognizes `external::` terminals as a special case); orphan edges where target is neither in-corpus nor a recognized external prefix are listed in `_meta.json.orphan_edges` and the gate `kg depgraph validate` exits non-zero. Validates each edge with `validate_edge()` passing the resolved source_kind + target_kind.
5. Builds `nodes/_index/by_source.json` (source_id → outgoing edges) and `nodes/_index/by_target.json` (target_id → incoming edges with source_id).
6. Builds `nodes/_index/by_repo.json`.
7. Writes `nodes/_meta.json` with corpus stats (primitive count, edge count, orphan_edge count, slug-collision count, regen_status).

Concrete validation pass:

```python
# In the new depgraph/extractors/reconcile.py
from depgraph.lib.primitives import (
    validate_primitive, check_slug_collisions, is_external_terminal,
)
from depgraph.lib.edges import validate_edge


def validate_corpus(primitives: list[dict]) -> dict:
    """Return a validation report. Caller decides whether to abort regen."""
    report = {"primitive_errors": [], "edge_errors": [],
              "slug_collisions": [], "orphan_edges": []}

    for p in primitives:
        for err in validate_primitive(p):
            report["primitive_errors"].append({"id": p.get("id"), "error": err})

    report["slug_collisions"] = check_slug_collisions(primitives)

    by_id = {p["id"]: p for p in primitives}
    for p in primitives:
        src_kind = p["primitive"]
        for e in p.get("edges_out", []):
            tgt = e.get("target")
            tgt_prim = by_id.get(tgt)
            if tgt_prim is None and not is_external_terminal(tgt or ""):
                report["orphan_edges"].append({
                    "source": p["id"], "target": tgt, "kind": e.get("kind"),
                })
                continue
            tgt_kind = tgt_prim["primitive"] if tgt_prim else None
            for err in validate_edge({**e, "source_kind": src_kind,
                                       "target_kind": tgt_kind}):
                report["edge_errors"].append({"source": p["id"],
                                                "target": tgt, "error": err})
    return report
```

Test for the validator (in `depgraph/tests/test_reconcile_v2.py`):

```python
def test_reconcile_flags_orphan_edge():
    from depgraph.extractors.reconcile import validate_corpus
    prims = [{
        "schema_version": 2,
        "id": "r::a.py::f", "primitive": "function", "name": "f",
        "owner": None,
        "source": {"repo": "r", "path": "a.py", "language": "python",
                   "line": 1, "end_line": 1},
        "signature": {"parameters": [], "return_type": None,
                       "is_async": False, "decorators": []},
        "attributes": {}, "structural_hash": "0", "kind": None,
        "extractor": "t",
        "edges_out": [{"target": "r::nowhere.py::ghost", "kind": "calls",
                        "via": "fn", "where": "a.py:1", "confidence": "exact"}],
    }]
    report = validate_corpus(prims)
    assert len(report["orphan_edges"]) == 1
    assert report["orphan_edges"][0]["target"] == "r::nowhere.py::ghost"


def test_reconcile_accepts_external_terminal_targets():
    from depgraph.extractors.reconcile import validate_corpus
    prims = [{
        "schema_version": 2,
        "id": "r::a.py::f", "primitive": "function", "name": "f",
        "owner": None,
        "source": {"repo": "r", "path": "a.py", "language": "python",
                   "line": 1, "end_line": 1},
        "signature": {"parameters": [], "return_type": None,
                       "is_async": False, "decorators": []},
        "attributes": {}, "structural_hash": "0", "kind": None,
        "extractor": "t",
        "edges_out": [{"target": "external::pypi::sqlalchemy::Session.query",
                        "kind": "db_access",
                        "via": "session.query", "where": "a.py:1",
                        "confidence": "exact"}],
    }]
    report = validate_corpus(prims)
    assert report["orphan_edges"] == []
```

Delete the legacy reconcile functions that fed pre-flip-shape concerns: `_join_route_calls`, `strip_legacy_fields`, `_run_embedding_pass` (preserve only if used in the new model).

- [ ] **Step 3: Implement regen entry point**

The user-facing CLI is `kg depgraph regen`. Supports two invocation modes:

**Mode A — multi-repo via project.toml** (the production path used for Concorda + kitchen-sink):
```
kg depgraph regen --data-dir <out> [--project-toml <path>]
```
If `--project-toml` is omitted, regen searches cwd-ancestors for `project.toml` (matching the existing kg project-resolution behavior). All `[repos.*]` blocks are processed.

**Mode B — single-repo direct invocation** (used by determinism CI test, useful for ad-hoc regens of a single repo without authoring a project.toml):
```
kg depgraph regen --data-dir <out> --repo-key <key> --repo-path <path> [--languages typescript,python,sql]
```
If `--languages` is omitted, infer from the file extensions present (TS files → typescript, .py → python, .sql → sql). No migration handling in Mode B unless explicitly enabled via `--migrations-dir <path>`.

Mode A is the canonical CLI for real corpora. Mode B is a developer ergonomics affordance.

Implementation steps:

1. Parse flags; decide mode based on whether `--repo-key` is present.
2. Mode A: Load `project.toml` (gives `repos.*` paths + per-repo `include_paths` / `languages` / `migrations_dirs`). Mode B: synthesize a single-repo config from the CLI args.
3. For each repo × language, invoke the language's extractor per `languages.toml` and collect primitives + edges.
4. **SQL pipeline.** For each repo with `sql` in `languages`:
   a. Run the standalone `.sql` extractor against any `.sql` files (no-op for Concorda).
   b. For each path in `migrations_dirs` (Mode A) or `--migrations-dir` (Mode B, if given), walk recursively: `is_migration_file(p)` → `extract_migration(p)` → collect `MigrationFile`s.
   c. `reconcile_schema(migration_files, repo_key=...)` → `schema_to_primitives(...)` → schema-primitive corpus for that repo.
   d. Attach `up_operations[]` to each migration module primitive (look up the module primitive by path, append the list of schema-primitive ids).
5. **Cross-reference pass.** `attach_model_schema_references(all_primitives)` adds the `references` edges from ORM model classes to schema primitives.
6. **`db_access` pass.** `attach_db_access_edges(all_primitives, repo_path=...)` adds db_access edges that target schema primitives where the chain resolves.
7. **Classification engine.** Runs over the unified corpus; produces decisions; schema primitives keep their `kind: "schema"` (set by the SQL extractor).
8. Write all primitives to disk via `write_classified`.
9. Run reconcile (Task 6.1's rewritten version) to build `_index/by_source.json` + `by_target.json`.

- [ ] **Step 4: Run end-to-end, verify pass + commit**

```bash
pytest depgraph/tests/test_reconcile_v2.py -v
git add depgraph/extractors/reconcile.py kg/cli/depgraph/ depgraph/tests/test_reconcile_v2.py
git commit -m "depgraph: rewrite reconcile + regen for v2 layered substrate"
```

### Task 6.2: Wire PreToolUse hook to new pipeline

The hook at `~/.claude/settings.json` calls `kg hook pre-edit`. That hook reads from `nodes/_index/by_target.json` (new shape) to surface incoming edges before edits. Update the hook's reader to consume v2 shape.

**File-to-primitive resolution algorithm.** The hook receives an absolute file path (e.g., `/home/user/concorda-api/routers/events.py`) via `--file` and must look up the primitives in that file. Resolution:

1. **Load project config.** Either via `DEPGRAPH_DATA_DIR` env var (test override) or the standard project resolver. From the resolved `project.toml`, build a map `{absolute_repo_path: repo_key}` from `repos.*.path`.
2. **Match the given file path against repo prefixes.** For each `(abs_repo_path, repo_key)`, check whether the file is under it. If yes, `rel_path = file_path.relative_to(abs_repo_path)` and the primitive id prefix is `{repo_key}::{rel_path}::*`.
3. **Filter `by_target.json` for incoming edges where the source has matching id prefix.** Surface those edges (the callers of anything in this file) in the injected context.
4. **No match → no injection.** Hook silently no-ops; the edit proceeds. This is the right default — a file outside any tracked repo shouldn't trigger errors, just no context.

For the integration test below: the fixture mimics the standard project layout — a project root with `project.toml` at top level, `depgraph/` as the data dir (where `DEPGRAPH_DATA_DIR` points), and the synthetic source repo (`api/`) as a sibling of `depgraph/`. The hook's resolution algorithm finds `project.toml` one level UP from `DEPGRAPH_DATA_DIR`, reads `[repos.api].path`, matches the `--file` argument against it, and surfaces matching incoming edges from `nodes/_index/by_target.json`.

- [ ] **Step 1: Add a hook integration test**

```python
# depgraph/tests/test_hook_pre_edit.py
import json
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture
def tiny_corpus(tmp_path):
    """Write a tiny v2 corpus matching the standard project layout:

        tmp_path/
          project_root/
            project.toml             ← lives at project root, NOT inside data_dir
            depgraph/                ← DEPGRAPH_DATA_DIR points here
              nodes/...
            api/                     ← the "repo" whose source the hook resolves against
              routers.py

    Returns the depgraph data dir (DEPGRAPH_DATA_DIR target). project.toml
    is at `data_dir.parent / "project.toml"` per the standard layout."""
    project_root = tmp_path / "project_root"
    data_dir = project_root / "depgraph"
    nodes = data_dir / "nodes"
    (nodes / "functions").mkdir(parents=True)
    (nodes / "_index").mkdir()

    helper = {
        "schema_version": 2, "id": "api::routers.py::helper",
        "primitive": "function", "name": "helper", "owner": None,
        "source": {"repo": "api", "path": "routers.py",
                   "language": "python", "line": 1, "end_line": 2},
        "signature": {"parameters": [], "return_type": None,
                      "is_async": False, "decorators": []},
        "attributes": {}, "edges_out": [], "structural_hash": "0",
        "kind": None, "extractor": "test",
    }
    create_event = {
        **helper,
        "id": "api::routers.py::create_event", "name": "create_event",
        "source": {**helper["source"], "line": 4, "end_line": 5},
        "edges_out": [{"target": "api::routers.py::helper", "kind": "calls",
                       "via": "fn", "where": "routers.py:5", "confidence": "exact"}],
    }
    (nodes / "functions/api__routers_py__helper.json").write_text(json.dumps(helper))
    (nodes / "functions/api__routers_py__create_event.json").write_text(json.dumps(create_event))

    by_target = {"api::routers.py::helper": [
        {"source": "api::routers.py::create_event", "kind": "calls",
         "via": "fn", "where": "routers.py:5", "confidence": "exact"}]}
    (nodes / "_index/by_target.json").write_text(json.dumps(by_target))
    (nodes / "_index/by_source.json").write_text(json.dumps({
        "api::routers.py::create_event": create_event["edges_out"]
    }))

    # Source root that the hook will resolve against, alongside project.toml
    # at the project root (one level UP from data_dir, per standard layout).
    src_root = project_root / "api"
    src_root.mkdir()
    (src_root / "routers.py").write_text(
        "def helper(): pass\n\n"
        "def create_event():\n"
        "    helper()\n"
    )
    (project_root / "project.toml").write_text(f"""
[project]
name = "fixture"

[repos.api]
path = "{src_root}"
languages = ["python"]
""")

    return data_dir   # what DEPGRAPH_DATA_DIR should point at


def test_hook_pre_edit_surfaces_callers(tiny_corpus):
    """The hook resolves the abs file path via project.toml (located at
    data_dir.parent / project.toml per standard layout); finds the matching
    repo prefix; surfaces incoming edges from by_target.json."""
    src_root = tiny_corpus.parent / "api"
    out = subprocess.run([
        sys.executable, "-m", "kg.cli", "hook", "pre-edit",
        "--file", str(src_root / "routers.py"),
    ], capture_output=True, text=True, check=True,
       env={"DEPGRAPH_DATA_DIR": str(tiny_corpus),
            "PATH": __import__("os").environ["PATH"]})
    assert "helper" in out.stdout
    assert "create_event" in out.stdout
```

- [ ] **Step 2: Update hook reader to v2 schema (consume `_index/by_target.json` for incoming edges, `by_source.json` for outgoing).**

- [ ] **Step 3: Run, pass, commit.**

### Task 6.3: Delete legacy extractors

- [ ] **Step 1: Confirm no test imports from `depgraph/extractors/generic/`**

Run: `grep -r "extractors.generic" depgraph/tests/ depgraph/lib/ kg/ || true`
Expected: empty output, or only the legacy test file (already deleted in Phase 0).

- [ ] **Step 2: Delete**

```bash
git rm -r depgraph/extractors/generic/
```

- [ ] **Step 3: Confirm tests still pass**

Run: `pytest depgraph/tests -v`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git commit -m "depgraph: delete legacy generic extractors (replaced by layered substrate)"
```

### Task 6.4: Migrate Concorda's project.toml

The existing `~/concorda-knowledge-graph/depgraph/project.toml` carries pre-flip fields (`extractor` command, `detectors` list, `files_arg`) that the v2 pipeline doesn't read. The v2 pipeline reads `languages` + `include_paths` + `exclude_paths` per repo and picks the extractor from the framework's `languages.toml`.

- [ ] **Step 1: Replace the three `[repos.*]` blocks**

```toml
# ~/concorda-knowledge-graph/depgraph/project.toml
# v2 schema — see ~/tools/knowledge-graph/docs/superpowers/specs/2026-05-15-layered-substrate-design.md

[project]
name = "concorda"
primary_repo = "concorda-api"

[logigraph]
data_dir = "~/concorda-knowledge-graph/logigraph"

[repos.concorda-api]
path = "~/concorda-api"
languages = ["python", "sql"]
include_paths = ["**/*.py", "**/*.sql"]
exclude_paths = ["**/__pycache__/**", "**/.venv/**", "**/venv/**", "**/tests/**"]
# The migrations directory contains Python files with embedded SQL.
# The SQL pipeline (depgraph/lib/sql/) recognizes these and extracts
# their schema operations; no special config needed beyond `sql` in
# languages above.
migrations_dirs = ["migrations"]

[repos.concorda-web]
path = "~/concorda-web"
languages = ["typescript"]
include_paths = ["src/**"]
exclude_paths = ["src/generated/**", "**/node_modules/**", "**/.next/**"]

[repos.concorda-test]
path = "~/concorda-test"
languages = ["typescript"]
include_paths = ["tests/**", "src/**"]
exclude_paths = ["**/node_modules/**"]

[memory]
mirror = "concorda/memory"
```

- [ ] **Step 2: Commit (Concorda-knowledge-graph repo, not framework)**

```bash
cd ~/concorda-knowledge-graph
git add depgraph/project.toml
git commit -m "depgraph: migrate project.toml to v2 (languages + include/exclude paths)"
```

### Task 6.5: Kitchen-sink end-to-end Claude verification

The kitchen-sink fixture is the framework's last gate before any real consumer (Concorda) is touched. Unlike per-phase wild fixtures, this one runs the full pipeline — extract → edges → SQL pipeline → cross-ref → db_access → classify → reconcile — and the gate is "the framework, validated independently on synthetic-pathological code, also produces a sane corpus on a multi-language mini-project."

**Files:**
- Create: `depgraph/tests/fixtures/wild/kitchen_sink/`
  - `README.md` — what's in the project + the expected kind distribution
  - `project.toml` — multi-repo config the test reads via `--project-toml`; declares the `api/`, `web/` "repos" pointing at the subdirs of this fixture, with `languages = ["python", "sql"]` for api and `languages = ["typescript"]` for web; `migrations_dirs = ["migrations"]` for api
  - `api/` — Python (FastAPI-shaped: routers, models, services, utils, tests)
  - `api/migrations/` — Python migrations with embedded `text("CREATE TABLE …")` calls
  - `web/` — TypeScript (Next.js-shaped: components, hooks, API clients, tests)
  - `db/` — standalone `.sql` schemas (subset of tables that aren't migration-sourced)
  - `expected.json` — kind-count distribution + key invariants
  - `verification.md` — end-to-end review log
- Create: `depgraph/tests/test_kitchen_sink.py`

- [ ] **Step 1: Author the kitchen-sink mini-project**

Goal: a project small enough to read end-to-end (~30 files, ~1000 LOC total) but large enough that all kinds appear and classification distribution is non-trivial. Target distribution:

| Kind | Count | Source |
|---|---|---|
| schema | 8 | 5 in migrations/, 3 in db/*.sql |
| model | 5 | api/models/*.py with `__tablename__` |
| endpoint | 5 | api/routers/*.py with route decorators |
| service | 4 | api/services/*.py with db_access edges, called from endpoints |
| util | 6 | shared helpers reachable from classified kinds |
| component | 3 | web/components/*.tsx returning JSX |
| hook | 2 | web/hooks/use*.ts |
| test | 4 | api/tests/test_*.py + web/__tests__/*.test.tsx |

(Counts are exact — the test gates on them.)

The mini-project's "story": a tiny event-RSVP app. Two ORM models (User, Event) + three more tables for relations (RSVP, EventTag, Tag). Endpoints for create/list/RSVP. Services do the DB work. Frontend has an event list page + RSVP button + a custom hook for fetching.

**Authoring approach — iterate, don't big-bang.** Writing all 30 files and then running the gate is the wrong sequence: a count mismatch at the end requires unwinding choices across many files. Instead, author one kind at a time and verify counts incrementally:

1. Write the 8 schema migrations + .sql files; run the SQL pipeline only; confirm 8 schema primitives emerge.
2. Add the 5 ORM models in api/models/; run extract + cross-ref; confirm 5 model classifications appear.
3. Add the 5 endpoints in api/routers/; confirm endpoint count.
4. Add the 4 services in api/services/; verify their `db_access` edges target the expected schemas; confirm service count.
5. Add 4 tests + 6 utils last (tests reference services; utils get pulled in by reachability).
6. Add web/components, web/hooks last (independent of backend).

Each step's diff is small enough that fixing a count mismatch is straightforward. Save the "30 files at once + run the gate + debug" path for actual real-corpus regens (Concorda) where iteration isn't an option.

- [ ] **Step 2: Author `expected.json`**

```json
{
  "kind_counts": {
    "schema": 8, "model": 5, "endpoint": 5, "service": 4,
    "util": 6, "component": 3, "hook": 2, "test": 4
  },
  "invariants": [
    "every model has exactly one references→schema edge via __tablename__",
    "every endpoint has at least one calls edge into a service or util",
    "every service has at least one db_access edge targeting a schema",
    "every component has signature.returns_jsx = true",
    "every hook has at least one calls edge to another hook or React built-in",
    "every test has at least one tests edge to a non-test function",
    "no orphan edges (every non-external target resolves to a primitive)",
    "no slug collisions",
    "two consecutive regens produce byte-identical output"
  ],
  "spot_check_classifications": [
    {"id": "fixture::api/routers/events.py::create_event", "kind": "endpoint"},
    {"id": "fixture::api/services/events.py::create_event_service", "kind": "service"},
    {"id": "fixture::api/utils/format.py::format_date", "kind": "util"},
    {"id": "fixture::web/components/EventCard.tsx::EventCard", "kind": "component"},
    {"id": "fixture::web/hooks/useEvents.ts::useEvents", "kind": "hook"},
    {"id": "fixture::api/models/event.py::Event", "kind": "model"},
    {"id": "fixture::schema::events", "kind": "schema"}
  ]
}
```

- [ ] **Step 3: Test harness**

```python
# depgraph/tests/test_kitchen_sink.py
"""End-to-end gate on the kitchen-sink mini-project.

Runs the full pipeline (extract → edges → SQL → cross-ref → db_access →
classify → reconcile) and asserts kind distribution + invariants."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "wild" / "kitchen_sink"


@pytest.fixture(scope="module")
def regen_kitchen_sink(tmp_path_factory):
    out = tmp_path_factory.mktemp("kitchen_sink_corpus")
    subprocess.run([
        sys.executable, "-m", "kg.cli", "depgraph", "regen",
        "--data-dir", str(out),
        "--project-toml", str(FIXTURE / "project.toml"),
    ], check=True)
    return out


def _load_all_nodes(data_dir: Path):
    nodes = []
    for p in (data_dir / "nodes").rglob("*.json"):
        if p.name.startswith("_") or "_index" in p.parts:
            continue
        nodes.append(json.loads(p.read_text()))
    return nodes


def test_kitchen_sink_kind_distribution(regen_kitchen_sink):
    expected = json.loads((FIXTURE / "expected.json").read_text())
    nodes = _load_all_nodes(regen_kitchen_sink)
    counts: dict[str, int] = {}
    for n in nodes:
        if n.get("kind"):
            counts[n["kind"]] = counts.get(n["kind"], 0) + 1
    for kind, expected_count in expected["kind_counts"].items():
        assert counts.get(kind) == expected_count, (
            f"{kind}: expected {expected_count}, got {counts.get(kind, 0)}"
        )


def test_kitchen_sink_spot_check_classifications(regen_kitchen_sink):
    expected = json.loads((FIXTURE / "expected.json").read_text())
    by_id = {n["id"]: n for n in _load_all_nodes(regen_kitchen_sink)}
    for check in expected["spot_check_classifications"]:
        actual_kind = by_id.get(check["id"], {}).get("kind")
        assert actual_kind == check["kind"], (
            f"{check['id']}: expected kind={check['kind']}, got {actual_kind}"
        )


def test_kitchen_sink_no_orphan_edges(regen_kitchen_sink):
    """Every non-external edge target must resolve."""
    nodes = _load_all_nodes(regen_kitchen_sink)
    by_id = {n["id"]: n for n in nodes}
    orphans = []
    for n in nodes:
        for e in n.get("edges_out", []):
            tgt = e["target"]
            if tgt.startswith("external::"):
                continue
            if tgt not in by_id:
                orphans.append({"source": n["id"], "target": tgt, "kind": e["kind"]})
    assert not orphans, f"orphan edges: {orphans}"


def test_kitchen_sink_models_reference_schemas(regen_kitchen_sink):
    """Invariant: every model has exactly one references→schema edge."""
    nodes = _load_all_nodes(regen_kitchen_sink)
    by_id = {n["id"]: n for n in nodes}
    for n in nodes:
        if n.get("kind") != "model":
            continue
        schema_refs = [e for e in n.get("edges_out", [])
                       if e["kind"] == "references"
                          and by_id.get(e["target"], {}).get("kind") == "schema"]
        assert len(schema_refs) == 1, (
            f"model {n['id']} has {len(schema_refs)} schema refs, expected 1"
        )


def test_kitchen_sink_determinism(regen_kitchen_sink, tmp_path):
    """Second regen must produce identical output."""
    import filecmp
    second = tmp_path / "second"
    subprocess.run([
        sys.executable, "-m", "kg.cli", "depgraph", "regen",
        "--data-dir", str(second),
        "--project-toml", str(FIXTURE / "project.toml"),
    ], check=True)
    cmp = filecmp.dircmp(regen_kitchen_sink, second)
    assert not cmp.diff_files, f"kitchen-sink non-deterministic: {cmp.diff_files}"
```

- [ ] **Step 4: Claude end-to-end verification**

The most important review step in the entire plan. Time-budget: a full reading pass through the kitchen-sink before signing.

1. Read every file under `kitchen_sink/api/` and `kitchen_sink/web/`. For each, write a one-line summary in `verification.md`: "what does this file contribute?"
2. Manually compute what kinds each function/class should be. Compare to `expected.json`'s `spot_check_classifications`.
3. Run the regen. Read the produced corpus directory by directory. For each `nodes/<kind>/`, list the slugified filenames; cross-reference against your kind-count predictions.
4. Pick 3 randomly-chosen edges from `nodes/_index/by_target.json`. For each, trace back to the source file and confirm the edge represents a real relationship.
5. Confirm the determinism gate passed.
6. Sign `verification.md` with full inventory, observed kind distribution, any discrepancies + their resolution.

- [ ] **Step 5: Commit**

```bash
git add depgraph/tests/fixtures/wild/kitchen_sink/ \
        depgraph/tests/test_kitchen_sink.py
git commit -m "depgraph: kitchen-sink end-to-end gate + Claude verification"
```

### Task 6.6: Regen Concorda corpus

- [ ] **Step 1: Backup current Concorda corpus**

```bash
cd ~/concorda-knowledge-graph
git stash push -m "pre-layered-regen-backup" -- depgraph/
```

Or move `depgraph/nodes/` aside to `depgraph/nodes.old/` as a safety net.

- [ ] **Step 2: Run regen**

```bash
cd ~/concorda-knowledge-graph
kg depgraph regen
```

Expected: corpus regenerates with v2 shape. Look for primitive count, edge count, classification distribution in the meta output.

- [ ] **Step 3: Validate**

```bash
kg depgraph validate
```

Expected: no orphan edges, no schema validation errors.

- [ ] **Step 4: Commit the regenerated corpus**

```bash
cd ~/concorda-knowledge-graph
git add depgraph/
git commit -m "depgraph: regen on layered substrate (v2 schema, JS/TS/Python)"
```

### Task 6.7: Determinism CI gate

Regen twice, diff the output directories — they must be byte-identical. Guards against accidental non-determinism (set iteration, time-of-day fields, etc.).

- [ ] **Step 1: Write the test**

```python
# depgraph/tests/test_regen_determinism.py
"""Regen-determinism gate: two consecutive regens of the same source must
produce byte-identical node dirs."""
from __future__ import annotations

import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tiny_project(tmp_path):
    src = tmp_path / "repo"
    (src / "api").mkdir(parents=True)
    (src / "api/routers.py").write_text(
        "def helper(): pass\n\n"
        "def create_event():\n"
        "    helper()\n"
    )
    return src


def _regen(repo_path: Path, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        sys.executable, "-m", "kg.cli", "depgraph", "regen",
        "--data-dir", str(data_dir),
        "--repo-key", "api", "--repo-path", str(repo_path / "api"),
    ], check=True)


def test_two_regens_produce_identical_corpus(tiny_project, tmp_path):
    a = tmp_path / "out_a"
    b = tmp_path / "out_b"
    _regen(tiny_project, a)
    _regen(tiny_project, b)
    cmp = filecmp.dircmp(a, b)
    assert not cmp.diff_files, f"differing files between regens: {cmp.diff_files}"
    assert not cmp.left_only and not cmp.right_only, (
        f"asymmetric files: only_in_a={cmp.left_only} only_in_b={cmp.right_only}"
    )
    # Recurse into subdirs
    def _walk(d):
        if d.diff_files or d.left_only or d.right_only:
            return False
        return all(_walk(sub) for sub in d.subdirs.values())
    assert _walk(cmp), "non-deterministic regen detected in subdirectories"
```

- [ ] **Step 2: Run; if it fails, find the source of non-determinism**

Common culprits: `set()` iteration leaking into output ordering, timestamp fields, dict iteration across different process runs (rare in Python 3.7+ but possible across worker procs), unsorted `glob()` results.

- [ ] **Step 3: Commit**

```bash
git add depgraph/tests/test_regen_determinism.py
git commit -m "depgraph: regen determinism CI gate"
```

### Task 6.8: Logigraph claim migration

**Expectation-setting for the initial cutover.** This task ships an auto-migration script, but on the *first* v2 regen the script handles a much smaller fraction of claims than it does on subsequent regens. Why: the spec resolution (2026-05-16) changed the `structural_hash` payload shape (now includes `body_text` per spec). Every pre-flip claim's `remote_hash` was computed against the OLD payload, so byte-equal hash matches against the new corpus are vanishingly rare even when the underlying primitive is semantically unchanged.

What that means practically:

| Bucket | Initial cutover | Future incremental drift |
|---|---|---|
| **Id-match** (depgraph_id still resolves) | Common — primitive ids are stable for top-level symbols whose path didn't move | Common — most edits don't move ids |
| **Hash-match** (old depgraph_id missing, but a new primitive has same structural_hash) | **Rare** — hash shape changed | Common when a file moves |
| **Name-match** (no hash match, but exactly one new primitive has the same name + repo) | Used heavily for first cutover — auto-rewrites where unambiguous | Used occasionally |
| **Truly stale** | The bulk; surfaced in `CANDIDATES.md` for re-authoring | Rare |

The script does Id-match + Hash-match + Name-match, in that priority order. On first cutover, most auto-rewrites come from the Name-match path with a confidence-degrade — the claim retains its `depgraph_id` rewrite but `remote_hash` gets refreshed to the new corpus's hash (since we couldn't match against the old).

Author your expectation accordingly: the cutover requires a manual review pass over re-authored claims to confirm the Name-match auto-rewrites picked the right primitive. Don't ship the regen + auto-migration as if no human attention is required.

Buckets:

1. **Id-match**: claim's `depgraph_id` still exists in the new corpus → leave alone, refresh `remote_hash` to current.
2. **Hash-match**: id missing but a new primitive has the same `structural_hash` → auto-rewrite.
3. **Name-match**: id missing, no hash match, but exactly one new primitive has the same `name` field within the same repo → auto-rewrite, refresh `remote_hash`, log to `CANDIDATES.md` under "review me — name-match without hash agreement."
4. **Truly stale**: no candidate by id, hash, or name → flag in `CANDIDATES.md` for manual re-authoring.

- [ ] **Step 1: Write the migration script**

```python
# kg/cli/depgraph/migrate_logigraph_claims.py
"""Auto-rewrite stale logigraph claims after a v2 regen.

Usage:
    python -m kg.cli.depgraph.migrate_logigraph_claims \\
        --depgraph-dir ~/concorda-knowledge-graph/depgraph \\
        --logigraph-dir ~/concorda-knowledge-graph/logigraph \\
        [--dry-run]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_depgraph_index(depgraph_dir: Path) -> tuple[
    dict[str, dict], dict[str, list[str]], dict[tuple[str, str], list[str]],
]:
    """Return (by_id, by_hash, by_repo_name).
    - by_id: depgraph_id -> node
    - by_hash: structural_hash -> [ids]
    - by_repo_name: (repo, name) -> [ids] — name from node.name field
    """
    by_id: dict[str, dict] = {}
    by_hash: dict[str, list[str]] = {}
    by_repo_name: dict[tuple[str, str], list[str]] = {}
    for p in (depgraph_dir / "nodes").rglob("*.json"):
        if p.name.startswith("_") or "_index" in p.parts:
            continue
        try:
            node = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        nid = node.get("id")
        if not nid:
            continue
        by_id[nid] = node
        h = node.get("structural_hash")
        if h:
            by_hash.setdefault(h, []).append(nid)
        repo = (node.get("source") or {}).get("repo")
        name = node.get("name")
        if repo and name:
            by_repo_name.setdefault((repo, name), []).append(nid)
    return by_id, by_hash, by_repo_name


def _old_id_components(old_id: str) -> tuple[str, str] | None:
    """Parse `<repo>::<path>::<symbol>` into (repo, symbol). Returns None
    for ids that don't fit the shape (e.g., external terminals)."""
    parts = old_id.split("::")
    if len(parts) < 3:
        return None
    return parts[0], parts[-1]


def migrate(*, depgraph_dir: Path, logigraph_dir: Path,
            dry_run: bool = False) -> dict:
    by_id, by_hash, by_repo_name = load_depgraph_index(depgraph_dir)
    stats = {"unchanged": 0,
             "hash_match_rewritten": 0,
             "name_match_rewritten": 0,
             "ambiguous": 0,
             "stale": 0}
    candidates_path = logigraph_dir / "CANDIDATES.md"
    lines = ["# Stale logigraph claims after v2 regen\n",
             "Entries marked NAME-MATCH were auto-rewritten by name; please "
             "skim and confirm each picked the right primitive.\n"]

    for rule_path in (logigraph_dir / "nodes" / "rules").rglob("*.json"):
        rule = json.loads(rule_path.read_text())
        changed = False
        for claim in rule.get("claims_code", []):
            old_id = claim.get("depgraph_id")
            if not old_id:
                continue
            # 1) Id-match
            if old_id in by_id:
                # Refresh hash in case primitive's body shifted
                claim["remote_hash"] = by_id[old_id]["structural_hash"]
                stats["unchanged"] += 1
                changed = True
                continue
            # 2) Hash-match
            old_hash = claim.get("remote_hash")
            hash_candidates = by_hash.get(old_hash, []) if old_hash else []
            if len(hash_candidates) == 1:
                claim["depgraph_id"] = hash_candidates[0]
                claim["remote_hash"] = by_id[hash_candidates[0]]["structural_hash"]
                stats["hash_match_rewritten"] += 1
                changed = True
                continue
            if len(hash_candidates) > 1:
                stats["ambiguous"] += 1
                lines.append(f"- AMBIGUOUS-HASH in rule `{rule['id']}`: old_id "
                              f"`{old_id}` hash matches {len(hash_candidates)} primitives")
                continue
            # 3) Name-match — initial-cutover workhorse
            comps = _old_id_components(old_id)
            if comps is None:
                stats["stale"] += 1
                lines.append(f"- STALE in rule `{rule['id']}`: `{old_id}` unparseable")
                continue
            repo, name = comps
            name_candidates = by_repo_name.get((repo, name), [])
            if len(name_candidates) == 1:
                claim["depgraph_id"] = name_candidates[0]
                claim["remote_hash"] = by_id[name_candidates[0]]["structural_hash"]
                stats["name_match_rewritten"] += 1
                lines.append(f"- NAME-MATCH in rule `{rule['id']}`: `{old_id}` "
                              f"→ `{name_candidates[0]}` (review and confirm)")
                changed = True
                continue
            if len(name_candidates) > 1:
                stats["ambiguous"] += 1
                lines.append(f"- AMBIGUOUS-NAME in rule `{rule['id']}`: `{old_id}` "
                              f"matches {len(name_candidates)} by name: {name_candidates}")
                continue
            # 4) Truly stale
            stats["stale"] += 1
            lines.append(f"- STALE in rule `{rule['id']}`: `{old_id}` "
                          f"has no id / hash / name match in new corpus")
        if changed and not dry_run:
            rule_path.write_text(json.dumps(rule, indent=2, sort_keys=True))

    has_review_lines = (stats["ambiguous"] or stats["stale"]
                         or stats["name_match_rewritten"])
    if has_review_lines and not dry_run:
        candidates_path.write_text("\n".join(lines))
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depgraph-dir", type=Path, required=True)
    ap.add_argument("--logigraph-dir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    stats = migrate(depgraph_dir=args.depgraph_dir,
                    logigraph_dir=args.logigraph_dir,
                    dry_run=args.dry_run)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Dry-run on Concorda**

```bash
python -m kg.cli.depgraph.migrate_logigraph_claims \
    --depgraph-dir ~/concorda-knowledge-graph/depgraph \
    --logigraph-dir ~/concorda-knowledge-graph/logigraph \
    --dry-run
```

Expected: prints stats `{unchanged, auto_rewritten, ambiguous, stale}`. Sanity-check the numbers before the real run.

- [ ] **Step 3: Real run + reconcile**

```bash
python -m kg.cli.depgraph.migrate_logigraph_claims \
    --depgraph-dir ~/concorda-knowledge-graph/depgraph \
    --logigraph-dir ~/concorda-knowledge-graph/logigraph
kg logigraph regen
kg logigraph gaps
```

`logigraph gaps` should show zero auto-resolvable stale claims and only the `ambiguous`/`stale` entries listed in `CANDIDATES.md`.

- [ ] **Step 4: Triage the remainder manually + commit**

```bash
cd ~/concorda-knowledge-graph
git add logigraph/
git commit -m "logigraph: auto-migrate claims to v2 depgraph corpus; CANDIDATES.md flags remainder"
```

---

## Phase 1 retro-tasks

*All previously-deferred retros (returns_jsx, default-export naming, overload skipping, Python decorator normalization) are folded into Phase 1 Task 1.5 and Phase 2 Task 2.3 directly. This section is intentionally empty — it remains as a heading anchor in case a future cross-link points here.*

---

## Performance budget + incremental regen

**Full regen budget.** A clean run of `kg depgraph regen` against Concorda's three repos (api ~75k LOC Python + 115 migrations, web ~50k LOC TS, test ~30k LOC TS) should finish in under **30 seconds** on the development host. Components, sized roughly:

- TS extractor: ts-morph parse + walk for ~80k LOC ≈ 8s.
- Python extractor: stdlib `ast.parse` + walk ≈ 3s.
- SQL pipeline (parser over 65 CREATE TABLEs + 50 ALTERs + reconciliation) ≈ 2s.
- L2 edge resolution (calls + imports + reads/assigns/decorates) ≈ 5s.
- Cross-reference + db_access ≈ 2s.
- Classification ≈ 1s.
- Reconcile (validate + index build) ≈ 5s.

If regen blows the 30s budget by more than 2x in real Concorda, profile before optimizing — usual suspects are: `ast.unparse(node)` on huge nodes for body_text, repeated `re.compile` in a hot loop, or per-file ts-morph project init (use one Project for the repo).

**Determinism gate** (Task 6.7) does **not** add real runtime — it runs twice in the suite but on a tiny synthetic project.

**Incremental regen (out of scope for v0, noted for the future).**

The legacy stop-hook called `depgraph regen` over only the touched files. The v2 pipeline as designed runs full regen because the SQL reconciler, cross-reference pass, and classifier engine all need a corpus-wide view. Patching individual primitives in place without re-running these passes can produce inconsistent corpora.

For v0, the stop-hook should call `kg depgraph regen` with full scope. If that exceeds the time budget in practice, the incremental path is:

1. Per-file: re-extract that file's primitives + L2 edges only, replace in `nodes/<primitive_type>/`.
2. Run reconcile's validation + index rebuild (cheap; pure I/O over node files).
3. Skip the SQL pipeline and classifier unless touched files include a migration / ORM model.

Land this incremental mode only when the full-regen budget becomes painful in real use — premature without a measured baseline.

---

## Done definition

**Automated gates:**

- All tests in `depgraph/tests/` pass (`pytest depgraph/tests -v`)
- `depgraph/extractors/generic/` is deleted
- `depgraph/extractors/{typescript,python,sql}/` are the production extractors
- Determinism CI gate (`test_regen_determinism.py`) passes — two consecutive regens produce byte-identical output
- Kitchen-sink gate (`test_kitchen_sink.py`) passes — kind distribution matches, no orphan edges, every model references a schema, determinism holds at the assembled-pipeline level
- All per-phase wild-corpus tests (`test_typescript_wild`, `test_python_wild`, `test_edges_wild`, `test_sql_wild`, `test_classification_wild`) pass

**Claude/reviewer-signed gates:**

- Every fixture under `depgraph/tests/fixtures/wild/` has a current `verification.md` signed `✓ verified` (~40 fixtures + 1 kitchen-sink)
- Every component under `depgraph/tests/verification_logs/` has a current log signed `✓ verified` (5 components from Task 0.6)
- Kitchen-sink end-to-end verification log records the manually-traced edge spot-checks

**Consumer-side gates (Concorda):**

- Concorda corpus has been regenerated on v2 schema with no validation errors
- Logigraph claims are reconciled: auto-migrated where structural_hash matches, flagged in `CANDIDATES.md` where not
- Hook still injects context on Edit/Write/MultiEdit (tested against a real file edit on Concorda)
- graphui surfaces the new `schemas/` kind dir + v2 primitive-type dirs without code change required

**Spec gate:**

- `docs/superpowers/specs/2026-05-15-layered-substrate-design.md` decision-point checkboxes are all checked

---

## Out of scope for this implementation

Documented here so the engineer doesn't accidentally pick up adjacent work:

- Go, Rust, C, C++ extractors (deferred to a later pass per spec scope decision 2026-05-16)
- Schema-language extractors other than SQL: Prisma DSL, OpenAPI, GraphQL SDL, JSON Schema, Protobuf (deferred; their pattern is the same as the SQL pipeline — register the language, write a DSL parser, emit schema primitives — so adding them later is incremental)
- Document-store schemas (MongoDB, Firestore, DynamoDB shape inference): not in scope. Future approach uses JSON Schema files or Pydantic/Marshmallow validators as the schema source.
- Full L3 system-edge taxonomy beyond `db_access`: `webhook_publish/subscribe`, `queue_produce/consume`, `cache_access`, `file_storage_access`, `notification_send`, `observability_emit`, `feature_flag_check`, `auth_trust`, `schedule_trigger`, `config_read`, `env_share`, `external_service_call` (deferred; only `db_access` lands in this pass — it's the substrate the service classifier requires)
- Logigraph L3-claim support (deferred; this pass only resolves the L1 claim shape, plus schema-primitive claim targets via the existing `claims_code` field — schema primitive ids are stable L1-shaped strings)
- Graphui changes — assumes graphui's existing reads from `nodes/<kind>/` keep working with `nodes/schema/` added for the new schema kind. If not, a separate plan addresses it.
