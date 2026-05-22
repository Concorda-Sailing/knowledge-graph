"""ORM family that encodes relationship targets in the annotation
rather than as a positional arg to the relationship call.

Mirrors the SQLModel pattern (issue #84): the base class is named
`HybridBase` to keep the fixture framework-agnostic, but the wire
shape — `field: Target | None = Relationship(...)` — is the exact
SQLModel call site.

`HybridBase` is in `_SQLA_BASE_NAMES` via the `SQLModel`-style alias?
No — we make subclasses match through `__tablename__` instead, so the
detector branch under test is the body-level tablename signal AND
the annotation-target resolver.
"""


class _BaseMeta(type):
    """Stand-in declarative metaclass."""


class HybridBase(metaclass=_BaseMeta):
    """Project-level base. No SQLAlchemy ancestor — subclasses must
    rely on `__tablename__` to be picked up by the ORM pass."""


def Relationship(*args, **kwargs):  # pragma: no cover - fixture stub
    """Stand-in for the framework's `Relationship` constructor. The
    extractor keys off the callee name, not the import source."""
    return None
