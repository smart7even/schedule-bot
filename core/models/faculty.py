from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from db import Base, Session


class Faculty(Base):
    """Faculty model"""
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    groups = relationship("Group")

    def get_groups(self):
        """returns groups that belong to the faculty"""
        return self.groups
