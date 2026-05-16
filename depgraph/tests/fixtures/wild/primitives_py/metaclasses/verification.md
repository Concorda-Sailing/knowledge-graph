# Verification log: metaclasses

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

Three classes in `src/meta.py`:

`AbstractBase` — uses `metaclass=ABCMeta` keyword syntax. The AST node is still
`ClassDef` with `name="AbstractBase"`. Two abstract methods: `run`, `status`.
Expected primitives: class + 2 functions.

`TypeSubclass` — inherits from `type`, so it is a metaclass. Has `__new__` and
`__init__`. Expected: class + 2 functions.

`ConcreteWithMeta` — ordinary subclass of `AbstractBase`. Has `run` and `status`
implementations. Expected: class + 2 functions.

Plus module primitive `src/meta.py`. No packages (no `__init__.py`).

Predicted ids (10 total):
1. `fixture::src/meta.py` (module)
2. `fixture::src/meta.py::AbstractBase` (class)
3. `fixture::src/meta.py::AbstractBase.run` (function)
4. `fixture::src/meta.py::AbstractBase.status` (function)
5. `fixture::src/meta.py::TypeSubclass` (class)
6. `fixture::src/meta.py::TypeSubclass.__new__` (function)
7. `fixture::src/meta.py::TypeSubclass.__init__` (function)
8. `fixture::src/meta.py::ConcreteWithMeta` (class)
9. `fixture::src/meta.py::ConcreteWithMeta.run` (function)
10. `fixture::src/meta.py::ConcreteWithMeta.status` (function)

No id-collision risk here (all names distinct).

## Prediction vs expected.json
- Matches: all 10 ids predicted correctly.

## Expected vs actual (from running the extractor)
Ran extractor against `metaclasses/` fixture root. Got exactly 10 primitives with the
predicted ids. No extras, no missing.

- Matches: ✓ all 10

## Notes
The `metaclass=ABCMeta` keyword arg in `ClassDef.keywords` is never inspected by
the extractor; it only reads `ClassDef.name`. This means the metaclass= syntax is
transparent to the id system — correct behavior. The `@abstractmethod` decorator is
captured in the function signature's `decorators` list but does not affect the
primitive type (still `function`).
