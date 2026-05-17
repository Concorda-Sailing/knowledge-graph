"""Event ORM model."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    def __repr__(self):
        return f"<Event id={self.id} title={self.title}>"
