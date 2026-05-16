# Verification log: nested_everything

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

`src/nesting.py` defines:

- `Outer` (class) with:
  - `Inner` (nested class) with:
    - `Deepest` (doubly-nested class) with `deep_method` (function)
    - `inner_method` (function)
  - `x` (variable, `int = 0`)
  - `outer_method` (function) — body contains `LocalClass` and `local_helper` which are NOT extracted
- `top_func` (function) — body contains `FuncLocal` and `nested_def` which are NOT extracted

Expected extracted ids (9 total):
1. `fixture::src/nesting.py` (module)
2. `fixture::src/nesting.py::Outer` (class)
3. `fixture::src/nesting.py::Outer.Inner` (class, owner=Outer)
4. `fixture::src/nesting.py::Outer.Inner.Deepest` (class, owner=Outer.Inner)
5. `fixture::src/nesting.py::Outer.Inner.Deepest.deep_method` (function, owner=Outer.Inner.Deepest)
6. `fixture::src/nesting.py::Outer.Inner.inner_method` (function, owner=Outer.Inner)
7. `fixture::src/nesting.py::Outer.x` (variable, owner=Outer)
8. `fixture::src/nesting.py::Outer.outer_method` (function, owner=Outer)
9. `fixture::src/nesting.py::top_func` (function, owner=null)

NOT extracted (v0 limitation — function-local):
- `LocalClass`, `local_helper` (inside `outer_method`)
- `FuncLocal`, `FuncLocal.value`, `FuncLocal.method`, `nested_def` (inside `top_func`)

## Prediction vs expected.json
- Matches: all 9 ids predicted correctly.
- The non-extraction of function-local definitions was correctly anticipated.

## Expected vs actual (from running the extractor)
Ran extractor. Got exactly 9 primitives matching the expected ids. The function-local
classes and functions were correctly absent.

- Matches: ✓ all 9

## Notes
**v0 documented limitation:** Classes and functions defined inside a `FunctionDef`
body are not extracted. The extractor's walk boundary is the function signature node —
it emits the function primitive but does not recurse into its body for further
definitions. This is the correct behavior for Phase 2: function-local names are not
stable module-public primitives. The `LocalClass` inside `outer_method` and
`FuncLocal` inside `top_func` are runtime-only constructs.

If a future phase adds closure / local-scope tracking, this fixture's expected.json
will need to be extended and the limitation note removed.
