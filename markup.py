from typing import List
from core.types.lesson import Lesson
from core.types.button import BtnTypes, ActionTypes
import json

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from models import Group, Faculty

keyboard_main = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton("Все расписания"),
            KeyboardButton("Мое расписание"),
            KeyboardButton("Выбрать мою группу")
        ]
    ],
    resize_keyboard=True
)


def create_change_week_markup(group: int, week: int) -> InlineKeyboardMarkup:
    """
    Эта функция создает разметку с кнопками для перехода на предыдущую и следующую неделю расписания
    :param group: id группы
    :param week: номер недели от начала учебного года
    :return: объект разметки telegram.InlineKeyboardMarkup
    """
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Пред. Неделя", callback_data=json.dumps(
                    {"type": BtnTypes.CHANGE_WEEK.name, "group": group, "week": week - 1})),
                InlineKeyboardButton(text="След. Неделя", callback_data=json.dumps(
                    {"type": BtnTypes.CHANGE_WEEK.name, "group": group, "week": week + 1}))
            ]
        ]
    )

    return markup


def create_more_markup(group_id: int, week: int):
    more_markup_button = InlineKeyboardButton(
        "Больше",
        callback_data=json.dumps({"type": BtnTypes.MORE.name, "group": group_id, "week": week})
    )
    more_markup = InlineKeyboardMarkup([[more_markup_button]])

    return more_markup


def create_get_full_days_markup(schedule: List[Lesson], group: int, week: int) -> InlineKeyboardMarkup:
    """
    Эта функция создает разметку с кнопками для перехода к подробному расписанию на определенный день
    :param schedule: объект Schedule
    :param group: id группы
    :param week: номер недели от начала учебного года
    :return: объект разметки telegram.InlineKeyboardMarkup
    """
    inline_keyboard_list = []
    day = None
    day_count = 0
    for lesson in schedule:
        if day != lesson.day:
            day = lesson.day
            day_count += 1
            inline_keyboard_list.append(
                [InlineKeyboardButton(
                    day,
                    callback_data=json.dumps(
                        {
                            "type": BtnTypes.GET_FULL_DAY.name,
                            "group": group,
                            "week": week,
                            "day": day_count
                        })
                )]
            )

    markup = InlineKeyboardMarkup(inline_keyboard_list)

    return markup


def create_schedule_folded_markup(group: int, week: int) -> InlineKeyboardMarkup:
    change_week_markup = create_change_week_markup(group, week)
    more_markup = create_more_markup(group, week)

    markup = mix_markups(change_week_markup, more_markup)

    return markup


def create_schedule_unfolded_markup(schedule: List[Lesson], group_id: int, week: int):
    change_week_markup = create_change_week_markup(group_id, week)
    get_full_days_markup = create_get_full_days_markup(schedule, group_id, week)

    markup = mix_markups(change_week_markup, get_full_days_markup)

    return markup


def mix_markups(*markups: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """
    Соединяет объекты разметки в одну разметку
    :param markups: объекты разметки InlineKeyboardMarkup
    :return: объект разметки InlineKeyboardMarkup
    """
    new_markup_list = []

    for markup in markups:
        for row in markup.inline_keyboard:
            new_markup_list.append(row)

    new_markup = InlineKeyboardMarkup(new_markup_list)

    return new_markup


def create_group_buttons(group_list: List[Group], action: ActionTypes) -> InlineKeyboardMarkup:
    markup_list = []

    for group in group_list:
        button = InlineKeyboardButton(group.name, callback_data=json.dumps({"type": BtnTypes.GROUP_BTN.name,
                                                                            "group_id": group.id,
                                                                            "action": action.value}))
        markup_list.append([button])

    markup = InlineKeyboardMarkup(markup_list)

    return markup


def create_faculty_buttons(faculties_list: List[Faculty], action: ActionTypes) -> InlineKeyboardMarkup:
    markup_list = []

    for faculty in faculties_list:
        button = InlineKeyboardButton(faculty.name, callback_data=json.dumps({"type": BtnTypes.FACULTY_BTN.name,
                                                                              "f_id": faculty.id,
                                                                              "action": action.value}))
        markup_list.append([button])

    markup = InlineKeyboardMarkup(markup_list)

    return markup


def create_course_buttons(course_list: List[int], faculty_id: int, action: ActionTypes) -> InlineKeyboardMarkup:
    markup_list = []

    for course in course_list:
        button = InlineKeyboardButton(str(course), callback_data=json.dumps({"type": BtnTypes.COURSE_BTN.name,
                                                                             "f_id": faculty_id,
                                                                             "c_id": course,
                                                                             "action": action.value}))
        markup_list.append([button])

    markup = InlineKeyboardMarkup(markup_list)

    return markup
