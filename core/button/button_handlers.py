import json
from typing import Optional

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from core.repositories.group_repository import GroupRepository
from core.repositories.schedule_cache_repository import ScheduleCacheRepository
from core.services.button_actions_service import ButtonActionsService
from core.services.schedule_service import ScheduleService
from core.types.button import BtnTypes, ActionTypes
from core.types.response import DefaultResponse, AnswerResponse
from core.button.markup import create_schedule_folded_markup, create_schedule_unfolded_markup, transform_markup_to_str
from db import Session
from core.models.current_week import get_current_week
from core.request import unecon_request
from core.schedule.schedule import Schedule
from core.schedule.site_parser import UneconParser


def handle_change_week_btn(schedule: Schedule, group_id: int, week: int) -> DefaultResponse:
    """
    :param schedule: Schedule object
    :param group_id: group id in the university site
    :param week: study week number since the start of study year
    :return: DefaultResponse object
    """
    response = DefaultResponse()

    markup = create_schedule_folded_markup(group_id, week)

    if schedule.lessons:
        session = Session()
        group_repository = GroupRepository(session)
        group = group_repository.get_group_by_id(group_id)
        session.close()
        schedule_str = schedule.transform_schedule_to_str(group_name=group.name, week=week)

        response.set_data(text=schedule_str, markup=markup)
    else:
        response.set_data(text="На эту неделю нет расписания", markup=markup)

    return response


def handle_more_btn(schedule: Schedule, group_id: int, week: int) -> DefaultResponse:
    """
    :param schedule: Schedule object
    :param group_id: group id in the university site
    :param week: study week number since the start of study year
    :return: DefaultResponse object
    """
    response = DefaultResponse()

    if schedule.lessons:
        markup = create_schedule_unfolded_markup(schedule.lessons, group_id, week)

        schedule_str = schedule.transform_schedule_to_str()

        response.set_data(text=schedule_str, markup=markup)

    return response


def handle_get_full_day_btn(schedule: Schedule, group_id: int, week: int, day: int) -> DefaultResponse:
    """
    :param schedule: Schedule object
    :param group_id: group id in the university site
    :param week: study week number since the start of study year
    :param day: DefaultResponse object
    :return:
    """
    response = DefaultResponse()

    if schedule.lessons:
        lessons_at_this_day = schedule.get_info_about_day(day)
        schedule_at_this_day = Schedule(lessons=lessons_at_this_day)
        lessons_str = schedule_at_this_day.transform_schedule_to_str(is_detail_mode=True)
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Назад к расписанию недели",
                callback_data=json.dumps(
                    {
                        "type": BtnTypes.CHANGE_WEEK.name,
                        "group": group_id,
                        "week": week
                    })
            )
        ]])

        response.set_data(text=lessons_str, markup=markup)

    return response


def handle_set_group_btn(group_id: int, user_id: int) -> AnswerResponse:
    """
    :param group_id: group id in the university site
    :param user_id: user id in Telegram
    :return: AnswerResponse object
    """
    response = AnswerResponse()
    set_group_response = ButtonActionsService(Session()).set_group(group_id, user_id)
    response.text = f"Группа {set_group_response.text} установлена!"
    return response


def handle_get_schedule_btn(group_id) -> DefaultResponse:
    """
    :param group_id: group id in the university site
    :return: DefaultResponse
    """
    current_week = get_current_week().week

    response = ScheduleService(Session()).get_schedule(group_id, current_week)
    return response


def handle_faculty_btn(callback_action_type: ActionTypes, faculty_id: int) -> DefaultResponse:
    """
    :param callback_action_type: Action that will be handled by buttons
    :param faculty_id: faculty id in the university site
    :return: DefaultResponse object
    """
    response = DefaultResponse()
    response.markup = ButtonActionsService(Session()).get_courses_choice_form(faculty_id, callback_action_type)
    response.text = "Выберите курс"

    return response


def handle_course_btn(callback_action_type: ActionTypes, faculty_id: int, course: int) -> DefaultResponse:
    """
    :param callback_action_type: Action that will be handled by buttons
    :param faculty_id: faculty id in the university site
    :param course: course number
    :return: DefaultResponse object
    """
    response = DefaultResponse()
    response.markup = ButtonActionsService(Session()).get_group_choice_form(faculty_id, course, callback_action_type)
    response.text = "Выберите группу"

    return response


def handle_schedule_btns(
        callback_btn_type: BtnTypes, group_id: int, week: int, day: Optional[int] = None) -> DefaultResponse:
    """
    :param callback_btn_type: Action that will be handled by buttons
    :param group_id: group id in the university site
    :param week: study week number since the start of study year
    :param day: study day number from the start of the week
    :return: DefaultResponse
    """
    button_click_response = DefaultResponse()

    session = Session()
    schedule_cache_repository = ScheduleCacheRepository(session)
    schedule_cache = schedule_cache_repository.get(group_id=group_id, week=week)

    schedule = None
    if not schedule_cache or callback_btn_type != BtnTypes.CHANGE_WEEK:
        page = unecon_request(group_id, week)
        parser = UneconParser(page.text)
        lessons = parser.parse_page()
        schedule = Schedule(lessons)

    if callback_btn_type == BtnTypes.CHANGE_WEEK:

        if schedule_cache:
            button_click_response.text = schedule_cache.text
            button_click_response.markup = InlineKeyboardMarkup.de_json(json.loads(schedule_cache.markup), bot=None)
        else:
            button_click_response = handle_change_week_btn(schedule, group_id, week)
            # schedule_cache_repository.add(
            #     group_id=group_id,
            #     week=week,
            #     text=button_click_response.text,
            #     markup=transform_markup_to_str(button_click_response.markup)
            # )
    elif callback_btn_type == BtnTypes.MORE:
        button_click_response = handle_more_btn(schedule, group_id, week)
    elif callback_btn_type == BtnTypes.GET_FULL_DAY:
        button_click_response = handle_get_full_day_btn(schedule, group_id, week, day)

    session.close()

    return button_click_response
