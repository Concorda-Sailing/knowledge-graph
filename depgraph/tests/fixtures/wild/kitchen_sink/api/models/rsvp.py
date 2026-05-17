"""RSVP ORM model."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RSVP(Base):
    __tablename__ = "rsvps"

    def __repr__(self):
        return f"<RSVP id={self.id} event_id={self.event_id} user_id={self.user_id}>"
