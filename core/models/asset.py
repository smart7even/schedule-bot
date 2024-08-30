import sqlalchemy
from sqlalchemy import Column, Text

from db import Base


class Asset(Base):
    __tablename__ = 'asset'

    id = Column("id", Text, primary_key=True)
    content = Column("content", sqlalchemy.JSON)
