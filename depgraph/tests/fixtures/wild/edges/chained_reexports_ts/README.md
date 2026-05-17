# chained_reexports_ts

Two-hop re-export chain: a consumer imports/re-exports through a barrel that itself re-exports from the definer.

## Pattern

- `definer.ts` defines `realFunc`.
- `barrel.ts` does `export { realFunc } from './definer'`.
- `consumer.ts` does both `import { realFunc } from './barrel'` and `export { realFunc } from './barrel'`, and calls `realFunc()` from a function body.

## Why tricky

Single-hop re-export resolution (which the extractor already supports) makes `barrel.ts → definer.ts::realFunc` work but stops there. When `consumer.ts` looks up `realFunc` in `barrel.ts`, the local-symbol map for `barrel.ts` doesn't contain `realFunc` (it's not defined there) — so resolution either falls back to an orphan target (`barrel.ts::realFunc`) or has to consult the re-export map for `barrel.ts` to chase one more hop.

This pattern is a common orphan-edge driver in real TS codebases: a top-level `src/index.ts` re-exports from a feature barrel (`src/<feature>/index.ts`), which in turn re-exports from a leaf module.

## v0 behavior

The re-export map is closed under transitive lookup. Both the import-decl branch and the re-export-emission branch consult the closed map after the direct local-symbol lookup misses. Edges from `consumer.ts` resolve all the way to `definer.ts::realFunc` with `confidence: "fuzzy"` (degraded from `exact` to signal that the resolution traversed re-exports rather than landing on a primitive defined in the immediate target module).
