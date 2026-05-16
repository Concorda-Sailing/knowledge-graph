# Fixture: if_name_main

## What it tests

Two patterns that should produce zero primitives even though they look like
module-level definitions:

1. **`if __name__ == "__main__":` guard** — `GUARDED_CONSTANT`, `GuardedClass`, and
   `guarded_helper` are defined inside the `If` body. The extractor walks `tree.body`
   only (direct children of the module node), and `If` nodes are not
   `Assign`/`AnnAssign`/`ClassDef`/`FunctionDef`, so the entire block is skipped.
2. **`DynConfig = type("DynConfig", (), {…})`** — a dynamic class created via
   `type()`. The AST node is a plain `Assign` whose value is a `Call`. The extractor
   handles `Assign` by iterating its targets and emitting a `variable` primitive for
   each `ast.Name` target. `DynConfig` is therefore extracted as a **variable**, not
   a class. This is correct Phase 2 behavior: only `ClassDef` nodes emit class
   primitives.

## Why it's tricky

- The `if __name__ == "__main__":` pattern is idiomatic Python for "run this only
  when executed directly." Extracting the guarded definitions would incorrectly treat
  them as public module members. The extractor's tree.body-only walk naturally
  excludes them — a desirable accident of design, not a special case.
- `type()` creates a class at runtime but is syntactically an assignment. A classifier
  that inspects `value_text` could later detect this pattern and re-classify the
  variable primitive as a dynamic class, but that is a Phase 5 concern.
