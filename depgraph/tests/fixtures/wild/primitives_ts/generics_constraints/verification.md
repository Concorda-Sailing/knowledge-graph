# Verification log: generics_constraints

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The source file `src/generics.ts` contains:
- `type Flatten<T>` — conditional type alias with one type param
- `class Repository<TEntity, TKey, TFilter, TResult>` — 4 constrained type params
  - field `items: Map<TKey, TEntity>` — class property
  - instance method `find(filter: TFilter): TResult`
  - instance method `set(key: TKey, entity: TEntity): void`
- `class Transformer` — non-generic class
  - instance method `transform<TIn, TOut>` — generic method on non-generic class

The extractor processes:
- `extractClasses`: `Flatten` (type alias → class primitive, template_parameters=["T"]),
  `Repository` (class, template_parameters=["TEntity","TKey","TFilter","TResult"]),
  `Transformer` (class, template_parameters=[])
- `extractFunctions`: `Repository.find`, `Repository.set`, `Transformer.transform`
  — all function primitives have `attributes.template_parameters: []` (the extractor
    does not capture method-level type params — known limitation)
- `extractVariables`: `Repository.items` (class field)
- `packagePrimitives`: `fixture::src`

Expected primitives:
- `fixture::src` (primitive=package, owner=null)
- `fixture::src/generics.ts` (primitive=module, owner=null)
- `fixture::src/generics.ts::Flatten` (primitive=class, owner=null) — type alias, template_parameters=["T"]
- `fixture::src/generics.ts::Repository` (primitive=class, owner=null) — template_parameters=["TEntity","TKey","TFilter","TResult"]
- `fixture::src/generics.ts::Repository.find` (primitive=function, owner=`fixture::src/generics.ts::Repository`)
- `fixture::src/generics.ts::Repository.set` (primitive=function, owner=`fixture::src/generics.ts::Repository`)
- `fixture::src/generics.ts::Repository.items` (primitive=variable, owner=`fixture::src/generics.ts::Repository`)
- `fixture::src/generics.ts::Transformer` (primitive=class, owner=null) — template_parameters=[]
- `fixture::src/generics.ts::Transformer.transform` (primitive=function, owner=`fixture::src/generics.ts::Transformer`)

Expected edges: none

## Prediction vs expected.json
- Matches: 9 of 9 — prediction exactly matched expected.json
- Discrepancies: none

## Expected vs actual (from running the extractor)
- Matches: 9 of 9 — all expected primitives present, no extras
- Discrepancies: none
- Key verifications:
  - `Repository.attributes.template_parameters` = ["TEntity","TKey","TFilter","TResult"] — 4 names, no constraint text
  - `Flatten.attributes.template_parameters` = ["T"] — conditional type alias works correctly
  - `Transformer.transform` has no template_parameters ([] by default) — method-level type params not captured, as predicted

## Notes
- Constraint text (e.g. `extends Record<string, unknown>`) must NOT appear in
  `attributes.template_parameters` — only the bare name (e.g. `"TFilter"`) should.
- Method-level type params on `transform<TIn, TOut>` are not captured (known limitation).
- The `Flatten` conditional type alias emits as a class primitive (same path as all type aliases).
