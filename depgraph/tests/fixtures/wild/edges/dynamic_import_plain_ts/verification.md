# Verification log: dynamic_import_plain_ts

## Pre-read prediction

Without the new pass, the four `await import(...)` call expressions emit no
edges — they fall through the static-import loop (the call isn't an
`ImportDeclaration`) and the shim branch in `attachCallEdges` doesn't match
(no `new Function(...)` binding). The fixture's `expected.json` triples all
fail.

With the new pass:

- `await import("./helper")` → relative-resolver finds `src/helper.ts` in the
  module map → `imports` edge to `fixture::src/helper.ts`, confidence `exact`.
- `await import("some-pkg")` → bare → `external::npm::some-pkg`, fuzzy.
- `await import("@some-scope/some-pkg")` → scoped bare → leading segment is
  `@some-scope`, strip `@` → `external::npm::some-scope`, fuzzy.
- `` await import(`./${which}`) `` — template literal with interpolation
  (`NoSubstitutionTemplateLiteral` is the no-interp variant; this one is a
  `TemplateExpression`), so the literal-text guard fails → no edge.

## Prediction vs expected.json

Matches. Three edges, no template-spec edge, no orphans.

## Notes

The relative resolver tries `<base>.<ext>` and `<base>/index.<ext>` in
`EXTS` order. The fixture's `./helper` resolves to `src/helper.ts` on the
first candidate.
