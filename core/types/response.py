from typing import Optional, List
from telebot.types import InlineKeyboardMarkup, InlineQueryResultArticle
from abc import ABC, abstractmethod


class Response(ABC):
    """Абстрактный класс ответа на запрос пользователя"""

    @abstractmethod
    def is_success(self) -> bool:
        """Метод, возвращающий состояние ответа: True, если ответ корректный, False, если ответ некорректный"""
        pass


class DefaultResponse(Response):
    """Класс ответа на команду /schedule"""
    def __init__(self):
        self.__text: Optional[str] = None
        self.__markup: Optional[InlineKeyboardMarkup] = None

    def set_data(self, text: str, markup: InlineKeyboardMarkup) -> None:
        self.text = text
        self.markup = markup

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value: str):
        if type(value) == str:
            self.__text = value
        else:
            raise ValueError(f"Expected str but got {type(value)}")

    @property
    def markup(self):
        return self.__markup

    @markup.setter
    def markup(self, value: InlineKeyboardMarkup):
        if type(value) == InlineKeyboardMarkup:
            self.__markup = value
        else:
            raise ValueError(f"Expected InlineKeyboardMarkup but got {type(value)}")

    def is_success(self) -> bool:
        if self.__text:
            return True
        return False


class InlineResponse(Response):
    """Класс ответа на inline команду @schedule_unecon_bot <команда>"""
    def __init__(self):
        self.__items: List[InlineQueryResultArticle] = []

    @property
    def items(self) -> List[InlineQueryResultArticle]:
        return self.__items

    def add_item(self, inline_item: InlineQueryResultArticle) -> None:
        if type(inline_item) == InlineQueryResultArticle:
            self.__items.append(inline_item)
        else:
            raise ValueError(f"Expected InlineQueryResultArticle but got {type(inline_item)}")

    def is_success(self) -> bool:
        if self.__items:
            return True
        return False
