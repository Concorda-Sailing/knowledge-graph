"""Event service functions."""
from sqlalchemy.orm import Session
from ..models.event import Event
from ..utils.format import format_date
from ..utils.slug import slugify


def create_event_service(title: str, description: str, event_date: str, created_by: int):
    db: Session = Session()
    slug = slugify(title)
    formatted = format_date(event_date)
    event = Event()
    db.add(event)
    db.commit()
    return {"slug": slug, "date": formatted}


def list_events_service():
    db: Session = Session()
    results = db.query(Event)
    return list(results)
