"""Multi-level attribute bases: `class X(a.b.Class)`.

The AST is `Attribute(Attribute(Name("sqlalchemy"), "orm"), "DeclarativeBase")`,
which the previous attribute-shape pre-check (only `Attribute(Name, attr)`)
ignored — falling through to the leaf-name path that resolved
"DeclarativeBase" against the empty imports table and landed on
`external::pypi::unknown::DeclarativeBase`. Fix walks down the chain to
find the root Name and uses it as the module local."""
from __future__ import annotations
import sqlalchemy.orm


class Account(sqlalchemy.orm.DeclarativeBase):
    """Multi-level external module + attr — synthesizes
    `external::pypi::sqlalchemy::DeclarativeBase` (root module local is
    `sqlalchemy`, which is what `import sqlalchemy.orm` actually binds)."""
    pass
