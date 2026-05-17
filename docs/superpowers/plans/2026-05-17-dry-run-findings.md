# Concorda dry-run findings — session boundary doc

**Date:** 2026-05-17
**Session HEAD:** `b56ec429` (Phase 6 safe set complete; pushed to origin/main)
**Dry-run scratch dir:** `/tmp/tmp.SuLy8xQyrn` (preserved for re-inspection)

## Status: REJECT — do not proceed to Task 6.6

The dry-run protocol caught three real problems that would have made the regenerated corpus strictly worse than the current v1. Fix-then-re-run before Task 6.6.

## What's complete

**Phases 0–5 + Phase 6 safe set on origin/main.**

- Phase 0: Foundation — primitives, edges, registry, verification logs, wild-corpus scaffold (11 commits)
- Phase 1: TS primitives — 8 wild fixtures, 40 tests (9 commits)
- Phase 2: Python primitives — 8 wild fixtures, 25 tests (5 commits)
- Phase 3: L2 edges — 9 wild fixtures, all edge kinds incl. intra-function type binding (9 commits)
- Phase 4: SQL pipeline — 8 wild fixtures, parser/migration/reconcile/cross-ref/db_access (8 commits)
- Phase 5: Classification — 8 wild fixtures, 7 classifiers + writer (9 commits)
- 3 Concorda blockers fixed: absolute imports, property getter/setter, inline FK syntax (3 commits)
- Phase 6 safe set: graphui compat, reconcile rewrite + regen CLI, kitchen-sink E2E gate (caught 5 framework bugs), determinism CI gate (4 commits)
- 3 doc/plan commits: broken-tests cleanup, known-limitations-v0.md, plan corrections (3 commits)

**v2 test suite:** 239 passed, 4 properly skipped, 0 failing.
**Total commits this rewrite:** 61, all pushed.

## What's left (Phase 6 cutover)

In the corrected order:

1. **6.5.5** (this task) — Concorda dry-run. **REJECTED.** Fix the 3 concerns below before re-running.
2. **6.4** — Migrate Concorda's `~/concorda-knowledge-graph/depgraph/project.toml` to v2 shape (currently v1 with `extractor=` and `detectors=` per-repo blocks).
3. **6.6** — Regen Concorda's corpus. Destructive but reversible via backup.
4. **6.2** — Update `depgraph/hooks/pre_edit_inject.py` for v2 schema reads. Must happen AFTER 6.6 (otherwise the script reads v1 corpus with v2 logic → empty injection).
5. **6.3** — Delete legacy extractors at `depgraph/extractors/generic/`. After 6.2 confirmed working.
6. **6.8** — Logigraph claim migration. Auto-rewrite via the name-match script; expect bulk of Concorda's claims to land in `CANDIDATES.md` for review.

## Dry-run findings (3 critical + 1 minor)

### Concern 1: Variable-SQL migrations not parsed (CRITICAL)

**Symptom:** 27 of ~60 expected schema tables are missing from the corpus. Final count: 33 schemas vs expected 50–70.

**Root cause:** `depgraph/lib/sql/migration.py::_extract_string` only handles literal-string arguments to `text(...)`. Concorda's largest migration `040_schema_redesign.py` (and probably others) stores SQL strings in a dict keyed by table name:

```python
TABLES = {
    "persons": "CREATE TABLE persons (id ... )",
    "boats":   "CREATE TABLE boats (id ... )",
    ...
}

def migrate():
    for tname, ddl in TABLES.items():
        conn.execute(text(ddl))   # ← text() arg is a variable, not a literal
```

`_extract_string(ast.Name("ddl"))` returns `("", "non-literal SQL expression")` and emits a warning instead of parsing.

**Impact:** affected tables include `persons`, `boats`, `organizations`, `person_auth`, `contracts`, `events`, `auth_tokens`, plus ~20 others. **Cascades into Concern 2.**

**Fix approach (medium complexity):**

In `_extract_string` (or a new pre-pass in `extract_migration`), build a per-file map of `{var_name: literal_value}` for top-level `Assign` statements whose RHS is a string literal or a string-literal dict. Then when `text(name)` is encountered, look up the name in that map and parse the literal.

For the dict-keyed pattern, also recognize iteration: `for k, ddl in TABLES.items(): conn.execute(text(ddl))` — walk the for-loop's iterable (`TABLES`) back to the literal dict and parse each value.

A conservative v0 fix: handle simple `var = "literal"` followed by `text(var)`. Document the dict-iteration pattern as deferred (would need flow-aware analysis to follow the loop binding).

Even the simple fix would catch many migrations.

### Concern 2: Cascade — 35 models lose classification (CRITICAL, downstream of #1)

**Symptom:** Model classifier expects both ORM-base `extends` edge AND `references→schema` via `__tablename__`. The 35 model classes whose tables are missing (from Concern 1) appear in the corpus as bare `<class>` primitives.

**Examples missed:** `Boat`, `Person`, `Organization`, `PersonAuth`, `Event`, `Contract`, ...

**Impact:** any rule or query that depends on `kind == "model"` will miss these. db_access edges originating from `session.query(Boat)` etc. land as `unresolved` because the cross-ref chain breaks at the missing schema.

**Fix:** automatic once Concern 1 is fixed. No standalone work.

### Concern 3: concorda-web entirely absent — TS extractor OOM (CRITICAL)

**Symptom:** Zero components, zero hooks, zero TS primitives from `concorda-web` (which has 276 source files in `src/`). The TS extractor crashed with exit code 134 (SIGABRT) during the regen.

**Root cause:** Node.js default heap (~2GB) exhausted by ts-morph's Project loading 276 files at once.

**Fix approach (5-minute, trivial):**

In `depgraph/lib/cli/regen.py`, change the TS subprocess invocation to set Node's max-old-space-size higher:

```python
# Before:
proc = subprocess.run(
    ["npx", "tsx", str(extractor), ...],
    ...
)

# After:
env = os.environ.copy()
env["NODE_OPTIONS"] = "--max-old-space-size=4096"
proc = subprocess.run(
    ["npx", "tsx", str(extractor), ...],
    env=env,
    ...
)
```

Or pass the flag explicitly: `["node", "--max-old-space-size=4096", str(npx_tsx_bin), str(extractor), ...]`.

If 4GB still OOMs (unlikely for 276 files but possible if ts-morph is doing aggressive resolution), bump to 8GB. Document in regen.py's docstring as the production heap limit.

### Concern 4: include_paths / exclude_paths not enforced (MINOR)

**Symptom:** 267 test primitives from `concorda-api/tests/` appear in the corpus despite `exclude_paths = ["**/tests/**"]` in the project.toml.

**Root cause:** `depgraph/lib/cli/regen.py::_extract_python` doesn't pass `include_paths`/`exclude_paths` from the repo config into `extract_repo`. The Python extractor's `_iter_py_files` only filters out hardcoded `__pycache__`, `.venv`, `venv`, `node_modules`.

**Impact:** corpus has 267 extra primitives but they're not incorrect, just unneeded. They classify correctly (`kind=test`). Lower priority.

**Fix:** thread `include_paths`/`exclude_paths` from project.toml through `_extract_python` to `extract_repo` to `_iter_py_files`. Use `fnmatch` against rel-path to apply.

## Spot-check results — structurally sound where extraction succeeded

What DID get extracted is correct:

- **Schema `regattas`**: kind=schema, primary_key + indexes in signature, defined_by paths captured ✓
- **Model `AccountSetupToken`**: references→schema via `__tablename__`, all column defines edges ✓
- **Endpoint `list_series_races`**: 12 calls edges including resolved service target, route decorator captured ✓
- **Service `pending_policies_for`**: db_access edges present (though many unresolved due to method-call resolution gaps documented in known-limitations-v0.md)

The per-classifier logic is sound. The dry-run gaps are coverage gaps in extraction, not classification bugs.

## Resume instructions for next session

1. **Confirm state** — `git log --oneline -5` should show `b56ec429` as origin/main HEAD. Phase 6 safe set is the most recent batch.

2. **Fix order** (do all three, then re-run dry-run):
   - First: Concern 3 (TS heap limit) — 5 minutes. Highest leverage per unit of effort.
   - Second: Concern 1 (variable-SQL extraction) — 30–60 minutes. Most consequential fix.
   - Third: Concern 4 (include_paths plumbing) — 15 minutes. Cleanest corpus.

3. **Re-run dry-run** (Task 6.5.5) with `depgraph/venv/bin/python -m kg.cli depgraph regen --data-dir $SCRATCH/depgraph --project-toml $SCRATCH/project.toml`. Same audit script. Re-verify ranges.

4. **Decide accept/reject again.** If accept → proceed Task 6.4 → 6.6 → 6.2 → 6.3 → 6.8.

5. **Existing scratch** at `/tmp/tmp.SuLy8xQyrn` may have been cleared by reboots; if not, the regen.log there has the full trace.

## What's known to be working

- The wild corpus (~40 fixtures across 5 phases + kitchen sink) is the gate. All wild tests pass.
- The kitchen-sink end-to-end test (Task 6.5) regens a 30-file synthetic project and exercises the full pipeline. Surfaced 5 framework bugs during authoring; all fixed.
- The determinism CI gate (Task 6.7) runs regen twice on a tiny project and asserts byte-identical output (with a documented `_meta.json` timestamp normalization — non-determinism that the gate filters out; cleanup TODO).
- The hook architecture is understood (kg/hook.py orchestrator routes file→graph→subsystem inject script). Phase 6.2 only needs to update the inject script's data reads, not the orchestrator.
- All 3 pre-cutover Concorda blockers were fixed: absolute imports, property getter/setter, inline column FK.

## What's known to be broken / pinned

Per `docs/superpowers/known-limitations-v0.md` — 13 v0 pinned behaviors covering edge cases in TS (constructor params, JSX over-detection, HOC wrapping, method generics), Python (function-local defs, if-name-main, walrus/match), edge resolution (chained calls, dynamic dispatch, monkey-patch, decorator-body-walk noise, conditional rebinding), SQL (Alembic op-style, standalone .sql), classification (endpoint+service no-conflict, hook one-hop).

The dry-run added 3 more (variable-SQL, TS OOM, include_paths) which are NOT in known-limitations-v0.md because they're real bugs to fix, not acceptable v0 gaps.

## Where things live

- Plan: `docs/superpowers/plans/2026-05-16-depgraph-extractor-rewrite.md` (~8400 lines)
- Spec: `docs/superpowers/specs/2026-05-15-layered-substrate-design.md`
- Limitations doc: `docs/superpowers/known-limitations-v0.md`
- This findings doc: `docs/superpowers/plans/2026-05-17-dry-run-findings.md`
- New code: `depgraph/lib/{primitives,edges,language_registry,sql/*,classification/*,system_stub/*,cli/regen.py}.py`, `depgraph/extractors/{typescript,python,sql}/`
- New tests: `depgraph/tests/{lib/*,extractors/test_*_primitives.py,extractors/test_*_edges.py,extractors/test_*_wild.py,extractors/test_python_pipeline.py,test_reconcile_v2.py,test_kitchen_sink.py,test_regen_determinism.py}`
- Wild corpus: `depgraph/tests/fixtures/wild/{primitives_ts,primitives_py,edges,sql,classification,kitchen_sink}/`
- Verification logs: `depgraph/tests/verification_logs/` (5 component-level logs from Phase 0.6)

## Session metrics

- 61 commits this rewrite (all pushed)
- 239 v2 tests passing
- 13 pinned v0 limitations documented
- 5 framework bugs caught by kitchen-sink + 3 by dry-run (8 real defects found by verification protocols)
- 4 review rounds (audit + 3 followup rounds) with self-generated churn acknowledged mid-session
- 1 plan misreading caught + corrected (Phase 6.2 hook architecture)
