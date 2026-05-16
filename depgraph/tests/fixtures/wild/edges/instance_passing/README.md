# instance_passing

Tests method call resolution when the instance is passed as a typed parameter.

## Pattern
`process(svc: Service)` calls `svc.do_work()` and `svc.cleanup()`.

## Why tricky
The instance is not constructed inside the function — it arrives via parameter.
The extractor must resolve the type from the annotation, not from an assignment.

## v0 behavior
Parameter annotation `svc: Service` seeds `var_types["svc"]`.
Both `svc.do_work()` and `svc.cleanup()` emit `calls` edges with `confidence: exact`.
