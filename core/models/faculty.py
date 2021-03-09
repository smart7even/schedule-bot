from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from db import Base, Session


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    groups = relationship("Group")

    @staticmethod
    def get_all():
        session = Session()

        faculties = session.query(Faculty).all()

        session.close()

        return faculties

    def get_groups(self):
        return self.groups
