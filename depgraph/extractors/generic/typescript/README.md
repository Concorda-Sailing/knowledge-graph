# Generic TypeScript extractors

Walk JS/TS source trees with the [TypeScript Compiler API](https://github.com/microsoft/TypeScript-wiki/blob/master/Using-the-Compiler-API.md).
Run via `npx tsx <extractor>.ts <args>`.

## Setup

One-time, from this directory:

```bash
cd ~/tools/knowledge-graph/depgraph/extractors/generic/typescript
npm install
```

This installs `typescript` and `tsx` into a local `node_modules/`. The
extractors import `typescript` directly; `tsx` handles the runtime.

## Available extractors

- `route-calls.ts` — emits `route_call` nodes for every `fetch(...)` site.
  See file header for full options.
