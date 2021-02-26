from typing import Optional

from telegram import InlineQueryResultArticle, InputTextMessageContent
from core.types.response import DefaultResponse, InlineResponse
from markup import create_schedule_folded_markup
from request import unecon_request
from schedule import Schedule
from site_parser import UneconParser


class ScheduleCreator:
    """
    Отвечает за создание ответа пользователю
    """

    def __init__(self, group_id: int, week: Optional[int] = None):
        self.group_id = group_id
        self.week = week

    def form_response(self, group_name: Optional[str] = None) -> DefaultResponse:
        """
        Формирует ответ на команду /schedule
        :return: объект ответа DefaultResponse
        """
        response = DefaultResponse()
        page = unecon_request(self.group_id, self.week)

        if page.status_code == 200:
            page_parser = UneconParser(page.content)
            lessons = page_parser.parse_page()
            schedule = Schedule(lessons)

            current_week = page_parser.get_current_week_number()

            markup = create_schedule_folded_markup(self.group_id, current_week)

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
        page = unecon_request(group=self.group_id)

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
