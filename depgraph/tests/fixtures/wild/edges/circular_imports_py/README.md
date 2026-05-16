# circular_imports_py

Tests that the extractor handles circular imports between Python modules without deadlocking.

## Pattern
`a.py` imports `greet` from `b.py`; `b.py` imports `hello` from `a.py`.

## Why tricky
Circular imports deadlock Python's import machinery at runtime. The static extractor
must resolve both without following import chains recursively.

## v0 behavior
The extractor is index-based: it parses all files first, builds the full symbol index,
then runs a single forward pass to resolve imports. No recursion, no deadlock.
Both imports resolve to their actual targets with `confidence: exact`.
Calls across the circular boundary also resolve correctly.
