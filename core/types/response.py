from typing import Optional, List
from telegram import InlineKeyboardMarkup, InlineQueryResultArticle
from abc import ABC, abstractmethod


class Response(ABC):
    """Abstract class of response to user request"""

    @abstractmethod
    def is_valid(self) -> bool:
        """Checks if response is valid"""
        pass


class DefaultResponse(Response):
    """Default response to user request"""

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
            raise ValueError(f"Expected telegram.InlineKeyboardMarkup but got {type(value)}")

    def is_valid(self) -> bool:
        if self.__text:
            return True
        return False


class InlineResponse(Response):
    """Inline response to user request"""

    def __init__(self):
        self.__items: List[InlineQueryResultArticle] = []

    @property
    def items(self) -> List[InlineQueryResultArticle]:
        return self.__items

    def add_item(self, inline_item: InlineQueryResultArticle) -> None:
        if type(inline_item) == InlineQueryResultArticle:
            self.__items.append(inline_item)
        else:
            raise ValueError(f"Expected telegram.InlineQueryResultArticle but got {type(inline_item)}")

    def is_valid(self) -> bool:
        if self.__items:
            return True
        return False


class AnswerResponse(Response):
    """Answer response to user request"""
    def __init__(self):
        self.__text: Optional[str] = None

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value: str):
        if type(value) == str:
            self.__text = value
        else:
            raise ValueError(f"Expected str but got {type(value)}")

    def is_valid(self) -> bool:
        if self.__text:
            return True
        return False
