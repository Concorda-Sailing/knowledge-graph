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
| A.1 | 1 | #83 | py-extractor edge cases (walrus, vararg, multi-attr, builtin extends) | [x] | 0017cea |
| A.2 | 2 | #54 | SQLAlchemy ORM extractor | [x] | c47e3b4 |
| A.3 | 2 | #45 | non-deterministic structural_hash | [x] | 93b5b6c (no repro found; expanded determinism gate as catch-net) |
| B.1 | 1 | #82 | TS scope shadowing in reads/assigns | [x] | 1c01ec0 (merged w/ 9a6a93f) |
| B.2 | 2 | #47 | TS sf.forget streaming | [x] | 473305e (architectural; byte-identical output verified) |
| C.1 | 1 | #57 | Dossier-draft generate-then-classify split | [x] | 0887b89 + ea3c2c2 (signature fix) |
| C.2 | 2 | #58 | Stale-dossier reverse-edge drift | [x] | 1d011c4 (Option B: inbound-count drift) |
| D.1 | 1 | #78 | Coverage caveat detector for typed_receiver_unresolved | [x] | 6b2c429 |
| D.2 | 1 | #79 | Wild-corpus probe infrastructure | [x] | cf5bcc1 (5 targets curated; probe surfaced 4 new bugs → #84/85/86/87) |
| D.3 | 1 | #80 | Test convention gate | [x] | 677695b (rename + gate in one) |
| D.4 | 1 | #81 | TS memory budget gate | [x] | 83f4c39 |
| D.5 | 1 | #52 | Tests included with kind=test tag | pending | NEEDS HUMAN: pick Option A/B/C |
| E.1 | 1 | #38-E | Stale-dossier corpus pass wired into regen | [x] | 0bf9be2 |
| E.2 | 1 | #38-G | Legacy field stripping in regen | [x] | 9e74e6b |
| F.1 | 3 | #53 | Confidence taxonomy redesign | pending | run last; serializer |
| A.4 | 3 | #84 | SQLModel-style ORM detection (gap in c47e3b4) | pending | wild-probe target: tiangolo-sqlmodel |
| B.3 | 3 | #85 | TS default-export expressions create orphan imports | pending | wild-probe target: colinhacks-zod |
| B.4 | 3 | #86 | TS `extends` to variable-kind violates taxonomy | pending | serialize after B.3; wild-probe target: colinhacks-zod |
| D.6 | 3 | #87 | Slug helper collisions on `/` vs `-` (and `::$` suffix) | pending | wild-probe target: colinhacks-zod |

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
- 2026-05-20 — Wave 1 complete: all 7 agents returned + cherry-picked + tests green
  - D.3 came back uncommitted (real offender found); merged + 677695b
  - B.1 conflicts with prior 9a6a93f tests; merged scope-tracking + name-slot guard
  - C.1 needed test signature fix (agent base predated #55/#56 kwargs); ea3c2c2
  - Full suite: 1114 passed, 4 skipped (was 1071 — +43 net new tests)
  - Wave 2 unblocked: A.2 #54, A.3 #45, B.2 #47, C.2 #58. Plus E.2 #38-G (E.1 done).
- 2026-05-20 — Wave 2 firing 1: dispatched 4 agents
  - A.2 #54 SQLAlchemy ORM, B.2 #47 TS sf.forget, C.2 #58 stale-dossier, E.2 #38-G
  - Deferred A.3 #45 (might overlap A.2 on canonical.py)
  - Each agent prompt now starts with a `git reset --hard main` step
    to avoid the "old base" issue that bit several Wave 1 agents
- 2026-05-20 — Wave 2 firing 2: A.2 returned safely; dispatched A.3 (canonical.py-only)
- 2026-05-20 — Wave 2 complete: all 5 issues landed
  - E.2 #38-G (9e74e6b), A.2 #54 (c47e3b4), C.2 #58 (1d011c4 Option B),
    A.3 #45 (93b5b6c — no repro), B.2 #47 (473305e architectural)
  - All cherry-picks clean (no merge conflicts in Wave 2)
  - Wave 3 unblocked: F.1 #53 (confidence taxonomy redesign — needs human design)
  - Pending human: D.2 #79 (wild-probe repo curation), D.5 #52 (kind=test option)
- 2026-05-21 — D.2 #79 wild-probe shipped (cf5bcc1)
  - 5 curated targets: encode-databases, pallets-click, tiangolo-sqlmodel,
    pydantic-pydantic-settings, colinhacks-zod
  - Probe runs end-to-end in ~12s across all 5; surfaces anomalies
    against real-corpus shapes the synthetic fixtures don't cover
  - 4 NEW bugs filed from the first run:
    - #84 SQLModel-style metaclass ORM bases not detected (gap in c47e3b4)
    - #85 TS default-export expressions create orphan import edges (gap in #47)
    - #86 TS `extends` to variable-kind target violates edge taxonomy
    - #87 Slug helper collides on `/` vs `-` paths
  - #53 confirmed empirically: 0 fuzzy edges across 4/5 targets
    (the one exception, zod, has 290 fuzzy edges — TS's re-export
    resolver uses fuzzy for barrel chains; Python never emits any)
- 2026-05-22 — Wave 3 dispatched: A.4 #84, B.3 #85, B.4 #86 (serial after B.3), D.6 #87
  - All four fixes verify against the wild-probe target that surfaced them
  - Synthetic pin fixtures added alongside the corpus verification

---

## Wave 3 task blocks

### A.4 — #84: SQLModel-style ORM base detection

**Files**: `depgraph/lib/coverage_caveats.py` (or wherever `is_sqlalchemy_model` lives), `depgraph/extractors/python/extract.py` (the `_attach_orm_edges` pass from c47e3b4), tests + fixtures.

**Scope**: `is_sqlalchemy_model` only matches a fixed `_SQLA_BASE_NAMES` set; SQLModel routes inheritance through a metaclass (`SQLModelMetaclass(ModelMetaclass, DeclarativeMeta)`) and never extends a name in that set, so the ORM extractor no-ops on SQLModel codebases. Land Option (2) from the issue body: also treat any class whose body assigns `__tablename__ = "..."` as an ORM model — a class-body signal, independent of base hierarchy. Add `SQLModel` to `_SQLA_BASE_NAMES` as belt-and-suspenders.

**Acceptance**:
- Synthetic pin fixture under `depgraph/tests/fixtures/wild/` (or extractor test fixtures) covering: a metaclass-only base (no `_SQLA_BASE_NAMES` match) that declares `__tablename__` and `relationship()` calls → `references_orm` edges emit.
- Wild-probe verification: `python tools/wild-probe/probe.py tiangolo-sqlmodel` no longer reports `#54 expected: sqlalchemy-orm target has 0 references_orm edges`; `references_orm` edge count > 0 on that target.
- Full suite green.
- Commit message ends with `Refs #84` (NOT `Closes/Fixes/Resolves` — see [[feedback-no-auto-close-issues]]).
- Generic placeholders in fixtures — Account/Membership/Order shapes, no consumer-project names ([[feedback-no-source-names-in-fixes]]).

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: fix issue #84 (SQLModel-style ORM bases not detected). Read
the issue body with `gh issue view 84` for full context.

Start: `git reset --hard origin/main` then `git pull --ff-only` is
NOT needed — your base is the local main (38 commits ahead of origin).
DO NOT reset to origin/main; you'll lose all the unpushed work.
Instead, `git status` should already be clean.

Constraints:
- Land Option 2 from the issue: detect `__tablename__` in class body
  as the ORM signal, in addition to the base-name check. Add
  `SQLModel` to `_SQLA_BASE_NAMES` belt-and-suspenders.
- Add a synthetic pin fixture (metaclass-only base, no _SQLA_BASE_NAMES
  hit, declares __tablename__) under the extractor tests.
- Verify against the wild corpus: run
  `.venv/bin/python tools/wild-probe/probe.py tiangolo-sqlmodel`
  and confirm references_orm count goes from 0 to > 0. Save the new
  results JSON; it lives under tools/wild-probe/results/.
- Bump EXTRACTOR_TAG in extract.py (current @2026-05-20e → @2026-05-22a).
- Generic Account/Membership/Order shapes in fixtures (no real project
  names).
- Commit message ends with `Refs #84` only — NO Closes/Fixes/Resolves.
- Run `.venv/bin/pytest -q` and confirm green before committing.
- ONE commit covering all changes.

If you hit a design decision not in the issue body, document the call
in the commit body and continue.
```

### B.3 — #85: TS default-export orphan imports

**Files**: `depgraph/extractors/typescript/extract.ts` (primitive emission, L1), tests + fixtures.

**Scope**: When the extractor sees `export default <expression>` (not `export default class X` or `export default function f`), emit a synthetic `variable` primitive with id `<file>::default`, name `"default"`, and signature = expression text (truncated). For `export default class X {}` and `export default function f() {}`, the existing primitive stays but ALSO needs `<file>::default` resolvable — emit an alias primitive that points at the class/function id, or have the consumer's import edge target the named id directly via `defaultExportMap`.

**Acceptance**:
- Synthetic pin fixture: file with `export default defineConfig({...})` style + a consumer that imports it. Pin test asserts no orphan edge.
- Wild-probe verification: `python tools/wild-probe/probe.py colinhacks-zod` shows `orphan_edges` with `::default` suffix dropping to 0 (was 81).
- Full suite green; existing default-export tests unaffected.
- Commit ends with `Refs #85`.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: fix issue #85 (TS default-export expressions create orphan imports).
Read the issue body with `gh issue view 85`.

DO NOT git reset — you're on local main, 38 commits ahead of origin.
git status should already be clean.

Constraints:
- Modify ONLY depgraph/extractors/typescript/extract.ts and files
  under depgraph/tests/extractors/. Coordinate with B.4 (#86) by
  not touching the L2 attachInheritanceEdges code path — that's
  the next lane's territory.
- Emit a synthetic `variable` primitive at `<file>::default` whenever
  a module has `export default <expression>`. For `export default
  class X` / `export default function f` patterns, keep the named
  primitive and ALSO make `<file>::default` resolve (alias or
  duplicate primitive — your call, document in the commit body).
- Add a synthetic pin fixture: defineConfig-style default export +
  consumer importing it. Test asserts the import edge resolves.
- Verify against the wild corpus: run
  `.venv/bin/python tools/wild-probe/probe.py colinhacks-zod`
  and confirm orphan_edges with ::default drops from 81 → 0.
- Bump EXTRACTOR_TAG in extract.ts.
- Commit ends with `Refs #85` only — no Closes/Fixes.
- Run `.venv/bin/pytest -q` before committing.
- ONE commit.
```

### B.4 — #86: TS extends-to-variable taxonomy

**Files**: `depgraph/extractors/typescript/extract.ts` (L2 inheritance edge emission), `depgraph/lib/edges.py` (taxonomy rules possibly), tests + fixtures.

**Dependency**: Serialize AFTER B.3 lands (both touch extract.ts; running both at once risks merge conflict).

**Scope**: TS extractor emits `extends` edges without checking target kind. In zod's v4 layout, `ZodType` is a const (variable primitive), and v3's `class ZodString extends ZodType` triggers a taxonomy violation (107 in zod). Land "fuzzy extends": when the target primitive is a variable, emit `extends` with `confidence: "fuzzy"`, and update the reconcile validator to permit `confidence=fuzzy` `extends` against variable targets.

**Acceptance**:
- Synthetic pin fixture: `const Factory = makeBase(); class Child extends Factory {}` — pin asserts edge is `extends` confidence `fuzzy`.
- Wild-probe verification: `python tools/wild-probe/probe.py colinhacks-zod` shows `edge_errors` dropping from 107 → 0 (or close).
- Schema updated if needed; reconcile validator updated.
- Full suite green.
- Commit ends with `Refs #86`.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: fix issue #86 (TS extends emits variable-kind targets that
violate edge taxonomy). Read `gh issue view 86`.

DO NOT git reset — you're on local main, ahead of origin.

Constraints:
- Modify depgraph/extractors/typescript/extract.ts L2 inheritance
  edge emission to look up the resolved target id in the primitives
  index. If it's a `class`: emit extends as today. If it's a
  `variable`: emit extends with confidence="fuzzy".
- Update depgraph/lib/edges.py / reconcile validator to permit
  `extends` with `confidence=fuzzy` when target.kind == "variable".
- If the schema (node.schema.json) constrains confidence per edge
  kind, update it.
- Add synthetic pin fixture: const-factory class pattern.
- Verify against the wild corpus: `tools/wild-probe/probe.py
  colinhacks-zod`; edge_errors should drop from 107 → 0.
- Bump EXTRACTOR_TAG in extract.ts.
- Commit ends with `Refs #86` only.
- Run `.venv/bin/pytest -q` before committing.
- ONE commit.

External targets are already permitted at `confidence=unresolved` per
the issue body. This is the symmetric in-corpus case.
```

### D.6 — #87: Slug helper collisions

**Files**: wherever the slug helper lives (likely `depgraph/lib/slugs.py` or `depgraph/lib/io.py` — look it up), tests.

**Scope**: Slug helper collapses `/` and `-` both to `_`, and strips trailing non-alphanumeric (`module` vs `module::$` collide). Land Option 1 from the issue body: detect collision and append a short hash of the original id. Stable across regens, unique by construction. Also investigate Pattern 2 — what does the `::$` suffix mean upstream? If it's an extractor-generated sentinel that's safe to elide, the collision goes away naturally; if it's load-bearing, the slug helper must preserve it.

**Acceptance**:
- Synthetic pin fixture / test that constructs two distinct ids whose default slugs collide and asserts disambiguation produces distinct on-disk names.
- Wild-probe verification: `tools/wild-probe/probe.py colinhacks-zod`; slug_collisions drops from 10 → 0.
- Commit ends with `Refs #87`.

**Agent prompt**:
```
You are working on the knowledge-graph repo at ~/knowledge-graph.
Task: fix issue #87 (slug helper collisions). Read `gh issue view 87`.

DO NOT git reset — you're on local main, ahead of origin.

Constraints:
- Find the slug helper (grep for slug, slugify, _slug — likely in
  depgraph/lib/). Land Option 1 from the issue: detect collision at
  slug time, append a short stable hash of the original id when a
  slug already exists. Stable across regens, unique by construction.
- Investigate Pattern 2 (::$ suffix): grep the codebase for where
  ids with `::$` get generated. If it's a sentinel safe to elide
  before slugging, do so; if not, ensure the slug preserves it.
  Document your finding in the commit body.
- Add a synthetic test that constructs colliding ids (v4-mini vs
  v4/mini) and asserts the slug helper disambiguates.
- Verify against the wild corpus: `tools/wild-probe/probe.py
  colinhacks-zod`; slug_collisions drops from 10 → 0.
- Commit ends with `Refs #87` only.
- Run `.venv/bin/pytest -q` before committing.
- ONE commit.
```
