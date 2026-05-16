# decorator_target_resolution

Tests `decorates` edge resolution: local decorator → edge; external decorator → no `decorates` edge.

## Pattern
- `@my_decorator` (local) on `local_target` → `decorates` edge
- `@functools.lru_cache()` (external) on `external_target` → no `decorates` edge
- `@my_class_decorator` (local) on `LocalClass` → `decorates` edge

## v0 behavior

### Decorates edges
`_attach_decorator_edges` emits `decorates` only for locally-defined decorators.
External decorators (functools.*) resolve to `external::pypi::*` via imports and are skipped.
Class decorators also work: `@my_class_decorator` on `LocalClass` emits the edge.

### Side effect: decorator Call nodes generate calls edges
`ast.walk(fn_node)` traverses into decorator_list nodes. `@functools.lru_cache(maxsize=128)`
appears as an `ast.Call` inside the walk and triggers `_attach_call_edges`, which emits
an unresolved `calls` edge from `external_target` to `functools.lru_cache`.

This is a known v0 artifact: decorator calls are indistinguishable from body calls at the
ast.walk level. The effect is benign (unresolved external call), but a future pass should
exclude decorator_list from the body-call walk. Documented here as a known gap.
