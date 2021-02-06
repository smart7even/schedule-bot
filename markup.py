from enum import Enum
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json


class BtnTypes(Enum):
    CHANGE_WEEK = 1
    MORE = 2
    GET_FULL_DAY = 3


def create_change_week_markup(week: int, group=12837) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="Пред. Неделя", callback_data=json.dumps(
            {"type": BtnTypes.CHANGE_WEEK.name, "group": group, "week": week-1})),
        InlineKeyboardButton(text="След. Неделя", callback_data=json.dumps(
            {"type": BtnTypes.CHANGE_WEEK.name, "group": group, "week": week+1}))
    )

    return markup


def create_more_markup(week):
    pass
