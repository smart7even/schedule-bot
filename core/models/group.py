from sqlalchemy import Column, Integer, String, ForeignKey

from db import Base, Session


class Group(Base):
    """Group model"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey('faculties.id', ondelete="CASCADE"))
    course = Column(Integer)

    def __repr__(self) -> str:
        return f"Group(group_id={self.id} group_name={self.name})"
