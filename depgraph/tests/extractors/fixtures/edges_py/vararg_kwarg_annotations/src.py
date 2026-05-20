"""Vararg / kwarg annotations seed var_types.

`def fan_out(*conns: Connection, **opts: Order)` previously skipped both
`vararg` and `kwarg`, so the bound names had no type even though the
annotation is right there. Method calls on either name then fell to the
unresolved sentinel.

Note: the runtime type of `conns` is `tuple[Connection, ...]`; seeding it
as `Connection` is intentionally a simplification — element-level vs.
container-level receiver semantics is a separate problem (#83 nests it
as a follow-up). Same caveat for `**opts` (runtime is `dict[str, Order]`)."""
from __future__ import annotations
from sqlalchemy.orm import Connection
from app.models import Order


def fan_out(*conns: Connection, **opts: Order):
    """Both `conns` (vararg) and `opts` (kwarg) carry annotations."""
    conns.append("ignored-by-runtime-but-still-a-method-call")
    opts.commit()
