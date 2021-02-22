from enum import Enum


class BtnTypes(Enum):
    """Типы кнопок"""
    CHANGE_WEEK = 1
    MORE = 2
    GET_FULL_DAY = 3
    GROUP_BTN = 4
    FACULTY_BTN = 5
    COURSE_BTN = 6


class ActionTypes(Enum):
    SET_USER_GROUP = 1
    GET_SCHEDULE = 2


