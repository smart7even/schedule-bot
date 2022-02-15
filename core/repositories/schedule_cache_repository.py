from typing import Optional

from core.models.schedule_cache import ScheduleCache
from db import Session


class ScheduleCacheRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, group_id: int, week: int, text: str, markup: str):
        """saves cache in db"""
        session = self.session

        new_cache = ScheduleCache(
            group_id=group_id,
            week=week,
            text=text,
            markup=markup
        )
        session.add(new_cache)
        session.commit()

    def get(self, group_id: int, week: int) -> Optional[ScheduleCache]:
        return self.session.query(ScheduleCache).filter(ScheduleCache.group_id == group_id,
                                                        ScheduleCache.week == week).one_or_none()
