# Extractors

Project-agnostic, language-specific extractors. Each language has its
own entry point under `generic/<lang>/`; they all implement the same
five-stage contract (discover → parse → emit primitives → run
detectors → write).

| Script | Owned by | Reads | Emits |
|---|---|---|---|
| `reconcile.py` | framework (this dir) | all node files in the data dir | rewrites them with reverse `dependents`, marks stale dossiers, archives orphans |
| `generic/python/extract.py` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |
| `generic/typescript/extract.ts` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |
| `generic/go/extract.py` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |
| `generic/rust/extract.py` | framework | one repo per invocation | per-kind node files under `<data_dir>/nodes/` |

## Wiring

In `<data-repo>/depgraph/project.toml`:

```toml
[repos.api]
path = "~/<project>-api"
extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
detectors = ["fastapi", "sqlalchemy", "pydantic", "pytest"]
files_arg = "--only"

[repos.web]
path = "~/<project>-web"
extractor = ["npx", "tsx", "{kg_dir}/depgraph/extractors/generic/typescript/extract.ts"]
detectors = ["react", "vitest", "route-calls"]
```

Substitutions: `{kg_dir}` → `~/tools/knowledge-graph`; `{data_dir}` →
the depgraph data dir; `{path}` → the repo's resolved path.

## Detectors

Detectors layer framework-specific semantics on top of AST primitives.
Shipped detectors:

| Language | Detector | Recognizes |
|---|---|---|
| python | `fastapi` | `@router.<method>(path)` / `@app.<method>(path)` |
| python | `sqlalchemy` | `DeclarativeBase`/`Base` subclasses; `__tablename__`; classes in `models/` inheriting from `BaseModel` |
| python | `pydantic` | `BaseModel` subclasses in `schemas/` (path-gated) |
| python | `pytest` | `test_*` functions in `test_*.py` / `*_test.py` |
| python | `service` | public top-level functions under `services/` or `utils/` |
| typescript | `react` | PascalCase + JSX returns; `use*` + hook calls; `const X = forwardRef(...)`; `const X = LibPrimitive.Root` |
| typescript | `vitest` | `describe`/`it`/`test` (and `test.only`/`test.skip`) in `*.test.*` / `*.spec.*`; deduped by qualified name |
| typescript | `route-calls` | `fetch(url)` call sites |
| typescript | `service` | public top-level functions under `lib/`, `pages/`, `services/`, `utils/` |

See each language's `README.md` for authoring guidance, and
`CONTRIBUTING-detectors.md` at the repo root for the PR process.

## Project-local detectors

A project can author its own detectors under
`<data-repo>/depgraph/extractors/detectors/<name>.py` (or `.ts`).
`bin/depgraph regen` passes `--detector-path` automatically; the
framework extractor searches both its own `detectors/` dir and the
project-local one.

## Authoring conventions

- Extractors must be **idempotent**.
- Extractors must write **only** under `<data_dir>/nodes/` (or stderr).
- Final summary line: `wrote N nodes (M labeled by detectors), skipped K files`.
- Non-zero exit on fatal failure. Per-file parse errors are non-fatal.
- Per-node files are **bit-stable**: no timestamps, no commit hashes, no derived data.
