# Verification log: overload_storm

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The source file `src/overloads.ts` contains:
- `parse`: 5 overload declarations (no body) + 1 implementation (has body)
- `Formatter`: class with overloaded constructor (2 decls + 1 impl) and overloaded `format` method (2 decls + 1 impl)
- `Formatter` also has two private properties via constructor parameter shorthand: `locale` and `options`

The extractor guards:
- `extractFunctions`: `if (!fn.hasBody()) continue` — so only the impl of `parse` emits
- Class methods: `if (!m.hasBody()) continue` — so only the impl of `format` emits
- Constructors: the extractor does NOT extract constructors as function primitives (only `getMethods()` is iterated, not `getConstructors()`)
- Class properties from constructor parameter shorthand (`private locale`, `private options`): these are `cls.getProperties()` in ts-morph, so they should emit as variable primitives

Expected primitives:
- `fixture::src` (primitive=package, owner=null) — src/ directory
- `fixture::src/overloads.ts` (primitive=module, owner=null) — the file
- `fixture::src/overloads.ts::parse` (primitive=function, owner=null) — only the impl
- `fixture::src/overloads.ts::Formatter` (primitive=class, owner=null) — the class
- `fixture::src/overloads.ts::Formatter.format` (primitive=function, owner=`fixture::src/overloads.ts::Formatter`) — only the impl method
- `fixture::src/overloads.ts::Formatter.locale` (primitive=variable, owner=`fixture::src/overloads.ts::Formatter`) — constructor parameter property
- `fixture::src/overloads.ts::Formatter.options` (primitive=variable, owner=`fixture::src/overloads.ts::Formatter`) — constructor parameter property (optional)

NOT expected:
- Any primitive for the 5 overload declarations of `parse`
- Any primitive for the 2 overload declarations of `format`
- Any primitive for the constructor itself

Expected edges: none beyond implicit structure

## Prediction vs expected.json
- Matches: 5 of 7 predicted primitives in original expected.json
- Discrepancies:
  - I predicted `Formatter.locale` and `Formatter.options` as variable primitives, reasoning
    that constructor parameter properties (e.g. `private locale`) would appear in
    `cls.getProperties()`. This was wrong — probing ts-morph confirmed `getProperties()` returns
    `[]` for parameter properties; they only appear via `ctor.getParameters()`. Removed from
    expected.json.

## Expected vs actual (from running the extractor)
- Matches: 5 of 5 (after correction)
- Discrepancies: none after correcting expected.json
- Key verification: `parse` appears exactly once (not 6 times), `Formatter.format` appears
  exactly once (not 3 times) — the `hasBody()` guard works correctly.

## Notes
- Constructor parameter properties (`private locale: string`) are NOT accessible via
  `cls.getProperties()` in ts-morph. They are only accessible through
  `ctor.getParameters()` filtered by `.isParameterProperty()` or scope check.
  The extractor currently does not walk constructor parameters, so these properties
  are invisible. This is a known limitation, not a bug — parameter properties are an
  enhancement target for a future task.
- The overload-deduplication guard (`hasBody()`) works correctly for both top-level
  functions and class methods.
