"""Typed receivers backed by external imports — the SQLAlchemy / FastAPI
shape. The bare-name annotation cases that show up by the thousand in
real Python services."""
from sqlalchemy.orm import Session
from fastapi import APIRouter
from typing import Annotated, Optional


def list_users(db: Session):
    return db.query("Account").all()


def commit_tx(db: Session) -> None:
    db.add(object())
    db.commit()


def annotated_param(db: Annotated[Session, "Depends(get_db)"]):
    db.refresh(object())


def optional_param(db: Optional[Session]):
    db.flush()


def register(router: APIRouter):
    router.get("/health")


def reassigned():
    db: Session = _get_session()
    db.rollback()


def _get_session():
    return None
