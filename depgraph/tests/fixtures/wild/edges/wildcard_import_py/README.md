# wildcard_import_py

`from x import *` pulls in every public name in `x`, but the extractor
doesn't statically resolve which symbols are bound (that would require
evaluating `__all__` or enumerating module contents at extraction time).
The right model is a single module-level edge with `confidence: "fuzzy"`.

## Pattern

```python
# consumer.py
from helpers import *
def use_them(): return util_a() + util_b()
```

## Why tracked

Before the fix, the extractor iterated `node.names` once with
`alias.name == "*"`, treated `*` like a regular symbol name, found no match
in the target module's symbol map, and fell back to the module id with
`confidence="exact"` and `local_binding="*"`. Two semantic problems:

- `confidence="exact"` lied: we didn't resolve to a specific symbol.
- `local_binding="*"` was meaningless: nothing else in the pipeline keys on
  the `*` binding.

## v0 behavior

Both the relative and absolute `ImportFrom` branches now short-circuit when
`alias.name == "*"`: emit one `imports` edge to the target module (or
`external::pypi::<root_pkg>` if the module isn't in-corpus) with
`via: "wildcard_import"`, `confidence: "fuzzy"`, and no `local_binding`.

The actual call sites (`util_a()`, `util_b()`) are then unresolved at the
calls pass — the bare-name branch can't find `util_a` in the local-symbol
map (no `local_binding` was attached to the wildcard edge), so it skips
emission. This is the v0 trade-off: we capture the module-level dependency
but not the symbol-level reachability through wildcards.
