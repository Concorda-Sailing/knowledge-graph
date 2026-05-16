# Verification log: dataclass_pydantic_namedtuple

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

`src/models.py` contains four classes. Predicted primitives:

- module: `fixture::src/models.py`
- `PointDC` (class, decorator: dataclass) + fields `x`, `y`, `tags` (variables)
- `PointDC3D` (class, decorator: dataclass) + field `z` (variable)
- `PointNT` (class, no decorator — NamedTuple via inheritance) + fields `x`, `y`, `label` (variables)
- `PointPydantic` (class, no decorator) + fields `x`, `y`, `label` (variables) + nested `Config` (class) + `Config.frozen` (variable)

Total: 1 module + 4 classes + 10 variables = 17 primitives.

The tricky prediction: `PointPydantic.Config` — is it extracted? Yes, because
`_emit_class` recurses into nested `ClassDef` nodes within a class body, and `Config`
is a `ClassDef` inside `PointPydantic`. Predicted: yes, extracted with owner
`fixture::src/models.py::PointPydantic`.

No packages (no `__init__.py`). No edges in Phase 2.

## Prediction vs expected.json
- Matches: all 17 ids predicted correctly.
- The `PointPydantic.Config` nested class recursion was correctly anticipated.

## Expected vs actual (from running the extractor)
Ran extractor. Got exactly 17 primitives matching the expected ids. No extras, no missing.

- Matches: ✓ all 17

## Notes
`PointDC3D` inherits from `PointDC` but the extractor does not resolve inheritance —
it only emits what is syntactically defined in `PointDC3D`'s body (just `z`). The
`x` and `y` fields inherited from `PointDC` do NOT re-appear under `PointDC3D`. This
is correct Phase 2 behavior; inheritance edges are a Phase 3 concern.
