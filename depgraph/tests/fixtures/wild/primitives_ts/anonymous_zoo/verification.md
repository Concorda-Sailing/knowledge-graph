# Verification log: anonymous_zoo

**Last reviewed:** 2026-05-22 by Claude (opus, #85 follow-up)
**Status:** ✓ verified

## 2026-05-22 update (#85)

The extractor now also emits a synthetic `variable` primitive at
`<file>::default` for every default-exporting module so consumers'
`import X from './mod'` edges never orphan. For this fixture's
`export default (input) => ...`, that adds one extra primitive:

- `fixture::src/anon.ts::default` (primitive=variable, owner=null)

The existing `<default:anon>` function primitive is unchanged.

## Pre-read prediction
*Written before looking at expected.json or running the extractor.*

The source file `src/anon.ts` contains:
1. `export const greet = (name: string): string => ...` — arrow function via variable decl
2. `export const handler = function myHandler(x: number): number { ... }` — named function expression via variable decl
3. `export const transform = (xs: number[]): number[] => ...` — arrow function via variable decl
4. `export default (input: string): boolean => ...` — anonymous arrow function as default export

The extractor handles these paths:
- Variable statements with arrow/function-expression initializers → function primitive using the decl name
- Export assignments with arrow/function-expression → synthetic name `<default:anon>`
- Named function expressions: extractor uses decl name (`handler`), not expression name (`myHandler`)

Expected primitives:

- `fixture::src/anon.ts` (primitive=module, owner=null) — the file itself
- `fixture::src/anon.ts::greet` (primitive=function, owner=null) — arrow function via variable decl
- `fixture::src/anon.ts::handler` (primitive=function, owner=null) — named function expression, but name taken from variable decl (`handler`), not inner name (`myHandler`)
- `fixture::src/anon.ts::transform` (primitive=function, owner=null) — arrow function via variable decl
- `fixture::src/anon.ts::<default:anon>` (primitive=function, owner=null) — anonymous default-exported arrow

No classes, no variables (all variable-decl initializers are functions so extractVariables skips them), no packages (src/ directory but file is directly under src/ so no sub-package dirs).

Expected edges (defines only, Phase 1):
- None needed beyond structural — the plan says Phase 1 edges are just `defines` which is implicit in owner.

## Prediction vs expected.json
- Matches: 5 of 5 predicted primitives present in expected.json
- Discrepancies: none — prediction correctly identified all 4 functions + module

## Expected vs actual (from running the extractor)
- Matches: 5 of 5 expected primitives present in actual output; 1 extra in actual
- Discrepancies:
  - Extra: `fixture::src` (primitive=package) — the `src/` directory is emitted as a package
    primitive by `packagePrimitives()`. I omitted this from my prediction because I focused on
    the file contents, forgetting that any source subdirectory generates a package node.
    Updated expected.json to include it. This is correct extractor behavior, not a bug.

## Notes
- The named function expression case (`handler = function myHandler()`) is subtle: extractFunctions
  iterates variable statements and uses `decl.getName()` (which gives `handler`), so the emitted
  primitive name is `handler`, not `myHandler`. This is correct behavior — the binding name is what
  matters for resolution.
- Going forward: always include a `fixture::src` package primitive in predictions whenever
  source files live under a `src/` subdirectory, since `packagePrimitives()` emits a node
  for every intermediate directory that contains source files.
