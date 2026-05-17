"""RSVP service functions."""
from sqlalchemy.orm import Session
from ..models.rsvp import RSVP
from ..utils.validate import validate_email
from ..utils.slug import compute_rsvp_count


def rsvp_service(event_id: int, user_id: int, status: str):
    db: Session = Session()
    valid = validate_email("test@example.com")
    count = compute_rsvp_count([])
    rsvp = RSVP()
    db.add(rsvp)
    db.commit()
    return {"event_id": event_id, "user_id": user_id, "status": status}
