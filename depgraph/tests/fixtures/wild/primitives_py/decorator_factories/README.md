# Fixture: decorator_factories

## What it tests

Three decorator patterns applied to both module-level functions and class methods:

1. **Parameterized factory** (`@require_role("admin")`) — the decorator expression
   is a `Call` node. `_decorator_name` resolves to the function name `require_role`,
   discarding the argument.
2. **Plain decorator** (`@log_call`) — a simple `Name` node; resolves to `log_call`.
3. **Stacked decorators** (`@require_role("user") @log_call @retry(times=5)`) —
   three separate decorator nodes on one function; all three appear in the
   `signature.decorators` list in declaration order (outermost first).
4. **`functools.wraps`** inside factory bodies — these are applied to closures
   (`wrapper`) inside the factory functions. The closures are NOT extracted
   (they are function-local), so `functools.wraps` only appears if it decorates
   a module-level or class-level definition. In this fixture it does not — it
   is only used inside the factory bodies.

## Why it's tricky

- `Call` decorators (`@require_role("admin")`) must resolve to the callee name, not
  the full call expression. `_decorator_name` dispatches on `ast.Call` and recurses
  on `.func`, ensuring `require_role` is captured, not `require_role('admin')`.
- Stacked decorators on `fetch_data` test that all three are captured in order and
  that dotted names (`functools.lru_cache`) are preserved via the `Attribute` branch
  of `_decorator_name`.
- The inner `wrapper` closures defined inside `require_role`, `log_call`, and `retry`
  are function-local and are NOT extracted (same v0 limitation as nested_everything).
