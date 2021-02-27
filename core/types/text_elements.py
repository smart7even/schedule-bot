from abc import ABC, abstractmethod


class TextElement(ABC):

    @abstractmethod
    def to_str(self) -> str:
        pass


class Bold(TextElement):

    def __init__(self, text: str):
        self.__element = f"<b>{text}</b>"

    def to_str(self) -> str:
        return self.__element


class Plain(TextElement):
    def __init__(self, text: str):
        self.__element = text

    def to_str(self) -> str:
        return self.__element


class NewLine(TextElement):
    def __init__(self, empty_lines_num: int = 1):
        self.__element = "\n" * empty_lines_num

    def to_str(self) -> str:
        return self.__element


class StrElement:
    def __init__(self, *elements: TextElement):
        self.__elements = elements

    def to_str(self):
        return "".join(element.to_str() for element in self.__elements)


def wrap_with_new_lines(element: TextElement) -> StrElement:
    modified_element = StrElement(NewLine(), element, NewLine())
    return modified_element
