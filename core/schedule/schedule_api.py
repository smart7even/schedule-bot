import json
from typing import Optional

from telegram import InlineKeyboardMarkup

from core.models.current_week import get_current_week
from core.models.group import Group
from core.models.schedule_cache import ScheduleCache
from core.repositories.user_repository import UserRepository
from core.types.response import DefaultResponse
from db import Session
from core.button.markup import transform_markup_to_str
from core.schedule.schedule_repsonse import ScheduleCreator


def get_schedule(group_id: int, week: Optional[int] = None) -> DefaultResponse:
    """

    :param group_id: group id in the university site
    :param week: study week number from the start of study year
    :return: DefaultResponse object
    """
    group = Group.get_group_by_id(group_id)

    session = Session()
    schedule_cache = session.query(ScheduleCache).filter(ScheduleCache.group_id == group_id,
                                                         ScheduleCache.week == week).one_or_none()
    session.close()

    response = DefaultResponse()
    if schedule_cache:
        response.text = schedule_cache.text
        response.markup = InlineKeyboardMarkup.de_json(json.loads(schedule_cache.markup), bot=None)
    else:
        if group:
            schedule_creator = ScheduleCreator(group_id, week)
            response = schedule_creator.form_response(group.name)
            ScheduleCache.save(
                group_id=group_id,
                week=week,
                text=response.text,
                markup=transform_markup_to_str(response.markup)
            )
        else:
            response = DefaultResponse()

    return response


def get_user_schedule(user_id: int) -> DefaultResponse:
    """
    gets schedule by user id
    :param user_id: user id in Telegram
    :return: DefaultResponse object
    """
    session = Session()
    user_repository = UserRepository(session)
    user = user_repository.get_user_by_id(user_id)

    current_week = get_current_week().week

    response = get_schedule(user.group_id, current_week)

    return response
