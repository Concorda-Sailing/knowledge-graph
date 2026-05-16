## Prediction (written before running extractor)

### Pattern
`a.py` imports `greet` from `.b`; `b.py` imports `hello` from `.a`. Circular.

### Expected behavior
The extractor is index-based (no recursive resolution). It:
1. Parses all files and builds the full primitive list.
2. Then runs `_attach_imports_edges` which resolves using pre-built indexes.

No deadlock risk — the resolve pass is a single forward pass over `trees_by_path`.

### Import resolution
`a.py: from .b import greet`:
- level=1, module="b", path="a.py"
- base_parts = ["b"], candidate_path = "b.py"
- target_mod_prim = b.py module
- sym_by_path["b.py"]["greet"] = fixture::b.py::greet
- Edge: a.py imports fixture::b.py::greet (exact)

`b.py: from .a import hello`:
- level=1, module="a", path="b.py"
- base_parts = ["a"], candidate_path = "a.py"
- target_mod_prim = a.py module
- sym_by_path["a.py"]["hello"] = fixture::a.py::hello
- Edge: b.py imports fixture::a.py::hello (exact)

### Call edges
`hello()` in a.py calls `greet("world")`:
- imports_by_path["a.py"]["greet"] = fixture::b.py::greet
- Emits `calls -> fixture::b.py::greet` (exact)

`call_back()` in b.py calls `hello()`:
- imports_by_path["b.py"]["hello"] = fixture::a.py::hello
- Emits `calls -> fixture::a.py::hello` (exact)

### Predicted edges (non-defines)
- a.py (module): imports fixture::b.py::greet (exact)
- b.py (module): imports fixture::a.py::hello (exact)
- hello: calls fixture::b.py::greet (exact)
- call_back: calls fixture::a.py::hello (exact)

### No deadlock, no crash — confirmed by static analysis of index-based resolution.
