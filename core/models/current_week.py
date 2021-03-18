from sqlalchemy import Column, Integer, DateTime

from db import Base, Session


class CurrentWeek(Base):
    """Current week model"""
    __tablename__ = "current_week"

    week = Column(Integer)
    date = Column(DateTime, primary_key=True)


def get_current_week() -> CurrentWeek:
    """Gets current week"""
    session = Session()

    current_week = session.query(CurrentWeek).order_by(CurrentWeek.date.desc()).first()

    session.close()

    return current_week
