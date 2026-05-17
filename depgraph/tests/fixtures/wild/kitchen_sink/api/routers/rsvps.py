"""RSVP endpoints."""
from fastapi import APIRouter
from ..services.rsvps import rsvp_service

router = APIRouter()


@router.post("/events/{event_id}/rsvp")
def rsvp_event(event_id: int, user_id: int, status: str = "attending"):
    return rsvp_service(event_id, user_id, status)
