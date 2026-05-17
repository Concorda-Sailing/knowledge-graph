# Verification log: callable_variable_ts

## Pre-read prediction

Without the fix: `caller()` walks the `aliased(41)` call expression, looks up
`aliased` in `localByPath`, finds the variable primitive id, the
`!allClassIds.has(targetId)` check passes (variables aren't classes), and
emits `calls → fixture::src/consumer.ts::aliased`. EDGE_KIND_RULES rejects it
as `calls.target = variable`.

With the fix: the bare-id branch checks `allFunctionIds.has(targetId)`. The
variable id isn't in that set, so no `calls` edge is emitted at the
`aliased(41)` site. The `realImpl(1)` site resolves to a function primitive
and emits `calls → fixture::src/consumer.ts::realImpl` as before.

## Prediction vs expected.json

Matches the fix-applied state: one `calls` edge, no taxonomy violations.

## Notes

The reads-pass attribution (`reads function→variable`) is exercised in the
broader read_assign_global fixture; here we focus on the calls/instantiates
taxonomy gate.
