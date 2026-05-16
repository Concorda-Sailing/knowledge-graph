## Prediction (written before running extractor)

### Pattern
- `@my_decorator` (local function) on `local_target`
- `@functools.lru_cache()` (external) on `external_target`
- `@my_class_decorator` (local function) on `LocalClass`

### Expected behavior

#### `@my_decorator` on `local_target`:
- `local_target` signature.decorators = ["my_decorator"]
- `_attach_decorator_edges` finds `head = "my_decorator"` in `locals_ = {"my_decorator": fixture::src.py::my_decorator, ...}`
- `source_id = fixture::src.py::my_decorator` — NOT external
- `source_prim = my_decorator function primitive`
- Emits: `my_decorator` → `decorates` → `local_target` (exact)

#### `@functools.lru_cache()` on `external_target`:
- signature.decorators = ["functools.lru_cache"]
- `head = "functools"`, `locals_.get("functools") = None` (functools is imported, not a local def)
- `imports.get("functools")` — from `import functools`, local_binding="functools", target=external::pypi::functools
- `source_id = external::pypi::functools` → starts with "external::" → skip, no edge
- Captured in signature only.

#### `@my_class_decorator` on `LocalClass`:
- `LocalClass` has decorators = ["my_class_decorator"]
- `head = "my_class_decorator"` found in locals_
- `source_id = fixture::src.py::my_class_decorator`
- Emits: `my_class_decorator` → `decorates` → `LocalClass` (exact)

### Predicted edges (decorates only):
- `fixture::src.py::my_decorator` decorates `fixture::src.py::local_target` (exact)
- `fixture::src.py::my_class_decorator` decorates `fixture::src.py::LocalClass` (exact)
- NO edge for `external_target` (functools.lru_cache is external)
