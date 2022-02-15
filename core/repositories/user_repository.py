from core.models.user import User
from db import Session


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_id(self, user_id: int) -> User:
        """
        Gets user by id from db or creates user in db
        :param user_id: user id in Telegram
        :return: User object
        """
        session = self.session

        user = session.query(User).filter(User.id == user_id).one_or_none()

        if user:
            session.close()
            return user

        new_user = User(id=user_id)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        session.close()

        return new_user
