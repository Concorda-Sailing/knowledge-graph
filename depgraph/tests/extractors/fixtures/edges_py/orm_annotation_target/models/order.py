"""Order — annotation-target relationship lookup target. Referenced
from Account via a forward-ref string (`list["Order"]`)."""
from models.base import HybridBase, Relationship


class Order(HybridBase):
    __tablename__ = "orders"

    # Forward-ref string back to Account (cross-file). Pins the
    # corpus-wide classname-index path through the annotation walker.
    account: "Account" = Relationship(back_populates="orders")  # noqa: F821
