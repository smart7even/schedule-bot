from core.types.button import ActionTypes
from markup import create_group_buttons, create_faculty_buttons, create_course_buttons
from core.types.response import DefaultResponse
from models import User, Group, Faculty
from schedule_repsonse import ScheduleCreator
from typing import Optional

from telegram import InlineKeyboardMarkup


class ButtonActions:

    @staticmethod
    def set_group(group_id: int, user_id: int):
        user = User.get_user(user_id)
        user.set_group(group_id)

        response = DefaultResponse()
        response.text = Group.get_group_by_id(group_id).name

        return response

    @staticmethod
    def get_faculties_choice_form(action: ActionTypes) -> InlineKeyboardMarkup:
        faculties = Faculty.get_all()
        markup = create_faculty_buttons(faculties, action)

        return markup

    @staticmethod
    def get_courses_choice_form(faculty_id: int, action: ActionTypes) -> InlineKeyboardMarkup:
        courses = Group.get_courses_in_faculty(faculty_id)
        print(courses)
        markup = create_course_buttons(courses, faculty_id, action)

        return markup

    @staticmethod
    def get_group_choice_form(faculty_id: int, course: int, action: ActionTypes) -> InlineKeyboardMarkup:
        groups = Group.get_groups_by_faculty_and_course(faculty_id, course)
        markup = create_group_buttons(groups, action)

        return markup

    @staticmethod
    def get_schedule(group_id: int, week: Optional[int] = None) -> DefaultResponse:
        group = Group.get_group_by_id(group_id)
        schedule_creator = ScheduleCreator(group_id, week)
        response = schedule_creator.form_response(group.name)

        return response

    @staticmethod
    def get_user_schedule(user_id: int) -> DefaultResponse:
        user = User.get_user(user_id)

        response = ButtonActions.get_schedule(user.group_id)

        return response
