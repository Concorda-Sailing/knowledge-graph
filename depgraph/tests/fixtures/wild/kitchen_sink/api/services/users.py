"""User service functions."""
from sqlalchemy.orm import Session
from ..models.user import User
from ..utils.format import build_event_url, parse_iso_date


def list_users_service():
    db: Session = Session()
    url = build_event_url("welcome")
    date = parse_iso_date("2026-01-01T00:00:00")
    results = db.query(User)
    return list(results)
