from sqlalchemy import Column, Integer, ForeignKey, String

from db import Base, Session


class ScheduleCache(Base):
    __tablename__ = "schedule_cache"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    week = Column(Integer)

    text = Column(String(3000))
    markup = Column(String(1000))

    @staticmethod
    def save(group_id: int, week: int, text: str, markup: str):
        session = Session()
        schedule_cache = session.query(ScheduleCache).filter(ScheduleCache.group_id == group_id,
                                                             ScheduleCache.week == week).one_or_none()

        new_cache = ScheduleCache(
            group_id=group_id,
            week=week,
            text=text,
            markup=markup
        )
        session.add(new_cache)
        session.commit()
        session.close()


def clear_schedule_cache():
    session = Session()
    session.execute("DELETE FROM schedule_cache")
    session.commit()
    session.close()