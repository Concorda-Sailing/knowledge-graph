# overload_storm

## What's tested

A standalone function with 5 overload declarations followed by 1 implementation signature,
and a class with methods that have multiple overload declarations followed by 1 implementation.

## Why a naive extractor would break

TypeScript overloads produce N+1 `FunctionDeclaration` nodes for a single logical function: N
declaration-only signatures (no body) plus 1 implementation with a body. A naive extractor that
iterates `sf.getFunctions()` without checking `fn.hasBody()` emits N+1 duplicate primitives with
the same name, polluting the graph with phantom nodes that have no implementation.

The guard `if (!fn.hasBody()) continue` (or equivalent on class methods) must be present. This
fixture verifies that exactly one primitive per overloaded name is emitted.
