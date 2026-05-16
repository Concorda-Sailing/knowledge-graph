# Verification log: tsconfig_paths_complex

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The fixture has 3 source files across 3 directories:
- `src/index.ts` — exports `function bootstrap()`
- `src/components/Card.ts` — exports `class Card` with method `render()` and field `title`
- `src/lib/utils.ts` — exports `function formatDate()` and `function truncate()`

The extractor walks the repo root recursively, picking up all `.ts` files under `src/`.
The `tsconfig.json` is at fixture root but `skipAddingFilesFromTsConfig: true` in the
Project constructor, so it is NOT used to drive file discovery — only the recursive walk matters.
Imports referencing path aliases (`~lib/utils`, `@/components/Card`) are present in source
but generate no primitives (Phase 1 ignores imports).

Package nodes emitted for directories containing source files:
- `fixture::src` (has direct source files: index.ts)
- `fixture::src/components` (has Card.ts)
- `fixture::src/lib` (has utils.ts)

Expected primitives:
- `fixture::src` (primitive=package, owner=null)
- `fixture::src/components` (primitive=package, owner=null)
- `fixture::src/lib` (primitive=package, owner=null)
- `fixture::src/index.ts` (primitive=module, owner=null)
- `fixture::src/components/Card.ts` (primitive=module, owner=null)
- `fixture::src/lib/utils.ts` (primitive=module, owner=null)
- `fixture::src/index.ts::bootstrap` (primitive=function, owner=null)
- `fixture::src/components/Card.ts::Card` (primitive=class, owner=null)
- `fixture::src/components/Card.ts::Card.render` (primitive=function, owner=`fixture::src/components/Card.ts::Card`)
- `fixture::src/components/Card.ts::Card.title` (primitive=variable, owner=`fixture::src/components/Card.ts::Card`)
- `fixture::src/lib/utils.ts::formatDate` (primitive=function, owner=null)
- `fixture::src/lib/utils.ts::truncate` (primitive=function, owner=null)

Note: `Card.title` — the `title` property is declared as `public title: string` in the
constructor parameter shorthand. From the overload_storm investigation, we know constructor
parameter properties do NOT appear in `cls.getProperties()`. So `Card.title` will NOT be emitted.

Revised expected:
- Drop `fixture::src/components/Card.ts::Card.title`

Expected edges: none

## Prediction vs expected.json
- Initial prediction had 12 primitives including `Card.title` (constructor parameter property)
- Revised to 11 after applying knowledge from overload_storm: constructor parameter properties
  not accessible via `cls.getProperties()`
- Final expected.json has 11 primitives, matching the revised prediction

## Expected vs actual (from running the extractor)
- Matches: 11 of 11 — all expected primitives present, no extras
- Discrepancies: none
- Key verifications:
  - Extractor did not crash despite tsconfig.json with complex overlapping path aliases present
  - No import-resolution primitives emitted for `~lib/utils` or `@/components/Card`
  - All 3 package nodes emitted for `src/`, `src/components/`, `src/lib/`
  - `Card.title` correctly absent (constructor parameter property, not in `cls.getProperties()`)

## Notes
- The tsconfig.json is present but does not affect Phase 1 extraction — the extractor uses
  `skipAddingFilesFromTsConfig: true` and walks the filesystem directly.
- Constructor parameter properties (e.g. `public title`) are not captured — learned from
  overload_storm investigation.
- Path-alias imports (`~lib/utils`, `@/components/Card`) present in source files do not
  generate any primitives in Phase 1.
