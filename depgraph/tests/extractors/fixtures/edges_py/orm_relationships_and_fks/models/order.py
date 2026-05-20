from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK to accounts table.
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
