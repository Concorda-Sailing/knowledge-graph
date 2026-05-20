from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK to accounts table — `ForeignKey("accounts.id")`.
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))

    # String reference back to Account.
    account: Mapped["Account"] = relationship("Account",
                                                back_populates="memberships")
