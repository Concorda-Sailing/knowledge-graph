"""Account — metaclass-based ORM model.

The class extends `HybridBase`, which is not a SQLAlchemy base name
and does not inherit from one. The only ORM signal is the
`__tablename__` assignment in the class body — the extractor must
treat the class as an ORM model on that signal alone.
"""
from sqlalchemy.orm import relationship

from models.base import HybridBase
from models.membership import Membership


class Account(HybridBase):
    __tablename__ = "accounts"

    # Direct class reference — `relationship(Membership, ...)`.
    memberships = relationship(Membership, back_populates="account")
    # String class reference — `relationship("Order", ...)`.
    orders = relationship("Order", back_populates="account")
