# Drift: How This System Lies to You

> A dependency graph is only useful if you trust it. It deserves trust only to the extent that it has a story for every realistic way it can be wrong.

This file enumerates every way the depgraph can become out of sync with reality, ordered roughly by how often each will happen and how much damage it can do. Each scenario specifies:

- **Symptom** — what the bad outcome looks like.
- **Detection** — how the system notices.
- **Mitigation** — how it recovers.
- **Residual risk** — what remains uncatchable.

The honest framing: structural drift is mostly mechanically catchable; intent drift (dossiers going stale) is not. The mitigations are layered so that the failure mode is always *loud*, even if it cannot always be auto-corrected.

> **Architecture-defect bookkeeping (current state):** The original architecture review listed 17 scenarios. As of now the following are addressed in code:
>
> - **#1 Truth/cache mixing** — `dependents` lives in `_index/dependents.json`, never on per-node files
> - **#2 Atomicity** — `_meta.regen_status` gates trust; per-file writes are tmp+rename
> - **#3 Edge confidence tier** — fuzzy and exact edges render in separate "Probable callers" / "Verified callers" blocks in the hook
> - **#4 Time leakage** — no `extracted_at` / `git_commit` on per-node files; corpus-level provenance lives in `_meta.json`
> - **#5 Extractor domain ownership** — each extractor writes a manifest of claimed ids; reconciler archives nodes whose extractor *did* run but didn't re-emit them
> - **#7 Schema versioning** — every node carries `schema_version: 1`; hook gates on it
> - **#8 Side-effect import** — `extract_api.py` is now pure-AST; no Stripe init, no DB connection, no startup hooks fire
> - **#11 Slug/id collisions** — web/expo/test ids are file-path-qualified (`<repo>::<file>::<symbol>`)
>
> Scenarios below were written before those fixes; the **Detection** and **Mitigation** notes still apply, but with stronger guarantees in some cases.

---

## 1. String-concatenated URLs across the HTTP boundary

**Symptom.** Web/Expo code does `fetch(\`/api/crew/${id}/invites\`)`. The extractor sees the template literal but cannot resolve `id`, so the call site is recorded as a `string_url` edge with `confidence: fuzzy`. If the route path changes from `/api/crew/{id}/invites` to `/api/boats/{id}/crew/invites`, the call site silently keeps pointing at a 404.

**Detection.**
- Extractor canonicalizes URLs by replacing `${...}` and `{}` segments with `*` wildcards, then matches against the FastAPI route table. Unresolvable URLs are recorded with a `warning: unresolved_string_url` and surface in the PreToolUse injection.
- `bin/depgraph orphans` lists endpoints whose `dependents` is empty *and* lists call sites whose target is not a known route — both are likely victims of route renames.

**Mitigation.** Edges are tagged `fuzzy` so I treat them as advisory; orphan check is a regular CI step.

**Residual risk.** A URL constructed from a fully-dynamic base (`fetch(buildUrl(resource, op))`) can defeat canonicalization. Mitigation: discourage this pattern; the few cases that need it should be wrapped in a typed helper that the extractor recognizes by name.

---

## 2. Endpoint renamed; old call sites still reference the old path

**Symptom.** Same as scenario 1 but in a deterministic form: handler renamed from `/api/crew/invites` to `/api/invites/crew`, and a literal call site still says `fetch("/api/crew/invites")`.

**Detection.** The endpoint node's `dependents` array drops the old call site (no route match). The call-site node now has an unresolvable target. Reconciler emits `warning: unresolved_call` for the call-site node and flags the endpoint as `dependents_dropped`.

**Mitigation.** Both warnings appear in the next PreToolUse injection on either file.

**Residual risk.** Low. Renames are mechanical and the warnings fire deterministically.

---

## 3. Response shape changed; route path stayed the same

**Symptom.** `GET /api/profile` still returns 200, but the response now has `display_name` instead of `displayName`. Call sites still link, dependents list is unchanged, *the graph looks healthy* — and every consumer is silently broken.

**Detection.** This is the headline scenario. Two layers:
1. **Structural hash.** The endpoint node's `structural_hash` is computed over the response Pydantic schema *and* the request body schema. Any field rename, addition, removal, or type change flips the hash. The dossier is auto-marked `status: stale` because `last_reviewed_against_hash` no longer matches.
2. **Schema-diff propagation.** Reconciler walks `dependents` and marks each consumer node with a `warning: upstream_schema_changed` referring back to the changed endpoint id. PreToolUse injection on the consumer surfaces the warning even if the consumer file itself didn't change.

**Mitigation.** Stale dossiers and propagated warnings are blockers — Claude is supposed to read the warning and walk the consumers before declaring the change done.

**Residual risk.** The structural hash is computed over *declared* schemas. If a handler returns an undeclared field (FastAPI lets you), the hash misses it. Mitigation: extractor warns on response models that are `dict`/`Any` rather than concrete Pydantic — those endpoints are flagged in their own node as `weakly_typed: true`, so I know to be extra careful.

---

## 4. Hook-on-hook composition; transitive dependents missed

**Symptom.** `useCrewInvites` calls `useCrewMembers`. Editing `useCrewMembers` should surface dependents of *both* hooks, since changing the inner hook can invalidate every component that uses the outer hook.

**Detection.** Reconciler computes a transitive closure of `dependents` up to depth 3 (configurable). The injection groups dependents by edge depth: "direct (1)" first, then "transitive (2)" with the path. Cycles short-circuit.

**Mitigation.** Depth cap of 3 keeps the injection from exploding for foundational hooks (the `apiClient` would otherwise pull half the codebase).

**Residual risk.** Depth-4+ effects are not surfaced. Acceptable for now; if a foundational change is being made, run `bin/depgraph dependents <id> --depth all` manually.

---

## 5. Tests that hit the API by URL, not import

**Symptom.** Playwright spec does `await page.request.post('/api/invite/abc/accept')`. The endpoint deletes; the spec keeps "running" but is now testing a 404 path it didn't intend.

**Detection.** Test extractor parses Playwright spec files for `request.<method>(...)` calls and `page.goto(...)` URLs, canonicalizes them, matches them against the route table. Unmatched URLs become `warning: test_targets_unknown_route` on the test node.

**Mitigation.** Endpoints get a `tests` array populated from the matched specs; deleting an endpoint while a test still names it produces an orphan warning.

**Residual risk.** Tests that build URLs at runtime from fixtures defeat static matching. Mitigation: project convention to keep URL literals in spec files where reasonable.

---

## 6. Generated code: migrations, OpenAPI clients

**Symptom.** Alembic migration references column `crew.invited_by_uuid`; column gets dropped from the model; migration still runs (it's a historical record of *past* state) but anyone reading the model thinks the column is gone — and a future migration referencing it as if it still exists slips through review.

**Detection.** Migration files are extracted as `kind: migration` nodes (a future addition; out of v1 scope). Each migration declares the columns/tables it touches, and the reconciler edges them to model nodes. Model deletions surface `dependents` in past migrations as informational, not blocking.

**Mitigation.** Out of v1 scope; flagged here so the schema accommodates it (`kind` enum is open to extension).

**Residual risk.** Until v2, migrations are not in the graph. Acceptable — Alembic linearity is well-understood and reviewed.

---

## 7. Dynamic dispatch and metaprogramming

**Symptom.** A FastAPI router uses `@router.api_route(path, methods=[m for m in METHODS if condition])`. Routes are real but invisible to a static walker.

**Detection.** Extractor records the router file as `extractor_warning: dynamic_routes_present` and the affected route is omitted with a `# (dynamic)` placeholder.

**Mitigation.** Project convention: avoid dynamic route registration. The few existing cases are documented in their dossier as `weakly_typed: true`.

**Residual risk.** A new dynamic pattern lands and we don't notice for weeks. Mitigation: extractor counts route definitions per file; a sudden drop relative to last extraction is flagged in the regen log.

---

## 8. Stale dossier prose

**Symptom.** Code changed; structural hash changed; dossier was auto-marked `stale` — but nobody updated it. Two months later a new edit reads the stale dossier and trusts it.

**Detection.** PreToolUse injection prepends `⚠ STALE DOSSIER (last reviewed against hash X, current hash Y)` to any stale body. CI check `bin/depgraph validate --strict` fails when nodes touched in the diff have stale dossiers.

**Mitigation.** Stale text is still useful — much of it is invariant — so we surface it with a banner rather than hiding it.

**Residual risk.** This is the system's softest spot. A stale dossier that is *subtly wrong* (an invariant that no longer holds) reads as authoritative. Only mitigation is the cultural rule: every edit that changes structural hash bumps the dossier in the same commit.

---

## 9. External consumers (mobile app builds in the wild)

**Symptom.** iOS app version 1.4.2 calls `POST /api/profile` with field `display_name`. We rename the field to `displayName`. Web is fine; current Expo dev build is fine; users on 1.4.2 break.

**Detection.** Out-of-band — the graph cannot prove a shipped binary is no longer in use.

**Mitigation.** Each endpoint dossier has an **External consumers** section (mirrored as `external_consumers` in node JSON). Endpoints with non-empty external consumers get a `⚠ EXTERNAL CONSUMERS PRESENT` banner in the PreToolUse injection. Schema-changing edits prompt: "do not break field names; add new fields and migrate over a release window."

**Residual risk.** Ultimately depends on the dossier being kept current. This is the trust-the-human edge.

---

## 10. Branch divergence

**Symptom.** Graph was last regenerated on `main`. Switch to feature branch with a new endpoint. PreToolUse on the new endpoint file finds no node. Worse: the call site of that new endpoint exists in a different file, and editing *that* file finds an old graph that still reflects `main`.

**Detection.** Each node records `git_commit` at extraction. If the current `git rev-parse HEAD` differs from the node's commit by more than N hours of history, PreToolUse prepends `⚠ GRAPH IS BEHIND BY <N> COMMITS` and includes a "regen suggested" hint.

**Mitigation.** Stop hook regenerates only touched files, so within a session the graph stays current. On branch switch, `bin/depgraph regen --since main` is a one-liner.

**Residual risk.** First edit on a fresh branch checkout is uncovered. Acceptable; the warning fires loudly.

---

## 11. Files moved or renamed

**Symptom.** `useInvites.ts` is moved from `hooks/` to `features/invites/hooks/`. Node JSON's `source.path` is now wrong; the next PreToolUse on the new path finds no node.

**Detection.** Extractor on the new path produces a node whose `id` matches an existing node (because `id` is `package::ExportedName`, location-independent). Reconciler detects the duplicate-id situation and merges, updating `source.path` rather than creating a second node.

**Mitigation.** Stable `id`s are exactly the design choice that prevents this from causing data loss. Dossier follows the node.

**Residual risk.** If both the file path *and* the export name change in the same commit, the merge logic cannot tell it's the same node. It produces a delete + create. Mitigation: preserve the old node in `_archive/` and let the dossier be reattached manually if needed.

---

## 12. New nodes that never get extracted

**Symptom.** I add a new hook in a session, hit Stop, but the extractor errors out (TypeScript compile error, broken import, syntax issue). New hook is not extracted. Future edits on its consumers don't see the new dependent.

**Detection.** Stop hook captures extractor exit code and surfaces extraction failures at end of turn. CI runs `bin/depgraph regen --all && git diff --exit-code nodes/` so a missing node fails build.

**Mitigation.** Loud failure on extraction error; CI catch.

**Residual risk.** A repo in a transient broken state during multi-step refactor will produce no new nodes for the duration. That's acceptable — the graph regen finishes when the code compiles.

---

## 13. Hook itself fails silently

**Symptom.** PreToolUse hook crashes; Claude receives no injection; edits proceed blind.

**Detection.** Hook wraps body in try/except and emits a structured error to stderr that surfaces as `additionalContext: "⚠ depgraph hook crashed: <error>; proceed with caution"`. Stop hook checks the session's PreToolUse log for any silent skips.

**Mitigation.** "Crash visible to Claude" is the bar. The hook is allowed to fail; it is not allowed to fail invisibly.

**Residual risk.** The hook is itself untracked code. Mitigation: hook has its own integration test (`bin/depgraph self-check`).

---

## 14. MultiEdit batching

**Symptom.** Single `MultiEdit` call edits 5 files. Without care, the hook injects context for only the first file.

**Detection.** Hook iterates over all `file_path` entries in the tool input and injects a single combined context block, deduplicated and ordered: shared dependencies once, per-file sections grouped.

**Mitigation.** Documented in `pre_edit_inject.py`. Batched edits are first-class.

**Residual risk.** None notable.

---

## 15. Endpoint deleted but node file lingers

**Symptom.** Route `@router.delete("/api/old-thing")` removed from code. Next regen sees the route is gone but doesn't remove the node JSON.

**Detection.** Reconciler runs a "live set" check: every node id should map to a real source symbol. Nodes whose `id` is not produced by any extractor in this run are marked `status: orphan`.

**Mitigation.** Orphan nodes do *not* auto-delete. They move to `nodes/_archive/<original-path>` with a tombstone field `archived_at`, `archived_reason: source_missing`. This preserves the dossier (often the only record of why the thing existed). `bin/depgraph orphans --purge` is the only path to actual deletion, and it is explicit.

**Residual risk.** If a route is *temporarily* gone (mid-rebase), it gets archived prematurely. Mitigation: rebase scenarios should run `bin/depgraph regen` only at clean checkpoints, not mid-conflict.

---

## 16. Cross-repo extractors disagree about node ids

**Symptom.** A test-repo Playwright spec hits `POST /api/invite/{code}/accept`. The test extractor creates an edge to `endpoint::POST::/api/invite/{code}/accept`. The api extractor produces `endpoint::POST::/api/invite/{invite_code}/accept` (different param name). They never link.

**Detection.** Reconciler normalizes path-param names to positional placeholders (`{0}`, `{1}`, …) before id matching. Both ids resolve to the same canonical form.

**Mitigation.** Built into reconciliation; tests are pinned to the same canonical schema.

**Residual risk.** A path-param semantic change (changing `{invite_code}` → `{boat_id}` because the route now means something different) is invisible at this level. The structural hash on the endpoint will change because the handler signature changed, which propagates through scenario 3.

---

## 17. The graph is wrong but Claude trusts it anyway

**Symptom.** The system is comprehensive enough that it feels authoritative. Claude makes a change based on a dependents list that turns out to be incomplete, and reports the work as done.

**Detection.** Cultural, not mechanical.

**Mitigation.** PROCESS.md states explicitly that the graph **reduces** blind spots, it does not make changes safe. Tests, code review, and walking the affected user flows remain non-negotiable. The injection block ends with a one-line reminder of this.

**Residual risk.** The whole system. Worth re-reading when something goes wrong despite a clean graph.

---

## A note on what we accept

This document is honest about residual risks because pretending they don't exist would itself be a kind of drift. The system is designed so that the *common* failure modes are caught loudly, and the *rare* ones are at least documented as known. If a scenario lands in production that isn't on this list, it should be added, with a detection plan even if we can't implement it yet.
