## Prediction (written before running extractor)

### Pattern
`dispatch(obj: Handler, name: str)` calls `getattr(obj, name)` then `method()`.
`dispatch_inline(obj: Handler, name: str)` calls `getattr(obj, name)()` inline.

### Analysis

#### `dispatch`:
- `getattr(obj, name)` — bare Name call `getattr`. `getattr` is not in `local_names`
  (it's a builtin) or `imports`. So `_resolve_call_edge` returns `[]`.
- `method()` — bare Name call. `method` is a local variable (set in `method = getattr(...)`)
  but is NOT in `local_names` (which only contains module-scope symbols: `Handler`, `dispatch`,
  `dispatch_inline`). So returns `[]`.

#### `dispatch_inline`:
- `getattr(obj, name)()` — The outer call's `call.func` is `ast.Call(...)` (a computed callee).
  The extractor hits "Computed callee — unresolved" → returns `[]`.

### Current implementation
The current `_resolve_call_edge` returns `[]` for computed callees (no unresolved edge).

### Plan intent vs implementation
The plan states `dynamic_dispatch` should have `unresolved_edges_expected: true` and that
the extractor should produce `calls` edges with `confidence: "unresolved"`.

### Bug: extractor drops computed callees silently
Current code returns `[]` for computed callees. The plan intends an unresolved edge.
This is a REAL extractor bug surfaced by this fixture. FIX: emit an unresolved edge
for computed callees instead of returning `[]`.

### Fix plan
In `_resolve_call_edge`, change the final `return []` to emit an unresolved edge:
```python
return [{"target": "external::unresolved::computed_callee",
          "kind": "calls", "via": "computed_callee",
          "where": f"{path}:{call.lineno}",
          "confidence": "unresolved"}]
```

This matches the plan's intent and makes the unresolved_edges_expected gate work.

### After fix, predicted edges:
- `dispatch`: `calls -> external::unresolved::getattr` (getattr is a bare Name not in locals)
  Actually: `getattr` not in local_names → returns `[]` still. The `method()` call:
  `method` not in module scope → `[]`.
- `dispatch_inline`: `getattr(obj, name)()` → computed callee → unresolved edge emitted.

Wait — `getattr` is itself a bare Name. It's not in local_names (module scope only has Handler,
dispatch, dispatch_inline). So `getattr()` call returns `[]` from the bare Name branch too.
Only `dispatch_inline`'s inline form produces the computed-callee case.

**After fix: `dispatch_inline` emits at least one unresolved edge. `dispatch` does not.**
