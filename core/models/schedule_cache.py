from sqlalchemy import Column, Integer, ForeignKey, String

from db import Base, Session


class ScheduleCache(Base):
    """Schedule Cache model"""
    __tablename__ = "schedule_cache"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    week = Column(Integer)

    text = Column(String(3000))
    markup = Column(String(1000))


def clear_schedule_cache():
    """clears schedule cache stored in db"""
    session = Session()
    session.execute("DELETE FROM schedule_cache")
    session.commit()
    session.close()
