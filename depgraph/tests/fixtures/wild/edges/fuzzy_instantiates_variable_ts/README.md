# fuzzy_instantiates_variable_ts

A function whose `new X(...)` target resolves to a `variable` primitive (a
const-factory / `$constructor`-style binding) must NOT emit `instantiates
-> variable` at `confidence=exact` — the reconcile validator rejects it per
`EDGE_KIND_RULES["instantiates"].target = ["class"]` (pre-fix). The fix
downgrades the edge to `confidence=fuzzy`; the taxonomy is updated to
permit `variable` (and `function`) targets only under fuzzy confidence
(#88).

## Pattern

```ts
function makeFactory() { return class { name() { return "made"; } }; }
export const Factory = makeFactory();         // <-- variable primitive
export function makeOne() { return new Factory(); } // <-- instantiates arrow
```

## Why tracked

Surfaced by the wild-corpus probe (#79) against `colinhacks/zod` — 71
edge_errors of the shape `edge 'instantiates' disallows target kind
'variable'`. zod's v4 layout declares `export const ZodObject =
core.$constructor("ZodObject", ...)`, and `schemas.ts` then does
`return new ZodObject(def)` inside the `object()` / `strictObject()` /
`looseObject()` factory functions. Same pattern shows up across
class-factory libraries that share a name between an `interface ZodObject`
type-side declaration (a `class` primitive) and the const-bound
runtime constructor (`variable`), where the two collide on canonical id
and reconcile resolves the kind to the variable.

## v0 behavior

`attachCallAndVarAccessEdges` now looks up the resolved target's primitive
kind in a side index and chooses confidence accordingly:

- target.kind == "class"    -> confidence: "exact"  (mainline `new Cls()`)
- target.kind == "variable" -> confidence: "fuzzy"
- target.kind == "function" -> confidence: "fuzzy"
- target external/unresolved/other -> dropped (existing 21ee469 behavior)

`depgraph/lib/edges.py::validate_edge` permits `instantiates` to
`variable`/`function` targets only when `confidence == "fuzzy"`. Exact
`instantiates -> variable` is still a taxonomy error, which catches
extractor regressions.
