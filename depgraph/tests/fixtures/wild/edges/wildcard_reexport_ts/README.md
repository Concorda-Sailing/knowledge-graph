# wildcard_reexport_ts

A barrel module re-exports everything from a definer with `export * from './types'`; a consumer imports named symbols through the barrel.

## Pattern

- `types.ts` defines `Gadget` (interface) and `Tool` (class).
- `barrel.ts` does `export * from './types'` — no named exports.
- `consumer.ts` does `import { Gadget, Tool } from './barrel'` and uses both.

## Why tricky

ts-morph's `exp.getNamedExports()` returns an empty list for `export *` declarations. The original re-export map only consulted named exports, so wildcard re-exports contributed nothing to the map. Imports from a wildcard-only barrel orphaned onto `barrel.ts::<name>` placeholders even though the underlying primitive existed in `./types`.

## v0 behavior

When building the re-export map, `export * from './target'` populates entries for every top-level symbol that `./target` exposes — including any further re-exports the target itself declared. The closure pass then collapses chains the same way it does for named re-exports.
