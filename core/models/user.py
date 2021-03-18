from sqlalchemy import Column, Integer, ForeignKey

from core.models.group import Group
from db import Base, Session


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))

    @staticmethod
    def get_user_by_id(user_id):
        """
        Gets user by id from db or creates user in db
        :param user_id: user id in Telegram
        :return: User object
        """
        session = Session()

        user = session.query(User).filter(User.id == user_id).one_or_none()

        if user:
            session.close()
            return user

        new_user = User(id=user_id)
        session.add(new_user)
        session.commit()
        session.close()

        return new_user

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
