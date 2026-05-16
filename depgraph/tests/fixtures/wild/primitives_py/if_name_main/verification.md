# Verification log: if_name_main

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

`src/entrypoint.py` has genuine module-level definitions and guarded definitions.

Extracted (module-scope, direct tree.body children):
- `APP_NAME: str = "myapp"` → variable
- `DEBUG: bool = False` → variable
- `class Config` → class + fields `host`, `port` → variables
- `def setup_logging(…)` → function
- `def main()` → function
- `DynConfig = type("DynConfig", …)` → **variable** (Assign, not ClassDef)

NOT extracted (inside `If __name__ == "__main__":` body):
- `GUARDED_CONSTANT` (Assign inside If body)
- `GuardedClass` (ClassDef inside If body)
- `guarded_helper` (FunctionDef inside If body)

Predicted ids (9 total):
1. `fixture::src/entrypoint.py` (module)
2. `fixture::src/entrypoint.py::APP_NAME` (variable)
3. `fixture::src/entrypoint.py::DEBUG` (variable)
4. `fixture::src/entrypoint.py::Config` (class)
5. `fixture::src/entrypoint.py::Config.host` (variable)
6. `fixture::src/entrypoint.py::Config.port` (variable)
7. `fixture::src/entrypoint.py::setup_logging` (function)
8. `fixture::src/entrypoint.py::main` (function)
9. `fixture::src/entrypoint.py::DynConfig` (variable)

## Prediction vs expected.json
- Matches: all 9 ids predicted correctly.
- `DynConfig` correctly predicted as variable (not class).
- Guarded definitions correctly predicted as absent.

## Expected vs actual (from running the extractor)
Ran extractor. Got exactly 9 primitives. `GUARDED_CONSTANT`, `GuardedClass`, and
`guarded_helper` absent. `DynConfig` present as variable with
`value_text = "type('DynConfig', (), {'host': 'localhost'})"`.

- Matches: ✓ all 9

## Notes
**Desired behavior confirmed:** the `if __name__ == "__main__":` guard correctly
excludes its contents. This matches Python module-loading semantics — guarded blocks
run only when the file is the entry point, not when imported. Treating guarded
definitions as module primitives would produce phantom nodes for any module that is
both importable and executable.

**`DynConfig` as variable:** The `type()` call pattern is common in older codebases
and generated code. Emitting it as a variable is the correct Phase 2 behavior. A
future classifier could detect `value_text` matching `type(...)` and annotate the
node, but extraction stays agnostic to this.
