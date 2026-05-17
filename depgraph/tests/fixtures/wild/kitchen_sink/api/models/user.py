"""User ORM model."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"
