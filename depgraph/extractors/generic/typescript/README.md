# TypeScript / JavaScript language extractor

Walks JS/TS source with the [TypeScript Compiler API](https://github.com/microsoft/TypeScript-wiki/blob/master/Using-the-Compiler-API.md).
Run via `npx tsx extract.ts`.

## Setup (one-time)

```bash
cd ~/tools/knowledge-graph/depgraph/extractors/generic/typescript
npm install
```

## Run

```bash
npx tsx extract.ts \
  --repo-key web --repo-path ~/myproj-web \
  --data-dir ~/myproj-knowledge-graph/depgraph \
  --detectors react,vitest,route-calls
```

## Authoring a detector

1. Copy `TEMPLATE_detector.ts` to `detectors/<name>.ts`.
2. Implement `detect()`.
3. Add a test in `depgraph/tests/extractors/test_typescript_extractor.py` (drives via tsx subprocess).
4. Add an eval case under `eval/corpus/typescript/_seed_<name>/`.
5. Open a PR. See `CONTRIBUTING-detectors.md`.

## Detector lookup order

1. Framework dir: this directory's `detectors/`.
2. Project-local: `<data-repo>/depgraph/extractors/detectors/` (via `--detector-path`).
