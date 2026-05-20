# Extractor cleanup roadmap — /loop driven

Driver doc for the parallel cleanup of 18 open issues surfaced in the
2026-05-20 review pass. This file is the canonical state. Each /loop
firing reads this file, dispatches background agents for unblocked
items, and updates the status table.

## How the loop body works

On every /loop firing, do exactly this:

1. **Read this file.** Parse the status table below.
2. **Inspect already-completed commits.** If `git log origin/main..HEAD`
   shows a commit whose body contains `Refs #<N>` and that issue's row
   shows status `dispatched`, mark it `[x]` and capture the commit sha
   in the Notes column.
3. **Pick eligible items.** An item is eligible when:
   - Its row status is `pending` (unchecked).
   - Its lane has NO row currently `dispatched` (one item per lane
     in flight; lanes serialize within themselves).
   - Its wave is `<=` the lowest wave with any non-`[x]` row (don't
     start Wave 2 until Wave 1 is fully done — except infra lanes
     which have no wave dependency).
4. **Run pre-flight checks.** Before dispatching any agent:
   - `cd ~/knowledge-graph && git status` must be clean (no
     uncommitted changes). If not clean, abort the firing with a
     summary of what's dirty.
   - `.venv/bin/pytest -q` must pass. If failing, abort.
5. **Dispatch.** For each eligible item, spawn a background Agent
   using the "Agent prompt" block under that item's heading. Mark the
   row `dispatched` and write the doc back.
6. **Wait for completion.** Background agents auto-notify on
   completion. When an agent returns:
   - Verify its commit landed (`git log -1 origin/main..HEAD`).
   - Run `.venv/bin/pytest -q` to confirm tests still green.
   - If both pass: mark the row `[x]` with the commit sha. If either
     fails: mark `[FAIL]`, append the failure detail to Notes,
     `git reset --hard origin/main` IS NOT permitted — leave the
     workspace as-is and surface to the user.
7. **Self-pace.** If there is still pending work, call
   `ScheduleWakeup` with `delaySeconds=1200` and pass the same /loop
   prompt back. If all rows are `[x]` or `[FAIL]`, omit the wakeup —
   loop exits.

## Status

Legend: `pending`, `dispatched`, `[x]` (done with sha), `[FAIL]`.

| Lane | Wave | Issue | Title | Status | Notes |
|---|---|---|---|---|---|
| A.1 | 1 | #83 | py-extractor edge cases (walrus, vararg, multi-attr, builtin extends) | dispatched | agent af5eeba6 (worktree) |
| A.2 | 2 | #54 | SQLAlchemy ORM extractor | pending | depends on A.1 |
| A.3 | 2 | #45 | non-deterministic structural_hash | pending | investigation; can parallel A.2 if it touches canonical.py only |
| B.1 | 1 | #82 | TS scope shadowing in reads/assigns | dispatched | agent a9ce3f50 (worktree) |
| B.2 | 2 | #47 | TS sf.forget streaming | pending | depends on B.1 |
| C.1 | 1 | #57 | Dossier-draft generate-then-classify split | dispatched | agent a9c2e282 (worktree) |
| C.2 | 2 | #58 | Stale-dossier reverse-edge drift | pending | likely tiny after #57 |
| D.1 | 1 | #78 | Coverage caveat detector for typed_receiver_unresolved | dispatched | agent a37b95ea (worktree) |
| D.2 | 1 | #79 | Wild-corpus probe infrastructure | pending | NEEDS HUMAN: repo curation |
| D.3 | 1 | #80 | Test convention gate | dispatched | agent aac30deb (worktree) |
| D.4 | 1 | #81 | TS memory budget gate | dispatched | agent a7d76f3b (worktree) |
| D.5 | 1 | #52 | Tests included with kind=test tag | pending | NEEDS HUMAN: pick Option A/B/C |
| E.1 | 1 | #38-E | Stale-dossier corpus pass wired into regen | dispatched | agent ad5a3e39 (worktree) |
| E.2 | 1 | #38-G | Legacy field stripping in regen | pending | serialize after E.1 (regen.py conflict) |
| F.1 | 3 | #53 | Confidence taxonomy redesign | pending | run last; serializer |

**Lanes**:
- **A** (py extractor): `depgraph/extractors/python/extract.py`
- **B** (ts extractor): `depgraph/extractors/typescript/extract.ts`
- **C** (dossier): `depgraph/lib/cli/dossier.py`, `summarizer/`
- **D** (infra): independent surfaces, all parallel
- **E** (regen): `depgraph/lib/cli/regen.py`
- **F** (cross-cutting): schema + every edge emitter

## Verification queue (user-driven, fully parallel)

These have commits merged and await real-corpus verification. The loop
does NOT touch these. The user closes them after running the corpus.

| Issue | Commit | What to verify |
|---|---|---|
| #55 | cb0d2eb | Coverage caveats stamped on regen'd corpus |
| #56 | 28baf60 | Dossiers render `## Dependencies` section |
| #59 | cbeafd1 | summarizer/openai tests green |
| #60 | 8b875bd | `depgraph regen --repo-key X` (no `--repo-path`) succeeds |
| #38 (A) | f558769 | `embeddings.{bin,jsonl}` written on regen |
| #38 (B) | c9e79fa | File-orphan nodes archived |
| #38 (C+H) | d32034a | Domain-orphan nodes archived via manifests |
| #38 (D) | 2cc2434 | Missing dossiers stubbed to unreviewed |
| #38 (F) | 0b4a65c | Cross-repo route_call → endpoint edges present |

---

## Tasks

Each task block below is self-contained. Copy the "Agent prompt" into a
new background Agent invocation. The agent runs autonomously and
commits its work with `Refs #<N>`.

### A.1 — #83: py-extractor edge cases

**Files**: `depgraph/extractors/python/extract.py`, `depgraph/tests/extractors/test_python_edges.py`, fixtures under `depgraph/tests/extractors/fixtures/edges_py/`

**Scope (4 sub-items, one commit covering all 4)**:
1. Walrus operator: `db := Session()` in conditions. Update `_attach_call_edges` to also visit `ast.NamedExpr` for var_types seeding.
2. Vararg/kwarg annotations: include `fn_node.args.vararg` and `fn_node.args.kwarg` in the annotation walk so `*conns: Connection` seeds.
3. Multi-level attribute bases: `class X(a.b.Class)`. Extend the attribute-shape pre-check in `_attach_inheritance_edges` to handle nested `Attribute(Attribute(...), attr)`.
4. Extends to builtin (`class X(list)`): apply the same `_BUILTIN_CLASS_NAMES` recognition used in `_annotation_class_ids` inside `_attach_inheritance_edges`.

**Acceptance**:
- One new fixture per sub-item under `fixtures/edges_py/`.
- One test per sub-item asserting the expected edge target + confidence.
- Full suite still passes (`pytest -q`).
- Commit message ends with `Refs #83`. Do NOT use `Closes/Fixes/Resolves`.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement the four sub-items of issue #83. Read the issue body
with `gh issue view 83` for full context.

Constraints:
- Only modify depgraph/extractors/python/extract.py and files under
  depgraph/tests/extractors/. Do not touch other files.
- Bump EXTRACTOR_TAG (current value @2026-05-20c → @2026-05-20d).
- Use generic placeholders in fixtures (no SQLAlchemy/FastAPI/concorda
  names; use Account/Membership/Order shapes).
- Commit message: `Refs #83` (no Closes/Fixes).
- Run `.venv/bin/pytest -q` and confirm green before committing.
- ONE commit covering all four sub-items.

If you hit a design decision that's not in the issue body, document
your call in the commit body and continue — do not abort.
```

### A.2 — #54: SQLAlchemy ORM extractor

**Files**: `depgraph/extractors/python/extract.py` (new pass), schema (new edge kinds), tests + fixtures.

**Scope**: New `_attach_orm_edges` pass that walks SQLAlchemy model classes and emits:
- `references_orm` edges from `relationship("Boat", ...)` and `relationship(Boat, ...)` calls.
- `references_table` edges from `ForeignKey("table.col")` arguments.

**Acceptance**:
- New edge kinds added to `node.schema.json` if schema enforces enum.
- `tablename_to_class_id` and `classname_to_id` indexes built once at pass start.
- Inheritance check uses the existing transitive-extends resolver from #50.
- Fixtures: small SQLAlchemy-shape models (use Account/Membership/Order with `__tablename__`, `relationship()`, `ForeignKey()`).
- Tests pin: direct `relationship(Cls)`, string `relationship("Cls")`, `ForeignKey("table.col")`.
- Full suite green.
- Commit: `Refs #54`.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement issue #54 (SQLAlchemy ORM extractor). Read the issue
body with `gh issue view 54` for the design discussion.

Constraints:
- Add a new pass `_attach_orm_edges` to depgraph/extractors/python/extract.py.
  Wire it into `extract_repo` AFTER the existing L2 passes so the
  imports table, classes index, and extends resolver are populated.
- Detect SQLAlchemy bases (`DeclarativeBase`, `Base` via
  `declarative_base()`, `MappedAsDataclass`) by walking the transitive
  extends graph. Reuse the same detector code used by the coverage-
  caveat detector in lib/coverage_caveats.py if it's exported; if not,
  read its logic and either extract or reproduce.
- Fixtures: generic Account/Membership/Order shapes. No SQLAlchemy-
  specific package names in tests beyond what's needed.
- Bump EXTRACTOR_TAG.
- Commit: `Refs #54` (no Closes/Fixes).
- Run `.venv/bin/pytest -q` before committing.

If a schema change is needed (new edge kinds in node.schema.json), make
that part of the same commit and update existing schema tests.

If the design has ambiguity, make a call and document in the commit body.
```

### A.3 — #45: non-deterministic structural_hash

**Files**: `depgraph/extractors/python/canonical.py` (likely), `depgraph/tests/test_regen_determinism.py`.

**Scope**: Identify what's non-deterministic in `structural_hash`. Likely sources: set iteration, dict order from non-stable source, unsorted edges. Fix the source, add a determinism gate that exercises the previously-failing shape.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: investigate and fix issue #45. Read `gh issue view 45`.

Approach:
1. Try to reproduce: write a small probe that extracts the same fixture
   twice with mismatched PYTHONHASHSEED and diffs structural_hash
   values per primitive.
2. If no diff appears in the framework's own fixtures, run against a
   real-world Python repo or augment the realistic-Python fixture
   already at depgraph/tests/test_regen_determinism.py.
3. If repro found: locate the order-dependent code path (likely sets,
   dict iteration, or unsorted edges). Fix it. Add a determinism gate
   that exercises the specific shape.
4. If no repro after a reasonable probe: extend the determinism gate
   with more comprehensive shapes (multi-decorator-arg, classvar,
   dataclass field default factories) and document the
   non-reproducibility in the commit body. The issue stays open as a
   catch-net.

Constraints:
- Commit: `Refs #45` (no Closes/Fixes).
- Run `.venv/bin/pytest -q` before committing.
```

### B.1 — #82: TS scope shadowing in reads/assigns

**Files**: `depgraph/extractors/typescript/extract.ts`, `depgraph/tests/extractors/test_typescript_edges.py`, fixtures.

**Scope**: Track a scope stack as `forEachDescendant` walks. Before emitting reads against `localVars`, check if the name is bound in an enclosing function/block scope; if so, the body reference is to the local, not the module var.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement issue #82 (TS scope shadowing). Read `gh issue view 82`.

Approach:
- Inside attachCallAndVarAccessEdges, maintain a stack of binding sets
  as forEachDescendant enters/leaves function-like nodes.
- Push a new scope on FunctionDeclaration / MethodDeclaration /
  ArrowFunction / Constructor / GetAccessor / SetAccessor enter.
- Collect parameter names + local const/let/var declarations into the
  current scope's binding set.
- When emitting a read against a module-scope var, walk the stack;
  if any frame has the name bound, skip (it's a local read).

Alternative: ts-morph's getSymbol().getDeclarations() can resolve scope
authoritatively. Slower but accurate. Pick whichever is cleaner.

Constraints:
- Only modify depgraph/extractors/typescript/extract.ts and TS test
  files. No other languages touched.
- Add at least 2 tests: parameter-shadow (declaration + body reads
  correctly handled) and destructure-shadow.
- Commit: `Refs #82` (no Closes/Fixes).
- Run `.venv/bin/pytest depgraph/tests/extractors/test_typescript_edges.py -q`
  and full suite before committing.
```

### B.2 — #47: TS sf.forget streaming

**Files**: `depgraph/extractors/typescript/extract.ts` (large refactor).

**Scope**: Architectural rewrite. L1 extracts primitives + per-file metadata then calls `sf.forget()`; L2 operates on metadata only, no AST. See issue body for constraints (path aliases, default-export chasing, type-name capture for method receivers).

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement issue #47 (TS sf.forget streaming). This is the largest
single task in the roadmap. Read `gh issue view 47` carefully — the
issue body lists three specific constraints to preserve.

Approach:
1. Define a per-file metadata schema (TypeScript interface) capturing
   everything L2 needs: imports by binding, re-exports (named +
   wildcard + default), class extends/implements names, call sites by
   callee name, identifier-read sites, parameter type-name strings,
   initializer type-name strings.
2. L1 pass: for each sf, extract primitives + populate the metadata
   record, then sf.forget().
3. L2 passes: rewrite to consume metadata + primitive list. No
   ts-morph Node access.
4. tsconfig path-alias resolution: do up-front before forgetting files,
   capture resolved specifiers in the metadata.

Constraints:
- Strict behavior-preservation: codegraph regen must produce a
  byte-identical corpus (modulo generated_at timestamp). If you have
  access to ~/target-knowledge-graph, regen there and diff against a
  snapshot taken before the change.
- All existing TS tests pass.
- Commit: `Refs #47` (no Closes/Fixes).

If you hit a design decision that requires choosing between
preservation and cleanup, default to preservation — file a separate
issue for the cleanup.
```

### C.1 — #57: Dossier-draft generate-then-classify split

**Files**: `depgraph/lib/cli/dossier.py`, `depgraph/lib/summarizer/agent.py`, tests.

**Scope**: Split the single-pass agentic loop into Pass A (structural classifier — produces JSON-shaped facts) and Pass B (prose pass — consumes the JSON and writes prose). See issue body.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement issue #57 (dossier-draft split). Read `gh issue view 57`
for the design.

Approach:
1. Define the Pass A output JSON shape (the issue body has a draft).
2. Implement Pass A as a tool-restricted LLM call (or a rule-based
   classifier where deterministic). Coverage caveats / node_kind /
   salient edges are all amenable to rule-based + cheap-LLM.
3. Implement Pass B as a prose-drafting call that takes the Pass A
   JSON + node grounding, no tool calls. Use structured outputs if
   the model supports them.
4. Update cmd_dossier_draft to call A then B.

Constraints:
- Tests update to cover both passes independently.
- Commit: `Refs #57` (no Closes/Fixes).
- This is the largest dossier-side change. If it gets too sprawling,
  commit Pass A first (Refs #57) and Pass B as a follow-up commit.

If a design ambiguity in the issue body needs a call (e.g., how to
encode the salient edges), make the call and document it.
```

### C.2 — #58: Stale-dossier reverse-edge drift

**Files**: `depgraph/lib/cli/dossier.py` (stale detection), possibly node schema.

**Scope**: Re-check after #57 lands. Option C from the issue body ("if #56's structural-only rendering takes care of edge-derived sections, stale-detection only needs to fire on prose sections — which are already gated by structural_hash") may make this trivial. Otherwise implement Option B (inbound-count drift threshold).

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: address issue #58 (stale-dossier reverse-edge drift). Read
`gh issue view 58` for the three options.

First step: check whether #56's structural-only `## External consumers`
and `## Dependencies` rendering is in place on disk. If those sections
are auto-rendered from current graph data, then Option C applies and
the prose-only stale-check is already correct — write a test that
confirms it and close out the issue.

If not (e.g., dossiers still bake prose text into the consumers
section), implement Option B: track inbound-edge count on the dossier,
flag drift ≥ N (suggest N=3) or ≥ 25% in dossier-rank.

Constraints:
- Commit: `Refs #58` (no Closes/Fixes).
- Test must verify the behavior (not just non-crash).
```

### D.1 — #78: Coverage caveat detector for typed_receiver_unresolved

**Files**: `depgraph/lib/coverage_caveats.py`, tests.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement the detector for issue #78. Read `gh issue view 78`.

Implementation:
- Add a detector function in depgraph/lib/coverage_caveats.py.
- Walk a primitive's edges_out; if any `via=method_call` edge has a
  target starting `external::unresolved::`, stamp
  `typed_receiver_unresolved` on the primitive.
- Wire it into the same `stamp_caveats` orchestration point as the
  existing detectors.

Constraints:
- Only modify lib/coverage_caveats.py and its tests.
- Tests: positive case (typed-receiver-unresolved present → stamped),
  negative (no method_call to unresolved → not stamped), no
  double-stamping if already present.
- Commit: `Refs #78` (no Closes/Fixes).
```

### D.2 — #79: Wild-corpus probe infrastructure

**Status**: NEEDS HUMAN — repo curation. Loop should SKIP this until
the user lists the repos to probe.

**Agent prompt** (do not auto-dispatch):
```
[Pending repo curation from user. Ask which repos to clone — small
SQLAlchemy/FastAPI app, Pydantic-heavy schema repo, deep-barrel
package, Next.js app. Need pinned commit shas + licenses.]
```

### D.3 — #80: Test convention gate

**Files**: new test file (e.g., `tests/test_extractor_test_location.py`).

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement the convention gate from issue #80. Read `gh issue view 80`.

Add a single test that asserts files matching extractor-shape names
(`test_extract*.py`, `test_python_*.py`, `test_typescript_*.py`) live
only under `depgraph/tests/extractors/`. Place the test in
`tests/test_extractor_test_location.py`.

Constraints:
- Single file; trivial diff.
- Commit: `Refs #80` (no Closes/Fixes).
```

### D.4 — #81: TS memory budget gate

**Files**: new test (e.g., `depgraph/tests/test_ts_memory_budget.py`), perhaps a fixture.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement the memory budget gate from issue #81. Read
`gh issue view 81`.

Approach:
- Add a pytest marker `@pytest.mark.memory_budget`.
- Test runs the TS extractor against `kitchen_sink` (or a similar
  fixture) under `/usr/bin/time -v`, parses max-resident-set-size, and
  asserts < 500 MB.
- Skip on platforms without GNU time (check for the binary first;
  pytest.skip if not available).

Constraints:
- Single test file.
- Commit: `Refs #81` (no Closes/Fixes).

If the kitchen_sink fixture is too small to be meaningful for memory
testing, create a new larger fixture with ~50 files of mixed TS
shapes.
```

### D.5 — #52: Tests included with kind=test tag

**Status**: NEEDS HUMAN — design decision (Option A vs B vs C in the
issue body). Loop should SKIP this until the user picks an option.

**Agent prompt** (do not auto-dispatch):
```
[Pending design decision: which option from issue #52 (A: kind=test
tag, B: separate test corpus, C: test_coverage.json index)?]
```

### E.1 — #38-E: Stale-dossier corpus pass wired into regen

**Files**: `depgraph/lib/cli/regen.py`, possibly `reconcile.py` (lift the existing function), tests.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: implement #38-E (stale-dossier corpus pass). Read `gh issue view 38`
for the umbrella context — sub-item E specifically.

Approach:
- The function `detect_stale_dossiers` exists in reconcile.py but has
  zero callers outside reconcile.py itself. Wire it into
  `_run_v2_pipeline` after stub_missing_dossiers (the path landed in
  commit 2cc2434).
- The function may need adaptation to operate on the live
  `all_primitives` list rather than walking disk; check what it takes
  today.

Constraints:
- Add a test that confirms the pass runs and stamps stale state.
- Commit: `Refs #38` (mention sub-item E in the body; no Closes/Fixes).
```

### E.2 — #38-G: Legacy field stripping

**Files**: `depgraph/lib/cli/regen.py` or reconcile.py.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: address #38-G (legacy field stripping). Read `gh issue view 38`
for context; sub-item G specifically.

First step: check whether commit fac7c0b already folded this in (its
body mentions "hygiene: align reconcile filename, dedupe dossier_state,
fix orphan archive collisions" — overlap is possible). If yes, mark
the issue's G sub-item done with a comment pointing at fac7c0b and
exit without commit.

Otherwise: lift `strip_legacy_fields` into _run_v2_pipeline as a small
finalization step.

Constraints:
- Commit (if needed): `Refs #38` (mention sub-item G; no Closes/Fixes).
```

### F.1 — #53: Confidence taxonomy redesign

**Status**: Wave 3. Do not dispatch until Lane A and Lane B finish.

**Files**: `node.schema.json`, every edge emitter in both extractors,
the unresolved-stats reporting, dossier rendering of confidence
labels.

**Agent prompt** (Wave 3 only):
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: redesign the confidence taxonomy per issue #53. Read
`gh issue view 53` and the discussion comments.

Approach: discuss with the user before dispatching. This is the only
cross-cutting change and benefits from a design pass with human input.
Do NOT auto-implement.
```

---

## Loop status log

(The loop appends one line per firing here with timestamp + what it
dispatched / completed.)

- 2026-05-20 — roadmap created; loop ready to start
- 2026-05-20 — Wave 1 firing 1: dispatched 7 agents in parallel with worktree isolation
  - A.1 #83, B.1 #82, C.1 #57, D.1 #78, D.3 #80, D.4 #81, E.1 #38-E
  - Skipped: D.2 #79 (NEEDS HUMAN), D.5 #52 (NEEDS HUMAN), E.2 #38-G (E lane conflict)
  - Awaiting agent completion notifications
