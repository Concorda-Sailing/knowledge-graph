## Prediction (written before running extractor)

### Pattern
`client.users.get().filter().first()` inside `run(client: Client)`.

### Expected behavior — v0 semantics

`run` has param `client: Client`, so `var_types["client"] = fixture::src/src.py::Client`.

`client.users` is NOT a Call — it's an attribute access on `client`.
`client.users.get()` — the call's func is `ast.Attribute(value=ast.Attribute(...))`.
The outer `value` is itself an `ast.Attribute`, not an `ast.Name`, so
`_resolve_call_edge` hits the `isinstance(call.func.value, ast.Name)` check: False.
Falls through to "Chained attribute (a.b.c()) — unresolved for v0" → returns `[]`.

Same for `.filter()` and `.first()` — each is a chained call, all return `[]`.

**Prediction: zero calls edges from `run`. No unresolved edges either (v0 drops
chained calls entirely rather than emitting unresolved).**

### Structural edges
- `Client` extends nothing (no bases).
- `UserSet.get` defines return annotation `UserQuery`.
- `_attach_inheritance_edges` looks at `ast.ClassDef.bases` which is empty for all three.
- `module` defines `UserQuery`, `UserSet`, `Client`, `run`.
- `Client.__init__` is defined. The `self.users = UserSet()` is in the body of `__init__` —
  but `__init__` is a method, and `_attach_call_edges` walks methods too. `UserSet()` is a
  bare Name call with `var_types` empty (no param annotations). `UserSet` is in `local_names`
  as a class. So `__init__` emits an `instantiates` edge to `UserSet`.

**Predicted edges from `__init__`: instantiates -> UserSet.**
**Predicted edges from `run`: none (all chained, dropped by v0).**

### Accuracy check
Will run extractor and compare. Key signal: do chained calls produce zero edges or
one unresolved edge? v0 returns `[]` for chained attributes, so the answer is zero.
