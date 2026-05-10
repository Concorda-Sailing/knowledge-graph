# Concorda Dependency Graph

> A continuously-maintained map of every endpoint, component, hook, and model in the Concorda system — and every other piece of code that depends on each one.
>
> Built so that when Claude (or a human) opens a file to edit it, the full operational and contextual surface area of that change is already on the table.

## Why this exists

Concorda is split across four repos that talk to each other across an HTTP boundary:

```
concorda-api  ──HTTP──▶  concorda-web   (browser)
                   └──▶  concorda-expo  (iOS app)
                   └──▶  concorda-test  (Playwright)
```

Standard import graphs (`madge`, `pydeps`, `dep-cruiser`) cannot see across that boundary — to them, `fetch("/api/invite/abc")` is just a string. So when an endpoint's response shape changes, *no static tool flags the call sites*. We have been bitten by exactly this class of bug, and it's the one this system is designed to catch.

The graph also tracks **intent**, not just structure. A dossier travels with each node: invariants, gotchas, external consumers, the reasons behind subtle decisions. Structure tells you *what's connected*; the dossier tells you *what'll break if you change it carelessly*.

## What you get

Before any `Edit`/`Write` on a tracked file, a `PreToolUse` hook injects, automatically:

1. **The node's own dossier** — purpose, invariants, gotchas.
2. **Reverse dependents** — every component, hook, test, and external consumer that calls into this node.
3. **Drift warnings** — if the structural hash has changed since the dossier was last reviewed, or if extraction emitted ambiguous edges.

No manual lookup. No "I forgot to check the Expo app." The information arrives whether or not Claude thought to ask.

## Anatomy

```
depgraph/
├── README.md                  ← you are here
├── PROCESS.md                 ← rules I follow before/during/after every edit
├── DRIFT.md                   ← every way this system can lie to you, and the mitigation
├── schema/
│   ├── node.schema.json       ← JSON-Schema for per-node files (kind/source/depends_on/...)
│   ├── dependents.schema.json ← format for the reverse-edge index (defect #1)
│   └── dossier.schema.md      ← format for dossier markdown
├── nodes/                     ← per-node JSON, owned by extractors, bit-stable across regens
│   ├── endpoints/             ← one file per HTTP route (METHOD::/path)
│   ├── components/            ← one file per React component (file-path-qualified id)
│   ├── hooks/                 ← one file per `use*` hook
│   ├── services/              ← one file per service-layer function (api lib, ApiClient methods, …)
│   ├── models/                ← one file per SQLAlchemy class
│   ├── tests/                 ← one file per Playwright `test(...)` call
│   ├── _index/dependents.json ← derived: reverse-edge map (defect #1)
│   ├── _manifests/<x>.json    ← per-extractor manifest of claimed ids (defect #5)
│   ├── _meta.json             ← corpus provenance + regen_status (defect #2 / #4)
│   └── _archive/              ← orphaned nodes (source deleted or symbol removed)
├── dossiers/
│   └── <kind>/                ← LLM-curated companion markdown for each node
├── extractors/
│   ├── extract_api.py         ← AST-walks routers/, models/, services/, utils/ — no app import (defect #8)
│   ├── extract_web.ts         ← walks Next.js source via ts-morph; resolves imports for cross-file edges
│   ├── extract_tests.ts       ← walks Playwright specs; tracks `const x = new ApiClient()` for accurate edges
│   ├── extract_expo.ts        ← skeleton (Expo not yet in production use)
│   └── reconcile.py           ← builds reverse index, archives orphans, stubs missing dossiers
├── hooks/
│   ├── pre_edit_inject.py     ← PreToolUse: emit additionalContext for the target file
│   └── post_edit_regen.py     ← Stop: re-extract touched files, flag drift
├── bin/
│   └── depgraph               ← CLI: regen, context, dependents, orphans, validate, self-check
└── examples/                  ← worked example: POST /api/invite/{code}/accept
```

Files or directories whose name (or any path component) starts with `_` are corpus metadata, not nodes — the extractors and reconciler use this as a stable rule to avoid colliding with kind subdirectories like `endpoints/`.

## The lifecycle

```
                ┌──────────────────────────┐
                │  source code             │
                └────────────┬─────────────┘
                             │
       Stop hook on touched file ↓ (or `bin/depgraph regen`)
                             │
                ┌──────────────────────────┐
                │  bin/depgraph regen      │  ← marks _meta.regen_status=in_progress
                └────────────┬─────────────┘
                             │
                ┌──────────────────────────┐
                │  extractors (per repo)   │  ← deterministic; pure AST/ts-morph; no LLM
                │   • emit per-node JSON   │     (atomic write, write-if-changed)
                │   • emit manifest of ids │
                └────────────┬─────────────┘
                             │
                ┌──────────────────────────┐
                │  reconcile.py            │  ← build reverse-edge index,
                │                          │    archive domain orphans,
                │                          │    stub missing dossiers,
                │                          │    flag stale dossiers,
                │                          │    set _meta.regen_status=complete
                └────────────┬─────────────┘
                             │
                ┌──────────────────────────┐
                │  nodes/*.json (truth)    │
                │  _index/dependents.json  │
                │  _meta.json (provenance) │
                │  dossiers/*.md (intent)  │
                └────────────┬─────────────┘
                             │
        PreToolUse on Edit/Write ↑
                             │
                ┌──────────────────────────┐
                │  Claude sees:            │
                │   • dossier              │
                │   • dependents list      │
                │   • drift warnings       │
                └──────────────────────────┘
```

Five properties hold:

1. **Structure is regenerated, not maintained.** Per-node `depends_on` is rewritten by extractors from source. The reverse map (`_index/dependents.json`) is rebuilt by the reconciler from those edges. Neither can drift — if they're stale, the next regen fixes them.
2. **Per-node files are bit-stable.** Regen with no source change produces zero file diffs. No timestamps, no commit hashes, no derived data on the per-node files — those live in `_meta.json` and `_index/dependents.json`. Git diffs reflect real source edits, not regen churn.
3. **Intent is reviewed, not auto-generated.** Dossiers are written by a human or by Claude with intent in mind. They go *stale* when their pinned `last_reviewed_against_hash` no longer matches the current `structural_hash`.
4. **Drift is loud.** Stale dossiers, fuzzy string-URL edges, schema-version mismatches, orphan nodes, missing extractor manifests, in-progress regens, and external-consumer banners all surface as warnings during the PreToolUse injection — never silently.
5. **Atomicity gates the truth.** `bin/depgraph regen` marks `_meta.regen_status: in_progress` before any extractor runs and `complete` only after reconciliation succeeds. The hook surfaces the in_progress state explicitly. Per-file writes use tmp+rename so a crash mid-write never produces a half-written JSON.

See **DRIFT.md** for the full taxonomy of failure modes and how each is detected.

## Why it lives in `concorda/`, not `.claude/`

The graph is a **project artifact**, not a per-assistant config. Three reasons:

- It's checked in, reviewed in PRs, and useful to humans reading code in any editor.
- Future Claude sessions, Codex sessions, or contributors with no Anthropic config still benefit.
- The extractors are project-shaped — they know about FastAPI's routing, Next.js's app dir, Expo's screens. They belong with the project.

Only the **hook wiring** (the `PreToolUse` / `Stop` invocation in `.claude/settings.json`) is per-assistant. The hook scripts themselves live here, in `depgraph/hooks/`.

## Quickstart

```bash
# Full regen — runs every extractor and reconciles. Idempotent.
~/concorda/depgraph/bin/depgraph regen

# Print the same context block the PreToolUse hook would inject
~/concorda/depgraph/bin/depgraph context concorda-api/routers/invite.py

# Walk the reverse graph from a node id (transitive)
~/concorda/depgraph/bin/depgraph dependents 'POST::/api/invite/{0}/accept' --depth 3

# Find orphans (nodes whose source file no longer exists)
~/concorda/depgraph/bin/depgraph orphans

# Validate every node file against the schema
~/concorda/depgraph/bin/depgraph validate

# Smoke-test the PreToolUse hook end-to-end
~/concorda/depgraph/bin/depgraph self-check

# Compact summary for a commit body trailer (blind-spot audit)
~/concorda/depgraph/bin/depgraph commit-summary             # uses git diff
~/concorda/depgraph/bin/depgraph commit-summary file1 file2
```

> **Commit message convention.** Every commit in any of the concorda-* repos should end with the output of `bin/depgraph commit-summary`. The trailer is greppable (`git log --grep="Depgraph:"`) so blind spots — bugs in nodes that don't appear in any commit's Depgraph trailer — surface during postmortems. See `~/.claude/.../feedback_depgraph_commit_trailers.md` for the rule.

> Selective regen (`--since <ref>`, `--only <file>`) is a planned enhancement — for now `regen` is full-graph each time. The Stop hook handles the per-edit case by running only the affected extractor.

## Status

The system is live across `concorda-api`, `concorda-web`, and `concorda-test`. As of the most recent regen:

- **1421 nodes** — 288 endpoints, 65 models, 198 services (including api-client + page-objects from concorda-test), 670 web components/hooks, 192 Playwright tests
- **2065 reverse edges** materialized in `_index/dependents.json`, including:
  - 270 cross-HTTP edges (web ↔ api)
  - 691 api → model / service / websocket edges from handler-body AST walking
  - 251 test → endpoint and test → ApiClient edges (with `new ClassName()` instance tracking)
- **Two consecutive regens produce 0 file diffs** (bit-stable)
- **Hook latency**: ~30ms with the 1421-node corpus
- **Full regen latency**: ~6s

`extract_expo.ts` is a deliberate skeleton — Expo isn't yet in production use. When it goes live, the rewrite is mechanical: it shares structure with `extract_web.ts`.

See **PROCESS.md** for the rules of engagement and **DRIFT.md** for the catalog of failure modes and their mitigations.
