# circular_imports_ts

Tests that the TS extractor handles circular imports without crashing.

## Pattern
`a.ts` imports `greet` from `b.ts`; `b.ts` imports `hello` from `a.ts`.

## Why tricky
TypeScript's type checker supports circular imports via deferred module resolution.
The extractor must not enter infinite loops or crash when resolving specifiers.

## v0 behavior
ts-morph handles circular imports gracefully. Both import edges and cross-boundary
call edges resolve with `confidence: exact`. No crash, no deadlock.
