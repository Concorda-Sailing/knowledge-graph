# Fixture: relative_dots

## What it tests

Multi-level relative imports (`from ..sub import X`, `from ...pkg.sub import Y`) in a
real package hierarchy:

```
src/
  pkg/
    __init__.py        → package primitive: src/pkg
    sub/
      __init__.py      → package primitive: src/pkg/sub
      x.py             → module primitive + its own definitions
```

Phase 2 captures:
- Two `package` primitives (one per directory containing `__init__.py`)
- Three `module` primitives (one per `.py` file)
- Variables and functions defined in each module

Phase 2 does NOT capture:
- `imports` edges from `from ..sub import SUB_VERSION` or
  `from ...pkg.sub import SUB_VERSION` — those are Phase 3.3 edge work.

## Why it's tricky

1. **Package detection** — `_iter_py_files` finds all `.py` files; the package pass
   then identifies directories containing `__init__.py` and emits package primitives
   with the relative directory path as the id suffix. Nested packages (`src/pkg` and
   `src/pkg/sub`) each get their own primitive.

2. **Three-dot relative imports** — `from ...pkg.sub import X` has `level=3`. The
   extractor does not parse `ImportFrom` nodes at all in Phase 2, so three-dot syntax
   is transparent. The module that contains it (`x.py`) is emitted normally.

3. **`__init__.py` as a module** — `src/pkg/__init__.py` is both the marker that
   makes `src/pkg` a package AND a module that defines `PKG_VERSION`. Both the package
   primitive and the module primitive are emitted; they carry different ids
   (`fixture::src/pkg` vs `fixture::src/pkg/__init__.py`).
