# Framework canonicalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `generic/<lang>/extract.{py,ts}` produce **byte-equivalent** depgraph nodes to pre-flip Concorda for every kind it tracks (endpoint, model, schema, service, test, component, hook, route_call). Same `id`, same `structural_hash`, same dossier filename, same `depends_on` taxonomy. So when Concorda flips, every existing dossier still finds its node, every `last_reviewed_against_hash` stays valid, and no human review state is lost.

**Architecture:** Add a canonicalization stage between "run detectors" and "write" in each language extractor. The stage knows the *exact* per-kind contract pinned in this plan (see § Canonical Node Contracts). Detectors expose the metadata the canonical layer needs to reproduce pre-flip byte-for-byte. The gate is a fixture-based regression test: a sample of real pre-flip Concorda nodes (one per kind) is committed to the test suite; the new extractor must produce byte-identical `id` + `structural_hash` + `signature` for each one before any subsequent task lands.

**Tech Stack:** Python 3 (stdlib `ast`), TypeScript with ts-morph (already in `~/concorda-knowledge-graph/depgraph/package.json`), `pytest`, `vitest`.

**Background reading required before starting:**
- `docs/superpowers/specs/2026-05-15-language-extractors-design.md` — original design
- `~/concorda-knowledge-graph/depgraph/extractors/extract_api.py` — pre-flip Python truth (1071 lines)
- `~/concorda-knowledge-graph/depgraph/extractors/extract_web.ts` — pre-flip TS truth (566 lines)
- `~/concorda-knowledge-graph/depgraph/extractors/extract_tests.ts` — pre-flip TS-test truth (519 lines)
- Audit findings in conversation history at `~/.claude/projects/-home-lgreenlee-tools-knowledge-graph/` — what went wrong in the first flip attempt at `0d1773e` (reverted at `cacf6edd` in `~/concorda-knowledge-graph`)

---

## Canonical Node Contracts

**One subsection per kind.** Each pins: `id` format, slugify variant, `signature`, `structural_hash` payload key-by-key, `depends_on` `via:` taxonomy, `source` block, JSON serialization. Implementers must follow these contracts exactly — divergence breaks the regression test.

### Common fields (all kinds except `route_call`)

Every canonical node has these top-level keys (Python writer uses `json.dumps(..., indent=2, sort_keys=True)`, so they end up alphabetized on disk):

```
schema_version: 1
id: <see per-kind>
kind: <see per-kind>
title: <see per-kind>
feature: null
source: {repo, path, symbol, line}    (insertion order)
signature: <see per-kind>
structural_hash: <sha256 hex; see per-kind payload>
depends_on: [ {target, via, where, confidence}, ... ]
external_consumers: []
tests: []
dossier: "dossiers/<plural-kind>/<slug>.md"
extractor: <pre-flip name; see below>
warnings: []
```

**`source.repo`** is the canonical repo name (e.g. `"concorda-api"`, `"concorda-web"`, `"concorda-test"`). It comes from `--repo-key` — see the [Project wiring](#project-wiring) section below.

**`extractor` field**: stamp the pre-flip extractor name per-kind for compatibility (`"extract_api.py"` for python kinds, `"extract_web.ts"` for component/hook/service-ts/route_call, `"extract_tests.ts"` for test-ts). The framework's actual extractor path differs but this field's value is pinned. (Justification: a few telemetry/UI surfaces may key off this string. Cheap to preserve.)

### Slugify variants

Two different slugify functions are in use today. Both must be supported.

```python
# slugify_id_py  — used for ALL python-produced kinds + ALL endpoint dossier filenames
def slugify_id_py(node_id: str) -> str:
    return (
        node_id.replace("::", "__")
        .replace("/", "_")
        .replace("{", "")
        .replace("}", "")
        .strip("_")
    )

# slugify_id_ts  — used for ALL typescript-produced kinds (component, hook, service-ts, test-ts, route_call)
def slugify_id_ts(node_id: str) -> str:
    # Equivalent to: id.replace(/::/g, "__").replace(/[^a-zA-Z0-9_]/g, "_").replace(/^_+|_+$/g, "")
    import re
    s = node_id.replace("::", "__")
    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)
    s = s.strip("_")
    return s
```

The TS slugify is strictly more aggressive (replaces `-`, `.`, `[`, `]`, etc.). They produce different filenames for the same id. Example: `concorda-web::src/app/code-of-conduct/page.tsx::CodeOfConductPage` →
- `slugify_id_py`: `concorda-web__src_app_code-of-conduct_page.tsx__CodeOfConductPage`
- `slugify_id_ts`: `concorda_web__src_app_code_of_conduct_page_tsx__CodeOfConductPage` ← what's on disk

### Hash function

```python
# Python: extract_api.py:499-501
def structural_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()

# TypeScript: extract_web.ts:76-78 and extract_tests.ts equivalent
function sha(payload: unknown): string {
    return crypto.createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}
```

**Critical:** Python sorts keys before hashing. TS uses `JSON.stringify` default which serializes in **insertion order**. The TS canonical layer must build payload objects with the same key insertion order pre-flip used per kind, or hashes diverge.

### canonical_path (endpoints)

```python
# extract_api.py:425-443
def canonical_path(path: str) -> str:
    """Replace named path params with positional placeholders.
    /users/{id} -> /users/{0}; /users/{user_id}/posts/{post_id} -> /users/{0}/posts/{1}"""
    out, depth, idx = [], 0, 0
    for ch in path:
        if ch == "{":
            depth = 1; out.append("{"); continue
        if ch == "}" and depth:
            depth = 0; out.append(f"{idx}}}"); idx += 1; continue
        if depth:
            continue
        out.append(ch)
    return "".join(out)
```

### Kind: `endpoint` (python)

- **id**: `f"{method.upper()}::{canonical_path(path)}"` — e.g. `DELETE::/api/admin/email-templates/{0}`
- **title**: `f"{method} {full_path}"` (path **un**-canonicalized, e.g. `DELETE /api/admin/email-templates/{template_id}`)
- **signature**:
  ```
  {
    "method": <METHOD>,
    "path": <un-canonicalized path>,
    "auth": "none" | "user" | "admin" | "agent_token",
    "request_schema_ref": null | <request type class name string, e.g. "LoginRequest">,
    "response_schema_ref": null | <response type class name string, e.g. "Token">,
  }
  ```
  **Note:** the AST extraction path (current production) emits the raw type class name. The runtime-introspection path emitted `#/components/<handler>/request`, but that code path is dead. Verify against the fixture: `endpoint__sample.json` has `request_schema_ref: "LoginRequest"`.
- **structural_hash payload** (sort_keys=True):
  ```
  {
    "method": <METHOD>,
    "path": canonical_path(path),
    "auth": <auth>,
    "request": <request_type_name or None>,    # class name string, NOT json schema dict
    "response": <response_type_name or None>,
  }
  ```
- **`auth` detection** (from handler AST):
  - Scan handler's parameter defaults for `Depends(<symbol>)` calls
  - If `<symbol>` matches case-insensitive `*admin*` → `"admin"`
  - elif `*agent*` → `"agent_token"`
  - elif `*auth*` or `*user*` → `"user"`
  - else → `"none"`
- **source.symbol**: handler function name. **source.line**: handler def line. **source.path**: relative to repo root.
- **depends_on**: from `walk_handler_body` semantics (see § depends_on resolution below)
- **slugify**: `slugify_id_py` → e.g. `DELETE___api_admin_email-templates_0`
- **dossier**: `f"dossiers/endpoints/{slugify_id_py(id)}.md"`
- **extractor**: `"extract_api.py"`
- **warnings**: include `weakly_typed_response` if `response_schema is None and method != "DELETE"`:
  ```
  {"code": "weakly_typed_response",
   "message": "Handler has no declared response_model; structural hash cannot detect response shape changes. See DRIFT.md scenario 3.",
   "where": f"{rel_path}:{handler_line}"}
  ```

### Kind: `model` (python)

- **id**: `f"concorda-api::{rel_path}::{class_name}"` (use canonical repo name from `--repo-key`)
- **title**: class name
- **signature**:
  ```
  {"name": <class>, "kind": "model", "tablename": <__tablename__ string or None>}
  ```
- **structural_hash payload** (sort_keys=True): **identical to signature**
  ```
  {"name": <class>, "kind": "model", "tablename": <string or None>}
  ```
- **source.symbol**: class name. **source.line**: class def line.
- **classification (extract_api.py:543-556)**: a class is a model IFF it inherits from `BaseModel` (by `ast.Name` or `ast.Attribute.attr == "BaseModel"`) OR has a `__tablename__` class-level assignment.
- **Files scanned**: `<repo>/models/**/*.py`, skipping `__init__.py` and `base.py` and `__pycache__`.
- **depends_on**: always `[]` pre-flip. Leave `[]`.
- **slugify**: `slugify_id_py`
- **dossier**: `f"dossiers/models/{slugify_id_py(id)}.md"`
- **extractor**: `"extract_api.py"`

### Kind: `schema` (python)

- **id**: `f"concorda-api::{rel_path}::{class_name}"`
- **title**: class name
- **signature**:
  ```
  {"name": <class>, "kind": "schema", "fields": <sorted list of field name strings>}
  ```
  Fields come from `ast.AnnAssign` statements in the class body whose target is `ast.Name`. The name is `target.id`. Any non-Name target becomes the literal string `"?"`. Then `sorted(...)` the list.
- **structural_hash payload** (sort_keys=True): **identical to signature**
- **Files scanned**: `<repo>/schemas/**/*.py`, skipping `__init__.py` and `__pycache__`.
- **Selection**: every top-level `ast.ClassDef` whose name does NOT start with `_`. (No inheritance check.)
- **depends_on**: `[]`
- **slugify**: `slugify_id_py`
- **dossier**: `f"dossiers/schemas/{slugify_id_py(id)}.md"`
- **extractor**: `"extract_api.py"`

### Kind: `service` (python)

- **id**: `f"concorda-api::{rel_path}::{func_name}"`
- **title**: function name
- **signature**:
  ```
  {"name": <func>, "kind": "service", "args": [arg.arg for arg in node.args.args]}
  ```
  `args` is the ordered list of positional arg names (excluding *args/**kwargs/keyword-only).
- **structural_hash payload** (sort_keys=True): **identical to signature**
- **Files scanned**: `<repo>/services/**/*.py` AND `<repo>/utils/**/*.py`, skipping `__init__.py` and `__pycache__`.
- **Selection**: top-level `ast.FunctionDef` / `ast.AsyncFunctionDef` whose name does NOT start with `_`.
- **depends_on**: `[]`
- **slugify**: `slugify_id_py`
- **dossier**: `f"dossiers/services/{slugify_id_py(id)}.md"`
- **extractor**: `"extract_api.py"`

### Kind: `test` (python — NEW)

There are no pre-flip python tests; `extract_tests.ts` only ran against `concorda-test`. The plan **disables** the `pytest` detector on Concorda's API repo for now (it would add ~500 new test nodes that the dossier system has never seen — that's an additive feature, not a parity goal).

Action: the python `pytest` detector remains in the framework for use by other projects, but Concorda's `[repos.concorda-api]` lists detectors `["fastapi", "sqlalchemy", "pydantic", "service"]` — **no `pytest`**. Document this in the project.toml comment.

### Kind: `component` and `hook` (typescript, extract_web.ts)

Components and hooks share emission logic; only `kind` differs.

- **classify rule** (extract_web.ts:204-208):
  - name matches `/^use[A-Z]/` → `"hook"`
  - elif name matches `/^[A-Z]/` → `"component"`
  - else → `"service"` (covered below)
- **id**: `f"{REPO_NAME}::{rel_path}::{fullName}"` where REPO_NAME is `"concorda-web"`
- **title**: `fullName` (the symbol's identifier; for object-literal methods this is `"ObjectName.methodName"`)
- **signature**: `{"name": fullName, "kind": kind}` ← **insertion order matters** (name first, then kind)
- **structural_hash payload** (insertion order, no sort_keys):
  ```
  {"name": fullName, "kind": kind, "text": symbolNode.getText().slice(0, 1024)}
  ```
  `text` is the **raw source text of the symbol's declaration node** (FunctionDeclaration, VariableStatement, MethodDeclaration, PropertyAssignment, ArrowFunction inside HOC, etc.), sliced to first 1024 chars. The exact `symbolNode` choice per emission pattern is pinned in `buildEmissions` (extract_web.ts:238-318):
  - FunctionDeclaration → that decl
  - VariableStatement with ArrowFunction/FunctionExpression initializer → the VariableDeclaration
  - VariableStatement wrapped in HOC (`forwardRef(...)`, `memo(...)`) → the inner ArrowFunction/FunctionExpression (not the VariableDeclaration)
  - VariableStatement with PropertyAccess initializer (e.g. `const Dialog = DialogPrimitive.Root`) → the VariableDeclaration
  - ObjectLiteral property with ArrowFunction value → the PropertyAssignment
  - ObjectLiteral method → the MethodDeclaration
- **source**: `{repo: "concorda-web", path: rel, symbol: fullName, line: symbolNode.getStartLineNumber()}`
- **slugify**: `slugify_id_ts`
- **dossier**: `f"dossiers/{kind === 'hook' ? 'hooks' : 'components'}/{slugify_id_ts(id)}.md"`
- **extractor**: `"extract_web.ts"`
- **depends_on**: from `attributeEdges` semantics (see § depends_on resolution below)
- **HOC handling** (extract_web.ts:222-235): treat `forwardRef(...)` and `memo(...)` as transparent. Anything else is not an HOC.

### Kind: `service` (typescript, extract_web.ts)

- Same emission logic as component/hook (above) but `kind: "service"` when `classify` returns service (lowerCamelCase top-level name OR object-literal property assigned an arrow function).
- **dossier**: `f"dossiers/services/{slugify_id_ts(id)}.md"`
- **extractor**: `"extract_web.ts"`
- Everything else identical to component/hook.

### Kind: `test` (typescript, extract_tests.ts)

Driver function pattern: `test('description', () => { ... })`, `test.only(...)`, `test.skip(...)`. `test.describe(...)` is SKIPPED (a grouping, not a leaf test).

- **id**: `f"{REPO_NAME}::{rel_path}::test@{line}"` where REPO_NAME is `"concorda-test"` and `line` is the line number of the `test(...)` call
- **title**: the first-arg string literal of the `test(...)` call — the human-readable test description
- **signature**: `{"name": f"test@{line}", "kind": "test"}` (insertion order: name, kind)
- **structural_hash payload** (insertion order):
  ```
  {"name": f"test@{line}", "kind": "test", "text": <symbolNode.getText().slice(0, 1024)>}
  ```
  `symbolNode` is the `CallExpression` node for the `test(...)` call. `text` is its source text sliced to 1024 chars.
- **source**: `{repo: "concorda-test", path: rel, symbol: f"test@{line}", line: line}`
- **slugify**: `slugify_id_ts`
- **dossier**: `f"dossiers/tests/{slugify_id_ts(id)}.md"`
- **extractor**: `"extract_tests.ts"`
- **TEST_VERBS** (allowed `test.*` suffixes from extract_tests.ts): `{"only", "skip", "fixme"}` — verify against the actual file when implementing.

### Kind: `route_call` (typescript outlier)

This kind has its own slim schema (no `feature`, no `external_consumers`, no `tests`, no `dossier`, no `warnings`, 8-char hash). Treat it as an outlier; the canonical layer needs a separate branch.

- **id**: `f"concorda-web::{rel_path}:{line}::response"`  ← single colon between path and line, double colon before "response"
- **title**: `f"fetch {method} {url_pattern}"`
- **kind**: `"route_call"`
- **source**: `{repo: "concorda-web", path: rel_path, line: line}` ← no `symbol` field
- **signature**: `{"method": <METHOD>, "url_pattern": <canonicalized url>}`
- **structural_hash**: `sha256(JSON.stringify(<signature>)).slice(0, 8)` ← **only 8 hex chars**
- **depends_on**: `[]`
- **extractor**: `"generic/typescript/route-calls"` (already pre-flip uses this exact string — it's the only kind whose extractor stamp matches the framework name)
- **No** `feature`, `external_consumers`, `tests`, `dossier`, `warnings` fields.
- **DOES** include `schema_version: 1` (initial inspection missed this — verified against `route_call__sample.json` fixture).

`route_call` is produced by the `route-calls` detector and bypasses most of the common canonicalization. Keep its emission separate.

### depends_on resolution

The taxonomy of `via:` labels and their conditions:

| via | Language | Source | Trigger |
|---|---|---|---|
| `import` | python | walk_handler_body | imported symbol resolves to a non-class, non-WEBSOCKET_SYMBOLS entry in symbol_index |
| `db_query` | python | walk_handler_body | imported symbol resolves to a class in symbol_index (i.e., a SQLAlchemy model) |
| `websocket` | python | walk_handler_body | imported symbol is in `WEBSOCKET_SYMBOLS = {"broadcast_event", "broadcast_to_room", "send_to_user"}` |
| `render` | typescript | attributeEdges (JSX) | `<Foo />` or `<Foo>...</Foo>` where Foo is an imported repo-internal component (PascalCase). Includes `<NS.Member>` |
| `hook_call` | typescript | attributeEdges (call expr) | call to an imported identifier or `imported.method` (excludes HTTP helpers — those go to http_call) |
| `http_call` | typescript | parseHttpCall | `fetchApi(...)`, `fetchApiAuthenticated(...)`, `fetch(...)`, `apiClient.get(...)`, `api.post(...)` etc. with a parseable url |
| `string_url` | typescript | parseHttpCall | same as http_call but the url is a template literal with `${...}` interpolation (fuzzy) |

**Edge shape** (all `via:` labels):
```
{
  "target": <canonical_id of target node>,
  "via": <label>,
  "where": <"<basename>:<line>" — basename only for TS, rel-path for Python>,
  "confidence": "exact" | "fuzzy"
}
```

The python implementation lives in `walk_handler_body` (extract_api.py:734-811). The typescript implementation lives in `attributeEdges` (extract_web.ts:372-448), `parseHttpCall` (extract_web.ts:130-194), `buildImportMap` (extract_web.ts:344-370). Read all three before implementing.

**HTTP helper recognition** (extract_web.ts:68-70):
```
HTTP_HELPERS = {"fetchApi", "fetchApiAuthenticated", "fetch"}
API_CLIENT_OBJECTS = {"apiClient", "api"}
VERB_METHODS = {"get", "post", "put", "delete", "patch"}
```

**Cross-file dedupe**: extract_web.ts dedupes by `${target}|${via}|${where}` (extract_web.ts:450-460). Preserve this.

---

## Project wiring

Concorda's project.toml `[repos.X]` table keys ARE the canonical repo names. The framework's existing `--repo-key` flag carries the canonical name to the extractor. No schema change.

```toml
[project]
primary_repo = "concorda-api"

[repos.concorda-api]
path = "~/concorda-api"
extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
detectors = ["fastapi", "sqlalchemy", "pydantic", "service"]   # NOT pytest — see Kind: test (python)
files_arg = "--only"

[repos.concorda-web]
path = "~/concorda-web"
extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]
detectors = ["react", "route-calls", "service"]               # NOT vitest

[repos.concorda-test]
path = "~/concorda-test"
extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]
detectors = ["vitest"]                                         # ONLY vitest for this repo
```

Note: TOML allows dashes in bare keys.

---

## File Structure

**New files (framework):**
- `depgraph/extractors/generic/python/canonical.py` — id helpers, slugify_id_py, structural_hash, depends_on resolver, per-kind signature + hash payload builders
- `depgraph/extractors/generic/typescript/canonical.ts` — TS port: slugify_id_ts, sha, per-kind builders
- `depgraph/tests/extractors/fixtures/pre_flip_nodes/` — committed sample of real pre-flip Concorda nodes (one per kind) for regression
- `depgraph/tests/extractors/test_pre_flip_parity.py` — the gate test
- `depgraph/tests/extractors/test_python_canonical.py` — unit tests for helpers
- `depgraph/tests/extractors/test_typescript_canonical.ts` — same for TS

**Modified files (framework):**
- `depgraph/extractors/generic/python/extract.py` — canonicalize pass
- `depgraph/extractors/generic/python/detectors/*.py` — each detector emits the metadata the canonical layer needs (see contracts above)
- `depgraph/extractors/generic/typescript/extract.ts` — canonicalize pass; depends_on attribution
- `depgraph/extractors/generic/typescript/detectors/*.ts` — same
- `scripts/concorda_parity.py` — shape diff + hash regression integration
- `scripts/concorda_parity_project.toml` — rename keys to canonical names

**Data-repo changes (Concorda, last task):**
- `~/concorda-knowledge-graph/depgraph/project.toml` — flip
- Delete bespoke `extract_*.{py,ts}` and `ingest_route_calls.py`

---

## Task 1: Capture pre-flip fixture + write the gate test

**Files:**
- Create: `depgraph/tests/extractors/fixtures/pre_flip_nodes/<kind>__sample.json` × 8 (one per kind)
- Create: `depgraph/tests/extractors/test_pre_flip_parity.py`

This is the *gate* — the test fails today (no framework canonical output) and stays failing until Tasks 2-9 land. Every subsequent task is judged against this test.

- [ ] **Step 1: Copy fixtures**

```bash
mkdir -p ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes
cd ~/concorda-knowledge-graph/depgraph/nodes
# Endpoint with a body for richer test:
cp endpoints/POST___api_auth_login.json \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/endpoint__sample.json
# (Or pick any other endpoint. Endpoint with body exercises request_schema_ref.)
cp models/concorda-api__models_account_setup_token.py__AccountSetupToken.json \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/model__sample.json
cp schemas/concorda-api__schemas_approval.py__ApprovalRequestCreate.json \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/schema__sample.json
cp services/concorda-api__services_approval_notifications.py__send_approval_notification.json \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/service_py__sample.json
cp components/concorda_web__src_app_code_of_conduct_page_tsx__CodeOfConductPage.json \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/component__sample.json
cp "hooks/concorda_web__src_components_dashboard_profile_completion_tsx__useProfileCompletion.json" \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/hook__sample.json
# Pick any test node:
cp "tests/$(ls ~/concorda-knowledge-graph/depgraph/nodes/tests/ | head -1)" \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/test__sample.json
# Pick any route_call:
cp "route_calls/$(ls ~/concorda-knowledge-graph/depgraph/nodes/route_calls/ | head -1)" \
   ~/tools/knowledge-graph/depgraph/tests/extractors/fixtures/pre_flip_nodes/route_call__sample.json
```

Inspect each fixture by hand to confirm: each has the fields documented in § Canonical Node Contracts for its kind. If a sample is missing fields, pick a different one.

- [ ] **Step 2: Write the regression test**

Create `depgraph/tests/extractors/test_pre_flip_parity.py`:

```python
"""Gate test: framework canonical output must match committed pre-flip
samples byte-for-byte on id, structural_hash, signature, dossier path,
and source block.

Each sample fixture is a real pre-flip Concorda node. The test runs the
framework extractor against the corresponding upstream source file in
~/concorda-{api,web,test}/, extracts the matching canonical node, and
asserts equality on the load-bearing fields.

depends_on is checked separately (compared as sets, since order is
non-deterministic) — see test_pre_flip_depends_on.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pre_flip_nodes"
KG_ROOT = Path(__file__).resolve().parents[3]


def _run_extractor(repo_key: str, repo_path: Path, detectors: list[str],
                   data_dir: Path, only: Path | None = None) -> None:
    lang_dir = {
        "concorda-api": "python",
        "concorda-web": "typescript",
        "concorda-test": "typescript",
    }[repo_key]
    if lang_dir == "python":
        cmd = [
            sys.executable, "-m", "extractors.generic.python.extract",
            "--repo-key", repo_key, "--repo-path", str(repo_path),
            "--data-dir", str(data_dir),
            "--detectors", ",".join(detectors),
        ]
    else:
        cmd = [
            "npx", "tsx",
            str(KG_ROOT / "depgraph" / "extractors" / "generic" / "typescript" / "extract.ts"),
            "--repo-key", repo_key, "--repo-path", str(repo_path),
            "--data-dir", str(data_dir),
            "--detectors", ",".join(detectors),
        ]
    if only:
        cmd += ["--only", str(only)]
    subprocess.run(cmd, check=True, cwd=KG_ROOT / "depgraph")


def _load_node(data_dir: Path, kind_dir: str, slug: str) -> dict:
    return json.loads((data_dir / "nodes" / kind_dir / f"{slug}.json").read_text())


@pytest.fixture(scope="module")
def regen_concorda(tmp_path_factory):
    """Regen with framework extractors into a scratch dir, once per module."""
    out = tmp_path_factory.mktemp("scratch") / "depgraph"
    out.mkdir(parents=True)
    _run_extractor("concorda-api", Path.home() / "concorda-api",
                   ["fastapi", "sqlalchemy", "pydantic", "service"], out)
    _run_extractor("concorda-web", Path.home() / "concorda-web",
                   ["react", "route-calls", "service"], out)
    _run_extractor("concorda-test", Path.home() / "concorda-test",
                   ["vitest"], out)
    return out


def _assert_equivalent(expected: dict, actual: dict, exclude=("depends_on",)) -> None:
    """Compare two nodes for byte-level equality on load-bearing fields."""
    for field in ("schema_version", "id", "kind", "title", "feature",
                  "source", "signature", "structural_hash",
                  "dossier", "extractor"):
        if field in exclude:
            continue
        if field not in expected:
            continue  # outlier kinds (route_call) lack some fields
        assert actual.get(field) == expected[field], (
            f"field {field!r} mismatch:\n"
            f"  expected: {expected.get(field)!r}\n"
            f"  actual:   {actual.get(field)!r}"
        )


# One test per kind — easier to triage individual failures.

def test_endpoint_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "endpoint__sample.json").read_text())
    # The slug is derivable from id via slugify_id_py
    from extractors.generic.python.canonical import slugify_id_py
    slug = slugify_id_py(expected["id"])
    actual = _load_node(regen_concorda, "endpoints", slug)
    _assert_equivalent(expected, actual)


def test_model_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "model__sample.json").read_text())
    from extractors.generic.python.canonical import slugify_id_py
    actual = _load_node(regen_concorda, "models", slugify_id_py(expected["id"]))
    _assert_equivalent(expected, actual)


def test_schema_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "schema__sample.json").read_text())
    from extractors.generic.python.canonical import slugify_id_py
    actual = _load_node(regen_concorda, "schemas", slugify_id_py(expected["id"]))
    _assert_equivalent(expected, actual)


def test_service_py_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "service_py__sample.json").read_text())
    from extractors.generic.python.canonical import slugify_id_py
    actual = _load_node(regen_concorda, "services", slugify_id_py(expected["id"]))
    _assert_equivalent(expected, actual)


def test_component_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "component__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "components", slugify_id_ts(expected["id"]))
    _assert_equivalent(expected, actual)


def test_hook_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "hook__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "hooks", slugify_id_ts(expected["id"]))
    _assert_equivalent(expected, actual)


def test_test_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "test__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "tests", slugify_id_ts(expected["id"]))
    _assert_equivalent(expected, actual)


def test_route_call_byte_equivalent(regen_concorda):
    expected = json.loads((FIXTURE_DIR / "route_call__sample.json").read_text())
    from extractors.generic.typescript.canonical import slugify_id_ts
    actual = _load_node(regen_concorda, "route_calls", slugify_id_ts(expected["id"]))
    # route_call lacks several fields — exclude them
    _assert_equivalent(expected, actual)


def test_depends_on_taxonomy(regen_concorda):
    """depends_on entries can be reordered; compare as sets of tuples."""
    for kind_file in ("endpoint__sample.json", "component__sample.json",
                      "hook__sample.json"):
        expected = json.loads((FIXTURE_DIR / kind_file).read_text())
        if not expected.get("depends_on"):
            continue
        kind_dir = {"endpoint": "endpoints", "component": "components",
                    "hook": "hooks"}[expected["kind"]]
        from extractors.generic.python.canonical import slugify_id_py
        from extractors.generic.typescript.canonical import slugify_id_ts
        slug = slugify_id_py(expected["id"]) if expected["kind"] == "endpoint" \
            else slugify_id_ts(expected["id"])
        actual = _load_node(regen_concorda, kind_dir, slug)
        expected_set = {(e["target"], e["via"]) for e in expected["depends_on"]}
        actual_set = {(e["target"], e["via"]) for e in actual.get("depends_on", [])}
        # Every pre-flip edge must be reproduced. Extra edges allowed
        # (architecture may detect more in future), but never fewer.
        missing = expected_set - actual_set
        assert not missing, (
            f"{kind_file}: missing depends_on edges: {missing}"
        )
```

- [ ] **Step 3: Run, confirm it fails**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_pre_flip_parity.py -v 2>&1 | tail -30
```

Expected: every test FAIL with `ModuleNotFoundError: extractors.generic.python.canonical` (no canonical module yet). This is the baseline — the test exists, it fails, subsequent tasks make it pass.

- [ ] **Step 4: Commit**

```bash
cd ~/tools/knowledge-graph && git add depgraph/tests/extractors/fixtures/ depgraph/tests/extractors/test_pre_flip_parity.py
git commit -m "tests: pre-flip parity fixtures + gate (currently red)"
```

---

## Task 2: Python canonical helpers (slugify, hash, id formatters)

**Files:**
- Create: `depgraph/extractors/generic/python/canonical.py`
- Test: `depgraph/tests/extractors/test_python_canonical.py`

Implement helpers strictly per § Canonical Node Contracts. Each helper has unit tests that pin specific input/output pairs from real pre-flip data.

- [ ] **Step 1: Write failing tests**

Create `depgraph/tests/extractors/test_python_canonical.py`:

```python
from extractors.generic.python.canonical import (
    slugify_id_py, structural_hash, canonical_path,
    canonical_id_for_endpoint, canonical_id_for_repo_symbol,
)


def test_slugify_id_py_matches_pre_flip():
    # From real pre-flip: endpoint dossier filename
    assert slugify_id_py("DELETE::/api/admin/email-templates/{0}") \
        == "DELETE___api_admin_email-templates_0"
    # Service dossier filename
    assert slugify_id_py("concorda-api::services/approvals.py::cast_vote") \
        == "concorda-api__services_approvals.py__cast_vote"


def test_structural_hash_endpoint_reproduces_pre_flip():
    # From DELETE /api/admin/email-templates/{template_id}
    payload = {
        "method": "DELETE",
        "path": "/api/admin/email-templates/{0}",
        "auth": "none",
        "request": None,
        "response": None,
    }
    assert structural_hash(payload) == \
        "dc232955b0ec6500ba3c7be14af012393377816b145ae350757ef09d79523a6a"


def test_structural_hash_model_reproduces_pre_flip():
    payload = {"name": "AccountSetupToken", "kind": "model",
               "tablename": "account_setup_tokens"}
    assert structural_hash(payload) == \
        "ffb3adef2bc6a3423c51e35cfa069d3fec41f5614e3bb0e798031d31d175235a"


def test_structural_hash_schema_reproduces_pre_flip():
    payload = {"name": "ApprovalRequestCreate", "kind": "schema",
               "fields": ["request_type", "subject_uuid", "target_state"]}
    assert structural_hash(payload) == \
        "3e9823a12a6c2272bbec9c9f6e020ab9d66ea3a9f2287a0ba2d057583f728593"


def test_canonical_path():
    assert canonical_path("/users/{id}") == "/users/{0}"
    assert canonical_path("/users/{user_id}/posts/{post_id}") \
        == "/users/{0}/posts/{1}"
    assert canonical_path("/health") == "/health"


def test_canonical_id_for_endpoint():
    assert canonical_id_for_endpoint("DELETE", "/api/admin/email-templates/{template_id}") \
        == "DELETE::/api/admin/email-templates/{0}"


def test_canonical_id_for_repo_symbol():
    assert canonical_id_for_repo_symbol("concorda-api", "models/user.py", "User") \
        == "concorda-api::models/user.py::User"
```

- [ ] **Step 2: Run, verify fail**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_python_canonical.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

Create `depgraph/extractors/generic/python/canonical.py`:

```python
"""Pure helpers for converting AST primitives into canonical depgraph nodes.

Pinned to pre-flip extract_api.py output byte-for-byte. See plan doc:
docs/superpowers/plans/2026-05-15-framework-canonicalization.md.
"""
from __future__ import annotations

import hashlib
import json
import re


def slugify_id_py(node_id: str) -> str:
    """Python-extractor slugify (extract_api.py:446-453)."""
    return (
        node_id.replace("::", "__")
        .replace("/", "_")
        .replace("{", "")
        .replace("}", "")
        .strip("_")
    )


def structural_hash(payload: dict) -> str:
    """extract_api.py:499-501 — sha256 of sort_keys JSON with default=str."""
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def canonical_path(path: str) -> str:
    """extract_api.py:425-443 — named params -> positional placeholders."""
    out, depth, idx = [], 0, 0
    for ch in path:
        if ch == "{":
            depth = 1; out.append("{"); continue
        if ch == "}" and depth:
            depth = 0; out.append(f"{idx}}}"); idx += 1; continue
        if depth:
            continue
        out.append(ch)
    return "".join(out)


def canonical_id_for_endpoint(method: str, path: str) -> str:
    return f"{method.upper()}::{canonical_path(path)}"


def canonical_id_for_repo_symbol(repo_key: str, rel_path: str, symbol: str) -> str:
    return f"{repo_key}::{rel_path}::{symbol}"
```

- [ ] **Step 4: Run, verify pass**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_python_canonical.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/canonical.py depgraph/tests/extractors/test_python_canonical.py
git commit -m "extractors/python: canonical helpers (slugify, hash, id formatters)"
```

---

## Task 3: Python depends_on resolver

**Files:**
- Modify: `depgraph/extractors/generic/python/canonical.py`
- Test: extend `test_python_canonical.py`

Reproduce the `walk_handler_body` taxonomy: `import` / `db_query` / `websocket`.

- [ ] **Step 1: Write failing tests**

Append to `test_python_canonical.py`:

```python
from extractors.generic.python.canonical import (
    build_symbol_index, resolve_endpoint_depends_on,
)


def test_build_symbol_index_classifies_classes_vs_functions():
    primitives = [
        {"id": "concorda-api:models/user.py:User", "kind": "class",
         "name": "User", "file": "models/user.py", "parent_id": None,
         "line": 5},
        {"id": "concorda-api:services/email.py:send_email", "kind": "function",
         "name": "send_email", "file": "services/email.py",
         "parent_id": None, "line": 10},
    ]
    idx = build_symbol_index(primitives, repo_key="concorda-api")
    assert idx["User"] == {"file": "models/user.py", "kind": "class", "line": 5}
    assert idx["send_email"] == {"file": "services/email.py",
                                  "kind": "function", "line": 10}


def test_resolve_endpoint_depends_on_db_query_label():
    primitives = [
        {"id": "concorda-api:models/user.py:User", "kind": "class",
         "name": "User", "file": "models/user.py", "parent_id": None,
         "line": 5},
        {"id": "concorda-api:routers/users.py:<module>", "kind": "module",
         "file": "routers/users.py", "name": "<module>", "parent_id": None},
        {"id": "concorda-api:routers/users.py:<module>#import:models.user.User",
         "kind": "import_edge",
         "from_id": "concorda-api:routers/users.py:<module>",
         "target": "models.user.User", "line": 1},
        {"id": "concorda-api:routers/users.py:get_user", "kind": "function",
         "name": "get_user", "file": "routers/users.py",
         "parent_id": None, "line": 10},
        {"id": "concorda-api:routers/users.py:get_user#call:User:11",
         "kind": "call_edge",
         "from_id": "concorda-api:routers/users.py:get_user",
         "target": "User", "line": 11},
    ]
    sym_idx = build_symbol_index(primitives, repo_key="concorda-api")
    edges = resolve_endpoint_depends_on(
        host_id="concorda-api:routers/users.py:get_user",
        host_file="routers/users.py",
        primitives=primitives, symbol_index=sym_idx,
        repo_key="concorda-api",
    )
    assert edges == [{
        "target": "concorda-api::models/user.py::User",
        "via": "db_query",
        "where": "routers/users.py:11",
        "confidence": "exact",
    }]


def test_resolve_endpoint_depends_on_websocket_label():
    primitives = [
        {"id": "concorda-api:utils/broadcast.py:broadcast_event",
         "kind": "function", "name": "broadcast_event",
         "file": "utils/broadcast.py", "parent_id": None, "line": 5},
        {"id": "concorda-api:routers/x.py:<module>", "kind": "module",
         "file": "routers/x.py", "name": "<module>", "parent_id": None},
        {"id": "concorda-api:routers/x.py:<module>#import:utils.broadcast.broadcast_event",
         "kind": "import_edge",
         "from_id": "concorda-api:routers/x.py:<module>",
         "target": "utils.broadcast.broadcast_event", "line": 1},
        {"id": "concorda-api:routers/x.py:handler", "kind": "function",
         "name": "handler", "file": "routers/x.py", "parent_id": None,
         "line": 10},
        {"id": "concorda-api:routers/x.py:handler#call:broadcast_event:11",
         "kind": "call_edge",
         "from_id": "concorda-api:routers/x.py:handler",
         "target": "broadcast_event", "line": 11},
    ]
    sym_idx = build_symbol_index(primitives, repo_key="concorda-api")
    edges = resolve_endpoint_depends_on(
        host_id="concorda-api:routers/x.py:handler",
        host_file="routers/x.py",
        primitives=primitives, symbol_index=sym_idx,
        repo_key="concorda-api",
    )
    assert edges == [{
        "target": "concorda-api::utils/broadcast.py::broadcast_event",
        "via": "websocket",
        "where": "routers/x.py:11",
        "confidence": "exact",
    }]
```

- [ ] **Step 2: Run, verify fail**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_python_canonical.py -v
```

Expected: ImportError on `build_symbol_index` / `resolve_endpoint_depends_on`.

- [ ] **Step 3: Implement**

Append to `canonical.py`:

```python
WEBSOCKET_SYMBOLS = frozenset({
    "broadcast_event", "broadcast_to_room", "send_to_user",
})


def build_symbol_index(primitives: list[dict], *, repo_key: str) -> dict[str, dict]:
    """Top-level symbol short-name -> {file, kind, line}.

    extract_api.py:511-533. Used by walk_handler_body to resolve imported
    names to canonical targets. Last definition wins on collision.
    """
    out: dict[str, dict] = {}
    for n in primitives:
        if n["kind"] not in ("class", "function"):
            continue
        # Top-level: parent is the module
        if n.get("parent_id") and not n["parent_id"].endswith(":<module>"):
            continue
        out[n["name"]] = {
            "file": n["file"], "kind": n["kind"],
            "line": n.get("line"),
        }
    return out


def resolve_endpoint_depends_on(
    *, host_id: str, host_file: str,
    primitives: list[dict], symbol_index: dict[str, dict],
    repo_key: str,
) -> list[dict]:
    """Reproduce walk_handler_body (extract_api.py:734-811).

    For each call_edge from host_id, look up the call target in the host
    module's import aliases, then in symbol_index. Emit edge with via:
      class -> db_query
      WEBSOCKET_SYMBOLS -> websocket
      otherwise -> import
    """
    module_id = f"{repo_key}:{host_file}:<module>"
    aliases: dict[str, str] = {}
    for n in primitives:
        if n["kind"] != "import_edge" or n["from_id"] != module_id:
            continue
        target = n["target"]
        local = target.rsplit(".", 1)[-1]
        aliases[local] = local  # local name maps to imported short name

    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for n in primitives:
        if n["kind"] != "call_edge" or n["from_id"] != host_id:
            continue
        callee = n["target"].split(".", 1)[0]
        if callee not in aliases:
            continue
        imported_name = aliases[callee]
        sym = symbol_index.get(imported_name)
        if not sym:
            continue
        target_id = (
            f"{repo_key}::{sym['file']}::{imported_name}"
        )
        if sym["kind"] == "class":
            via = "db_query"
        elif imported_name in WEBSOCKET_SYMBOLS:
            via = "websocket"
        else:
            via = "import"
        key = (target_id, via)
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "target": target_id, "via": via,
            "where": f"{host_file}:{n['line']}",
            "confidence": "exact",
        })
    return edges
```

**Note:** This simplified resolver assumes `call_edge.target` matches the locally-imported name. The real walk_handler_body in extract_api.py also looks at `ast.Name` references inside the handler body that aren't necessarily call sites. If the regression test (Task 9) shows missing edges, extend the resolver to scan `ast.Name` references (not just `ast.Call`). For now: ship simpler, verify against fixtures, iterate.

- [ ] **Step 4: Run, verify pass**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_python_canonical.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/canonical.py depgraph/tests/extractors/test_python_canonical.py
git commit -m "extractors/python: depends_on resolver with full via taxonomy"
```

---

## Task 4: Python detector metadata + canonicalize stage

**Files:**
- Modify: `depgraph/extractors/generic/python/detectors/{fastapi,sqlalchemy,pydantic,service}.py`
- Modify: `depgraph/extractors/generic/python/extract.py`
- Test: gate test starts to pass for python kinds

Each detector grows the metadata its RelabelNode emits, then a `canonicalize(primitives, *, repo_key)` stage converts them into pre-flip-shape nodes.

- [ ] **Step 1: Read each pre-flip extractor for the metadata it captures**

For each kind, identify what `extract_api.py` extracts beyond AST primitives:
- `endpoint`: method, raw path, auth (from `Depends(...)` detection), request_type_name, response_type_name. See extract_api.py:283-365.
- `model`: class name, line, tablename (from `__tablename__` assignment). See extract_api.py:559-602.
- `schema`: class name, line, sorted field names from `AnnAssign`. See extract_api.py:631-680.
- `service`: function name, line, arg names. See extract_api.py:685-728.

The framework's current detectors call `RelabelNode(node_id, new_kind, metadata={})`. Each must populate `metadata` with the structural fields the canonicalize stage needs.

- [ ] **Step 2: Modify each detector**

For `fastapi.py`: metadata = `{"method": ..., "path": <un-canonical>, "auth": <from handler params>, "request_schema_ref": ..., "response_schema_ref": ..., "request_type_name": ..., "response_type_name": ...}`. Read the handler's AST to compute auth; reproduce extract_api.py:228-280 (already AST-only in pre-flip).

For `sqlalchemy.py`: metadata = `{"tablename": <__tablename__ value or None>}`.

For `pydantic.py`: metadata = `{"fields": <sorted list of AnnAssign target names>}`.

For `service.py`: metadata = `{"args": [arg.arg for arg in node.args.args]}`.

- [ ] **Step 3: Add canonicalize stage to extract.py**

After detectors run, before `write_nodes`, transform primitives into canonical nodes per § Canonical Node Contracts. Skeleton:

```python
from extractors.generic.python.canonical import (
    slugify_id_py, structural_hash, canonical_path,
    canonical_id_for_endpoint, canonical_id_for_repo_symbol,
    build_symbol_index, resolve_endpoint_depends_on,
)

CANONICAL_KINDS = {"endpoint", "model", "schema", "service"}
PRIMITIVE_KINDS_TO_DROP = {"module", "class", "function", "import_edge", "call_edge"}


def _canonicalize_endpoint(n, *, primitives, sym_idx, repo_key):
    meta = n
    method = meta["method"]
    path = meta["path"]
    auth = meta.get("auth", "none")
    request_type_name = meta.get("request_type_name")
    response_type_name = meta.get("response_type_name")
    cid = canonical_id_for_endpoint(method, path)
    sig = {
        "method": method, "path": path, "auth": auth,
        "request_schema_ref": meta.get("request_schema_ref"),
        "response_schema_ref": meta.get("response_schema_ref"),
    }
    hpayload = {
        "method": method, "path": canonical_path(path), "auth": auth,
        "request": request_type_name, "response": response_type_name,
    }
    out = {
        "schema_version": 1, "id": cid, "kind": "endpoint",
        "title": f"{method} {path}", "feature": None,
        "source": {"repo": repo_key, "path": meta["file"],
                   "symbol": meta["name"], "line": meta["line"]},
        "signature": sig,
        "structural_hash": structural_hash(hpayload),
        "depends_on": resolve_endpoint_depends_on(
            host_id=n["id"], host_file=meta["file"],
            primitives=primitives, symbol_index=sym_idx,
            repo_key=repo_key),
        "external_consumers": [], "tests": [],
        "dossier": f"dossiers/endpoints/{slugify_id_py(cid)}.md",
        "extractor": "extract_api.py", "warnings": [],
    }
    if response_type_name is None and method != "DELETE":
        out["warnings"].append({
            "code": "weakly_typed_response",
            "message": "Handler has no declared response_model; structural hash cannot detect response shape changes. See DRIFT.md scenario 3.",
            "where": f"{meta['file']}:{meta['line']}",
        })
    return out


def _canonicalize_model(n, *, repo_key):
    meta = n
    cid = canonical_id_for_repo_symbol(repo_key, meta["file"], meta["name"])
    payload = {"name": meta["name"], "kind": "model",
               "tablename": meta.get("tablename")}
    return {
        "schema_version": 1, "id": cid, "kind": "model",
        "title": meta["name"], "feature": None,
        "source": {"repo": repo_key, "path": meta["file"],
                   "symbol": meta["name"], "line": meta["line"]},
        "signature": payload,
        "structural_hash": structural_hash(payload),
        "depends_on": [], "external_consumers": [], "tests": [],
        "dossier": f"dossiers/models/{slugify_id_py(cid)}.md",
        "extractor": "extract_api.py", "warnings": [],
    }


def _canonicalize_schema(n, *, repo_key):
    meta = n
    cid = canonical_id_for_repo_symbol(repo_key, meta["file"], meta["name"])
    payload = {"name": meta["name"], "kind": "schema",
               "fields": meta.get("fields", [])}
    return {
        "schema_version": 1, "id": cid, "kind": "schema",
        "title": meta["name"], "feature": None,
        "source": {"repo": repo_key, "path": meta["file"],
                   "symbol": meta["name"], "line": meta["line"]},
        "signature": payload,
        "structural_hash": structural_hash(payload),
        "depends_on": [], "external_consumers": [], "tests": [],
        "dossier": f"dossiers/schemas/{slugify_id_py(cid)}.md",
        "extractor": "extract_api.py", "warnings": [],
    }


def _canonicalize_service(n, *, repo_key):
    meta = n
    cid = canonical_id_for_repo_symbol(repo_key, meta["file"], meta["name"])
    payload = {"name": meta["name"], "kind": "service",
               "args": meta.get("args", [])}
    return {
        "schema_version": 1, "id": cid, "kind": "service",
        "title": meta["name"], "feature": None,
        "source": {"repo": repo_key, "path": meta["file"],
                   "symbol": meta["name"], "line": meta["line"]},
        "signature": payload,
        "structural_hash": structural_hash(payload),
        "depends_on": [], "external_consumers": [], "tests": [],
        "dossier": f"dossiers/services/{slugify_id_py(cid)}.md",
        "extractor": "extract_api.py", "warnings": [],
    }


def canonicalize(primitives, *, repo_key):
    sym_idx = build_symbol_index(primitives, repo_key=repo_key)
    out = []
    for n in primitives:
        k = n["kind"]
        if k in PRIMITIVE_KINDS_TO_DROP or k not in CANONICAL_KINDS:
            continue
        if k == "endpoint":
            out.append(_canonicalize_endpoint(n, primitives=primitives,
                                              sym_idx=sym_idx, repo_key=repo_key))
        elif k == "model":
            out.append(_canonicalize_model(n, repo_key=repo_key))
        elif k == "schema":
            out.append(_canonicalize_schema(n, repo_key=repo_key))
        elif k == "service":
            out.append(_canonicalize_service(n, repo_key=repo_key))
    return out
```

Wire into `main()`: after `all_nodes` accumulates and before `write_nodes`, call `canonical = canonicalize(all_nodes, repo_key=args.repo_key)` and write `canonical`. Update `_KIND_DIR` and `_safe_filename` to use `slugify_id_py` for canonical IDs.

- [ ] **Step 4: Run python parity tests**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_pre_flip_parity.py::test_endpoint_byte_equivalent depgraph/tests/extractors/test_pre_flip_parity.py::test_model_byte_equivalent depgraph/tests/extractors/test_pre_flip_parity.py::test_schema_byte_equivalent depgraph/tests/extractors/test_pre_flip_parity.py::test_service_py_byte_equivalent -v
```

Expected: all 4 PASS. **If any fail, fix per the field-level mismatch report before moving on.** Do not proceed to Task 5.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/python/
git commit -m "extractors/python: canonicalize stage reproduces pre-flip byte-equivalent"
```

---

## Task 5: TypeScript canonical helpers

**Files:**
- Create: `depgraph/extractors/generic/typescript/canonical.ts`
- Test: `depgraph/tests/extractors/test_typescript_canonical.ts`

Mirror Task 2 in TS, plus the TS-specific `slugify_id_ts` (different from python — see § Slugify variants).

- [ ] **Step 1: Write failing tests** pinning the slugify_id_ts behavior against real pre-flip filenames:

```typescript
import { describe, it, expect } from "vitest";
import { slugifyIdTs, sha, canonicalIdForRepoSymbol, canonicalIdForRouteCall } from "../../extractors/generic/typescript/canonical";

describe("typescript canonical helpers", () => {
  it("slugifyIdTs matches pre-flip component filename", () => {
    expect(slugifyIdTs("concorda-web::src/app/code-of-conduct/page.tsx::CodeOfConductPage"))
      .toBe("concorda_web__src_app_code_of_conduct_page_tsx__CodeOfConductPage");
  });

  it("slugifyIdTs matches pre-flip test filename", () => {
    expect(slugifyIdTs("concorda-test::tests/admin/club-management.spec.ts::test@12"))
      .toBe("concorda_test__tests_admin_club_management_spec_ts__test_12");
  });

  it("sha reproduces pre-flip component hash", () => {
    // From CodeOfConductPage — text is exactly the first 1024 chars of the
    // FunctionDeclaration node text in src/app/code-of-conduct/page.tsx.
    // The text fixture lives in pre_flip_nodes/component__sample_text.txt
    // (committed alongside this test).
    const fs = require("fs");
    const path = require("path");
    const text = fs.readFileSync(
      path.join(__dirname, "fixtures/pre_flip_nodes/component__sample_text.txt"),
      "utf8"
    );
    const payload = { name: "CodeOfConductPage", kind: "component", text };
    expect(sha(payload)).toBe(
      "90b1d7839d61794ad7897fee587ebdbee97a4cb43885ce94d9f325c53c3255c1"
    );
  });

  it("canonicalIdForRepoSymbol", () => {
    expect(canonicalIdForRepoSymbol("concorda-web", "src/x.tsx", "Foo"))
      .toBe("concorda-web::src/x.tsx::Foo");
  });

  it("canonicalIdForRouteCall", () => {
    expect(canonicalIdForRouteCall("concorda-web", "src/lib/api.ts", 10))
      .toBe("concorda-web::src/lib/api.ts:10::response");
  });
});
```

You must also extract the `component__sample_text.txt` fixture — the first 1024 chars of `CodeOfConductPage`'s FunctionDeclaration node text. Do this with a one-shot script using ts-morph in the depgraph/ dir of concorda-knowledge-graph (where ts-morph is installed).

- [ ] **Step 2: Run, verify fail**

```bash
cd ~/tools/knowledge-graph/depgraph && npx vitest run tests/extractors/test_typescript_canonical.ts
```

Expected: module not found.

- [ ] **Step 3: Implement**

Create `depgraph/extractors/generic/typescript/canonical.ts`:

```typescript
import { createHash } from "node:crypto";

export function slugifyIdTs(nodeId: string): string {
  let s = nodeId.replace(/::/g, "__");
  s = s.replace(/[^a-zA-Z0-9_]/g, "_");
  s = s.replace(/^_+|_+$/g, "");
  return s;
}

export function sha(payload: unknown): string {
  // extract_web.ts:76-78 — no sort, insertion-order JSON.
  return createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}

export function canonicalIdForRepoSymbol(
  repoKey: string, relPath: string, symbol: string,
): string {
  return `${repoKey}::${relPath}::${symbol}`;
}

export function canonicalIdForRouteCall(
  repoKey: string, relPath: string, line: number,
): string {
  return `${repoKey}::${relPath}:${line}::response`;
}
```

- [ ] **Step 4: Run, verify pass**

```bash
cd ~/tools/knowledge-graph/depgraph && npx vitest run tests/extractors/test_typescript_canonical.ts
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add depgraph/extractors/generic/typescript/canonical.ts depgraph/tests/extractors/test_typescript_canonical.ts depgraph/tests/extractors/fixtures/pre_flip_nodes/component__sample_text.txt
git commit -m "extractors/typescript: canonical helpers (slugify, sha, id formatters)"
```

---

## Task 6: TypeScript detector metadata + canonicalize stage

**Files:**
- Modify: `depgraph/extractors/generic/typescript/detectors/{react,vitest,service,route-calls}.ts`
- Modify: `depgraph/extractors/generic/typescript/extract.ts`

Each detector exposes the symbolNode text slice and any other metadata canonical needs. The `attributeEdges` logic (depends_on resolution: render, hook_call, http_call, string_url) gets ported into the framework — read `extract_web.ts` end-to-end first.

This is the heaviest task in the plan. **Sub-steps:**

- [ ] **Step 1: Port `parseHttpCall` + `canonicalizeUrl` + HTTP_HELPERS/API_CLIENT_OBJECTS constants** to the framework — these are detector-level concerns. Put them in `depgraph/extractors/generic/typescript/detectors/route-calls.ts` so they're reusable.

- [ ] **Step 2: Port `buildImportMap`** to a shared location — both `react` and `vitest` detectors need it for hook_call edge resolution.

- [ ] **Step 3: Port `attributeEdges`** — JSX render + hook_call + http_call/string_url attribution. Each detector calls into this with its own emissions and gets the per-emission depends_on populated.

- [ ] **Step 4: Port `unwrapHocCall` + `buildEmissions`** — these determine which `symbolNode` text gets sliced for the hash payload. Critical.

- [ ] **Step 5: Run gate tests for TS kinds:**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_pre_flip_parity.py::test_component_byte_equivalent depgraph/tests/extractors/test_pre_flip_parity.py::test_hook_byte_equivalent depgraph/tests/extractors/test_pre_flip_parity.py::test_test_byte_equivalent depgraph/tests/extractors/test_pre_flip_parity.py::test_route_call_byte_equivalent -v
```

Expected: all 4 PASS. If any fail, fix per mismatch report. Do not proceed.

- [ ] **Step 6: Commit**

```bash
git add depgraph/extractors/generic/typescript/
git commit -m "extractors/typescript: canonicalize stage reproduces pre-flip byte-equivalent"
```

---

## Task 7: Run gate end-to-end

- [ ] **Step 1: Run the full regression test**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/test_pre_flip_parity.py -v
```

Expected: 9 PASS (8 byte-equivalent + depends_on taxonomy). **If anything fails, do not proceed.** The plan exists specifically to make this test green before any flip.

- [ ] **Step 2: Run all extractor tests**

```bash
cd ~/tools/knowledge-graph && pytest depgraph/tests/extractors/ -v
cd ~/tools/knowledge-graph/depgraph && npx vitest run
```

Expected: all green.

---

## Task 8: Parity script shape-diff + hash regression

**Files:**
- Modify: `scripts/concorda_parity.py`
- Modify: `scripts/concorda_parity_project.toml`

The parity script's count diff was insufficient (count-equivalent doesn't mean shape-equivalent — see audit). Add:
- `shape_check(scratch)`: per kind, sample N files, assert required fields present and well-formed
- `hash_regression(scratch, current)`: for every node in `current/`, look up the same id in `scratch/`; assert structural_hash matches; report ANY mismatch

- [ ] **Step 1: Update parity project.toml** to canonical repo keys (no `pytest` for api repo per Canonical Node Contracts § Kind: test):

```toml
[project]
primary_repo = "concorda-api"

[repos.concorda-api]
path = "~/concorda-api"
extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
detectors = ["fastapi", "sqlalchemy", "pydantic", "service"]
files_arg = "--only"

[repos.concorda-web]
path = "~/concorda-web"
extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]
detectors = ["react", "route-calls", "service"]

[repos.concorda-test]
path = "~/concorda-test"
extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]
detectors = ["vitest"]
```

- [ ] **Step 2: Add shape_check + hash_regression to concorda_parity.py**

```python
def shape_check(scratch: Path) -> list[str]:
    """Assert every per-kind file has the required fields."""
    failures: list[str] = []
    nodes_dir = scratch / "nodes"
    for kind_dir in sorted(nodes_dir.iterdir()):
        if not kind_dir.is_dir() or kind_dir.name.startswith("_"):
            continue
        for f in sorted(kind_dir.glob("*.json"))[:5]:
            try:
                node = json.loads(f.read_text())
            except Exception as e:
                failures.append(f"{f}: parse error {e}")
                continue
            kind = node.get("kind")
            # Per-kind required fields. route_call is a known outlier.
            if kind == "route_call":
                required = ("schema_version", "id", "kind", "source",
                            "signature", "structural_hash")
            else:
                required = ("schema_version", "id", "kind", "title", "source",
                            "signature", "structural_hash", "depends_on",
                            "dossier", "extractor")
            for r in required:
                if r not in node:
                    failures.append(f"{f}: missing {r}")
            if node.get("id") and kind != "route_call" and "::" not in node["id"]:
                failures.append(f"{f}: id lacks '::'")
            sh = node.get("structural_hash", "")
            if kind != "route_call" and not (len(sh) == 64 and all(c in "0123456789abcdef" for c in sh)):
                failures.append(f"{f}: structural_hash not 64-hex")
    return failures


def hash_regression(scratch: Path, current: Path) -> list[str]:
    """Every id present in current/ must have matching structural_hash in scratch/."""
    failures: list[str] = []
    # Index scratch by id
    by_id: dict[str, str] = {}
    for f in (scratch / "nodes").rglob("*.json"):
        if "_index" in f.parts or "_archive" in f.parts or "_manifests" in f.parts:
            continue
        try:
            n = json.loads(f.read_text())
        except Exception:
            continue
        if "id" in n and "structural_hash" in n:
            by_id[n["id"]] = n["structural_hash"]

    # Walk current and compare
    for f in (current / "nodes").rglob("*.json"):
        if "_index" in f.parts or "_archive" in f.parts or "_manifests" in f.parts:
            continue
        try:
            n = json.loads(f.read_text())
        except Exception:
            continue
        nid = n.get("id")
        if not nid or "structural_hash" not in n:
            continue
        if nid not in by_id:
            failures.append(f"missing in scratch: {nid}")
            continue
        if by_id[nid] != n["structural_hash"]:
            failures.append(
                f"hash mismatch for {nid}: expected {n['structural_hash']}, got {by_id[nid]}"
            )
    return failures
```

Wire both into `main`: if `--diff <scratch>` is passed, run count_diff, shape_check, hash_regression; report each; return 0 only if all clean.

- [ ] **Step 3: Run parity into scratch**

```bash
SCRATCH=$(mktemp -d)/depgraph && mkdir -p "$SCRATCH" && \
  cp ~/tools/knowledge-graph/scripts/concorda_parity_project.toml "$SCRATCH/project.toml" && \
  DEPGRAPH_DATA_DIR="$SCRATCH" ~/tools/knowledge-graph/depgraph/bin/depgraph regen && \
  python3 ~/tools/knowledge-graph/scripts/concorda_parity.py --diff "$SCRATCH"
```

Expected: zero shape failures, zero hash regressions. The count diff still shows the previously-accepted services -478 / tests-py NOT-EMITTED (because we disabled pytest on api) — that's expected.

- [ ] **Step 4: Commit**

```bash
git add scripts/concorda_parity.py scripts/concorda_parity_project.toml
git commit -m "parity: shape-check + hash-regression gates"
```

---

## Task 9: Re-flip Concorda

Only proceed if Task 7 (gate) and Task 8 (parity zero hash regressions) are both green. Otherwise stop.

- [ ] **Step 1: Rewrite concorda's project.toml** — same shape as `scripts/concorda_parity_project.toml`. Keep `[memory]` and `[logigraph]`. Drop `[repos.web_routes]` (route-calls now part of the web detector list).

- [ ] **Step 2: Regen real concorda**

```bash
DEPGRAPH_DATA_DIR=~/concorda-knowledge-graph/depgraph ~/tools/knowledge-graph/depgraph/bin/depgraph regen 2>&1 | tail -20
```

Expected: clean. Zero fs orphans. Zero new stale dossiers (existing stale dossiers from session-start remain).

- [ ] **Step 3: Verify on disk by hand**

```bash
# Sample one of each kind and visually confirm schema
for k in endpoints models schemas services components hooks tests route_calls; do
  echo "=== $k ==="
  ls ~/concorda-knowledge-graph/depgraph/nodes/$k/ | head -1 | \
    xargs -I{} cat ~/concorda-knowledge-graph/depgraph/nodes/$k/{} | head -25
done
```

Expected: every kind matches its pre-flip shape per § Canonical Node Contracts.

- [ ] **Step 4: Confirm dossiers still attach**

```bash
# Should be ~1678 dossiers, ~0 orphans (or whatever the pre-flip orphan count was)
cd ~/concorda-knowledge-graph
for k in components endpoints hooks models schemas services tests; do
  total=0; missing=0
  for d in $(ls depgraph/dossiers/$k/ 2>/dev/null); do
    total=$((total+1)); node="${d%.md}.json"
    [ -f depgraph/nodes/$k/"$node" ] || missing=$((missing+1))
  done
  printf "%-12s %4d dossiers  %4d orphaned\n" "$k" "$total" "$missing"
done
```

Expected: 0 orphans per kind (or matches the pre-flip orphan count, which should be 1).

- [ ] **Step 5: Confirm no dossier turned stale**

```bash
DEPGRAPH_DATA_DIR=~/concorda-knowledge-graph/depgraph ~/tools/knowledge-graph/depgraph/bin/depgraph dossier-rank --only-stale 2>&1 | tail -10
```

Expected: same 5 stale dossiers that were stale pre-flip. No new ones.

- [ ] **Step 6: Delete bespoke extractors**

```bash
cd ~/concorda-knowledge-graph
git rm depgraph/extractors/extract_api.py \
       depgraph/extractors/extract_web.ts \
       depgraph/extractors/extract_tests.ts \
       depgraph/extractors/ingest_route_calls.py
```

- [ ] **Step 7: Commit**

```bash
cd ~/concorda-knowledge-graph
git add -A depgraph/
git commit -m "depgraph: flip to framework generic extractors (byte-equivalent canonicalization)"
```

- [ ] **Step 8: Final self-check**

```bash
DEPGRAPH_DATA_DIR=~/concorda-knowledge-graph/depgraph ~/tools/knowledge-graph/depgraph/bin/depgraph self-check
```

Expected: no `schema_version mismatch` warning.

---

## Out of scope (deferred)

- **Python tests via pytest** on concorda-api. Additive feature, not parity goal. Land separately after the flip stabilizes.
- **Go and Rust canonicalization**. Concorda doesn't use them. They emit AST primitives today; add canonical stages when another project flips them.
- **Logigraph rule re-pinning**. The plan preserves structural_hashes per kind, so most logigraph claims should remain valid. Run `logigraph validate` after Task 9 and address any drift as a separate commit.

---

## Self-review checklist (run after this plan is final)

- [x] Every required field in pre-flip nodes is reproduced by a documented contract in § Canonical Node Contracts (or explicitly called an outlier, like route_call).
- [x] Slugify variant difference (python vs typescript) is captured.
- [x] Hash function difference (sort_keys vs insertion-order) is captured.
- [x] depends_on `via:` taxonomy is enumerated; resolver tasks reproduce every label.
- [x] Each kind's hash payload is pinned key-by-key with field name + value source.
- [x] Gate test (Task 1) commits failing FIRST; subsequent tasks make it pass.
- [x] No task lands without its gate green.
- [x] Concrete code with type signatures, not placeholders.
- [x] Pre-flip hash reproduced in a unit test in Task 2 (endpoint/model/schema).
- [x] TS hash reproduced in a unit test in Task 5 (component, using committed text fixture).
