# Verification log: relative_dots

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

Package layout under `src/`:
- `src/pkg/__init__.py` → directory `src/pkg` has `__init__.py` → package primitive
- `src/pkg/sub/__init__.py` → directory `src/pkg/sub` has `__init__.py` → package primitive
- Three `.py` files → three module primitives

Per-file content:
- `src/pkg/__init__.py`: defines `PKG_VERSION: str = "1.0"` → variable primitive
- `src/pkg/sub/__init__.py`: defines `SUB_VERSION: str = "1.0"` → variable primitive
- `src/pkg/sub/x.py`: defines `EXPORT_KEY: str = …` (variable) + `def load()` (function)
  — the two `from ... import` statements are `ImportFrom` nodes, not handled in Phase 2

Predicted ids (9 total):
1. `fixture::src/pkg` (package)
2. `fixture::src/pkg/sub` (package)
3. `fixture::src/pkg/__init__.py` (module)
4. `fixture::src/pkg/__init__.py::PKG_VERSION` (variable)
5. `fixture::src/pkg/sub/__init__.py` (module)
6. `fixture::src/pkg/sub/__init__.py::SUB_VERSION` (variable)
7. `fixture::src/pkg/sub/x.py` (module)
8. `fixture::src/pkg/sub/x.py::EXPORT_KEY` (variable)
9. `fixture::src/pkg/sub/x.py::load` (function)

No edges — relative import edges are Phase 3.3.

## Prediction vs expected.json
- Matches: all 9 ids predicted correctly.
- Package/module split for `__init__.py` files correctly anticipated.

## Expected vs actual (from running the extractor)
Ran extractor. Got exactly 9 primitives with the predicted ids. The `from ..sub import`
and `from ...pkg.sub import` statements were transparently ignored. Both package
primitives emitted with directory paths (no `.py` suffix). Both `__init__.py` files
also emitted as module primitives (distinct ids from their package primitives).

- Matches: ✓ all 9

## Notes
**Package vs module duality of `__init__.py`:** The extractor emits a `package`
primitive for the directory (id = `repo::src/pkg`) and a separate `module` primitive
for the file (id = `repo::src/pkg/__init__.py`). A downstream consumer that wants to
link "module defines package" would add a `defines` edge between them in Phase 3.

**Relative import transparency:** `ImportFrom` nodes with `level > 0` (relative
imports) are never inspected by Phase 2. The three-dot syntax (`level=3`) parses
correctly in Python 3.x `ast.parse` — it does not raise a `SyntaxError` even if the
import would fail at runtime (the fixture's package structure is self-referential for
the three-dot case). Phase 3.3 will need to resolve the level + anchor module to
build the `imports` edge.
