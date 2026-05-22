"""Hybrid ORM base shape: declarative wiring is plumbed through a
custom metaclass, not via inheritance from `DeclarativeBase`. Mirrors
the SQLModel pattern (issue #84) without naming it.

The detector must NOT find a known SQLAlchemy base name in the
inheritance chain — `_BaseMeta` is the metaclass, not a parent class
— so the only signal that subclasses are ORM models is the
`__tablename__ = "..."` assignment in their bodies.
"""


class _BaseMeta(type):
    """Stand-in for a declarative metaclass. Stubbed; the fixture only
    needs the shape so the extractor sees `metaclass=_BaseMeta`."""


class HybridBase(metaclass=_BaseMeta):
    """Project-level base for the hybrid ORM family. No SQLAlchemy
    base in its MRO — extension alone does NOT mark a subclass as an
    ORM model."""
