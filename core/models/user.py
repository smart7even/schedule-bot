from sqlalchemy import Column, Integer, ForeignKey

from core.models.group import Group
from db import Base, Session


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))

    def __repr__(self) -> str:
        return f"User(id={self.id} group_id={self.group_id})"
