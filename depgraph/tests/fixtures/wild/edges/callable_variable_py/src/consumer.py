"""A module-level binding to a function reference is a `variable` primitive,
not a `function`. Calling it bare must NOT produce `calls -> variable`.
"""


def real_impl(x: int) -> int:
    return x + 1


# `aliased` is a variable holding a function reference.
aliased = real_impl


def caller() -> int:
    # Without the fix: `calls -> fixture::consumer.py::aliased` (variable),
    # violating EDGE_KIND_RULES["calls"].target = ["function"].
    # With the fix: no `calls` edge here. The reads pass attributes the
    # relationship as `reads function->variable` separately.
    return aliased(41) + real_impl(1)
