# fuzzy_extends_variable_ts

A class whose `extends` target resolves to a `variable` primitive (i.e. a
const-factory base class) must NOT emit `extends -> variable` at
`confidence=exact` — the reconcile validator rejects it per
`EDGE_KIND_RULES["extends"].target = ["class"]`. The fix downgrades the
edge to `confidence=fuzzy`; the taxonomy is updated to permit `variable`
targets only under fuzzy confidence (#86).

## Pattern

```ts
function makeBase() { return class { tag() { return "base"; } }; }
const Factory = makeBase();              // <-- variable primitive
class Child extends Factory { /* ... */ } // <-- inheritance arrow
```

## Why tracked

Surfaced by the wild-corpus probe (#79) against `colinhacks/zod` — 107
edge_errors of the shape `edge 'extends' disallows target kind 'variable'`.
zod's v4 layout declares `ZodType` as `const ZodType = createZodType(...)`,
which extracts as a `variable`; v3's `types.ts` then does
`class ZodString extends ZodType { ... }`. The same pattern shows up across
mixin libraries, parameterized class factories, etc.

## v0 behavior

`attachInheritanceEdges` now looks up the resolved target's primitive kind
and chooses confidence accordingly:

- target.kind == "class"    -> confidence: "exact"
- target.kind == "variable" -> confidence: "fuzzy"
- target.kind == "function" -> confidence: "fuzzy"
- target external/unresolved -> existing behavior

`depgraph/lib/edges.py::validate_edge` permits `extends` (and `implements`)
to `variable`/`function` targets only when `confidence == "fuzzy"`. Exact
`extends -> variable` is still a taxonomy error.
