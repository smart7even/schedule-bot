import json
from typing import List

import telebot

from data_types import Lesson, BtnTypes, Response, InlineResponse, ButtonClickResponse
from bs4 import BeautifulSoup
import re

from markup import create_change_week_markup, create_get_full_days_markup, mix_markups
from request import unecon_request

from typing import Optional


class Schedule:

    @staticmethod
    def get_schedule_from_html(content: bytes) -> List[Lesson]:
        soup = BeautifulSoup(content, features="html.parser")
        lessons = []
        day = None
        week = None
        for tr in soup.find_all("tr"):
            tr_class_names = tr["class"]
            if 'new_day_border' not in tr_class_names:

                if 'new_day' in tr_class_names:
                    day = tr.find("span", {"class": "date"}).string
                    week = tr.find("span", {"class": "day"}).string

                lesson_day = day
                lesson_day_of_week = week
                lesson_name = tr.find("span", {"class": "predmet"}).string
                lesson_time = tr.find("span", {"class": "time"}).string
                lesson_professor_span = tr.find("span", {"class": "prepod"})
                if lesson_professor_span.a:
                    lesson_professor = lesson_professor_span.a.text
                else:
                    lesson_professor = None

                lesson_location_span = tr.find("span", {"class": "aud"})

                if lesson_location_span.text:
                    lesson_location = lesson_location_span.text.strip()
                else:
                    lesson_location = None

                lesson = Lesson(lesson_name, lesson_day,
                                lesson_day_of_week, lesson_time, lesson_professor, lesson_location)
                lessons.append(lesson)

        return lessons

    @staticmethod
    def transform_schedule_to_str(lessons: List[Lesson], is_detail_mode=False) -> str:
        day = None
        prev_lesson_time = None
        schedule = ""
        for lesson in lessons:
            if lesson.day != day or not day:
                day = lesson.day
                schedule += f"\n<b>{day} {lesson.day_of_week}</b>\n"

            if prev_lesson_time != lesson.time:
                if is_detail_mode:
                    schedule += "\n"
                schedule += f"<b>{lesson.time}</b>\n{lesson.name}\n"
            else:
                if is_detail_mode:
                    schedule += "\n"

            if is_detail_mode:
                schedule += f"Преподаватель: {lesson.professor}\n"
                schedule += f"{lesson.location}\n"

            prev_lesson_time = lesson.time

        return schedule

    @staticmethod
    def get_info_about_day(schedule: List[Lesson], day_number: int):
        lessons_at_one_day = []
        day_count = 0
        day = None
        for lesson in schedule:
            if day != lesson.day:
                day = lesson.day
                day_count += 1

            if day_count == day_number:
                lessons_at_one_day.append(lesson)

        return lessons_at_one_day

    @staticmethod
    def get_current_week_number(content: bytes) -> int:
        soup = BeautifulSoup(content, features="html.parser")

        week = r"w=(\d{2})"

        prev_week_link = soup.find("span", {"class": "prev"}).a["href"]
        next_week_link = soup.find("span", {"class": "next"}).a["href"]

        prev_week_number = int(re.search(week, prev_week_link).groups()[0])
        current_weak_number = prev_week_number + 1

        return current_weak_number


class ResponseCreator:
    def __init__(self, group: int, week: Optional[int] = None):
        self.group = group
        self.week = week

    def form_response(self) -> Response:
        response = Response()
        page = unecon_request(self.group, self.week)

        if page.status_code == 200:
            schedule = Schedule.get_schedule_from_html(page.content)

            current_week = Schedule.get_current_week_number(page.content)

            markup = create_change_week_markup(self.group, current_week)
            markup.add(telebot.types.InlineKeyboardButton(
                "Больше",
                callback_data=json.dumps({"type": BtnTypes.MORE.name, "group": self.group, "week": current_week})))

            if schedule:
                schedule_str = Schedule.transform_schedule_to_str(schedule)

                response.markup = markup
                response.message = schedule_str
            else:
                response.message = "На эту неделю нет расписания"
        else:
            response.message = "К расписанию нет доступа. Попробуйте позже"

        return response

    def form_inline_response(self) -> InlineResponse:
        inline_response = InlineResponse()
        page = unecon_request(group=self.group)

        if page.status_code == 200:
            schedule = Schedule.get_schedule_from_html(page.content)
            if schedule:

                schedule_str = Schedule.transform_schedule_to_str(schedule)
                this_week = telebot.types.InlineQueryResultArticle(
                    id="1",
                    title="Расписание на эту неделю",
                    input_message_content=telebot.types.InputTextMessageContent(
                        message_text=schedule_str,
                        parse_mode="HTML"
                    )
                )

                inline_response.add_item(this_week)

                current_week_number = Schedule.get_current_week_number(page.content)
                next_week_page = unecon_request(group=12837, week=current_week_number + 1)

                if next_week_page.status_code == 200:
                    next_week_schedule = Schedule.get_schedule_from_html(next_week_page.content)
                    next_week_schedule_str = Schedule.transform_schedule_to_str(next_week_schedule)
                    next_week = telebot.types.InlineQueryResultArticle(
                        id="2",
                        title="Расписание на следующую неделю",
                        input_message_content=telebot.types.InputTextMessageContent(
                            message_text=next_week_schedule_str,
                            parse_mode="HTML"
                        )
                    )
                    inline_response.add_item(next_week)
        else:
            inline_response.is_success = False

        return inline_response

    def form_on_button_click_response(self, btn_data: dict) -> ButtonClickResponse:
        button_click_response = ButtonClickResponse()

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

            if schedule:
                schedule_str = Schedule.transform_schedule_to_str(schedule)

                button_click_response.text = schedule_str
                button_click_response.markup = markup
            else:
                button_click_response.text = "На эту неделю нет расписания"
                button_click_response.markup = markup

        elif callback_btn_type == BtnTypes.MORE:
            if schedule:
                buttons_markup = create_change_week_markup(self.group, self.week)
                get_full_days_markup = create_get_full_days_markup(schedule, self.group, self.week)
                markup = mix_markups(buttons_markup, get_full_days_markup)

                schedule_str = Schedule.transform_schedule_to_str(schedule)

                button_click_response.text = schedule_str
                button_click_response.markup = markup

        elif callback_btn_type == BtnTypes.GET_FULL_DAY:
            if schedule:
                lessons_at_this_day = Schedule.get_info_about_day(schedule, btn_data["day"])
                lessons_str = Schedule.transform_schedule_to_str(lessons_at_this_day, is_detail_mode=True)
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
                button_click_response.text = lessons_str
                button_click_response.markup = markup

        return button_click_response

