import json
from typing import Optional

from telegram import InlineKeyboardMarkup

from core.models.current_week import get_current_week
from core.repositories.group_repository import GroupRepository
from core.repositories.schedule_cache_repository import ScheduleCacheRepository
from core.repositories.user_repository import UserRepository
from core.types.response import DefaultResponse
from db import Session
from core.button.markup import transform_markup_to_str
from core.schedule.schedule_repsonse import ScheduleCreator


class ScheduleService:
    def __init__(self, session: Session):
        self.session = session

    def get_schedule(self, group_id: int, week: Optional[int] = None) -> DefaultResponse:
        """
        :param group_id: group id in the university site
        :param week: study week number from the start of study year
        :return: DefaultResponse object
        """
        session = self.session
        group_repository = GroupRepository(session)
        group = group_repository.get_group_by_id(group_id)

        schedule_cache_repository = ScheduleCacheRepository(session)
        schedule_cache = schedule_cache_repository.get(group_id=group_id, week=week)

        response = DefaultResponse()
        if schedule_cache:
            response.text = schedule_cache.text
            response.markup = InlineKeyboardMarkup.de_json(json.loads(schedule_cache.markup), bot=None)
        else:
            if group:
                schedule_creator = ScheduleCreator(group_id, week)
                response = schedule_creator.form_response(group.name)
                # schedule_cache_repository.add(
                #     group_id=group_id,
                #     week=week,
                #     text=response.text,
                #     markup=transform_markup_to_str(response.markup)
                # )
                session.close()
            else:
                response = DefaultResponse()

        session.close()

        return response

    def get_user_schedule(self, user_id: int) -> DefaultResponse:
        """
        gets schedule by user id
        :param user_id: user id in Telegram
        :return: DefaultResponse object
        """
        user_repository = UserRepository(self.session)
        user = user_repository.get_user_by_id(user_id)

        current_week = get_current_week().week

        response = self.get_schedule(user.group_id, current_week)
        self.session.close()

        return response
