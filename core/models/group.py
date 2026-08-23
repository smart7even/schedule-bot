from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.sql import func

from db import Base, Session


class Group(Base):
    """Group model"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey('faculties.id', ondelete="CASCADE"))
    course = Column(Integer)
    is_active = Column(Boolean, nullable=False, default=True, server_default='true')
    first_seen_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    last_seen_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    missing_since = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"Group(group_id={self.id} group_name={self.name})"
