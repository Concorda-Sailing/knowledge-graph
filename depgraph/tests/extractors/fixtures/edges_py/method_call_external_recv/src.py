"""Typed receivers backed by external imports — the SQLAlchemy / FastAPI
shape. The bare-name annotation cases that show up by the thousand in
real Python services."""
from sqlalchemy.orm import Session
from sqlalchemy.engine import Connection
from fastapi import APIRouter
from typing import Annotated, Optional, Union


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


def constructed():
    # Pattern 2: `db = Session()` — no annotation, but the constructor name
    # is an external class. The Pattern-2 path should accept external-shaped
    # class targets so downstream `db.query(...)` resolves like the
    # annotated cases above.
    db = Session()
    db.query("Account")


def union_recv(x: Union[Session, Connection]):
    # `x.execute()` could route to Session.execute OR Connection.execute —
    # both branches should be emitted so the reverse index records both
    # external classes as consumers.
    x.execute("SELECT 1")
