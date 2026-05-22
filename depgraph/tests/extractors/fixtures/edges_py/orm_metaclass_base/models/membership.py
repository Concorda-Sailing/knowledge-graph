"""Membership — metaclass-based ORM model with a FK back to Account."""
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from models.base import HybridBase


class Membership(HybridBase):
    __tablename__ = "memberships"

    # FK to accounts table — `ForeignKey("accounts.id")`.
    account_id = Column(Integer, ForeignKey("accounts.id"))

    # String reference back to Account.
    account = relationship("Account", back_populates="memberships")
