from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.membership import Membership


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Direct class reference — `relationship(Membership, ...)`.
    memberships: Mapped[list["Membership"]] = relationship(Membership,
                                                            back_populates="account")
    # String class reference — `relationship("Order", ...)`.
    orders: Mapped[list["Order"]] = relationship("Order",
                                                  back_populates="account")
