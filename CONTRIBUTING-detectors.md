# Contributing a detector

Detectors are how the framework recognizes specific frameworks
(FastAPI, React, Vitest, …) on top of the language AST primitives.
This guide covers the PR process for upstreaming a new detector.

## Where things live

- Language entry points: `depgraph/extractors/generic/<lang>/extract.{py,ts}`
- Detector contract: `depgraph/extractors/generic/<lang>/detector_api.{py,ts}`
- Shipped detectors: `depgraph/extractors/generic/<lang>/detectors/`
- TEMPLATE: `depgraph/extractors/generic/<lang>/TEMPLATE_detector.{py,ts}`

## Steps

1. **Copy the TEMPLATE** for the right language into `detectors/<name>.{py,ts}`. Rename the class and the `name` field; the file's `name` field must match the filename.
2. **Implement `detect()`**. The contract is documented in `detector_api.{py,ts}`. Detectors must be pure functions of their inputs — no I/O, no globals, no side effects. Exceptions are caught at the extractor boundary, but a noisy detector hurts everyone.
3. **Add tests** in `depgraph/tests/extractors/test_<lang>_detectors.py`. Cover: the happy path; the negative case (no false positives on unrelated constructs); one realistic edge case from the framework you're recognizing.
4. **Add an eval case** under `depgraph/extractors/eval/corpus/<lang>/_seed_<name>/`. Tiny `source/` tree; `expected.json` listing the kinds your detector produces; `case.toml` with `language` and `detectors`. The case becomes part of CI from then on.
5. **Run the deterministic harness**: `python3 -m extractors.eval.harness run <lang> --case _seed_<name>` — must report `passed: true`.
6. **Open a PR** with: detector source, tests, eval case, and a short PR description explaining what framework you're recognizing and what node kind(s) you produce. Include a link to upstream docs for the framework if you can.

## Acceptance criteria

- Tests in `test_<lang>_detectors.py` pass.
- Eval case in `corpus/<lang>/_seed_<name>/` passes deterministic mode.
- No regression: `KG_EVAL=1 pytest depgraph/tests/extractors/` is green.
- The detector's `name` is unique across the language.
- The detector emits a documented `new_kind` — if it's a new kind not already in the framework, add it to `depgraph/extractors/README.md` and explain what it represents.

## Style

- Keep detectors small. If a detector grows past ~150 lines, consider whether it's recognizing one framework or two.
- Detectors compose: a project can enable multiple detectors against the same source. Don't try to be exhaustive in one file.
- Don't reach across files. A detector sees one AST + one file's primitives. Cross-file reasoning belongs in `reconcile.py`.

## Project-local detectors

If your detector is specific to one project, keep it in
`<data-repo>/depgraph/extractors/detectors/<name>.{py,ts}`. The
framework extractor picks it up automatically via `--detector-path`.
Promote to a framework PR once it stabilizes and could plausibly help
another project.
