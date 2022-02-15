from sqlalchemy import Column, Integer, ForeignKey

from core.models.group import Group
from db import Base, Session


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))

    def set_group(self, group_id: int):
        """
        Sets user group in db
        :param group_id: group id in the university site
        """
        session = Session()

        user = session.query(User).filter(User.id == self.id).one()

        group = session.query(Group).filter(Group.id == group_id).one()
        user.group_id = group.id

        session.add(user)
        session.commit()
        session.close()

    def __repr__(self) -> str:
        return f"User(id={self.id} group_id={self.group_id})"
