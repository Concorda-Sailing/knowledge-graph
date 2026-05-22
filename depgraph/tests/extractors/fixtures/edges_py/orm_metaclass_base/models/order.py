"""Order — metaclass-based ORM model with a FK to accounts."""
from sqlalchemy import Column, ForeignKey, Integer

from models.base import HybridBase


class Order(HybridBase):
    __tablename__ = "orders"

    # FK to accounts table.
    account_id = Column(Integer, ForeignKey("accounts.id"))
