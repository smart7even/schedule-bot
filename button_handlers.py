import json
from typing import Optional

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from button_actions import ButtonActions
from core.types.button import BtnTypes, ActionTypes
from core.types.response import DefaultResponse, AnswerResponse
from markup import create_schedule_folded_markup, create_schedule_unfolded_markup
from models import Group
from request import unecon_request
from schedule import Schedule
from site_parser import UneconParser


def handle_change_week_btn(schedule: Schedule, group_id: int, week: int) -> DefaultResponse:
    response = DefaultResponse()

    markup = create_schedule_folded_markup(group_id, week)

    if schedule.lessons:
        group = Group.get_group_by_id(group_id)
        schedule_str = schedule.transform_schedule_to_str(group_name=group.name, week=week)

        response.set_data(text=schedule_str, markup=markup)
    else:
        response.set_data(text="На эту неделю нет расписания", markup=markup)

    return response


def handle_more_btn(schedule: Schedule, group_id: int, week: int) -> DefaultResponse:
    response = DefaultResponse()

    if schedule.lessons:
        markup = create_schedule_unfolded_markup(schedule.lessons, group_id, week)

        schedule_str = schedule.transform_schedule_to_str()

        response.set_data(text=schedule_str, markup=markup)

    return response


def handle_get_full_day_btn(schedule: Schedule, group_id: int, week: int, day: int) -> DefaultResponse:
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
    response = AnswerResponse()
    set_group_response = ButtonActions.set_group(group_id, user_id)
    response.text = f"Группа {set_group_response.text} установлена!"
    return response


def handle_get_schedule_btn(group_id) -> DefaultResponse:
    response = ButtonActions.get_schedule(group_id)
    return response


def handle_faculty_btn(callback_action_type: ActionTypes, faculty_id: int) -> DefaultResponse:
    response = DefaultResponse()
    response.markup = ButtonActions.get_courses_choice_form(faculty_id, callback_action_type)
    response.text = "Выберите курс"

    return response


def handle_course_btn(callback_action_type: ActionTypes, faculty_id: int, course: int):
    response = DefaultResponse()
    response.markup = ButtonActions.get_group_choice_form(faculty_id, course, callback_action_type)
    response.text = "Выберите группу"

    return response


def handle_schedule_btns(
        callback_btn_type: BtnTypes, group_id: int, week: int, day: Optional[int] = None) -> DefaultResponse:
    button_click_response = DefaultResponse()

    page = unecon_request(group_id, week)
    parser = UneconParser(page.content)
    lessons = parser.parse_page()
    schedule = Schedule(lessons)

    if callback_btn_type == BtnTypes.CHANGE_WEEK:
        button_click_response = handle_change_week_btn(schedule, group_id, week)
    elif callback_btn_type == BtnTypes.MORE:
        button_click_response = handle_more_btn(schedule, group_id, week)
    elif callback_btn_type == BtnTypes.GET_FULL_DAY:
        button_click_response = handle_get_full_day_btn(schedule, group_id, week, day)

    return button_click_response
