"""Walrus operator, match/case, PEP 695 generic syntax."""
from __future__ import annotations

import re

# Walrus at module scope: the assignment expression binds `_version_match`
# in the enclosing scope (module), but only inside the `if` condition.
# The extractor walks tree.body; `if` nodes are not ast.Assign/AnnAssign,
# so `_version_match` is NOT extracted as a variable primitive.
if _version_match := re.match(r"(\d+)\.(\d+)", "3.12"):
    VERSION_MAJOR: int = int(_version_match.group(1))
    VERSION_MINOR: int = int(_version_match.group(2))

# Plain module-level constant (is extracted)
SCHEMA_VERSION: int = 2


def classify_input(value: object) -> str:
    """match/case — the match block is opaque to the extractor (not Assign/ClassDef/FunctionDef)."""
    match value:
        case 0 | None:
            return "empty"
        case int(n) if n > 0:
            return f"positive:{n}"
        case str(s) if s.startswith("http"):
            return "url"
        case {"type": t, **rest}:
            return f"mapping:{t}"
        case _:
            return "unknown"


# PEP 695 generic class — type_params appear on the ClassDef node
class Stack[T]:
    """Generic stack using PEP 695 syntax."""

    items: list[T]

    def push[U: T](self, item: U) -> None:
        """PEP 695 generic method — type_params on FunctionDef."""
        pass

    def pop(self) -> T:
        pass


# PEP 695 generic function
def first[T](items: list[T]) -> T:
    """Generic free function."""
    return items[0]


def zip_pairs[T, U](a: list[T], b: list[U]) -> list[tuple[T, U]]:
    """Two type parameters."""
    return list(zip(a, b))
