# Verification log: callable_variable_py

## Pre-read prediction

Without the fix: `caller()` walks the `aliased(41)` call, resolves `aliased`
to the module-level variable primitive id, the
`"instantiates" if target in classes_by_id else "calls"` ternary picks
"calls", and emits `calls -> fixture::consumer.py::aliased` (variable target).
Reconciliation rejects this as `calls.target = variable`.

With the fix: the bare-name branch checks `target in functions_by_id`. The
variable id isn't in that set, so no edge is emitted at the `aliased(41)`
site. The `real_impl(1)` site resolves to a function primitive and emits
`calls -> fixture::consumer.py::real_impl`.

## Prediction vs expected.json

Matches the fix-applied state.

## Notes

`real_impl` is itself a target of one `reads` edge from `caller` (because the
identifier `real_impl` is read where the alias is constructed at module
scope — that's the variable definition, not in `caller`'s body). The
`reads function->variable` from `caller` to `aliased` is the read-edge half
of the missing-`calls` story; both halves together preserve reachability.
