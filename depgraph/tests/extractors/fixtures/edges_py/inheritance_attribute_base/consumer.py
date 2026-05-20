"""Attribute-style class bases: `import base; class X(base.BaseModel)`.

`_name_from_base` returns only the leaf attr name (`"BaseModel"`), which
isn't in the imports table — only `"base"` is. Inheritance resolution
needs to look the attr up inside the module's symbol table for this
shape to land an in-corpus edge."""
import base
import sqlalchemy


class FromInCorpusModule(base.BaseModel):
    """`import base; class X(base.BaseModel)` — in-corpus module + attr."""
    pass


class FromExternalModule(sqlalchemy.Base):
    """`import sqlalchemy; class X(sqlalchemy.Base)` — external module +
    attr; target synthesizes `external::pypi::sqlalchemy::Base`."""
    pass


class FromInCorpusUnknownAttr(base.NotARealClass):
    """Module is in-corpus but the attr doesn't name a class — should
    fall through to the unresolved sentinel, not crash."""
    pass
