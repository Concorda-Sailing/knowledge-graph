"""User endpoints."""
from fastapi import APIRouter
from ..services.users import list_users_service

router = APIRouter()


@router.get("/users")
def list_users():
    return list_users_service()
