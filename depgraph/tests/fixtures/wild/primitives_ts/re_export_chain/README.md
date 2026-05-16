# re_export_chain

## What's tested

A 3-hop barrel re-export chain:
- `src/impl.ts` — defines the actual implementation (class + function)
- `src/barrel.ts` — re-exports everything from `src/impl.ts` (`export * from "./impl"`)
- `src/index.ts` — re-exports everything from `src/barrel.ts` (`export * from "./barrel"`)

## Why a naive extractor would break

A naive extractor that only emits primitives for files that contain top-level declarations
would emit nothing for barrel files (they contain only `export * from ...` statements, no
function/class/variable declarations). That is actually correct behavior for Phase 1.

A subtler failure: a naive extractor might try to follow `export *` chains and emit
duplicated primitives from `impl.ts` under the ids of `barrel.ts` and `index.ts`, producing
3x duplicates of every declaration. Phase 1 must emit each primitive exactly once, from the
file where it is declared, regardless of re-export chains.

Phase 3.3 will add `re_exports` edges between the barrel modules. For now, expected.json
captures only the primitives from `impl.ts`; the barrel files emit only module primitives
(no class/function/variable primitives, since they contain no declarations).
