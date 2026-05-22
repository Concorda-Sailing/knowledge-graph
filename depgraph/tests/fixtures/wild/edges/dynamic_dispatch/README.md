# dynamic_dispatch

Tests extractor soundness on computed callees (`getattr(obj, name)()`).

## Pattern
`dispatch_inline(obj: Handler, name: str)` calls `getattr(obj, name)()` directly.
`dispatch(obj: Handler, name: str)` calls `getattr(obj, name)` then `method()`.

## Why tricky
Computed callees — where `call.func` is itself a `Call` node — cannot be statically
resolved. The extractor must not crash, and should preserve information that a call
site exists.

## v0 behavior
`dispatch_inline`: `getattr(obj, name)()` — the outer call has a computed callee.
Emits `calls -> external::unresolved::computed_callee` with `confidence: "unresolved_receiver"` (the typed-receiver bucket; the `dynamic` confidence value is reserved for a future dedicated detector — see issue #53).

`dispatch`: `method()` — `method` is a local variable (not module-scope), so it's
not in `local_names`; returns `[]` from the bare-Name branch.

## Fix applied during Phase 3.8
Original implementation silently returned `[]` for computed callees. The plan
requires `unresolved_edges_expected: true`. Fixed by emitting an unresolved edge
instead of dropping the call site.
