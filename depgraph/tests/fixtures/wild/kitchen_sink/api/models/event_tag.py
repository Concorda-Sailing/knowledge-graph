"""EventTag ORM model."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class EventTag(Base):
    __tablename__ = "event_tags"

    def __repr__(self):
        return f"<EventTag id={self.id} event_id={self.event_id} tag_id={self.tag_id}>"
