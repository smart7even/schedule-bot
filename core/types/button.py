from enum import Enum
from models import Group
from typing import List

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import json


class BtnTypes(Enum):
    """Типы кнопок"""
    CHANGE_WEEK = 1
    MORE = 2
    GET_FULL_DAY = 3
    GROUP_BUTTON = 4


class ActionTypes(Enum):
    SET_USER_GROUP = 1
    GET_SCHEDULE = 2


def create_group_buttons(group_list: List[Group], action: ActionTypes) -> InlineKeyboardMarkup:
    markup_list = []

    for group in group_list:
        button = InlineKeyboardButton(group.name, callback_data=json.dumps({"type": BtnTypes.GROUP_BUTTON.name,
                                                                            "group_id": group.id,
                                                                            "action": action.value}))
        markup_list.append([button])

    markup = InlineKeyboardMarkup(markup_list)

    return markup
