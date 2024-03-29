from typing import Optional

from telegram import InlineQueryResultArticle, InputTextMessageContent
from core.types.response import DefaultResponse, InlineResponse
from core.button.markup import create_schedule_folded_markup
from core.request import unecon_request
from core.schedule.schedule import Schedule
from core.schedule.site_parser import UneconParser


class ScheduleCreator:
    """Handles schedule requests"""

    def __init__(self, group_id: int, week: Optional[int] = None):
        """
        :param group_id: group id in the university site
        :param week: study week number since the start of study year
        """
        self.group_id = group_id
        self.week = week

    def form_response(self, group_name: Optional[str] = None) -> DefaultResponse:
        """
        Gets and returns schedule as a DefaultResponse object
        :param group_name: group name to add group name to string representation
        :return: DefaultResponse object
        """
        response = DefaultResponse()
        page = unecon_request(self.group_id, self.week)

        if page.status_code == 200:
            page_parser = UneconParser(page.text)
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
        """Gets and returns schedule as a InlineResponse object"""
        inline_response = InlineResponse()
        page = unecon_request(group_id=self.group_id)

        if page.status_code == 200:
            page_parser = UneconParser(page.text)
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
                next_week_page = unecon_request(group_id=12837, week=current_week_number + 1)

                if next_week_page.status_code == 200:
                    next_page_parser = UneconParser(next_week_page.text)
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
