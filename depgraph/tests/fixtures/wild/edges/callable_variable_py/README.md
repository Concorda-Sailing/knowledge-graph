# callable_variable_py

Python counterpart to `callable_variable_ts/`. A module-level variable bound
to a function reference must not produce a `calls -> variable` edge.

## Pattern

```python
def real_impl(x: int) -> int: ...
aliased = real_impl     # variable primitive holding a function reference

def caller():
    aliased(41)         # <-- the buggy case
    real_impl(1)        # <-- direct call, fine
```

## v0 behavior

`_resolve_call_edge` (`depgraph/extractors/python/extract.py`) now checks the
resolved target's primitive kind:

- target in `classes_by_id` -> `instantiates`
- target in `functions_by_id` -> `calls`
- otherwise (variable, module, ...) -> no edge

The reads pass continues to emit `reads function->variable` for the
identifier read at the call site, so call-graph reachability is preserved
without violating taxonomy.
