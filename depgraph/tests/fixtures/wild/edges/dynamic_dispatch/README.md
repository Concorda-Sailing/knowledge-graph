# dynamic_dispatch

Tests extractor soundness on computed callees (`getattr(obj, name)()`).

## Pattern
`dispatch_inline(obj: Handler, name: str)` calls `getattr(obj, name)()` directly.
`dispatch(obj: Handler, name: str)` calls `getattr(obj, name)` then `method()`.

## Why tricky
Computed callees — where `call.func` is itself a `Call` node — cannot be statically
resolved. The extractor must not crash, and should preserve information that a call
site exists.

## Behavior (post-#90)
`dispatch_inline`: `getattr(obj, name)()` — recognized by the dynamic-callee
detector. Emits `calls -> external::dynamic::getattr::<callsite>` with
`confidence: "dynamic"`. The dynamic bucket is the *irreducible* gap (no
static pass can close it), distinct from `unresolved_receiver` (typed-receiver
gaps the extractor could close).

`dispatch`: `method()` — `method` is a local variable (not module-scope), so
it's not in `local_names`; returns `[]` from the bare-Name branch.

## History
Pre-#90: emitted `external::unresolved::computed_callee` with
`unresolved_receiver` confidence. That collapsed runtime-only dispatch into
the typed-receiver bucket — wrong destination for maintainer triage.
