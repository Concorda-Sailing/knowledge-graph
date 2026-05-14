# Cross-Repo Route-Call Extractor

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture HTTP-call edges between tracked repos (e.g. `concorda-web::src/lib/api.ts::fetchEvents` → `concorda-api::routers/events.py::POST /api/events/import`) so the depgraph dependents index — and therefore graphui's `↑ inbound / ↓ outbound` counts — start carrying real cross-repo signal. Today the index has 2089 edges, all intra-repo.

**Architecture:** Two-phase. **Phase 1** — a new generic TypeScript extractor walks any JS/TS repo with the TypeScript Compiler API, finds `fetch(...)` call expressions, extracts `(method, url_pattern)` from each call (including template-literal URLs with `${API_BASE_URL}` prefix), and emits a new `route_call` node kind. **Phase 2** — reconcile.py gains a join pass that normalizes URL patterns (`{id}`, `:id`, `<var>` → `<var>`) and emits reverse edges from matching `endpoint` nodes back to the `route_call` sites. Adds a new `{framework_dir}` substitution to `lib/config.py::render_extractor` so project.toml can reference framework-shipped generic extractors via stable paths.

**Tech Stack:** Python 3.11+ stdlib · pytest · Node.js + `tsx` + `typescript` (for the extractor only).

**Spec context:** Out of band — this is Layer 3 of the extractor brainstorm. Settings page already surfaces the extractor inventory (graphui Plan C); this plan populates the empty `generic` scope and starts producing cross-repo edges.

---

## File Structure

**New files (depgraph framework):**
- `schema/node.schema.json` — modified: add `route_call` to the kind enum + a new `signature.url_pattern` field doc
- `lib/config.py` — modified: add `{framework_dir}` substitution to `render_extractor`
- `extractors/reconcile.py` — modified: new `_normalize_url_pattern` helper + new `_join_route_calls` pass that runs after the main reverse-index build
- `extractors/generic/typescript/route-calls.ts` — new TypeScript AST walker
- `extractors/generic/typescript/package.json` — tiny manifest declaring `typescript` + `tsx` deps
- `extractors/generic/typescript/README.md` — one-paragraph usage doc
- `extractors/generic/README.md` — describes the `extractors/generic/` directory convention
- `tests/test_url_normalize.py` — unit tests for the URL-pattern normalizer (Python side)
- `tests/test_reconcile_route_calls.py` — integration: fixture dir with one endpoint + one route_call, run reconcile, assert edge in dependents.json
- `tests/fixtures/route_calls/nodes/endpoints/example_endpoint.json`
- `tests/fixtures/route_calls/nodes/route_calls/example_call.json`
- `tests/fixtures/route_calls/nodes/_meta.json`
- `tests/fixtures/route_calls/project.toml`
- `tests/fixtures/typescript_extractor/sample.ts` — synthetic input for the extractor test
- `tests/test_route_call_extractor_ts.py` — runs the TS extractor as a subprocess and asserts the emitted JSON

**Modified files (Concorda data dir, separate repo):**
- `~/concorda/knowledge-graph/depgraph/project.toml` — add a new `[repos.web_routes]` table pointing at the framework-generic extractor (kept distinct from the existing `[repos.web]` so both extractors emit side-by-side during transition)

**Out of scope (future):**
- axios / RTK Query / custom-wrapper detection — concorda-web uses only `fetch`, so v1 doesn't need them
- Resolving URLs from non-template variables (e.g. `const URL = '/api/x'; fetch(URL)`) — adds variable-flow analysis
- The graphui repo — no changes here; once reconcile emits cross-repo edges, the existing dashboard + repo-detail counts pick them up automatically

---

## Conventions for this plan

- **Test-first** for both Python pieces (reconcile + helpers).
- **Subprocess test** for the TS extractor — easier than mocking the TypeScript compiler from Python.
- All commits via `pytest` from the depgraph repo root (`cd ~/tools/knowledge-graph/depgraph && pytest`).
- Pure-additive on `reconcile.py` — keep the existing reverse-index build untouched; new `_join_route_calls` runs after it.
- Trailer convention: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

---

## Task 1: Schema — add `route_call` kind

**Files:**
- Modify: `schema/node.schema.json` — add `route_call` to the kind enum; document `signature.method` + `signature.url_pattern`

- [ ] **Step 1: Read the current schema**

Run: `grep -n '"kind"\|"signature"\|"url_pattern"' schema/node.schema.json`
Find the `enum` line under `properties.kind`. Find the `signature` block.

- [ ] **Step 2: Update the kind enum**

Add `"route_call"` to the enum list. The order matters only for human readability — keep it next to `endpoint` since they pair:

Old:
```json
"enum": ["endpoint", "component", "hook", "service", "model", "test", "schema"],
```
New:
```json
"enum": ["endpoint", "route_call", "component", "hook", "service", "model", "test", "schema"],
```

- [ ] **Step 3: Document `signature.url_pattern`**

In the `signature` block's `properties`, add the `url_pattern` field after `path`:
```json
"url_pattern": {
  "type": ["string", "null"],
  "description": "For route_call nodes: the HTTP URL pattern after stripping any base-URL placeholder. Variable segments use the token <var> (e.g. /api/events/<var>/import). Reconcile normalizes endpoint paths to the same shape for matching."
}
```

- [ ] **Step 4: Validate the schema is still well-formed JSON**

Run: `python3 -c "import json; json.load(open('schema/node.schema.json'))"` — silence = success.

- [ ] **Step 5: Commit**

```
git add schema/node.schema.json
git commit -m "feat(schema): add route_call node kind + signature.url_pattern field

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Config — `{framework_dir}` substitution

**Files:**
- Modify: `lib/config.py` — extend `render_extractor` with the new substitution
- Modify: `tests/` — add a test in any existing test file or create `tests/test_render_extractor.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_render_extractor.py`:
```python
"""Tests for lib.config.render_extractor — specifically the {framework_dir}
substitution that lets project.toml reference framework-shipped extractors."""
from pathlib import Path
import lib.config as config


def test_framework_dir_substitution():
    repo_info = {
        "path": "/some/repo",
        "extractor": ["python3", "{framework_dir}/extractors/generic/foo.py", "--path", "{path}"],
    }
    out = config.render_extractor(repo_info, Path("/some/data_dir"))
    assert out is not None
    # framework_dir resolves to the depgraph repo root (parent of lib/).
    expected_root = str(Path(config.__file__).resolve().parent.parent)
    assert out[1].startswith(expected_root)
    assert out[1].endswith("/extractors/generic/foo.py")
    assert out[3] == "/some/repo"


def test_existing_substitutions_unchanged():
    """Make sure the original {data_dir} and {path} substitutions still work."""
    repo_info = {"path": "/r", "extractor": ["x", "{data_dir}/y", "{path}/z"]}
    out = config.render_extractor(repo_info, Path("/d"))
    assert out == ["x", "/d/y", "/r/z"]
```

- [ ] **Step 2: Run — verify FAIL**

`pytest tests/test_render_extractor.py -v`
Expected: `test_framework_dir_substitution` fails with `KeyError: 'framework_dir'`.

- [ ] **Step 3: Implement**

In `lib/config.py`, find `render_extractor`. Update the `subs` dict:

Old:
```python
    subs = {
        "data_dir": str(data_dir),
        "path": str(repo_info["path"]),
    }
```
New:
```python
    subs = {
        "data_dir": str(data_dir),
        "path": str(repo_info["path"]),
        "framework_dir": str(Path(__file__).resolve().parent.parent),
    }
```

- [ ] **Step 4: PASS**

`pytest tests/test_render_extractor.py -v` → 2 passed.

- [ ] **Step 5: Full suite**

`pytest tests/ -v` — confirm no regressions (existing tests should still pass).

- [ ] **Step 6: Commit**

```
git add lib/config.py tests/test_render_extractor.py
git commit -m "feat(config): {framework_dir} substitution in render_extractor

Lets project.toml reference framework-shipped generic extractors via
a stable path that doesn't bake the user's home dir into the config.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Reconcile — URL normalization helper

**Files:**
- Modify: `extractors/reconcile.py` — add `_normalize_url_pattern`
- Create: `tests/test_url_normalize.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_url_normalize.py`:
```python
"""URL-pattern normalization makes route_call URLs (from JS template literals)
join cleanly against endpoint paths (from Python framework decorators).

Normalization rule: collapse every variable segment to the literal token <var>.
Variable segments in input forms we expect:
  - FastAPI/Starlette  /api/events/{id}/import          → /api/events/<var>/import
  - FastAPI typed      /api/events/{id:int}/import      → /api/events/<var>/import
  - Express/Vue/Rails  /api/events/:id/import           → /api/events/<var>/import
  - Already-tokenized  /api/events/<var>/import         → unchanged
"""
from extractors.reconcile import _normalize_url_pattern


def test_fastapi_braces():
    assert _normalize_url_pattern("/api/events/{id}/import") == "/api/events/<var>/import"


def test_fastapi_typed_braces():
    assert _normalize_url_pattern("/api/events/{id:int}/import") == "/api/events/<var>/import"
    assert _normalize_url_pattern("/api/files/{path:path}") == "/api/files/<var>"


def test_express_colon_prefix():
    assert _normalize_url_pattern("/api/events/:id/import") == "/api/events/<var>/import"


def test_already_tokenized_passthrough():
    assert _normalize_url_pattern("/api/events/<var>/import") == "/api/events/<var>/import"


def test_static_path_unchanged():
    assert _normalize_url_pattern("/api/health") == "/api/health"
    assert _normalize_url_pattern("/api/events/import/csv") == "/api/events/import/csv"


def test_multiple_variables():
    assert _normalize_url_pattern("/api/orgs/{org_id}/users/:user_id") == "/api/orgs/<var>/users/<var>"


def test_trailing_slash_preserved():
    assert _normalize_url_pattern("/api/events/") == "/api/events/"


def test_empty_and_none():
    assert _normalize_url_pattern("") == ""
    assert _normalize_url_pattern(None) is None
```

- [ ] **Step 2: Verify FAIL**

`pytest tests/test_url_normalize.py -v`
Expected: ImportError because `_normalize_url_pattern` doesn't exist yet.

- [ ] **Step 3: Implement**

In `extractors/reconcile.py`, add this helper (near the top of the module, after imports):

```python
import re


# `_normalize_url_pattern` collapses each variable segment in a URL path to the
# literal token `<var>`. This is the join key between route_call signature.url_pattern
# (emitted by JS extractors) and endpoint signature.path (emitted by Python/FastAPI
# extractors). Both forms — `{name}`, `{name:type}`, `:name` — collapse to `<var>`.
_URL_VAR_RE = re.compile(r"""
    \{[^}]+\}        # FastAPI/Starlette/OpenAPI:  {id} or {id:int} or {path:path}
    |
    :[A-Za-z_][A-Za-z0-9_]*   # Express/Vue/Rails: :id (must follow / not [a-z])
""", re.VERBOSE)


def _normalize_url_pattern(url: str | None) -> str | None:
    if url is None:
        return None
    if not url:
        return ""
    return _URL_VAR_RE.sub("<var>", url)
```

- [ ] **Step 4: PASS**

`pytest tests/test_url_normalize.py -v` → 8 passed.

- [ ] **Step 5: Commit**

```
git add extractors/reconcile.py tests/test_url_normalize.py
git commit -m "feat(reconcile): _normalize_url_pattern helper for route_call joins

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Reconcile — `_join_route_calls` pass

**Files:**
- Modify: `extractors/reconcile.py` — add the join pass
- Create: `tests/test_reconcile_route_calls.py`
- Create: `tests/fixtures/route_calls/project.toml`
- Create: `tests/fixtures/route_calls/nodes/_meta.json`
- Create: `tests/fixtures/route_calls/nodes/endpoints/example_endpoint.json`
- Create: `tests/fixtures/route_calls/nodes/route_calls/example_call.json`

- [ ] **Step 1: Create the fixture directory and files**

Create `tests/fixtures/route_calls/project.toml`:
```toml
[project]
name = "rc-fixture"

[repos.api]
path = "/tmp/rc-api"
extractor = ["python3", "noop.py"]

[repos.web]
path = "/tmp/rc-web"
extractor = ["npx", "tsx", "noop.ts"]
```

Create `tests/fixtures/route_calls/nodes/_meta.json`:
```json
{"regen_status": "complete", "regen_at": "2026-05-13T10:00:00+00:00", "node_count": 2, "flags": []}
```

Create `tests/fixtures/route_calls/nodes/endpoints/example_endpoint.json`:
```json
{
  "schema_version": 1,
  "id": "rc-api::routers/events.py::import_events_endpoint",
  "kind": "endpoint",
  "title": "POST /api/events/import",
  "source": {"repo": "rc-api", "path": "routers/events.py"},
  "signature": {"method": "POST", "path": "/api/events/{id}/import"},
  "structural_hash": "h1",
  "extractor": "noop",
  "depends_on": []
}
```

Create `tests/fixtures/route_calls/nodes/route_calls/example_call.json`:
```json
{
  "schema_version": 1,
  "id": "rc-web::src/lib/api.ts:42::importEvent",
  "kind": "route_call",
  "title": "fetch POST /api/events/<var>/import",
  "source": {"repo": "rc-web", "path": "src/lib/api.ts", "line": 42},
  "signature": {"method": "POST", "url_pattern": "/api/events/<var>/import"},
  "structural_hash": "h2",
  "extractor": "noop",
  "depends_on": []
}
```

- [ ] **Step 2: Write the failing integration test**

Create `tests/test_reconcile_route_calls.py`:
```python
"""Integration test: reconcile.py joins route_call nodes against endpoint
nodes and writes the cross-repo edge to dependents.json."""
import json
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "route_calls"


def test_reconcile_emits_route_call_dependent(tmp_path):
    # Mirror the fixture into a tmp dir so reconcile can write _index/ without
    # dirtying the test source tree.
    import shutil
    work = tmp_path / "depgraph"
    shutil.copytree(FIXTURE, work)
    repo_root = Path(__file__).resolve().parent.parent  # depgraph repo root

    result = subprocess.run(
        [sys.executable, str(repo_root / "extractors" / "reconcile.py"),
         "--data-dir", str(work)],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, f"reconcile failed: {result.stderr}"

    dependents_path = work / "nodes" / "_index" / "dependents.json"
    assert dependents_path.exists(), "reconcile did not write dependents.json"
    idx = json.loads(dependents_path.read_text())
    by_target = idx.get("by_target") or {}

    endpoint_id = "rc-api::routers/events.py::import_events_endpoint"
    assert endpoint_id in by_target, f"endpoint missing from dependents: {sorted(by_target)}"
    dependers = by_target[endpoint_id]
    # The route_call node should appear as a depender on the endpoint.
    dep_ids = [d["id"] for d in dependers]
    assert "rc-web::src/lib/api.ts:42::importEvent" in dep_ids


def test_reconcile_skips_route_call_with_mismatched_method(tmp_path):
    import shutil
    work = tmp_path / "depgraph"
    shutil.copytree(FIXTURE, work)
    # Tweak the route_call to use GET instead of POST; reconcile must NOT join it.
    call_path = work / "nodes" / "route_calls" / "example_call.json"
    call = json.loads(call_path.read_text())
    call["signature"]["method"] = "GET"
    call_path.write_text(json.dumps(call))

    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, str(repo_root / "extractors" / "reconcile.py"),
         "--data-dir", str(work)],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0

    idx = json.loads((work / "nodes" / "_index" / "dependents.json").read_text())
    by_target = idx.get("by_target") or {}
    endpoint_id = "rc-api::routers/events.py::import_events_endpoint"
    dependers = by_target.get(endpoint_id, [])
    dep_ids = [d["id"] for d in dependers]
    assert "rc-web::src/lib/api.ts:42::importEvent" not in dep_ids
```

- [ ] **Step 3: Verify FAIL**

`pytest tests/test_reconcile_route_calls.py -v`
Expected: both tests fail (endpoint not in dependents — reconcile doesn't emit route-call edges yet).

- [ ] **Step 4: Implement `_join_route_calls`**

In `extractors/reconcile.py`, find the section that builds `by_target` (the reverse-index assembly). After that block completes, add a call to a new function `_join_route_calls(nodes, by_target)`.

Add this function (after `_normalize_url_pattern` from Task 3):

```python
def _join_route_calls(nodes: list[dict], by_target: dict[str, list[dict]]) -> int:
    """For every route_call node, find endpoint nodes whose
    (method, normalized_path) matches its (method, normalized_url_pattern)
    and emit an edge endpoint ← route_call.

    Mutates by_target in place. Returns the count of edges added.

    This pass is what produces cross-repo dependents — a JS fetch call
    site referencing a Python FastAPI route becomes a dependent on that
    route.
    """
    endpoints_by_key: dict[tuple[str, str], list[dict]] = {}
    route_calls: list[dict] = []
    for n in nodes:
        kind = n.get("kind")
        sig = n.get("signature") or {}
        if kind == "endpoint":
            method = (sig.get("method") or "").upper()
            path = _normalize_url_pattern(sig.get("path"))
            if not method or not path:
                continue
            endpoints_by_key.setdefault((method, path), []).append(n)
        elif kind == "route_call":
            route_calls.append(n)

    added = 0
    for rc in route_calls:
        sig = rc.get("signature") or {}
        method = (sig.get("method") or "").upper()
        url = _normalize_url_pattern(sig.get("url_pattern"))
        if not method or not url:
            continue
        for ep in endpoints_by_key.get((method, url), []):
            target_id = ep["id"]
            dep_entry = {"id": rc["id"], "kind": "route_call"}
            existing = by_target.setdefault(target_id, [])
            if dep_entry not in existing:
                existing.append(dep_entry)
                added += 1
    return added
```

Then find where reconcile assembles `by_target` and insert one line right before it writes the file:

```python
# Cross-repo: join route_call sites against endpoint paths.
_join_route_calls(nodes, by_target)
```

(The exact insertion point depends on the existing structure of reconcile.py — look for where `by_target` is fully assembled but before it's serialized to disk.)

Also: reconcile.py should accept a `--data-dir` flag (most CLIs in this repo already do). If it doesn't, add `argparse` boilerplate so the integration test can point it at the fixture. Check first.

- [ ] **Step 5: PASS**

`pytest tests/test_reconcile_route_calls.py -v` → 2 passed.

- [ ] **Step 6: Full suite — confirm no regressions**

`pytest tests/ -v` — every prior test still passes.

- [ ] **Step 7: Commit**

```
git add extractors/reconcile.py tests/test_reconcile_route_calls.py tests/fixtures/route_calls/
git commit -m "feat(reconcile): join route_call sites to endpoints by (method, url)

Emits cross-repo dependents — a JS fetch site becomes a dependent on
the FastAPI route it calls. Repo-card inbound/outbound counts in
graphui pick this up automatically once reconcile runs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Generic-extractor scaffolding

**Files:**
- Create: `extractors/generic/README.md` (one-paragraph convention doc)
- Create: `extractors/generic/typescript/README.md`
- Create: `extractors/generic/typescript/package.json`

- [ ] **Step 1: Write the convention doc**

Create `extractors/generic/README.md`:
```markdown
# Generic extractors

This directory holds framework-shipped extractors that any project can use
without writing their own. Each subdirectory is one language / framework:

- `typescript/` — JS/TS source-walking extractors (uses the TypeScript Compiler API)
- (more to come)

## Using a generic extractor from `project.toml`

Reference the file via the `{framework_dir}` substitution that
`lib/config.render_extractor` resolves to the depgraph repo root:

```toml
[repos.web]
path = "~/concorda-web"
extractor = ["npx", "tsx",
             "{framework_dir}/extractors/generic/typescript/route-calls.ts",
             "--scan", "{path}/src", "--repo-key", "concorda-web"]
```

Each extractor declares `__extractor_version__ = "1.0.0"` (or the
TypeScript equivalent — a top-level `export const EXTRACTOR_VERSION = "1.0.0"`).
The graphui Settings page reads this and shows it in the inventory.

## Conventions

- Project-custom extractors stay the escape hatch. If a generic extractor
  can't express your project's analysis, hand-write one under
  `<data_dir>/extractors/` and reference it via `{data_dir}/...`.
- Generic extractors should be deterministic and side-effect-free: read,
  emit JSON to stdout (one node per line), don't touch the filesystem.
- They MUST be runnable headless from the framework root — no project-
  specific assumptions in code, only via CLI args.
```

- [ ] **Step 2: TypeScript subdir docs**

Create `extractors/generic/typescript/README.md`:
```markdown
# Generic TypeScript extractors

Walk JS/TS source trees with the [TypeScript Compiler API](https://github.com/microsoft/TypeScript-wiki/blob/master/Using-the-Compiler-API.md).
Run via `npx tsx <extractor>.ts <args>`.

## Setup

One-time, from this directory:

```bash
cd ~/tools/knowledge-graph/depgraph/extractors/generic/typescript
npm install
```

This installs `typescript` and `tsx` into a local `node_modules/`. The
extractors import `typescript` directly; `tsx` handles the runtime.

## Available extractors

- `route-calls.ts` — emits `route_call` nodes for every `fetch(...)` site.
  See file header for full options.
```

- [ ] **Step 3: package.json**

Create `extractors/generic/typescript/package.json`:
```json
{
  "name": "depgraph-generic-typescript-extractors",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "engines": { "node": ">=18" },
  "dependencies": {
    "typescript": "^5.4.0",
    "tsx": "^4.7.0"
  }
}
```

- [ ] **Step 4: Install (one-time)**

Run: `cd extractors/generic/typescript && npm install && cd -`
Confirms typescript + tsx land in `node_modules/`.

- [ ] **Step 5: Add `node_modules` to `.gitignore`**

If the depgraph repo doesn't already gitignore `node_modules/`:
```
echo "extractors/generic/typescript/node_modules/" >> .gitignore
```
Verify: `git status` should NOT show node_modules.

- [ ] **Step 6: Commit (without node_modules)**

```
git add extractors/generic/README.md extractors/generic/typescript/README.md extractors/generic/typescript/package.json .gitignore
git commit -m "feat(extractors): generic/ directory scaffolding + typescript setup

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 7: Commit the lock file separately**

`npm install` produced `package-lock.json`. Commit it for reproducibility:
```
git add extractors/generic/typescript/package-lock.json
git commit -m "chore(extractors): lock typescript + tsx versions"
```

---

## Task 6: Generic extractor — `route-calls.ts`

**Files:**
- Create: `extractors/generic/typescript/route-calls.ts`
- Create: `tests/test_route_call_extractor_ts.py`
- Create: `tests/fixtures/typescript_extractor/sample.ts`

- [ ] **Step 1: Write the synthetic input fixture**

Create `tests/fixtures/typescript_extractor/sample.ts`:
```typescript
// Sample JS code the extractor must handle.

const API_BASE_URL = 'https://api.example.com';

export async function getHealth() {
  const r = await fetch(`${API_BASE_URL}/health`);
  return r.json();
}

export async function importEvent(id: string, payload: unknown) {
  return fetch(`${API_BASE_URL}/api/events/${id}/import`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listOrgs() {
  return fetch('/api/organizations', { method: 'GET' });
}

// Should be SKIPPED — first arg is a bare variable, can't resolve.
async function dynamic(url: string) {
  return fetch(url);
}
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_route_call_extractor_ts.py`:
```python
"""Subprocess test for the TS route-call extractor.

Runs `npx tsx <extractor> --scan <fixture-dir> --repo-key fake-web` and
asserts the emitted JSON-Lines output contains one route_call node per
fetch() site, with method and url_pattern extracted correctly."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTOR = REPO_ROOT / "extractors" / "generic" / "typescript" / "route-calls.ts"
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "typescript_extractor"


def _have_tsx() -> bool:
    return shutil.which("npx") is not None and (
        REPO_ROOT / "extractors" / "generic" / "typescript" / "node_modules" / "tsx"
    ).exists()


@pytest.mark.skipif(not _have_tsx(), reason="tsx not installed (run npm install in extractors/generic/typescript)")
def test_extractor_emits_three_route_calls():
    result = subprocess.run(
        ["npx", "tsx", str(EXTRACTOR), "--scan", str(FIXTURE_DIR), "--repo-key", "fake-web"],
        cwd=str(REPO_ROOT / "extractors" / "generic" / "typescript"),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"extractor failed: {result.stderr}"
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    nodes = [json.loads(l) for l in lines]

    # Three resolvable fetch sites in sample.ts (the bare-variable one is skipped).
    assert len(nodes) == 3
    by_url = {n["signature"]["url_pattern"]: n for n in nodes}

    # Health endpoint: template literal with only the base var → / path remains
    assert "/health" in by_url, f"missing /health; saw {sorted(by_url)}"
    assert by_url["/health"]["signature"]["method"] == "GET"
    assert by_url["/health"]["kind"] == "route_call"
    assert by_url["/health"]["source"]["repo"] == "fake-web"

    # Variable in path → tokenized to <var>
    assert "/api/events/<var>/import" in by_url
    assert by_url["/api/events/<var>/import"]["signature"]["method"] == "POST"

    # Plain string literal first arg
    assert "/api/organizations" in by_url
    assert by_url["/api/organizations"]["signature"]["method"] == "GET"
```

- [ ] **Step 3: Verify FAIL**

`pytest tests/test_route_call_extractor_ts.py -v`
Expected: skipped if tsx not installed, else fails (extractor doesn't exist yet).

If skipped: install first via `cd extractors/generic/typescript && npm install`.

- [ ] **Step 4: Implement the extractor**

Create `extractors/generic/typescript/route-calls.ts`:
```typescript
#!/usr/bin/env tsx
/**
 * route-calls.ts — emit one `route_call` node per fetch() call site under --scan.
 *
 * Usage:
 *   npx tsx route-calls.ts --scan <dir> --repo-key <basename> [--base-url-var <name>]
 *
 * - --scan: directory to walk recursively for .ts/.tsx files.
 * - --repo-key: the repo basename used as the leading segment of the node id
 *   (must match a [repos.*].path basename in project.toml so reconcile resolves it).
 * - --base-url-var: optional. If a fetch URL starts with this template var
 *   (e.g. `${API_BASE_URL}/foo`), strip it. Defaults to API_BASE_URL.
 *
 * Emits NDJSON to stdout — one node per line.
 */

import * as ts from "typescript";
import * as fs from "fs";
import * as path from "path";

export const EXTRACTOR_VERSION = "1.0.0";

interface RouteCall {
  schema_version: 1;
  id: string;
  kind: "route_call";
  title: string;
  source: { repo: string; path: string; line: number };
  signature: { method: string; url_pattern: string | null };
  extractor: string;
  structural_hash: string;
  depends_on: never[];
}

function parseArgs(argv: string[]): { scan: string; repoKey: string; baseUrlVar: string } {
  const args = { scan: "", repoKey: "", baseUrlVar: "API_BASE_URL" };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--scan") args.scan = argv[++i];
    else if (argv[i] === "--repo-key") args.repoKey = argv[++i];
    else if (argv[i] === "--base-url-var") args.baseUrlVar = argv[++i];
  }
  if (!args.scan || !args.repoKey) {
    console.error("usage: route-calls.ts --scan <dir> --repo-key <basename> [--base-url-var <name>]");
    process.exit(2);
  }
  return args;
}

function* walk(dir: string): Generator<string> {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
      yield* walk(full);
    } else if (entry.isFile() && /\.tsx?$/.test(entry.name)) {
      yield full;
    }
  }
}

function urlFromTemplate(node: ts.TemplateExpression, baseUrlVar: string): string | null {
  const parts: string[] = [];
  // The head text (before the first ${...}).
  parts.push(node.head.text);
  for (const span of node.templateSpans) {
    // Substitution: replace with a placeholder token, unless this is the
    // leading base-URL variable and the head was empty.
    const expr = span.expression;
    const isBaseUrl =
      ts.isIdentifier(expr) && expr.text === baseUrlVar && parts.length === 1 && parts[0] === "";
    if (isBaseUrl) {
      // Drop the placeholder — skip emitting anything for this span's expression.
    } else {
      parts.push("<var>");
    }
    parts.push(span.literal.text);
  }
  const url = parts.join("");
  return url || null;
}

function urlFromArg(arg: ts.Expression, baseUrlVar: string): string | null {
  if (ts.isStringLiteral(arg) || ts.isNoSubstitutionTemplateLiteral(arg)) {
    return arg.text;
  }
  if (ts.isTemplateExpression(arg)) {
    return urlFromTemplate(arg, baseUrlVar);
  }
  return null;
}

function methodFromOpts(arg: ts.Expression | undefined): string {
  if (!arg || !ts.isObjectLiteralExpression(arg)) return "GET";
  for (const prop of arg.properties) {
    if (
      ts.isPropertyAssignment(prop) &&
      ts.isIdentifier(prop.name) &&
      prop.name.text === "method"
    ) {
      const v = prop.initializer;
      if (ts.isStringLiteral(v) || ts.isNoSubstitutionTemplateLiteral(v)) {
        return v.text.toUpperCase();
      }
    }
  }
  return "GET";
}

function symbolForCall(call: ts.CallExpression, sf: ts.SourceFile): string {
  // Walk up to find an enclosing function/method name for a friendlier id.
  let p: ts.Node | undefined = call.parent;
  while (p) {
    if (ts.isFunctionDeclaration(p) && p.name) return p.name.text;
    if (
      (ts.isVariableDeclaration(p) || ts.isPropertyAssignment(p)) &&
      ts.isIdentifier(p.name)
    )
      return p.name.text;
    if (
      ts.isMethodDeclaration(p) &&
      ts.isIdentifier(p.name)
    )
      return p.name.text;
    p = p.parent;
  }
  // Fallback: anonymous-call-at-line tag.
  const { line } = sf.getLineAndCharacterOfPosition(call.getStart(sf));
  return `fetch_at_${line + 1}`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scanRoot = path.resolve(args.scan);
  // Compute the path the extractor will emit, relative to its repo root,
  // not the scan root — repo_key/path stays consistent.
  const repoRoot = scanRoot.endsWith("/src") ? path.dirname(scanRoot) : scanRoot;

  for (const file of walk(scanRoot)) {
    const text = fs.readFileSync(file, "utf-8");
    const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);

    function visit(node: ts.Node) {
      if (
        ts.isCallExpression(node) &&
        ts.isIdentifier(node.expression) &&
        node.expression.text === "fetch"
      ) {
        const url = urlFromArg(node.arguments[0], args.baseUrlVar);
        if (url !== null) {
          const method = methodFromOpts(node.arguments[1]);
          const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
          const symbol = symbolForCall(node, sf);
          const repoRelative = path.relative(repoRoot, file);
          const nodeId = `${args.repoKey}::${repoRelative}:${line + 1}::${symbol}`;

          // structural_hash: sha-style content fingerprint over (method, url, repo, path, symbol).
          const hashInput = `${method}|${url}|${args.repoKey}|${repoRelative}|${symbol}`;
          // Lightweight non-crypto hash — reconcile only needs stability, not security.
          let h = 0;
          for (let i = 0; i < hashInput.length; i++) {
            h = (h * 31 + hashInput.charCodeAt(i)) | 0;
          }
          const structuralHash = (h >>> 0).toString(16).padStart(8, "0");

          const out: RouteCall = {
            schema_version: 1,
            id: nodeId,
            kind: "route_call",
            title: `fetch ${method} ${url}`,
            source: { repo: args.repoKey, path: repoRelative, line: line + 1 },
            signature: { method, url_pattern: url },
            extractor: "generic/typescript/route-calls",
            structural_hash: structuralHash,
            depends_on: [],
          };
          console.log(JSON.stringify(out));
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(sf);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

- [ ] **Step 5: PASS**

`pytest tests/test_route_call_extractor_ts.py -v` → 1 passed.

If the test still skips, install: `cd extractors/generic/typescript && npm install`.

- [ ] **Step 6: Commit**

```
git add extractors/generic/typescript/route-calls.ts tests/test_route_call_extractor_ts.py tests/fixtures/typescript_extractor/
git commit -m "feat(extractors): generic TypeScript route-call extractor

Walks JS/TS files via the TypeScript Compiler API, finds fetch()
calls, extracts method + url_pattern (handling \${API_BASE_URL}
template prefix), emits one route_call NDJSON node per site.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Wire to Concorda + verify edge emission

**Files:**
- Modify: `~/concorda/knowledge-graph/depgraph/project.toml` (DIFFERENT REPO — the Concorda data dir, not the depgraph framework)

- [ ] **Step 1: Edit the project.toml**

Open `~/concorda/knowledge-graph/depgraph/project.toml`. Below the existing `[repos.web]` table, add:

```toml
[repos.web_routes]
path = "~/concorda-web"
extractor = ["npx", "tsx",
             "{framework_dir}/extractors/generic/typescript/route-calls.ts",
             "--scan", "{path}/src",
             "--repo-key", "concorda-web"]
```

(Same repo path as `[repos.web]`; different extractor.)

- [ ] **Step 2: Run regen**

```bash
cd ~/concorda
DEPGRAPH_DATA_DIR=$HOME/concorda/knowledge-graph/depgraph \
  $HOME/tools/knowledge-graph/depgraph/bin/depgraph regen
```

Watch for the new `route_call` nodes appearing under `~/concorda/knowledge-graph/depgraph/nodes/route_calls/`.

- [ ] **Step 3: Verify cross-repo edges in the index**

```bash
python3 -c "
import json, pathlib
idx = json.loads(pathlib.Path('$HOME/concorda/knowledge-graph/depgraph/nodes/_index/dependents.json').read_text())
bt = idx.get('by_target') or {}
xrepo = sum(
    1 for tid, deps in bt.items() for d in deps
    if d.get('id') and d['id'].split('::',1)[0] != tid.split('::',1)[0]
)
print('cross-repo edges:', xrepo)
"
```

Expected: a non-zero number. Earlier we measured `0`. After this lands, it should be at least 14 (one per fetch site in concorda-web).

- [ ] **Step 4: Commit (in the Concorda repo, not depgraph)**

```bash
cd ~/concorda
git add knowledge-graph/depgraph/project.toml
git commit -m "feat(graph): wire generic route-call extractor for concorda-web

Emits route_call nodes for every fetch() site in concorda-web/src so
reconcile can join them against concorda-api endpoints. Cross-repo
edges in dependents.json go from 0 to N (one per resolvable fetch
site).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Restart graphui + visual verification

**Files:** (none modified)

- [ ] **Step 1: Restart graphui**

`systemctl --user restart graphui`

- [ ] **Step 2: Browser check**

Open `http://localhost:8081/graph/` and look at the repo cards' footers:
- `concorda-web` card: `↓ outbound` should now show > 0 (the fetch calls)
- `concorda-api` card: `↑ inbound` should show > 0 (the routes being called)

Open `http://localhost:8081/graph/repo/concorda-api?tab=deps`:
- The Inbound table should list rows where `from_repo = concorda-web` and the symbol names match the fetch call sites.

Open `http://localhost:8081/graph/settings`:
- The Extractors table should list `route-calls.ts` with scope `generic` and declared_version `1.0.0`.

- [ ] **Step 3: If anything looks wrong, fix it in its own commit before declaring done**

Common issues to expect:
- URL pattern mismatch (concorda-api uses `{org_id}` but the test fixture expected `{id}`) → adjust normalization.
- `${API_BASE_URL}` not stripped because the variable name differs → add `--base-url-var BASE_URL` (or whatever Concorda uses) to the project.toml extractor command.
- node_modules missing on the dev box → run `npm install` in `extractors/generic/typescript/` once.

---

## Self-Review Checklist

1. **Coverage**:
   - ✓ `route_call` kind added to schema (Task 1)
   - ✓ `{framework_dir}` substitution (Task 2)
   - ✓ URL normalization handles all four input forms (Task 3)
   - ✓ Reconcile join pass (Task 4)
   - ✓ Generic extractor directory convention (Task 5)
   - ✓ TS extractor for fetch() (Task 6)
   - ✓ Concorda wiring (Task 7)
   - ✓ Graphui verification (Task 8)

2. **Placeholder scan:** no TBD / TODO patterns; concrete code in every step.

3. **Type consistency:**
   - `route_call.signature.url_pattern` (Task 1) matches what the TS extractor emits (Task 6) and what `_join_route_calls` reads (Task 4).
   - `endpoint.signature.path` already exists; reconcile normalizes both sides identically.
   - `_normalize_url_pattern` accepts `None` and `""` — both Task 4 callers pass guarded values.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-cross-repo-route-call-extractor.md` (in the **depgraph** repo, not graphui). Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review, fast iteration.
**2. Inline Execution** — execute here with checkpoints.

Which approach?
