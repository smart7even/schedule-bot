from typing import List
from data_types import Lesson, BtnTypes
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json

keyboard_main = ReplyKeyboardMarkup(True, True)
keyboard_main.row("/schedule")


def create_change_week_markup(group: int, week: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="Пред. Неделя", callback_data=json.dumps(
            {"type": BtnTypes.CHANGE_WEEK.name, "group": group, "week": week - 1})),
        InlineKeyboardButton(text="След. Неделя", callback_data=json.dumps(
            {"type": BtnTypes.CHANGE_WEEK.name, "group": group, "week": week + 1}))
    )

    return markup


def create_get_full_days_markup(schedule: List[Lesson], group: int, week: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    day = None
    day_count = 0
    for lesson in schedule:
        if day != lesson.day:
            day = lesson.day
            day_count += 1
            markup.add(
                InlineKeyboardButton(
                    day,
                    callback_data=json.dumps(
                        {
                            "type": BtnTypes.GET_FULL_DAY.name,
                            "group": group,
                            "week": week,
                            "day": day_count
                        })
                )
            )

    return markup


def mix_markups(*markups: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    new_markup = InlineKeyboardMarkup()

    for markup in markups:
        for row in markup.keyboard:
            new_markup.add(*row)

    return new_markup
