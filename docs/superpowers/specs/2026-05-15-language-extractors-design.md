# Project-agnostic, language-specific extractors

**Status:** Design — approved 2026-05-15
**Owner:** Logan Greenlee
**Scope:** `~/tools/knowledge-graph/depgraph/extractors/`

## Problem

Today the framework ships one generic extractor (`extractors/generic/typescript/route-calls.ts`). Real node coverage — endpoints, components, hooks, models, schemas, tests — lives in per-project files. Concorda has ~2,300 lines across `extract_api.py`, `extract_web.ts`, `extract_tests.ts`, and `ingest_route_calls.py`. New projects either copy that code (drift) or author from scratch (high bar). The framework should provide reusable, language-specific extractors that yield many deps from syntax alone, with a template for framework-detector contributions.

## Goals

- Ship language-level AST extractors for Python, TypeScript/JavaScript, Go, and Rust in a single coordinated release.
- Preserve Concorda's existing extractor logic by lifting it into the framework as detector modules.
- Provide a documented detector contract + template so community PRs can add framework support.
- Establish an evaluation foundation (harness + case format) so extractor accuracy is measurable as the corpus grows.

## Non-goals

- No graphui changes — node kinds and reverse-dependency semantics are unchanged.
- No logigraph changes — rule claims still bind by `depgraph_id`.
- No new Claude Code hook entries — `kg` dispatcher is unchanged.
- No Go/Rust framework detectors shipped at launch. Those are community-PR territory; the language extractors emit AST primitives on day one.

## Architecture

```
~/tools/knowledge-graph/depgraph/extractors/
├── reconcile.py                    (existing, unchanged)
├── generic/
│   ├── python/                     native: stdlib `ast`
│   │   ├── extract.py              entry point
│   │   ├── detectors/              fastapi.py, sqlalchemy.py, pydantic.py, pytest.py
│   │   ├── detector_api.py         abstract contract
│   │   ├── TEMPLATE_detector.py    scaffold for community PRs
│   │   └── README.md
│   ├── typescript/                 native: typescript Compiler API
│   │   ├── extract.ts              entry point
│   │   ├── detectors/              react.ts, vitest.ts, express.ts, route-calls.ts
│   │   ├── detector_api.ts
│   │   ├── TEMPLATE_detector.ts
│   │   └── README.md
│   ├── go/                         tree-sitter via Python driver
│   │   ├── extract.py              tree-sitter-go grammar
│   │   ├── detectors/              empty + TEMPLATE
│   │   └── README.md
│   └── rust/                       tree-sitter via Python driver
│       ├── extract.py              tree-sitter-rust grammar
│       ├── detectors/              empty + TEMPLATE
│       └── README.md
└── eval/
    ├── harness.py                  case runner + diff/judge
    ├── corpus/<lang>/<case>/{source/, expected.json, case.toml, README.md}
    ├── judgments/                  Claude-Code-session-produced advisory judgments
    └── README.md
```

## Project wiring

`<data-repo>/depgraph/project.toml` gains a `detectors` key on each `[repos.*]` table and a new `{kg_dir}` substitution:

```toml
[repos.api]
path = "~/concorda-api"
extractor = ["python3", "{kg_dir}/depgraph/extractors/generic/python/extract.py"]
detectors = ["fastapi", "sqlalchemy", "pydantic", "pytest"]
files_arg = "--only"
```

Substitutions:
- `{kg_dir}` → `~/tools/knowledge-graph` (new).
- `{data_dir}` → the project's `depgraph` data dir (existing).
- `{path}` → the repo's resolved source path (existing).

Custom project-local detectors live at `<data-repo>/depgraph/extractors/detectors/<name>.py` (or `.ts`) and are discovered automatically — the framework extractor passes `--detector-path <data_dir>/extractors/detectors` to itself.

## Language extractor contract

Every entry point follows the same five-stage shape so `reconcile.py` and the runner stay uniform.

1. **Discover** — walk the repo's source roots (excluding `node_modules`, `.venv`, `target`, `dist`, `build`, plus per-repo `exclude` globs from `project.toml`).
2. **Parse** — produce an AST per file. Native parser (Py: stdlib `ast`; TS: typescript Compiler API) or tree-sitter (Go: tree-sitter-go; Rust: tree-sitter-rust). Parse errors emit a stderr diagnostic and skip the file; non-fatal.
3. **Emit primitives** — per file, JSON nodes for: `module`, `class`, `function` (incl. methods), `import` edges, `call` edges. IDs use `<repo_key>:<rel_path>:<symbol>`; methods carry `parent_id`.
4. **Run detectors** — each enabled detector receives `(ast, primitives, ctx)` and returns a list of mutations: `RelabelNode(node_id, new_kind, extra_metadata)`, `AddEdge(from, to, kind)`, `AddNode(kind, payload)`. Mutations apply in order; later detectors see earlier mutations.
5. **Write** — per-node files under `<data_dir>/nodes/<kind>/`. Bit-stable (no timestamps, no hashes). Final stdout: `wrote N nodes (M labeled by detectors), skipped K files`.

### CLI flags (uniform across languages)

- `--only <file>` — restrict to one file (post-edit hook path).
- `--detectors <name>,<name>` — override the project.toml list (for eval/debug).
- `--detector-path <dir>` — extra search dir for custom detectors.
- `--repo-key <key>` and `--repo-path <path>` — passed by the runner; substituted into node IDs.

### Detector contract

- Each detector is a single module exporting `detect(ast, primitives, ctx) -> list[Mutation]`.
- `ctx` carries: repo key, file path, project config slice.
- Detectors are pure functions of their inputs. No I/O. No globals.
- An exception inside a detector is caught at the extractor boundary, logged as `detector_error`, and the detector is skipped for that file. Other detectors and other files continue.

## Concorda lift

Each existing Concorda extractor decomposes into AST-walk (into the framework language extractor) + framework recognition (into detector modules).

| Source (Concorda) | Lift target (framework) |
|---|---|
| `extract_api.py` AST walk | `python/extract.py` |
| `extract_api.py` FastAPI route detection | `python/detectors/fastapi.py` |
| `extract_api.py` SQLAlchemy model detection | `python/detectors/sqlalchemy.py` |
| `extract_api.py` Pydantic schema detection | `python/detectors/pydantic.py` |
| `extract_api.py` pytest detection | `python/detectors/pytest.py` |
| `extract_web.ts` AST walk | `typescript/extract.ts` |
| `extract_web.ts` React component/hook detection | `typescript/detectors/react.ts` |
| `extract_web.ts` Express detection (if present) | `typescript/detectors/express.ts` |
| `extract_tests.ts` Vitest detection | `typescript/detectors/vitest.ts` |
| `extractors/generic/typescript/route-calls.ts` | promoted to `typescript/detectors/route-calls.ts` |
| `ingest_route_calls.py` | stays in Concorda until route-calls is fully integrated, then retired |

### Parity gate

Before Concorda's `project.toml` flips to framework extractors:

1. Run `bin/depgraph regen` with new extractors writing to a scratch nodes dir.
2. Diff scratch dir vs current `<data>/nodes/`.
3. Acceptable diffs: new optional metadata fields; reordering of `dependents`/`imports` lists.
4. Node count per kind must match within ±2%. Any missing node must be diagnosable to a specific detector gap and either fixed or explicitly accepted in the migration commit message.
5. Once parity is verified in the same commit: flip `project.toml`, delete `extract_api.py` / `extract_web.ts` / `extract_tests.ts` from Concorda.

## Evaluation harness

Lives at `~/tools/knowledge-graph/depgraph/extractors/eval/`.

### Case shape

```
corpus/<lang>/<case_name>/
├── source/             input tree (small, real-ish code)
├── expected.json       declared ground truth: node IDs by kind, import edges, detector labels
├── case.toml           detectors to enable + extractor flags
└── README.md           what this case is meant to test
```

Only declared expectations are checked. Omitted fields mean "don't check that surface."

### Two modes (one harness, one CLI)

- **Deterministic mode** (gates PRs): `harness.py run <lang> [--case <name>]` diffs emitted nodes/edges against `expected.json` and prints precision/recall per kind. Exit non-zero on regression. Fast, no LLM.
- **Judgment mode** (advisory): `harness.py judge <lang> --case <name>` emits a judgment package (source tree + extractor output + fixed prompt template) to `eval/judgments/<case>/pending.md`. During a Claude Code session, the model reads the package and writes back to `judgments/<case>/<YYYY-MM-DD>.md`. No API key, no automation; the format is stable so commit history shows the progression.

### Seeding

- Ship one minimal seed case per language (`_seed_imports/` for the AST primitives; `_seed_<framework>/` per landed detector — e.g., `_seed_fastapi/`).
- A one-shot bootstrap script (lives in the migration branch, not the framework) lifts a handful of representative files from Concorda's repos plus their current node outputs and proposes them as `expected.json`. Human trims before commit.

### CI

`KG_EVAL=1 pytest tests/eval/` runs deterministic mode across all languages on every framework PR. Required to pass before merge.

## Error handling

| Failure | Behavior |
|---|---|
| Parse error on a file | stderr diagnostic with file + line; skip file; non-fatal; summary reports skip count |
| Detector raises | caught at extractor boundary; `detector_error` diagnostic; that detector skipped for that file; others continue |
| Toolchain missing (e.g. `tree-sitter-go`) | extractor exits non-zero at startup with install hint; `bin/depgraph regen` logs and continues with other repos |
| No detectors matched a file | not an error; primitives still emitted |
| Unknown detector name in `project.toml` | extractor exits non-zero with available-detector list |
| Crash mid-regen | existing semantics: `_meta.regen_status: in_progress`; next hook surfaces torn-graph banner |

## Testing

- **Framework unit tests** in `~/tools/knowledge-graph/depgraph/tests/`:
  - One test per language extractor exercising the five-stage contract against a fixture.
  - One test per shipped detector (fastapi, sqlalchemy, pydantic, pytest, react, express, vitest, route-calls) — single-file fixture, asserts expected mutations.
  - Detector-contract tests: raising detector doesn't break the run; unknown detector name produces a clear error.
- **Eval CI**: deterministic mode across seed cases, gated on `KG_EVAL=1`.
- **Concorda parity test**: one-off script in the migration branch; not ongoing CI.

## Rollout

Single coordinated release across all four languages.

1. Land framework scaffolding (`extract.py` / `extract.ts` for all four languages) + detector API + TEMPLATE files. Empty detector lists exit 0.
2. Lift Concorda's detectors into `python/detectors/` and `typescript/detectors/`. Unit tests pass.
3. Land eval harness + seed cases. CI gates green.
4. Bootstrap Concorda corpus cases (one-shot script from real files). Add as cases.
5. Flip Concorda's `project.toml`. Verify parity. Delete old Concorda extractors in the same commit.
6. Update top-level `README.md` runbook entries ("Add a new tracked repo" → framework extractors + detector list) and `depgraph/extractors/README.md`.
7. Add `CONTRIBUTING-detectors.md`: detector contract, eval case authoring, PR checklist.

## Open questions

None at design-approval time. Capture in this section if any surface during planning or implementation.
