from typing import List
from core.types.lesson import Lesson
from core.types.button import BtnTypes, ActionTypes
import json

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from core.models.group import Group
from core.models.faculty import Faculty

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
    :param group: group id in the university site
    :param week: week number since the start of study year
    :return: telegram.InlineKeyboardMarkup object
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


def create_more_markup(group_id: int, week: int) -> InlineKeyboardMarkup:
    """
    :param group_id: group id in the university site
    :param week: week number since the start of study year
    :return: telegram.InlineKeyboardMarkup object
    """
    more_markup_button = InlineKeyboardButton(
        "Больше",
        callback_data=json.dumps({"type": BtnTypes.MORE.name, "group": group_id, "week": week})
    )
    more_markup = InlineKeyboardMarkup([[more_markup_button]])

    return more_markup


def create_get_full_days_markup(lessons: List[Lesson], group: int, week: int) -> InlineKeyboardMarkup:
    """
    :param lessons: lessons in the particular day
    :param group: group id in the university site
    :param week: week number since the start of study year
    :return: telegram.InlineKeyboardMarkup object
    """
    inline_keyboard_list = []
    day = None
    day_count = 0
    for lesson in lessons:
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


def create_schedule_folded_markup(group_id: int, week: int) -> InlineKeyboardMarkup:
    """
    :param group_id: group id in the university site
    :param week: week number since the start of study year
    :return: telegram.InlineKeyboardMarkup object
    """
    change_week_markup = create_change_week_markup(group_id, week)
    more_markup = create_more_markup(group_id, week)

    markup = mix_markups(change_week_markup, more_markup)

    return markup


def create_schedule_unfolded_markup(lessons: List[Lesson], group_id: int, week: int) -> InlineKeyboardMarkup:
    """
    :param lessons: list of lessons
    :param group_id: group id in the university site
    :param week: week number since the start of study year
    :return: telegram.InlineKeyboardMarkup object
    """
    change_week_markup = create_change_week_markup(group_id, week)
    get_full_days_markup = create_get_full_days_markup(lessons, group_id, week)

    markup = mix_markups(change_week_markup, get_full_days_markup)

    return markup


def mix_markups(*markups: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """
    Mixes markups into one markup
    :param markups: markups to be mixed
    :return: telegram.InlineKeyboardMarkup object
    """
    new_markup_list = []

    for markup in markups:
        for row in markup.inline_keyboard:
            new_markup_list.append(row)

    new_markup = InlineKeyboardMarkup(new_markup_list)

    return new_markup


def create_group_buttons(group_list: List[Group], action: ActionTypes) -> InlineKeyboardMarkup:
    """
    :param group_list: list of Group objects
    :param action: Action dispatched on button click
    :return: telegram.InlineKeyboardMarkup object
    """
    markup_list = []

    for group in group_list:
        button = InlineKeyboardButton(group.name, callback_data=json.dumps({"type": BtnTypes.GROUP_BTN.name,
                                                                            "group_id": group.id,
                                                                            "action": action.value}))
        markup_list.append([button])

    markup = InlineKeyboardMarkup(markup_list)

    return markup


def create_faculty_buttons(faculties_list: List[Faculty], action: ActionTypes) -> InlineKeyboardMarkup:
    """
    :param faculties_list: list of Faculty objects
    :param action: Action that will be dispatched on button click
    :return: telegram.InlineKeyboardMarkup object
    """
    markup_list = []

    for faculty in faculties_list:
        button = InlineKeyboardButton(faculty.name, callback_data=json.dumps({"type": BtnTypes.FACULTY_BTN.name,
                                                                              "f_id": faculty.id,
                                                                              "action": action.value}))
        markup_list.append([button])

    markup = InlineKeyboardMarkup(markup_list)

    return markup


def create_course_buttons(course_list: List[int], faculty_id: int, action: ActionTypes) -> InlineKeyboardMarkup:
    """
    :param course_list: list of course numbers
    :param faculty_id: faculty id in the university site
    :param action: Action that will be dispatched on button click
    :return: telegram.InlineKeyboardMarkup object
    """
    markup_list = []

    for course in course_list:
        button = InlineKeyboardButton(str(course), callback_data=json.dumps({"type": BtnTypes.COURSE_BTN.name,
                                                                             "f_id": faculty_id,
                                                                             "c_id": course,
                                                                             "action": action.value}))
        markup_list.append([button])

    markup = InlineKeyboardMarkup(markup_list)

    return markup


def transform_markup_to_str(markup: InlineKeyboardMarkup) -> str:
    """
    transform telegram.InlineKeyboardMarkup object to str to serialize it
    :param markup: markup to be serialized
    :return: json str
    """
    return json.dumps(markup.to_dict())
