# Extractors

This directory holds the framework's project-agnostic reconciler. Project-specific extractors (the ones that walk your actual source repos) live in your project's data dir, not here.

| Script | Owned by | Reads | Emits |
|---|---|---|---|
| `reconcile.py` | framework (this dir) | all node files in the data dir | rewrites them with reverse `dependents`, marks stale dossiers, archives orphans |
| `extract_*.py` / `extract_*.ts` | your project (data dir) | one repo each, per `[repos.*]` in `project.toml` | per-kind subdirs of `nodes/` (endpoints, components, hooks, services, models, tests, …) |

## Wiring

Each `[repos.<key>]` table in your project's `project.toml` declares an `extractor` command:

```toml
[repos.api]
path = "~/<project>-api"
extractor = ["python3", "{data_dir}/extractors/extract_api.py"]
files_arg = "--only"

[repos.web]
path = "~/<project>-web"
extractor = ["npx", "tsx", "{data_dir}/extractors/extract_web.ts"]
```

Substitutions: `{data_dir}` resolves to the project's depgraph data dir; `{path}` to the repo's resolved path.

`bin/depgraph regen` walks the configured `[repos.*]` set, runs each extractor in turn, then runs `reconcile.py` to materialize reverse edges, resolve fuzzy URL targets, archive orphans, and stub missing dossiers. The CLI's run order is repos-in-config-order, then reconcile.

## Authoring conventions for project extractors

- Extractors must be **idempotent** — two runs with the same source produce the same output.
- Extractors must write **only** under `<data_dir>/nodes/` (or stderr for diagnostics).
- Extractors must emit a final summary line (`wrote N nodes, ...`) so the Stop hook can parse status.
- Extractors must **exit non-zero on failure**. Partial extraction is acceptable but the caller needs to know.
- Per-node files should be **bit-stable**: no timestamps, no commit hashes, no derived data. Provenance lives in `_meta.json`; reverse edges live in `_index/dependents.json`. Git diffs reflect real source edits, not regen churn.

## What "skeleton" means

Some extractors ship as skeletons — they declare structure (entry points, IO, node ID generation, schema warnings) but defer expensive analysis (AST walking, type extraction) until needed. Every TODO is grep-able in the source. The point of a skeleton commit is to wire the design end-to-end with one worked example, surface the schema and process, then fill in depth incrementally.
