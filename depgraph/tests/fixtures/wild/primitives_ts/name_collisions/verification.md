# Verification log: name_collisions

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The source file `src/collisions.ts` contains:
- `type value = string | number` — type alias at module scope
- `class Container` with:
  - field `value: string = ""` — class property
  - instance method `getValue(): string` — distinct name avoids field/method collision
  - static method `value(input: unknown): string` — same local name as field, but `:static` suffix

The extractor processes these via:
- `extractClasses`: emits `Container` (class), and `value` type alias (also as class primitive)
- `extractFunctions`: emits `Container.getValue` (instance method), `Container.value:static` (static method)
- `extractVariables`: emits `Container.value` (class field)
- `packagePrimitives`: emits `fixture::src` package

Expected primitives:
- `fixture::src` (primitive=package, owner=null)
- `fixture::src/collisions.ts` (primitive=module, owner=null)
- `fixture::src/collisions.ts::value` (primitive=class, owner=null) — type alias treated as class
- `fixture::src/collisions.ts::Container` (primitive=class, owner=null)
- `fixture::src/collisions.ts::Container.getValue` (primitive=function, owner=`fixture::src/collisions.ts::Container`)
- `fixture::src/collisions.ts::Container.value:static` (primitive=function, owner=`fixture::src/collisions.ts::Container`)
- `fixture::src/collisions.ts::Container.value` (primitive=variable, owner=`fixture::src/collisions.ts::Container`)

Key: `Container.value` (variable) and `Container.value:static` (function) are DISTINCT ids.
`value` (type alias) is at module scope with no owner, also distinct.

Expected edges: none

## Prediction vs expected.json
- Matches: 7 of 7 — prediction exactly matched expected.json
- Discrepancies: none

## Expected vs actual (from running the extractor)
- Matches: 7 of 7 — all expected primitives present in actual, no extras
- Discrepancies: none
- Key verification: `Container.value` (variable) and `Container.value:static` (function) are
  distinct ids in the output, confirming `:static` suffix disambiguates correctly.

## Notes
The `:static` suffix is the critical disambiguation. Without it, static and instance methods
with the same name (or a static method and a same-named field) would share the same canonical id.
