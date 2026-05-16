# Verification log: decorator_factories

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

`src/decorators.py` defines three factory/decorator functions at module scope
(`require_role`, `log_call`, `retry`), two decorated module-level functions
(`delete_record`, `fetch_data`), and a class `Service` with two methods.

Inner closures (`wrapper`, `decorator`) inside each factory body are NOT extracted —
they are function-local.

Predicted ids (9 total):
1. `fixture::src/decorators.py` (module)
2. `fixture::src/decorators.py::require_role` (function, no decorators)
3. `fixture::src/decorators.py::log_call` (function, no decorators)
4. `fixture::src/decorators.py::retry` (function, no decorators)
5. `fixture::src/decorators.py::delete_record` (function, decorators: ["require_role"])
6. `fixture::src/decorators.py::fetch_data` (function, decorators: ["require_role", "log_call", "retry"])
7. `fixture::src/decorators.py::Service` (class)
8. `fixture::src/decorators.py::Service.admin_action` (function, decorators: ["require_role"])
9. `fixture::src/decorators.py::Service.retried_action` (function, decorators: ["log_call", "retry"])

No packages. No edges.

Key decorator name predictions:
- `@require_role("admin")` → `"require_role"` (Call node, func resolved to Name)
- `@retry(times=5)` → `"retry"`
- `@retry()` → `"retry"`
- `@log_call` → `"log_call"`

## Prediction vs expected.json
- Matches: all 9 ids predicted correctly.
- Decorator name resolution via `_decorator_name` correctly strips call arguments.

## Expected vs actual (from running the extractor)
Ran extractor. Got exactly 9 primitives with the predicted ids. Decorator lists
confirmed by inspecting signature output: `fetch_data` carries
`["require_role", "log_call", "retry"]` in declaration (outermost-first) order.

- Matches: ✓ all 9

## Notes
The inner `wrapper` and `decorator` closures inside each factory are correctly absent.
`functools.wraps` only appears in the `wrapper` function signatures inside the factory
bodies — it never decorates a module-level or class-level definition in this fixture,
so it never appears in any extracted primitive's `decorators` list. That is the
intended design: the fixture documents that `functools.wraps` usage inside a factory
does not pollute the extracted decorator graph.
