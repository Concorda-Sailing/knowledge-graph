# Verification log: decorator_stack

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The source file `src/decorated.ts` contains:
- 5 standalone functions: `log`, `Role`, `Guard`, `Audit`, `Deprecated` — all top-level named functions with bodies
- `class ApiController` with two instance methods: `handleRequest` and `deleteRecord`

The extractor will:
- `packagePrimitives`: emit `fixture::src` package
- `moduleFor`: emit `fixture::src/decorated.ts` module
- `extractClasses`: emit `ApiController` class
- `extractFunctions` top-level: emit `log`, `Role`, `Guard`, `Audit`, `Deprecated`
- `extractFunctions` class methods: emit `ApiController.handleRequest` and `ApiController.deleteRecord`,
  each with `signature.decorators` populated from `m.getDecorators().map(d => d.getName())`

For `handleRequest`: decorators = ["log", "Role", "Guard", "Audit"]
For `deleteRecord`: decorators = ["log", "Role", "Guard", "Audit", "Deprecated"]

Key: `d.getName()` returns the identifier only, not the argument list (confirmed by probe).

Expected primitives:
- `fixture::src` (primitive=package, owner=null)
- `fixture::src/decorated.ts` (primitive=module, owner=null)
- `fixture::src/decorated.ts::log` (primitive=function, owner=null)
- `fixture::src/decorated.ts::Role` (primitive=function, owner=null)
- `fixture::src/decorated.ts::Guard` (primitive=function, owner=null)
- `fixture::src/decorated.ts::Audit` (primitive=function, owner=null)
- `fixture::src/decorated.ts::Deprecated` (primitive=function, owner=null)
- `fixture::src/decorated.ts::ApiController` (primitive=class, owner=null)
- `fixture::src/decorated.ts::ApiController.handleRequest` (primitive=function, owner=`fixture::src/decorated.ts::ApiController`)
- `fixture::src/decorated.ts::ApiController.deleteRecord` (primitive=function, owner=`fixture::src/decorated.ts::ApiController`)

Expected edges: none

## Prediction vs expected.json
- Matches: 10 of 10 — prediction exactly matched expected.json
- Discrepancies: none

## Expected vs actual (from running the extractor)
- Matches: 10 of 10 — all expected primitives present, no extras
- Discrepancies: none
- Key verification: `ApiController.handleRequest.signature.decorators` = ["log", "Role", "Guard", "Audit"]
  and `ApiController.deleteRecord.signature.decorators` = ["log", "Role", "Guard", "Audit", "Deprecated"]
  — all 4 and 5 decorators captured, parameterized ones produce clean names without argument lists.

## Notes
The probe confirmed `d.getName()` returns plain identifier names for both plain and
parameterized decorators. The `signature.decorators` array for `handleRequest` should be
["log", "Role", "Guard", "Audit"] — clean names, no argument lists.
