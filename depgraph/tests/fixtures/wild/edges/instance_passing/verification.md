## Prediction (written before running extractor)

### Pattern
`process(svc: Service, value: int)` calls `svc.do_work(value)` and `svc.cleanup()`.

### Expected behavior
Parameter annotation `svc: Service` → `var_types["svc"] = fixture::src.py::Service`.
`value: int` → `int` is not in `local_names` or `imports` as a class → no binding.

`svc.do_work(value)`:
- `call.func = ast.Attribute(value=ast.Name("svc"), attr="do_work")`
- `recv = "svc"`, `method = "do_work"`
- `recv_class_id = var_types["svc"] = fixture::src.py::Service`
- `method_id = methods_by_class[Service]["do_work"] = fixture::src.py::Service.do_work`
- Emits `calls -> fixture::src.py::Service.do_work, confidence: exact`

`svc.cleanup()`:
- Same path → `calls -> fixture::src.py::Service.cleanup, confidence: exact`

`value` inside `svc.do_work(value)` is a bare Name in a Call argument — the outer Call
is `svc.do_work(value)`, not `value()`. So no edge from `value` lookup.

### Predicted edges from `process`:
- `calls -> fixture::src.py::Service.do_work` (exact)
- `calls -> fixture::src.py::Service.cleanup` (exact)

### No `instantiates` edges — `process` receives an existing instance, does not construct.
