# Verification log: re_export_chain

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The fixture has 3 source files all under `src/`:
- `src/impl.ts` — declares `class Widget` (with field `label` and method `render`) and `function createWidget`
- `src/barrel.ts` — only `export * from "./impl"` — no declarations
- `src/index.ts` — only `export * from "./barrel"` — no declarations

Package nodes: only `fixture::src` (all files are directly under src/, no subdirectories).

The extractor:
- Does NOT follow `export *` chains — it only extracts from what is syntactically present in each file
- `barrel.ts` and `index.ts` contain zero classes/functions/variables → emit only module primitives
- `impl.ts` has: class `Widget`, field `label`, method `render`, function `createWidget`
- `Widget.label` is a regular class property (not constructor parameter), so it DOES appear in `cls.getProperties()` → emits as variable primitive

Expected primitives:
- `fixture::src` (primitive=package, owner=null)
- `fixture::src/impl.ts` (primitive=module, owner=null)
- `fixture::src/barrel.ts` (primitive=module, owner=null)
- `fixture::src/index.ts` (primitive=module, owner=null)
- `fixture::src/impl.ts::Widget` (primitive=class, owner=null)
- `fixture::src/impl.ts::Widget.label` (primitive=variable, owner=`fixture::src/impl.ts::Widget`)
- `fixture::src/impl.ts::Widget.render` (primitive=function, owner=`fixture::src/impl.ts::Widget`)
- `fixture::src/impl.ts::createWidget` (primitive=function, owner=null)

NOT expected:
- Any Widget/createWidget primitives under barrel.ts or index.ts ids (no duplication)

Expected edges: none

## Prediction vs expected.json
- Matches: 8 of 8 — prediction exactly matched expected.json
- Discrepancies: none

## Expected vs actual (from running the extractor)
- Matches: 8 of 8 — all expected primitives present, no extras
- Discrepancies: none
- Key verifications:
  - `barrel.ts` and `index.ts` emit only module primitives (no declarations extracted from re-export statements)
  - `Widget.label` correctly emitted as variable — regular class property, not parameter property
  - No duplication: Widget and createWidget appear exactly once each, under impl.ts ids only

## Notes
- `Widget.label` is declared as a regular class field (`label: string`), then assigned in the
  constructor body (`this.label = label`). This is NOT a constructor parameter property — it's
  a regular property declaration, so `cls.getProperties()` WILL include it. Contrast with
  `overload_storm` where `private locale` was a parameter property shorthand.
- Phase 3.3 will add re-export edges between the three modules; for now the barrel files are
  structurally empty in the primitive output.
