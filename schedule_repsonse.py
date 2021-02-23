import json
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent

from core.types.button import BtnTypes
from core.types.response import DefaultResponse, InlineResponse
from markup import (
    create_schedule_folded_markup,
    create_schedule_unfolded_markup,
)
from request import unecon_request
from schedule import Schedule
from site_parser import UneconParser

from models import Group


class ScheduleCreator:
    """
    Отвечает за создание ответа пользователю
    """

    def __init__(self, group_id: int, week: Optional[int] = None):
        self.group = group_id
        self.week = week

    def form_response(self, group_name: Optional[str] = None) -> DefaultResponse:
        """
        Формирует ответ на команду /schedule
        :return: объект ответа DefaultResponse
        """
        response = DefaultResponse()
        page = unecon_request(self.group, self.week)

        if page.status_code == 200:
            page_parser = UneconParser(page.content)
            lessons = page_parser.parse_page()
            schedule = Schedule(lessons)

            current_week = page_parser.get_current_week_number()

            markup = create_schedule_folded_markup(self.group, current_week)

            if schedule:
                schedule_str = schedule.transform_schedule_to_str(group_name=group_name, week=current_week)

                response.set_data(text=schedule_str, markup=markup)
            else:
                response.text = "На эту неделю нет расписания"
        else:
            response.text = "К расписанию нет доступа. Попробуйте позже"

        return response

    def form_inline_response(self) -> InlineResponse:
        """
        Формирует inline ответ при вызове бота в любом чате через "@schedule_unecon_bot <команда>"
        :return:
        """
        inline_response = InlineResponse()
        page = unecon_request(group=self.group)

        if page.status_code == 200:
            page_parser = UneconParser(page.content)
            lessons = page_parser.parse_page()
            schedule = Schedule(lessons)

            if schedule.lessons:

                schedule_str = schedule.transform_schedule_to_str()
                this_week = InlineQueryResultArticle(
                    id="1",
                    title="Расписание на эту неделю",
                    input_message_content=InputTextMessageContent(
                        message_text=schedule_str,
                        parse_mode="HTML"
                    )
                )

                inline_response.add_item(this_week)

                current_week_number = page_parser.get_current_week_number()
                next_week_page = unecon_request(group=12837, week=current_week_number + 1)

                if next_week_page.status_code == 200:
                    next_page_parser = UneconParser(next_week_page.content)
                    next_week_lessons = next_page_parser.parse_page()
                    next_week_schedule = Schedule(next_week_lessons)
                    next_week_schedule_str = next_week_schedule.transform_schedule_to_str()
                    next_week = InlineQueryResultArticle(
                        id="2",
                        title="Расписание на следующую неделю",
                        input_message_content=InputTextMessageContent(
                            message_text=next_week_schedule_str,
                            parse_mode="HTML"
                        )
                    )
                    inline_response.add_item(next_week)

        return inline_response

    def form_on_button_click_response(self, btn_data: dict) -> DefaultResponse:
        """
        Формирует ответ бота при нажатии на кнопку
        :param btn_data: callback_data кнопки
        :return: объект ответа DefaultResponse
        """
        button_click_response = DefaultResponse()

        callback_btn_type = None
        for btn_type in BtnTypes:
            if btn_type.name == btn_data["type"]:
                callback_btn_type = btn_type

        page = unecon_request(group=self.group, week=self.week)
        parser = UneconParser(page.content)
        lessons = parser.parse_page()
        schedule = Schedule(lessons)

        if callback_btn_type == BtnTypes.CHANGE_WEEK:
            markup = create_schedule_folded_markup(self.group, self.week)

            if schedule.lessons:
                group = Group.get_group_by_id(self.group)
                schedule_str = schedule.transform_schedule_to_str(group_name=group.name, week=self.week)

                button_click_response.set_data(text=schedule_str, markup=markup)
            else:
                button_click_response.set_data(text="На эту неделю нет расписания", markup=markup)

        elif callback_btn_type == BtnTypes.MORE:
            if schedule.lessons:
                markup = create_schedule_unfolded_markup(schedule.lessons, self.group, self.week)

                schedule_str = schedule.transform_schedule_to_str()

                button_click_response.set_data(text=schedule_str, markup=markup)

        elif callback_btn_type == BtnTypes.GET_FULL_DAY:
            if schedule.lessons:
                lessons_at_this_day = schedule.get_info_about_day(btn_data["day"])
                schedule_at_this_day = Schedule(lessons=lessons_at_this_day)
                lessons_str = schedule_at_this_day.transform_schedule_to_str(is_detail_mode=True)
                markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "Назад к расписанию недели",
                        callback_data=json.dumps(
                            {
                                "type": BtnTypes.CHANGE_WEEK.name,
                                "group": self.group,
                                "week": self.week
                            })
                    )
                ]])

                button_click_response.set_data(text=lessons_str, markup=markup)

        return button_click_response
