"""Tag endpoints."""
from fastapi import APIRouter
from ..services.events import list_events_service

router = APIRouter()


@router.get("/tags")
def list_tags():
    return list_events_service()
