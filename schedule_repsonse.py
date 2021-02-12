import json
from typing import Optional

import telebot

from core.types.button import BtnTypes
from core.types.response import DefaultResponse, InlineResponse
from markup import create_change_week_markup, create_get_full_days_markup, mix_markups
from request import unecon_request
from schedule import Schedule, UneconParser


class ResponseCreator:
    def __init__(self, group: int, week: Optional[int] = None):
        self.group = group
        self.week = week

    def form_response(self) -> DefaultResponse:
        response = DefaultResponse()
        page = unecon_request(self.group, self.week)

        if page.status_code == 200:
            page_parser = UneconParser(page.content)
            lessons = page_parser.parse_page()
            schedule = Schedule(lessons)

            current_week = page_parser.get_current_week_number()

            markup = create_change_week_markup(self.group, current_week)
            markup.add(telebot.types.InlineKeyboardButton(
                "Больше",
                callback_data=json.dumps({"type": BtnTypes.MORE.name, "group": self.group, "week": current_week})))

            if schedule:
                schedule_str = schedule.transform_schedule_to_str()

                response.set_data(text=schedule_str, markup=markup)
            else:
                response.text = "На эту неделю нет расписания"
        else:
            response.text = "К расписанию нет доступа. Попробуйте позже"

        return response

    def form_inline_response(self) -> InlineResponse:
        inline_response = InlineResponse()
        page = unecon_request(group=self.group)

        if page.status_code == 200:
            page_parser = UneconParser(page.content)
            lessons = page_parser.parse_page()
            schedule = Schedule(lessons)

            if schedule.lessons:

                schedule_str = schedule.transform_schedule_to_str()
                this_week = telebot.types.InlineQueryResultArticle(
                    id="1",
                    title="Расписание на эту неделю",
                    input_message_content=telebot.types.InputTextMessageContent(
                        message_text=schedule_str,
                        parse_mode="HTML"
                    )
                )

                inline_response.add_item(this_week)

                current_week_number = page_parser.get_current_week_number()
                next_week_page = unecon_request(group=12837, week=current_week_number + 1)

                if next_week_page.status_code == 200:
                    next_week_schedule = Schedule.get_schedule_from_html(next_week_page.content)
                    next_week_schedule_str = next_week_schedule.transform_schedule_to_str()
                    next_week = telebot.types.InlineQueryResultArticle(
                        id="2",
                        title="Расписание на следующую неделю",
                        input_message_content=telebot.types.InputTextMessageContent(
                            message_text=next_week_schedule_str,
                            parse_mode="HTML"
                        )
                    )
                    inline_response.add_item(next_week)

        return inline_response

    def form_on_button_click_response(self, btn_data: dict) -> DefaultResponse:
        button_click_response = DefaultResponse()

        callback_btn_type = None
        for btn_type in BtnTypes:
            if btn_type.name == btn_data["type"]:
                callback_btn_type = btn_type

        page = unecon_request(group=self.group, week=self.week)
        schedule = Schedule.get_schedule_from_html(page.content)

        if callback_btn_type == BtnTypes.CHANGE_WEEK:
            markup = create_change_week_markup(self.group, self.week)
            markup.add(telebot.types.InlineKeyboardButton(
                "Больше", callback_data=json.dumps({"type": BtnTypes.MORE.name, "group": 12837, "week": self.week})))

            if schedule.lessons:
                schedule_str = schedule.transform_schedule_to_str()

                button_click_response.set_data(text=schedule_str, markup=markup)
            else:
                button_click_response.set_data(text="На эту неделю нет расписания", markup=markup)

        elif callback_btn_type == BtnTypes.MORE:
            if schedule.lessons:
                buttons_markup = create_change_week_markup(self.group, self.week)
                get_full_days_markup = create_get_full_days_markup(schedule.lessons, self.group, self.week)
                markup = mix_markups(buttons_markup, get_full_days_markup)

                schedule_str = schedule.transform_schedule_to_str()

                button_click_response.set_data(text=schedule_str, markup=markup)

        elif callback_btn_type == BtnTypes.GET_FULL_DAY:
            if schedule.lessons:
                lessons_at_this_day = schedule.get_info_about_day(btn_data["day"])
                schedule_at_this_day = Schedule(lessons=lessons_at_this_day)
                lessons_str = schedule_at_this_day.transform_schedule_to_str(is_detail_mode=True)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(
                    telebot.types.InlineKeyboardButton(
                        "Назад к расписанию недели",
                        callback_data=json.dumps(
                            {
                                "type": BtnTypes.CHANGE_WEEK.name,
                                "group": self.group,
                                "week": self.week
                            })
                    )
                )
                button_click_response.set_data(text=lessons_str, markup=markup)

        return button_click_response
