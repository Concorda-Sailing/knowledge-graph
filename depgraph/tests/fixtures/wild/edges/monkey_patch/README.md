# monkey_patch

Tests extractor behavior when a class method is replaced at module scope via assignment.

## Pattern
`SomeClass.method = lambda self, x: x * 2` at module level.

## Why tricky
The assignment target is an Attribute (`SomeClass.method`), not a Name.
The lambda value is not a FunctionDef.

## v0 behavior
- Lambda is NOT extracted as a function primitive (extractor handles FunctionDef/AsyncFunctionDef only).
- The Attribute assignment target is skipped in `_variable_primitives`.
- `use_it(obj: SomeClass)` still emits `calls -> SomeClass.method` (the original definition).
- The monkey-patch does NOT redirect existing `calls` edges — v0 limitation.

## Out of scope
Redirecting calls edges to the patched function requires tracking assignment to Attribute
targets and resolving the lambda as a method replacement. Documented for future work.
