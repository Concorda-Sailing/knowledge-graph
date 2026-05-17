# Extractors

Project-agnostic, language-specific extractors. Each one walks a repo
configured in `<data-repo>/project.toml [repos.<key>]`, parses source
to AST, and emits per-language primitives (modules, classes, functions,
variables) that the v2 pipeline then resolves edges over and classifies
into kinds (component, hook, endpoint, service, model, schema, test,
util).

| Path | Language | Driven by |
|---|---|---|
| `python/extract.py` | Python | `[repos.<key>] languages` includes `"python"` |
| `typescript/extract.ts` | TypeScript / JavaScript | `[repos.<key>] languages` includes `"typescript"` |
| `sql/` | SQL migrations | `[repos.<key>] languages` includes `"sql"` + `migrations_dirs` |
| `reconcile.py` | n/a | runs after every regen — validates the unified primitive set, builds the reverse-edge index, archives orphan nodes |

The Python and SQL extractors run in-process (no subprocess) for speed.
The TypeScript extractor runs as a `tsx` subprocess because there's no
Python binding for ts-morph. All three accept the same per-repo
`include_paths` / `exclude_paths` config and apply them with identical
glob semantics — see `lib/path_filters.py` and its JS port in
`typescript/extract.ts`.

## Pipeline order

`lib/cli/regen.py` orchestrates a single regen invocation. Per repo, in
language order: Python → TypeScript → SQL. After every repo has emitted
primitives, three cross-cutting passes run over the unified corpus:

1. **Cross-ref pass** — resolves ORM model classes to their backing
   schema primitives via `__tablename__`.
2. **`db_access` pass** — attaches `db_access` edges from services
   that call `session.query(Model)` etc. onto the schema primitive.
3. **Classification** — applies the rule engine in `lib/classification/`
   to assign a `kind` to each primitive based on its source path,
   decorators, base classes, and surrounding edges.

The classified corpus is then written to disk via
`lib/classification/writer.py`. Classified primitives land under
`nodes/<kind_dir>/<slug>.json`; unclassified primitives keep their raw
primitive shape under `nodes/<primitive_dir>/<slug>.json`.

## Wiring a repo

In `<data-repo>/project.toml`:

```toml
[repos.api]
path = "~/<project>-api"
languages = ["python", "sql"]
migrations_dirs = ["migrations"]
exclude_paths = ["**/tests/**", "**/test_*.py", "**/*_test.py"]

[repos.web]
path = "~/<project>-web"
languages = ["typescript"]
exclude_paths = ["**/__tests__/**", "**/*.test.ts", "**/*.test.tsx", "**/build/**"]
```

`languages` is inferred from file extensions if omitted. Everything else
is documented at `depgraph/README.md` (per-repo configuration keys table)
and in the comment block of the `project.toml` that `kg install init`
scaffolds for new projects.

## Authoring conventions for the shipped extractors

- Extractors must be **idempotent**. Two regens against the same source
  produce byte-identical primitive output. The
  `tests/test_regen_determinism.py` CI gate enforces this.
- Per-primitive output must be a stable view of the source: no
  timestamps, no commit hashes, no derived data. Anything time- or
  run-dependent lives in `nodes/_meta.json`.
- Per-file parse errors are non-fatal — the extractor logs and
  continues; the bad primitive is omitted from the corpus rather than
  crashing the whole regen.
- The extractor never writes to disk — it returns primitives to the
  pipeline, which is responsible for writing.

## Project-local extractors

The v1 framework supported invoking arbitrary `extractor = ["cmd", ...]`
commands from `[repos.<key>]`. That code path still exists in
`lib/cli/regen.py::_mode_a_v1_fallback` for projects that need to run a
custom extractor for a language the framework doesn't ship. New projects
should prefer the shipped per-language extractors and configure scope
via `include_paths` / `exclude_paths` instead.
