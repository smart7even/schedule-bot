from core.types.button import create_group_buttons, ActionTypes
from core.types.response import DefaultResponse
from models import User, Group
from schedule_repsonse import ScheduleCreator
from typing import Optional


class ButtonActions:

    @staticmethod
    def set_group(group_id, user_id: int):
        user = User.get_user(user_id)
        user.set_group(group_id)

    @staticmethod
    def get_group_choice_form():
        groups = Group.get_all()
        markup = create_group_buttons(groups, action=ActionTypes.SET_USER_GROUP)

        return markup

    @staticmethod
    def get_groups(faculty_id: int, course: int):
        pass

    @staticmethod
    def get_courses(faculty_id: int):
        pass

    @staticmethod
    def get_faculty():
        pass

    @staticmethod
    def get_schedule(group_id: int, week: Optional[int] = None) -> DefaultResponse:
        schedule_creator = ScheduleCreator(group_id, week)
        response = schedule_creator.form_response()

        return response

    @staticmethod
    def get_my_schedule(user_id: int) -> DefaultResponse:
        user = User.get_user(user_id)

        response = ButtonActions.get_schedule(user.group_id)

        return response
