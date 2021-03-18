from core.types.button import ActionTypes
from core.button.markup import create_group_buttons, create_faculty_buttons, create_course_buttons
from core.types.response import DefaultResponse
from core.models.user import User
from core.models.group import Group
from core.models.faculty import Faculty

from telegram import InlineKeyboardMarkup


class ButtonActions:

    @staticmethod
    def set_group(group_id: int, user_id: int) -> DefaultResponse:
        """
        Sets user group.
        :param group_id: group id in university site
        :param user_id: user id in Telegram
        :return: DefaultResponse object
        """
        user = User.get_user_by_id(user_id)
        user.set_group(group_id)

        response = DefaultResponse()
        response.text = Group.get_group_by_id(group_id).name

        return response

    @staticmethod
    def get_faculties_choice_form(action: ActionTypes) -> InlineKeyboardMarkup:
        """
        :param action: Action that will be handled by buttons
        :return: telegram.InlineKeyBoardMarkup object
        """
        faculties = Faculty.get_all()
        markup = create_faculty_buttons(faculties, action)

        return markup

    @staticmethod
    def get_courses_choice_form(faculty_id: int, action: ActionTypes) -> InlineKeyboardMarkup:
        """
        :param faculty_id: faculty id in the university site
        :param action: Action that will be handled by buttons
        :return: telegram.InlineKeyBoardMarkup object
        """
        courses = Group.get_courses_in_faculty(faculty_id)
        print(courses)
        markup = create_course_buttons(courses, faculty_id, action)

        return markup

    @staticmethod
    def get_group_choice_form(faculty_id: int, course: int, action: ActionTypes) -> InlineKeyboardMarkup:
        """
        :param faculty_id: faculty id in the university site
        :param course: course number
        :param action: Action that will be handled by buttons
        :return: telegram.InlineKeyBoardMarkup object
        """
        groups = Group.get_groups_by_faculty_and_course(faculty_id, course)
        markup = create_group_buttons(groups, action)

        return markup


