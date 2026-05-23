"""`with Cls(...) as r:` should seed `var_types[r]` to Cls's class id.

Before #91 (b3), the body walker only handled `ast.Assign` /
`ast.AnnAssign` / `ast.NamedExpr` — `ast.With` items were never inspected,
so `with Session(engine) as session: session.query(...)` (the canonical
SQLAlchemy shape) leaked every `session.X` call into the unresolved
bucket."""
from __future__ import annotations


class Resource:
    def __init__(self, name: str) -> None:
        self.name = name

    def __enter__(self) -> "Resource":
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def use(self) -> None:
        pass


def use_with():
    with Resource("x") as r:
        # `r.use(...)` should resolve to Resource.use, not
        # `external::unresolved::r.use`.
        r.use()
