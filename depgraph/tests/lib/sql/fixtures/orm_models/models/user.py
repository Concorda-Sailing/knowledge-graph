from .base import Base

class User(Base):
    __tablename__ = "users"
    # In real ORM models columns are defined here too, but we only need
    # tablename for the cross-reference test.
