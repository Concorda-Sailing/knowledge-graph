# Verification log: walrus_match_pep695

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

`src/modern.py` contains:

- `if _version_match := re.match(…):` — walrus inside `If` test. `If` node is in
  `tree.body` but is not `Assign`/`AnnAssign`/`ClassDef`/`FunctionDef`, so it is
  skipped. `VERSION_MAJOR` and `VERSION_MINOR` are inside the `If` body — also
  skipped. Neither the walrus binding nor the two constants are extracted.
- `SCHEMA_VERSION: int = 2` — top-level `AnnAssign` at `tree.body` level. Extracted.
- `def classify_input(…)` — `FunctionDef` at module scope. Extracted. The `match`
  statement inside its body is transparent.
- `class Stack[T]` — `ClassDef` with PEP 695 type params. Extracted as class.
  Members: `items` (AnnAssign variable) + `push` (method with type param `U`) +
  `pop` (method).
- `def first[T](…)` — generic function. Extracted.
- `def zip_pairs[T, U](…)` — two type params. Extracted.

Predicted ids (9 total):
1. `fixture::src/modern.py` (module)
2. `fixture::src/modern.py::SCHEMA_VERSION` (variable)
3. `fixture::src/modern.py::classify_input` (function)
4. `fixture::src/modern.py::Stack` (class)
5. `fixture::src/modern.py::Stack.items` (variable)
6. `fixture::src/modern.py::Stack.push` (function)
7. `fixture::src/modern.py::Stack.pop` (function)
8. `fixture::src/modern.py::first` (function)
9. `fixture::src/modern.py::zip_pairs` (function)

NOT extracted: `_version_match` (walrus), `VERSION_MAJOR`, `VERSION_MINOR`
(inside If body).

## Prediction vs expected.json
- Matches: all 9 ids predicted correctly.
- The walrus and If-body exclusions were correctly anticipated.

## Expected vs actual (from running the extractor)
Ran extractor. Got exactly 9 primitives. `VERSION_MAJOR` and `VERSION_MINOR` absent
as predicted. `SCHEMA_VERSION` present. PEP 695 classes/functions extracted normally.

- Matches: ✓ all 9

## Notes
**Walrus at module scope:** `NamedExpr` nodes are never `Assign` or `AnnAssign`, so
they are invisible to the extractor regardless of where they appear. Variables bound
only via walrus are not module primitives — correct Phase 2 behavior.

**`VERSION_MAJOR` / `VERSION_MINOR`:** These are `AnnAssign` nodes but they live
inside the `If` body, not at `tree.body` level. `_walk_module_body` only iterates
`tree.body` (the top-level statement list), so they are excluded. This matches Python
semantics: these assignments only execute when `__name__ != "__main__"` AND the regex
matches — they are conditional, not unconditionally module-public.

**PEP 695 template_parameters:** `Stack` carries `template_parameters: ["T"]` in its
`attributes`; `Stack.push` carries `["U"]`; `first` carries `["T"]`; `zip_pairs`
carries `["T", "U"]`. These are stored but not tested by the id-set comparison in the
harness — a future attribute-level test could verify them.
