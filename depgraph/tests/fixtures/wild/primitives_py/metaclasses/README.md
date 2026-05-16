# Fixture: metaclasses

## What it tests

Three metaclass patterns that naive extractors might mishandle:

1. `class Foo(metaclass=ABCMeta)` — `metaclass=` keyword in the class bases
   list. AST represents it as a keyword arg on `ClassDef.keywords`, not a
   base class in `ClassDef.bases`. The extractor must still emit Foo as a
   `class` primitive (it does — it never inspects bases at all).
2. `class Bar(type)` — a metaclass that is itself a class. Ordinary class
   extraction applies; the tricky part is that `__new__` and `__init__`
   must surface as function primitives owned by `Bar`.
3. `class ConcreteWithMeta(AbstractBase)` — a normal concrete subclass of
   the abstract base. Confirms the extractor doesn't try to resolve the
   metaclass chain and simply emits the class + its methods.

## Why it's tricky

`metaclass=` is not a base class; it lives in `ClassDef.keywords`. A
naive extractor that only reads `ClassDef.bases` might reject or misname
the class. The layered extractor ignores both `bases` and `keywords` for
primitive emission — only `ClassDef.name` matters for the id.
