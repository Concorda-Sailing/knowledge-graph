# Extractors

Each extractor reads source from one repo and writes node JSON files into `depgraph/nodes/`. They are deliberately deterministic — no LLM calls, no network, no human judgment. Run them as many times as you like; the output is a function of the source.

| Script | Reads | Emits |
|---|---|---|
| `extract_api.py` | `concorda-api/` | `nodes/endpoints/`, `nodes/models/`, `nodes/services/` |
| `extract_web.ts` | `concorda-web/` | `nodes/components/`, `nodes/hooks/` (with http_call edges) |
| `extract_expo.ts` | `concorda-expo/` | same kinds, repo=concorda-expo |
| `extract_tests.ts` | `concorda-test/` | `nodes/tests/` |
| `reconcile.py` | all node files | rewrites them with reverse `dependents`, marks stale dossiers, archives orphans |

## Run order

```
extract_api.py         # endpoint + model nodes
extract_web.ts         # component + hook nodes (with raw URL edges)
extract_expo.ts
extract_tests.ts       # test nodes
reconcile.py           # materialize reverse edges, resolve fuzzy URLs, archive orphans
```

The CLI (`bin/depgraph regen`) runs them in this order.

## What "skeleton" means in v1

The four scripts in this directory have:

- **Real**: entry points, argument parsing, file IO, node ID generation, structural hash for declared schemas, git HEAD capture, schema warnings for weakly-typed responses.
- **TODO(impl)**: handler-body AST walking for `depends_on`, prop type extraction across re-exports, full Pydantic schema canonicalization, fuzzy URL match scoring.

Every TODO is marked in-source so it's grep-able. The point of the v1 commit is to wire the design end-to-end with one worked example, surface the schema and process, then fill in extraction depth incrementally.

## Authoring conventions

- Extractors must be idempotent.
- Extractors must never write outside `depgraph/nodes/` or stderr.
- Extractors must emit a final summary line (`wrote N nodes, ...`) so the Stop hook can parse status.
- Failures must exit non-zero; partial extraction is acceptable but the caller needs to know.
