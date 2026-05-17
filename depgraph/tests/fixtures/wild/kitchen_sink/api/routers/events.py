"""Event endpoints."""
from fastapi import APIRouter
from ..services.events import create_event_service, list_events_service

router = APIRouter()


@router.post("/events")
def create_event(title: str, description: str, event_date: str, created_by: int):
    return create_event_service(title, description, event_date, created_by)


@router.get("/events")
def list_events():
    return list_events_service()
