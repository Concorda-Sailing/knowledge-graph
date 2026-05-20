"""Walrus-operator (`name := Call()`) seeds var_types like Pattern 2.

`db := Session()` is `ast.NamedExpr`, not `ast.Assign`. Before the fix,
`_attach_call_edges` only walked Assign / AnnAssign, so `db` was never
typed and the downstream `db.query(...)` fell to
`external::unresolved::db.query`."""
from __future__ import annotations
from sqlalchemy.orm import Session


def use_walrus():
    """`if db := Session(): db.query(...)` — same shape as Pattern 2
    (name = constructor call), just nested inside an `if`."""
    if db := Session():
        db.query("accounts")
