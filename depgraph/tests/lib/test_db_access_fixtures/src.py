from sqlalchemy.orm import Session
from .models import User  # ORM model class

def get_user(session: Session, user_id):
    return session.query(User).filter(User.id == user_id).first()

def save_user(session: Session, user):
    session.add(user)
    session.commit()
