"""Three coexisting class styles with overlapping field names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

# Pydantic import kept as a plain string to avoid requiring the library
# at fixture-authoring time; the extractor reads AST, not runtime.
# In a real project this would be `from pydantic import BaseModel`.


@dataclass
class PointDC:
    """Dataclass with two annotated fields and one with a default factory."""
    x: float
    y: float
    tags: list[str] = field(default_factory=list)


@dataclass
class PointDC3D(PointDC):
    """Dataclass subclassing another dataclass — adds a third field."""
    z: float = 0.0


class PointNT(NamedTuple):
    """NamedTuple — fields are annotated assignments in the class body."""
    x: float
    y: float
    label: str = ""


# Simulated Pydantic model (no import needed for AST extraction)
class PointPydantic:
    """Looks like a Pydantic BaseModel but is a plain class here."""
    x: float
    y: float
    label: str

    class Config:
        frozen = True
