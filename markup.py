from typing import List
from core.types.lesson import Lesson
from core.types.button import BtnTypes
import json

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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


def mix_markups(*markups: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """
    Соединяет объекты разметки в одну разметку
    :param markups: объекты разметки InlineKeyboardMarkup
    :return: объект разметки telebot.types.InlineKeyboardMarkup
    """
    new_markup_list = []

    for markup in markups:
        for row in markup.inline_keyboard:
            new_markup_list.append(row)

    new_markup = InlineKeyboardMarkup(new_markup_list)

    return new_markup
