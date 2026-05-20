"""Inheritance from builtin classes (`class X(list)`, `class E(Exception)`).

Builtin names aren't in the imports table — they're implicit at runtime
— so the inheritance pass previously fell to
`external::pypi::unknown::list`. With the `_BUILTIN_CLASS_NAMES` check
the target becomes `external::builtins::list` (mirrors the receiver-type
shape used by `_annotation_class_ids`)."""
from __future__ import annotations


class Membership(list):
    """Extending a builtin container — common when modeling a typed
    collection of domain objects."""
    pass


class MembershipError(Exception):
    """Extending a builtin exception — equally common."""
    pass
