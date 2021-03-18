from abc import ABC, abstractmethod


class TextElement(ABC):
    """Abstract class representing text elements"""

    @abstractmethod
    def to_str(self) -> str:
        pass


class Bold(TextElement):
    """Bold text"""

    def __init__(self, text: str):
        self.__element = f"<b>{text}</b>"

    def to_str(self) -> str:
        return self.__element


class Plain(TextElement):
    """Plain text"""
    def __init__(self, text: str):
        self.__element = text

    def to_str(self) -> str:
        return self.__element


class NewLine(TextElement):
    """New line"""
    def __init__(self, new_lines_num: int = 1):
        self.__element = "\n" * new_lines_num

    def to_str(self) -> str:
        return self.__element


class ElementsContainer:
    """Container to store text elements"""
    def __init__(self, *elements: TextElement):
        self.__elements = elements

    def to_str(self):
        return "".join(element.to_str() for element in self.__elements)


def wrap(element: TextElement, wrapper: TextElement) -> ElementsContainer:
    """Wraps text element with other text element"""
    modified_element = ElementsContainer(wrapper, element, wrapper)
    return modified_element


def wrap_with_new_lines(element: TextElement) -> ElementsContainer:
    """Wraps text element with new lines"""
    return wrap(element, wrapper=NewLine())
