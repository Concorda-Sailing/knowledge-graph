"""Tag ORM model."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Tag(Base):
    __tablename__ = "tags"

    def __repr__(self):
        return f"<Tag id={self.id} name={self.name}>"
