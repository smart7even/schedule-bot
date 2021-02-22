from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
import os
import settings
from collections import namedtuple

Base = declarative_base()


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    groups = relationship("Group")

    def get_groups(self):
        return self.groups


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey('faculties.id', ondelete="CASCADE"))
    course = Column(Integer)

    @staticmethod
    def get_group_by_id(group_id: int):
        session = Session()

        group = session.query(Group).filter(Group.id == group_id).one()

        session.close()

        return group

    @staticmethod
    def get_all():
        session = Session()

        groups = session.query(Group).all()

        session.close()

        return groups

    def __repr__(self) -> str:
        return f"Group(group_id={self.id} group_name={self.name})"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))

    @staticmethod
    def get_user(user_id):
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
        session = Session()

        user = session.query(User).filter(User.id == self.id).one()

        group = session.query(Group).filter(Group.id == group_id).one()
        user.group_id = group.id

        session.add(user)
        session.commit()
        session.close()

    def __repr__(self) -> str:
        return f"User(id={self.id} group_id={self.group_id})"


DB = namedtuple("DB", ["user", "password", "host", "port"])

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

db = DB(db_user, db_password, db_host, db_port)
connect_url = f"postgresql+psycopg2://{db.user}:{db.password}@{db.host}:{db.port}/schedule-tg-bot"

engine = create_engine(connect_url, echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker()
Session.configure(bind=engine)
