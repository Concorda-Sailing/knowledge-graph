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
    system_stub/
      __init__.py                                 NEW
      db_access.py                                NEW   SQLAlchemy / cursor patterns
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
      test_db_access_stub.py                      NEW
      test_reconcile_v2.py                        NEW
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

### Phasing summary

| Phase | Goal | Tests | Cutover safe? |
|---|---|---|---|
| 0 | Foundation: schema, language registry, retire pre-flip gate, freeze legacy extractors | Schema validation tests | Yes (legacy still works) |
| 1 | TS primitives extractor | Primitive coverage tests | Legacy still works for Python |
| 2 | Python primitives extractor | Primitive coverage tests | Legacy still works for TS until cutover |
| 3 | L2 edge resolution (TS + Python) | Per-edge-kind tests | Phases 1+2 run together if both done |
| 4 | L3 db_access stub | SQLAlchemy / cursor recognition tests | n/a |
| 5 | Classification engine | Per-kind classifier tests | n/a |
| 6 | Cutover: reconcile + CLI wiring, delete legacy, regen Concorda | Integration test against real Concorda corpus | Final |

Phases 0–5 can land independently. The world only flips in Phase 6.

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
    parameters: list[SignatureParameter] = field(default_factory=list)
    return_type: str | None = None
    is_async: bool = False
    decorators: list[str] = field(default_factory=list)


@dataclass
class Attributes:
    abstract: bool = False
    generated: bool = False
    external: bool = False
    template_parameters: list[str] = field(default_factory=list)
    macro: bool = False
    mutable: bool = True               # for variables
    instantiable: bool = True          # for classes
    inheritable: bool = True           # for classes


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


def test_load_shipped_languages_includes_ts_and_py():
    langs = load_languages(FRAMEWORK_TOML)
    names = {l.name for l in langs}
    assert "typescript" in names
    assert "python" in names


def test_typescript_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    ts = langs["typescript"]
    assert ts.extensions == [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]


def test_python_extensions():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    py = langs["python"]
    assert py.extensions == [".py"]


def test_extractor_path_resolves_under_framework_root():
    langs = {l.name: l for l in load_languages(FRAMEWORK_TOML)}
    for name in ("typescript", "python"):
        l = langs[name]
        assert l.extractor.exists(), f"{name} extractor missing: {l.extractor}"
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
```

- [ ] **Step 3: Write `depgraph/lib/language_registry.py`**

```python
"""Language registry loader. Reads languages.toml from framework or project."""
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


def load_languages(toml_path: Path) -> list[Language]:
    """Load language definitions. `extractor` is resolved relative to the
    framework root (the parent of `depgraph/`)."""
    framework_root = toml_path.parent.parent  # languages.toml lives at depgraph/languages.toml
    data = tomllib.loads(toml_path.read_text())
    langs = []
    for name, spec in data.get("languages", {}).items():
        langs.append(Language(
            name=name,
            extensions=list(spec["extensions"]),
            extractor=(framework_root / spec["extractor"]).resolve(),
            runtime=spec["runtime"],
        ))
    return langs
```

- [ ] **Step 4: Create extractor stubs so registry tests pass**

The registry test asserts the extractor files exist. Phase 1 / 2 fill these with real code; for now they're empty placeholders.

```bash
mkdir -p depgraph/extractors/typescript depgraph/extractors/python
touch depgraph/extractors/typescript/extract.ts
touch depgraph/extractors/python/extract.py
echo '"""TS extractor — implemented in Phase 1."""' > depgraph/extractors/python/__init__.py
```

- [ ] **Step 5: Run tests**

Run: `pytest depgraph/tests/lib/test_language_registry.py -v`
Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add depgraph/languages.toml depgraph/lib/language_registry.py \
        depgraph/tests/lib/test_language_registry.py \
        depgraph/extractors/typescript/extract.ts \
        depgraph/extractors/python/extract.py depgraph/extractors/python/__init__.py
git commit -m "depgraph: v2 language registry (languages.toml + loader)"
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

### Task 1.5: Function primitives (top-level + method + arrow-bound)

- [ ] **Step 1: Create fixture**

```typescript
// depgraph/tests/extractors/fixtures/primitives_ts/functions/src/all.ts
export function topLevel(x: number): string { return String(x); }
export async function asyncFn() { return 1; }
export const arrow = (a: string) => a.length;
export const arrowConst: () => void = () => {};

export class Holder {
  method(x: number): string { return String(x); }
  async asyncMethod() {}
  static staticMethod() {}
  private privateMethod() {}
}
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
```

- [ ] **Step 3: Run, verify fail**

Run: `pytest depgraph/tests/extractors/test_typescript_primitives.py -v -k function or method`
Expected: all function/method tests FAIL.

- [ ] **Step 4: Implement function extraction**

Add to `extract.ts`:

```typescript
function functionPrimitive(
  node: { getStartLineNumber(): number; getEndLineNumber(): number },
  name: string,
  owner: string | null,
  signature: { parameters: { name: string; type_annotation: string | null }[];
               return_type: string | null;
               is_async: boolean;
               decorators: string[] },
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
    structural_hash: structuralHash({ kind: "function", symbol, signature }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function paramShape(p: any) {
  return { name: p.getName(), type_annotation: p.getTypeNode()?.getText() ?? null };
}

function extractFunctions(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];

  for (const fn of sf.getFunctions()) {
    if (!fn.getName()) continue;  // anonymous default exports etc.
    out.push(functionPrimitive(fn, fn.getName()!, null, {
      parameters: fn.getParameters().map(paramShape),
      return_type: fn.getReturnTypeNode()?.getText() ?? null,
      is_async: fn.isAsync(),
      decorators: [],
    }, repoKey, relPath));
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
        }, repoKey, relPath));
      }
    }
  }

  for (const cls of sf.getClasses()) {
    const classId = canonicalId(repoKey, relPath, cls.getName() ?? "<anonymous>");
    for (const m of cls.getMethods()) {
      out.push(functionPrimitive(m, m.getName(), classId, {
        parameters: m.getParameters().map(paramShape),
        return_type: m.getReturnTypeNode()?.getText() ?? null,
        is_async: m.isAsync(),
        decorators: m.getDecorators().map((d) => d.getName()),
      }, repoKey, relPath));
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
  repoKey: string, relPath: string,
): Primitive {
  const symbol = owner ? `${owner.split("::").pop()}.${name}` : name;
  return {
    schema_version: 2, id: canonicalId(repoKey, relPath, symbol),
    primitive: "variable", name: symbol, owner,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature: { type_annotation },
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({ kind: "variable", symbol, mutable, type_annotation }),
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
        repoKey, relPath));
    }
  }

  for (const cls of sf.getClasses()) {
    const classId = canonicalId(repoKey, relPath, cls.getName() ?? "<anonymous>");
    for (const prop of cls.getProperties()) {
      out.push(variablePrimitive(prop, prop.getName(), classId,
        !prop.isReadonly(),
        prop.getTypeNode()?.getText() ?? null,
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
          }, repoKey, relPath));
        } else if (Node.isPropertyAssignment(prop)) {
          out.push(variablePrimitive(prop, prop.getName(), classId, true, null, repoKey, relPath));
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


def _emit_class(node: ast.ClassDef, *, repo_key: str, rel_path: str) -> Iterator[dict]:
    class_id = canonical_id(repo_key, rel_path, node.name)
    tparams = [tp.name for tp in getattr(node, "type_params", [])]
    yield _base_primitive(
        schema_id=class_id, primitive="class", name=node.name, owner=None,
        repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
        signature={"decorators": [_decorator_name(d) for d in node.decorator_list]},
        attributes_overrides={"abstract": False, "instantiable": True,
                              "template_parameters": tparams},
        structural_payload={"kind": "class", "name": node.name,
                            "bases": [ast.unparse(b) for b in node.bases]},
    )
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield _function_primitive(child, owner=class_id, repo_key=repo_key, rel_path=rel_path)
        elif isinstance(child, (ast.Assign, ast.AnnAssign)):
            yield from _variable_primitives(child, owner=class_id, repo_key=repo_key, rel_path=rel_path)


def _function_primitive(node: ast.FunctionDef | ast.AsyncFunctionDef,
                        *, owner: str | None, repo_key: str, rel_path: str) -> dict:
    symbol = f"{owner.split('::')[-1]}.{node.name}" if owner else node.name
    params = [{"name": a.arg, "type_annotation": _annotation_text(a.annotation),
               "default": None}
              for a in node.args.args + node.args.kwonlyargs]
    tparams = [tp.name for tp in getattr(node, "type_params", [])]
    return _base_primitive(
        schema_id=canonical_id(repo_key, rel_path, symbol),
        primitive="function", name=symbol, owner=owner,
        repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
        signature={
            "parameters": params,
            "return_type": _annotation_text(node.returns),
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "decorators": [_decorator_name(d) for d in node.decorator_list],
        },
        attributes_overrides={"template_parameters": tparams,
                              "instantiable": False, "inheritable": False},
        structural_payload={"kind": "function", "name": symbol,
                            "params": [p["name"] for p in params]},
    )


def _variable_primitives(node: ast.Assign | ast.AnnAssign,
                          *, owner: str | None, repo_key: str, rel_path: str) -> Iterator[dict]:
    if isinstance(node, ast.AnnAssign):
        targets = [node.target]
        type_ann = _annotation_text(node.annotation)
    else:
        targets = node.targets
        type_ann = None
    for tgt in targets:
        if not isinstance(tgt, ast.Name):
            continue
        symbol = f"{owner.split('::')[-1]}.{tgt.id}" if owner else tgt.id
        yield _base_primitive(
            schema_id=canonical_id(repo_key, rel_path, symbol),
            primitive="variable", name=symbol, owner=owner,
            repo=repo_key, path=rel_path, line=node.lineno, end_line=node.end_lineno or node.lineno,
            signature={"type_annotation": type_ann},
            attributes_overrides={"mutable": tgt.id != tgt.id.upper(),
                                  "instantiable": False, "inheritable": False},
            structural_payload={"kind": "variable", "name": symbol, "type": type_ann},
        )
```

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

- [ ] **Step 3: Run, verify fail. Implement. Verify pass.**

TS: walk `sf.getImportDeclarations()`. For each named import, resolve module specifier to a tracked source file via ts-morph's `getModuleSpecifierSourceFile()` (works for relative imports; non-resolved imports emit `confidence: "unresolved"` and `target: external::npm::<module>::<symbol>`).

Python: walk `ast.Import` and `ast.ImportFrom`. For `ImportFrom`, resolve module to a tracked file via a corpus-wide module index built from the package + module set. For dotted absolute imports (`from concorda_api.routers.events import create_event`), match the dot-joined name against module paths under the repo root.

- [ ] **Step 4: Commit**

```bash
git commit -m "depgraph/extractors: emit imports edges (exact for tracked targets, unresolved for external)"
```

### Task 3.4: `calls` + `instantiates`

- [ ] **Step 1: TS fixture**

```typescript
// fixtures/edges_ts/calls/src/file.ts
function helper(): string { return "ok"; }
class Service {}
export function root() {
  helper();
  const s = new Service();
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
```

- [ ] **Step 2: Python fixture**

```python
# fixtures/edges_py/calls/src.py
def helper(): return "ok"
class Service: pass
def root():
    helper()
    s = Service()
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
```

- [ ] **Step 3: Implement**

For both languages, walk the function body AST. For each call expression:
- Resolve the callee name against (a) local symbols, (b) imported names. If callee resolves to a class primitive, emit `instantiates`; if a function primitive, emit `calls`.
- Where unresolved (dynamic dispatch, computed property access), record edge with `confidence: "unresolved"` and skip from "exact" gates.

Python implementation sketch:

```python
def _walk_function_body_for_calls(fn_node, *, fn_primitive_id, primitives_by_name, file_imports):
    edges = []
    for sub in ast.walk(fn_node):
        if isinstance(sub, ast.Call):
            callee_name = _callee_name(sub.func)
            target_id = primitives_by_name.get(callee_name) or file_imports.get(callee_name)
            if not target_id:
                continue
            kind = "instantiates" if _is_class_id(target_id, primitives_by_name) else "calls"
            edges.append({"target": target_id, "kind": kind, "via": "function_call",
                          "where": f"{file}:{sub.lineno}", "confidence": "exact"})
    return edges
```

Same approach in TS using `descendants.filter((d) => Node.isCallExpression(d) || Node.isNewExpression(d))`.

- [ ] **Step 4: Run, verify pass + commit.**

### Task 3.5: `references` + `reads` + `assigns` + `decorates`

These are quieter edges but matter for classification.

- [ ] **Step 1: TS fixture**

```typescript
// fixtures/edges_ts/references/src/file.ts
function reader(): number {
  return globalCount;
}
function writer() {
  globalCount = 1;
}
let globalCount = 0;
function decorated() {}
```

Tests check that `reader` has a `reads` edge to `globalCount`, `writer` has an `assigns` edge to it.

- [ ] **Step 2: Python fixture**

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
def decorated(): pass
```

Tests check `reads` and `assigns` edges plus `decorates` from `functools.lru_cache` → `decorated`.

- [ ] **Step 3: Implement, run, pass, commit**

For both languages: walk function body looking for variable access (Name in load context → reads; Name in store context → assigns). For decorators, the function/class primitive's `signature.decorators` already lists them; convert to `decorates` edges from the decorator-source (Name reference at module/import level) to the decorated target.

### Task 3.6: `tests` edges

A function whose body calls a known test framework primitive is a test. The function being tested is identified by name correlation (`test_foo` → `foo`) or by explicit assertion targets.

- [ ] **Step 1: TS fixture (vitest)**

```typescript
// fixtures/edges_ts/tests/src/example.test.ts
import { describe, it, expect } from "vitest";
import { add } from "./math.js";
describe("add", () => {
  it("adds", () => { expect(add(1, 2)).toBe(3); });
});
```

```typescript
// fixtures/edges_ts/tests/src/math.ts
export function add(a: number, b: number): number { return a + b; }
```

Test:

```python
def test_tests_edge_to_subject():
    prims = run_extractor("tests", which="edges")
    test_fn = next(p for p in prims if p["primitive"] == "function"
                   and p["source"]["path"].endswith(".test.ts"))
    tests = [e for e in test_fn["edges_out"] if e["kind"] == "tests"]
    assert any(e["target"] == "fixture::src/math.ts::add" for e in tests)
```

- [ ] **Step 2: Python fixture (pytest)**

```python
# fixtures/edges_py/tests/src/math.py
def add(a, b): return a + b
```

```python
# fixtures/edges_py/tests/src/test_math.py
from .math import add
def test_add(): assert add(1, 2) == 3
```

Test:

```python
def test_tests_edge_py():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE_DIR / "tests"))
    tfn = next(p for p in prims if p["name"] == "test_add")
    tests = [e for e in tfn["edges_out"] if e["kind"] == "tests"]
    assert any(e["target"] == "fixture::src/math.py::add" for e in tests)
```

- [ ] **Step 3: Implement**

A test function is one whose body contains a call to a known test framework primitive (`expect`, `it`, `test`, `describe` for vitest; `pytest.fixture`, `assert` in a test_*-named function for pytest). For each call inside the test function to an imported function from a non-test module, emit a `tests` edge to that target.

The exact recognition rules:
- TS: function inside a `*.test.ts` file → test function. `tests` edge target = each imported function that's called inside the test body.
- Python: function whose name starts with `test_` OR has a `@pytest.fixture` decorator → test function. Same target rule.

- [ ] **Step 4: Run, verify pass + commit.**

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

---

## Phase 4 — L3 Thin Stub: db_access

The classifier needs `db_access` edges to recognize a service. We implement the minimum needed for JS/TS/Python: SQLAlchemy session method calls and raw `cursor.execute` calls in Python. (TypeScript ORMs are mostly schema-language-sourced — Prisma — which is out of this scope; we accept that TS service classification will be evidence-light in this pass.)

**Files:**
- Create: `depgraph/lib/system_stub/__init__.py`
- Create: `depgraph/lib/system_stub/db_access.py`
- Test: `depgraph/tests/lib/test_db_access_stub.py`

### Task 4.1: SQLAlchemy session db_access (Python)

A function that calls `session.query(...)`, `session.add(...)`, `session.commit()`, `session.execute(...)`, or `cursor.execute(...)` emits a `db_access` edge (system-level edge stored under `edges_out` like other edges; targets a synthetic terminal `external::pypi::sqlalchemy::Session.<method>` or the table primitive once SQL extraction exists in a later pass).

For this pass, target is the synthetic terminal (since we have no schema-language extraction in scope).

- [ ] **Step 1: Fixture**

```python
# depgraph/tests/extractors/fixtures/edges_py/db_access/src.py
def get_user(session, user_id):
    return session.query(User).filter(User.id == user_id).first()

def save_user(session, user):
    session.add(user)
    session.commit()
```

- [ ] **Step 2: Write failing test**

```python
# depgraph/tests/lib/test_db_access_stub.py
from pathlib import Path
from depgraph.extractors.python.extract import extract_repo
from depgraph.lib.system_stub.db_access import attach_db_access_edges

FIXTURE = Path(__file__).resolve().parents[1] / "extractors/fixtures/edges_py/db_access"

def test_sqlalchemy_session_query_recognized():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE))
    attach_db_access_edges(prims, repo_path=FIXTURE)
    fn = next(p for p in prims if p["name"] == "get_user")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    assert any("query" in e["via"] for e in dba)

def test_sqlalchemy_session_add_recognized():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE))
    attach_db_access_edges(prims, repo_path=FIXTURE)
    fn = next(p for p in prims if p["name"] == "save_user")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    methods = {e["via"] for e in dba}
    assert "session.add" in methods or "add" in methods
    assert "session.commit" in methods or "commit" in methods
```

- [ ] **Step 3: Run, verify fail.**

- [ ] **Step 4: Implement `depgraph/lib/system_stub/db_access.py`**

```python
"""Thin L3 stub — recognize SQLAlchemy session + cursor patterns.

This is *not* full L3 system-edge extraction. It exists to feed the
service classifier's evidence requirement (function with at least one
db_access / queue_produce / etc. edge).

Full L3 extraction (DSL-sourced schema targets, ORM-client method
resolution) is a later pass.
"""
from __future__ import annotations

import ast
from pathlib import Path

_SQLALCHEMY_METHODS = {"query", "add", "commit", "execute", "scalars",
                       "scalar", "delete", "merge", "flush", "rollback"}


def attach_db_access_edges(primitives: list[dict], *, repo_path: Path) -> list[dict]:
    """Re-parse each Python source file once, walk function bodies, append
    db_access edges for SQLAlchemy session and DB-API cursor calls.

    Mutates `primitives` in place; returns the same list for chaining.
    """
    by_path: dict[str, list[dict]] = {}
    for p in primitives:
        if p["source"]["language"] != "python":
            continue
        by_path.setdefault(p["source"]["path"], []).append(p)

    for path, prims_in_file in by_path.items():
        source_text = (repo_path / path).read_text()
        tree = ast.parse(source_text)
        fn_by_line = {p["source"]["line"]: p
                      for p in prims_in_file if p["primitive"] == "function"}

        # First pass: identify variable names that hold a cursor (assigned
        # from a `.cursor()` call). Used so `cur.execute(...)` after
        # `cur = conn.cursor()` is recognized as db_access.
        cursor_names_per_fn: dict[int, set[str]] = {}
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            cursor_names: set[str] = set()
            for sub in ast.walk(fn_node):
                if (isinstance(sub, ast.Assign)
                        and isinstance(sub.value, ast.Call)
                        and isinstance(sub.value.func, ast.Attribute)
                        and sub.value.func.attr == "cursor"):
                    for tgt in sub.targets:
                        if isinstance(tgt, ast.Name):
                            cursor_names.add(tgt.id)
            cursor_names_per_fn[fn_node.lineno] = cursor_names

        # Second pass: emit db_access edges
        for fn_node in ast.walk(tree):
            if not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fn_prim = fn_by_line.get(fn_node.lineno)
            if not fn_prim:
                continue
            cursor_names = cursor_names_per_fn.get(fn_node.lineno, set())
            for sub in ast.walk(fn_node):
                if not isinstance(sub, ast.Call):
                    continue
                if not isinstance(sub.func, ast.Attribute):
                    continue
                method = sub.func.attr
                receiver_text = ast.unparse(sub.func.value)
                receiver_root = receiver_text.split(".")[0]

                # Pattern A: SQLAlchemy session-style methods
                if method in _SQLALCHEMY_METHODS:
                    target = f"external::pypi::sqlalchemy::Session.{method}"
                # Pattern B: DB-API cursor.execute / cursor.fetchone etc.
                elif method in {"execute", "executemany", "fetchone", "fetchall", "fetchmany"} \
                        and (receiver_root in cursor_names or "cur" in receiver_root.lower()):
                    target = f"external::python-dbapi::Cursor.{method}"
                else:
                    continue

                fn_prim["edges_out"].append({
                    "target": target, "kind": "db_access",
                    "via": f"{receiver_text}.{method}",
                    "where": f"{path}:{sub.lineno}",
                    "confidence": "exact",
                })
    return primitives
```

- [ ] **Step 5: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/test_db_access_stub.py -v
git add depgraph/lib/system_stub/ depgraph/tests/lib/test_db_access_stub.py \
        depgraph/tests/extractors/fixtures/edges_py/db_access/
git commit -m "depgraph: L3 stub — SQLAlchemy db_access edge recognition (Python)"
```

### Task 4.2: Raw cursor.execute pattern

- [ ] **Step 1: Fixture + test**

Fixture adds:

```python
def raw_query(conn, uid):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (uid,))
    return cur.fetchone()
```

Test:

```python
def test_raw_cursor_execute_recognized():
    prims = list(extract_repo(repo_key="fixture", repo_path=FIXTURE))
    attach_db_access_edges(prims, repo_path=FIXTURE)
    fn = next(p for p in prims if p["name"] == "raw_query")
    dba = [e for e in fn["edges_out"] if e["kind"] == "db_access"]
    assert any("execute" in e["via"] for e in dba)
```

- [ ] **Step 2: Confirm — Task 4.1's `attach_db_access_edges` already implements the cursor recognition path (the "Pattern B" branch + the cursor-name pre-pass). No code change needed; this task adds the second test fixture and asserts the existing implementation covers it.**

- [ ] **Step 3: Run, verify pass + commit**

```bash
pytest depgraph/tests/lib/test_db_access_stub.py::test_raw_cursor_execute_recognized -v
git add depgraph/tests/extractors/fixtures/edges_py/db_access/ \
        depgraph/tests/lib/test_db_access_stub.py
git commit -m "depgraph: L3 stub — DB-API cursor.execute recognition (Python)"
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
    decisions: dict[str, Decision] = {
        p["id"]: Decision(kind=None, rule="unclassified") for p in primitives
    }
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
from dataclasses import dataclass, field

@dataclass
class ClassificationConfig:
    route_decorators: set[str] = field(default_factory=lambda: {
        "router.get", "router.post", "router.put", "router.patch", "router.delete",
        "app.get", "app.post", "app.put", "app.patch", "app.delete",
        "router.head", "router.options",
    })
    orm_base_classes: set[str] = field(default_factory=lambda: {
        "DeclarativeBase", "Base", "Model",  # SQLAlchemy
        "BaseModel",                          # Pydantic (acts model-like)
    })
    test_framework_primitives: set[str] = field(default_factory=lambda: {
        # JS/TS
        "it", "test", "describe", "expect",
        # Python
        "pytest.fixture", "pytest.mark", "assert",
    })
    hook_call_names: set[str] = field(default_factory=lambda: {
        "useState", "useEffect", "useMemo", "useCallback", "useRef",
        "useContext", "useReducer", "useLayoutEffect",
    })


def default_config() -> ClassificationConfig:
    return ClassificationConfig()
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

> NOTE: For `returns_jsx` to be available, the TS extractor needs to set it on the function signature. **Add a step in Phase 1 (Task 1.5 revisited)** that records `returns_jsx: true` when the function body contains a `JsxElement` or `JsxFragment` descendant. The engineer should retro-apply this when implementing this classifier — see "Phase 1 retro-tasks" at the end of this plan.

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

### Task 5.6: Model classifier

- [ ] **Step 1: Test**

```python
# test_classifier_model.py
def test_class_extending_orm_base_is_model():
    user_class = {
        "id": "r::models/user.py::User", "primitive": "class", "name": "User",
        "owner": None,
        "source": {"path": "models/user.py", "line": 1, "end_line": 1, "language": "python", "repo": "r"},
        "signature": {"decorators": []}, "attributes": {},
        "edges_out": [{"target": "external::pypi::sqlalchemy::DeclarativeBase",
                       "kind": "extends", "via": "class_decl", "where": "models/user.py:1", "confidence": "exact"}],
        "structural_hash": "0", "kind": None, "extractor": "t", "schema_version": 2,
    }
    from depgraph.lib.classification.engine import classify_corpus
    decisions = classify_corpus([user_class])
    assert decisions["r::models/user.py::User"].kind == "model"
```

- [ ] **Step 2: Implement**

```python
# lib/classification/model.py
KIND = "model"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    decisions = {}
    for p in primitives:
        if p["primitive"] != "class":
            continue
        for e in by_source.get(p["id"], []):
            if e["kind"] != "extends":
                continue
            # The target id might be external::pypi::sqlalchemy::Base or a local
            # primitive whose name is one of the ORM base names.
            target_last = e["target"].split("::")[-1]
            if target_last in config.orm_base_classes:
                decisions[p["id"]] = {
                    "rule": "extends_orm_base",
                    "evidence": [{"base": target_last, "via": e["via"]}],
                }
                break
    return decisions
```

- [ ] **Step 3: Run, verify pass + commit.**

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

- [ ] **Step 1b: Implement util**

```python
# lib/classification/util.py
KIND = "util"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    """Function is util iff at least one caller is already classified
    AND the function itself is not yet classified."""
    classified_ids = {pid for pid, dec in decisions_so_far.items() if dec.kind}

    callers_by_target: dict[str, list[str]] = {}
    for src_id, edges in by_source.items():
        for e in edges:
            if e["kind"] == "calls":
                callers_by_target.setdefault(e["target"], []).append(src_id)

    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        if p["id"] in classified_ids:
            continue
        classified_callers = [c for c in callers_by_target.get(p["id"], [])
                              if c in classified_ids]
        if classified_callers:
            decisions[p["id"]] = {
                "rule": "called_by_classified",
                "evidence": [{"caller": c} for c in classified_callers],
            }
    return decisions
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
    "service": "services", "model": "models", "test": "tests", "util": "utils",
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

---

## Phase 6 — Cutover

**Goal:** Wire the new pipeline into `kg depgraph regen` + `kg depgraph context` + the PreToolUse hook. Delete the frozen legacy extractors. Regen Concorda's corpus.

**Files:**
- Modify: `depgraph/extractors/reconcile.py` (rewrite for v2)
- Modify: `kg/cli/depgraph/regen.py` (or wherever regen lives) — invoke new extractors per language registry
- Delete: `depgraph/extractors/generic/` (whole subtree)
- Test: `depgraph/tests/test_reconcile_v2.py` (full end-to-end against a tiny synthetic project)

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
2. Validates each against `validate_primitive`.
3. Builds `nodes/_index/by_source.json` (source_id → outgoing edges) and `nodes/_index/by_target.json` (target_id → incoming edges with source_id).
4. Builds `nodes/_index/by_repo.json`.
5. Writes `nodes/_meta.json` with corpus stats (primitive count, edge count, regen_status).

Delete the legacy reconcile functions that fed pre-flip-shape concerns: `_join_route_calls`, `strip_legacy_fields`, `_run_embedding_pass` (preserve only if used in the new model).

- [ ] **Step 3: Implement regen entry point**

The user-facing CLI is `kg depgraph regen`. It must:
1. Load `project.toml` (gives `repos.*` paths + per-repo `include_paths` / `languages`).
2. For each repo × language, invoke the language's extractor (per `languages.toml`) and collect primitives + edges.
3. Run the L3 stub (Python only).
4. Run the classification engine.
5. Write all primitives to disk via `write_classified`.
6. Run reconcile to build indexes.

- [ ] **Step 4: Run end-to-end, verify pass + commit**

```bash
pytest depgraph/tests/test_reconcile_v2.py -v
git add depgraph/extractors/reconcile.py kg/cli/depgraph/ depgraph/tests/test_reconcile_v2.py
git commit -m "depgraph: rewrite reconcile + regen for v2 layered substrate"
```

### Task 6.2: Wire PreToolUse hook to new pipeline

The hook at `~/.claude/settings.json` calls `kg hook pre-edit`. That hook reads from `nodes/_index/by_target.json` (new shape) to surface incoming edges before edits. Update the hook's reader to consume v2 shape.

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
    """Write a tiny v2 corpus by hand (skip the full regen pipeline)."""
    nodes = tmp_path / "nodes"
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
    return tmp_path


def test_hook_pre_edit_surfaces_callers(tiny_corpus, tmp_path):
    src_root = tmp_path / "api"
    src_root.mkdir()
    (src_root / "routers.py").write_text("def helper(): pass\n\ndef create_event():\n    helper()\n")

    out = subprocess.run([
        sys.executable, "-m", "kg.cli", "hook", "pre-edit",
        "--file", str(src_root / "routers.py"),
    ], capture_output=True, text=True, check=True,
       env={"DEPGRAPH_DATA_DIR": str(tiny_corpus), "PATH": __import__("os").environ["PATH"]})
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
languages = ["python"]
include_paths = ["**/*.py"]
exclude_paths = ["**/__pycache__/**", "**/.venv/**", "**/venv/**", "**/tests/**"]

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

### Task 6.5: Regen Concorda corpus

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

### Task 6.6: Logigraph reconcile

Existing logigraph claims point at depgraph node ids. Many will have changed (or moved to different paths). Run `logigraph regen` → `logigraph gaps` to see which claims are stale.

- [ ] **Step 1: Run**

```bash
kg logigraph regen
kg logigraph gaps
```

- [ ] **Step 2: Address stale claims**

For each stale claim: either auto-rewrite if structural_hash matches a new node, or flag for manual re-authoring. Document the migration in `~/concorda-knowledge-graph/logigraph/CANDIDATES.md`.

- [ ] **Step 3: Commit logigraph state**

```bash
cd ~/concorda-knowledge-graph
git add logigraph/
git commit -m "logigraph: reconcile against v2 depgraph corpus (claim migration)"
```

---

## Phase 1 retro-tasks (referenced from Phase 5)

A handful of attributes used by the classifier need to be set by the L1 extractors. Add these as in-place edits to the extractor files when the classifier task arrives.

### Retro 1: TS extractor records `returns_jsx`

When emitting a function primitive (Task 1.5), walk the body for any `JsxElement` / `JsxFragment` descendant. If found, set `signature.returns_jsx = true`. Otherwise omit the key.

```typescript
// inside functionPrimitive's signature construction
const hasJsx = fn.getDescendantsOfKind(SyntaxKind.JsxElement).length > 0
              || fn.getDescendantsOfKind(SyntaxKind.JsxFragment).length > 0
              || fn.getDescendantsOfKind(SyntaxKind.JsxSelfClosingElement).length > 0;
signature.returns_jsx = hasJsx ? true : false;
```

Add a corresponding test in `test_typescript_primitives.py`:

```python
def test_function_returning_jsx_records_attribute():
    # fixture: src/component.tsx with `export function Foo() { return <div/>; }`
    prims = run_extractor("returns_jsx")
    foo = next(p for p in prims if p["name"] == "Foo")
    assert foo["signature"]["returns_jsx"] is True
```

### Retro 2: Python extractor records `decorators` consistently

The decorator list should be dotted-name strings (e.g., `"router.post"` not `"router.post('/events')"`). The classifier's match logic depends on this.

---

## Done definition

- All tests in `depgraph/tests/` pass (`pytest depgraph/tests -v`)
- `depgraph/extractors/generic/` is deleted
- `depgraph/extractors/{typescript,python}/` are the production extractors
- Concorda corpus has been regenerated on v2 schema with no validation errors
- Logigraph claims are reconciled (stale claims either rewritten or flagged in `CANDIDATES.md`)
- Hook still injects context on Edit/Write/MultiEdit (tested against a real file edit on Concorda)
- `docs/superpowers/specs/2026-05-15-layered-substrate-design.md` decision-point checkboxes are all checked

---

## Out of scope for this implementation

Documented here so the engineer doesn't accidentally pick up adjacent work:

- Go, Rust, C, C++ extractors (deferred to a later pass per spec scope decision 2026-05-16)
- Schema-language extractors: SQL, Prisma, OpenAPI, GraphQL, JSON Schema, Protobuf (deferred)
- Full L3 system-edge taxonomy: webhook_publish/subscribe, queue_produce/consume, cache_access, file_storage_access, notification_send, observability_emit, feature_flag_check, auth_trust, schedule_trigger, config_read, env_share, external_service_call (deferred; only db_access stubbed in this pass)
- Logigraph L3-claim support (deferred; this pass only resolves the L1 claim shape)
- Graphui changes — assumes graphui's existing reads from `nodes/<kind>/` keep working; if not, a separate plan addresses it.
