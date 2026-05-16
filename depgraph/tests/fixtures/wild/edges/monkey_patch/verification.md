## Prediction (written before running extractor)

### Pattern
`SomeClass.method = lambda self, x: x * 2` at module level.

### Expected behavior

#### Lambda extraction
`_walk_module_body` handles `ast.FunctionDef` and `ast.AsyncFunctionDef` only.
Lambda nodes (`ast.Lambda`) are NOT extracted as function primitives.

#### Module-level assignment
`SomeClass.method = lambda ...` — the target is `ast.Attribute(value=ast.Name("SomeClass"), attr="method")`.
`_variable_primitives` iterates targets and does `if not isinstance(tgt, ast.Name): continue`.
Attribute targets are skipped. So NO variable primitive is emitted for the patch.

#### `use_it(obj: SomeClass)`
- `obj: SomeClass` binds `var_types["obj"] = fixture::src.py::SomeClass`
- `obj.method(5)` — recv=`obj`, method=`method`, recv_class_id=SomeClass
- `methods_by_class[SomeClass]["method"]` = `fixture::src.py::SomeClass.method` (the original method)
- Emits `calls -> fixture::src.py::SomeClass.method` (the original, not the patched lambda)

### Predicted edges
- `use_it`: `calls -> fixture::src.py::SomeClass.method` (exact) — points to original, not lambda
- Lambda: NOT extracted, NOT an edge source

### Out-of-scope behavior documented
The monkey-patch doesn't redirect existing `calls` edges. This is a known v0 limitation
documented in the plan: "the lambda IS extracted as a function primitive, but the
assignment doesn't redirect existing calls edges."

Actually, correction: the lambda is NOT extracted in the current implementation.
The plan's statement about lambda extraction was aspirational. The documented out-of-scope
behavior (no redirect of calls edges) holds either way.
