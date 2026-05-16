# read_assign_global

Tests that `reads` and `assigns` edges are distinct and correctly emitted for module-scope variables.

## Pattern
`COUNTER = 0`, `NAME = "default"` at module scope.
- `get_counter()` reads COUNTER → `reads` edge
- `get_name()` reads NAME → `reads` edge
- `increment()` uses `COUNTER += 1` → `assigns` edge only (AugAssign target is Store; no separate Load node in AST)
- `reset()` assigns both → two `assigns` edges

## Why tricky
`COUNTER += 1` (AugAssign) could be confused with a read-then-write. At the AST level,
`AugAssign.target` is a `Name` with `Store` context — no separate `Load` node is emitted.
So only `assigns` is produced, not `reads`. This is correct AST semantics.

## v0 behavior
Reads and assigns edges correctly distinguished by `ast.Load` vs `ast.Store` context.
AugAssign produces only `assigns`. `global` statement nodes are not Name nodes, so
they produce no edges.
