from collections import namedtuple
from enum import Enum
from telebot.types import InlineKeyboardMarkup, InlineQueryResultArticle
from typing import Union

Lesson = namedtuple(
    "lesson", ["name", "day", "day_of_week", "time", "professor", "location"])


class Response:
    def __init__(self):
        self.message: Union[str, None] = None
        self.markup: Union[InlineKeyboardMarkup, None] = None


class InlineResponse:
    def __init__(self):
        self.items = []
        self.is_success = True

    def add_item(self, inline_item: InlineQueryResultArticle) -> None:
        self.items.append(inline_item)


class ButtonClickResponse:
    def __init__(self):
        self.text: Union[str, None] = None
        self.markup: Union[InlineKeyboardMarkup, None] = None


class BtnTypes(Enum):
    CHANGE_WEEK = 1
    MORE = 2
    GET_FULL_DAY = 3
