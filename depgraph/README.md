# Dependency Graph

> A continuously-maintained map of every endpoint, component, hook, and model in your project — and every other piece of code that depends on each one.
>
> Built so that when Claude (or a human) opens a file to edit it, the full operational and contextual surface area of that change is already on the table.

## Why this exists

Multi-repo projects routinely split source across an HTTP boundary:

```
<api-repo>  ──HTTP──▶  <web-repo>      (browser)
                  └──▶  <mobile-repo>   (iOS/Android)
                  └──▶  <test-repo>     (E2E)
```

Standard import graphs (`madge`, `pydeps`, `dep-cruiser`) cannot see across that boundary — to them, `fetch("/api/invite/abc")` is just a string. So when an endpoint's response shape changes, *no static tool flags the call sites*. This system is designed to catch exactly that class of bug.

The graph also tracks **intent**, not just structure. A dossier travels with each node: invariants, gotchas, external consumers, the reasons behind subtle decisions. Structure tells you *what's connected*; the dossier tells you *what'll break if you change it carelessly*.

## What you get

Before any `Edit`/`Write` on a tracked file, a `PreToolUse` hook injects, automatically:

1. **The node's own dossier** — purpose, invariants, gotchas.
2. **Reverse dependents** — every component, hook, test, and external consumer that calls into this node.
3. **Drift warnings** — if the structural hash has changed since the dossier was last reviewed, or if extraction emitted ambiguous edges.

No manual lookup. No "I forgot to check the mobile app." The information arrives whether or not Claude thought to ask.

## Layout

The framework (this repo, cloned to `~/tools/knowledge-graph/` — depgraph is a sibling subdir alongside `logigraph`, `graphui`, and the `kg` orchestrator) is project-agnostic. Per-project data — nodes, dossiers, project-specific extractors — lives in a separate **data dir** owned by your project (e.g. `~/<project>-knowledge-graph/depgraph/`). The two are bridged by `project.toml` in the data dir:

```toml
[project]
name = "<project>"
primary_repo = "api"

[repos.api]
path = "~/<project>-api"
extractor = ["python3", "{data_dir}/extractors/extract_api.py"]
files_arg = "--only"

[repos.web]
path = "~/<project>-web"
extractor = ["npx", "tsx", "{data_dir}/extractors/extract_web.ts"]
```

```
~/tools/knowledge-graph/depgraph/       (this framework subdir; siblings: logigraph/, graphui/, kg/)
├── README.md                  ← you are here
├── PROCESS.md                 ← rules to follow before/during/after every edit
├── DRIFT.md                   ← every way this system can lie to you, and the mitigation
├── lib/config.py              ← shared project.toml parser
├── schema/
│   ├── node.schema.json
│   ├── dependents.schema.json
│   └── dossier.schema.md
├── extractors/
│   └── reconcile.py           ← builds reverse index, archives orphans, stubs missing dossiers
├── hooks/
│   ├── pre_edit_inject.py     ← PreToolUse: emit additionalContext for the target file
│   ├── post_edit_regen.py     ← Stop: re-extract touched files, flag drift
│   └── post_edit_telemetry.py ← Stop: scan transcripts for rule/dossier acks
├── bin/
│   └── depgraph               ← CLI: regen, context, dependents, orphans, validate, self-check
└── examples/                  ← worked example: a generic POST endpoint

~/<project>-knowledge-graph/depgraph/   (per-project data dir; sibling: logigraph/)
├── project.toml               ← [repos.*] config; consumed by the framework
├── nodes/                     ← per-node JSON, owned by extractors, bit-stable across regens
│   ├── endpoints/             ← one file per HTTP route (METHOD::/path)
│   ├── components/            ← one file per React component
│   ├── hooks/                 ← one file per `use*` hook
│   ├── services/              ← one file per service-layer function
│   ├── models/                ← one file per ORM class
│   ├── tests/                 ← one file per E2E test
│   ├── _index/dependents.json ← derived: reverse-edge map
│   ├── _manifests/<x>.json    ← per-extractor manifest of claimed ids
│   ├── _meta.json             ← corpus provenance + regen_status
│   └── _archive/              ← orphaned nodes (source deleted or symbol removed)
├── dossiers/<kind>/           ← LLM-curated companion markdown for each node
└── extractors/                ← project-specific extractors (extract_api.py, extract_web.ts, …)
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

## Why per-project data, not per-assistant

The graph is a **project artifact**, not a per-assistant config. Three reasons:

- It's checked in, reviewed in PRs, and useful to humans reading code in any editor.
- Future Claude sessions, Codex sessions, or contributors with no Anthropic config still benefit.
- The extractors are project-shaped — they know about FastAPI's routing, Next.js's app dir, Expo's screens. They belong with the project, in the project's data dir.

Only the **hook wiring** (the `PreToolUse` / `Stop` invocation in `.claude/settings.json`) is per-assistant. The hook scripts themselves live here, in `hooks/`.

## Quickstart

Set `DEPGRAPH_DATA_DIR` to point at your project's data dir, or `cd` into it before running CLI commands. Examples below assume `DEPGRAPH_DATA_DIR=~/<project>-knowledge-graph/depgraph` (or that you've cd'd there).

```bash
# Full regen — runs every extractor and reconciles. Idempotent.
bin/depgraph regen

# Print the same context block the PreToolUse hook would inject
bin/depgraph context <repo-name>/path/to/file.py

# Walk the reverse graph from a node id (transitive)
bin/depgraph dependents '<METHOD>::/api/path' --depth 3

# Find orphans (nodes whose source file no longer exists)
bin/depgraph orphans

# Validate every node file against the schema
bin/depgraph validate

# Smoke-test the PreToolUse hook end-to-end
bin/depgraph self-check

# Compact summary for a commit body trailer (blind-spot audit)
bin/depgraph commit-summary             # uses git diff
bin/depgraph commit-summary file1 file2
```

> **Commit message convention.** Every commit in any of the project's tracked repos should end with the output of `bin/depgraph commit-summary`. The trailer is greppable (`git log --grep="Depgraph:"`) so blind spots — bugs in nodes that don't appear in any commit's Depgraph trailer — surface during postmortems.

> Selective regen (`--since <ref>`, `--only <file>`) is a planned enhancement — for now `regen` is full-graph each time. The Stop hook handles the per-edit case by running only the affected extractor.

## License

[MIT](./LICENSE). Copyright (c) 2026 Logan Greenlee.

The software is provided **AS IS**, without warranty of any kind,
express or implied, including but not limited to merchantability,
fitness for a particular purpose, and non-infringement. See the
LICENSE file for the full text.
