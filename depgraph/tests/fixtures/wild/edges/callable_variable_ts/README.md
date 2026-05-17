# callable_variable_ts

A bare-name call site whose identifier resolves to a `variable` primitive (the
variable holds a function reference) must NOT produce a `calls → variable`
edge. The edge taxonomy at `depgraph/lib/edges.py::EDGE_KIND_RULES` requires
`calls.target = function`.

## Pattern

```ts
const aliased = realImpl;   // variable primitive, type=function-ref
function caller() {
  aliased(41);              // <-- the buggy case
  realImpl(1);              // <-- direct function call, fine
}
```

## Why tracked

Before the fix, `attachCallEdges`'s bare-id branch in extract.ts gated on
`!allClassIds.has(targetId)` only — so any non-class target (including
variables and modules) emitted a `calls` edge. Reconciliation's per-edge
target-kind validation flagged these as `edge_errors`, but the codegraph
regen masked the bug because the variable-targeted shim call was the only
in-the-wild example until the dynamic-import-shim fix landed.

## v0 behavior

The bare-id branch now gates on `allFunctionIds.has(targetId)` (positive
check). Only direct function-target calls emit a `calls` edge. Variable
references are picked up by the reads pass as
`reads function→variable`, preserving call-graph reachability without
violating taxonomy.
