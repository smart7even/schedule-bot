from core.types.lesson import Lesson
from bs4 import BeautifulSoup
import re

from typing import List, Optional


class UneconParser:
    def __init__(self, html_content: bytes):
        self.html_content = html_content

    def parse_page(self):
        soup = BeautifulSoup(self.html_content, features="html.parser")
        day = None
        week = None
        lessons = []
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

    def get_current_week_number(self) -> int:
        soup = BeautifulSoup(self.html_content, features="html.parser")

        week = r"w=(\d{2})"

        prev_week_link = soup.find("span", {"class": "prev"}).a["href"]
        next_week_link = soup.find("span", {"class": "next"}).a["href"]

        prev_week_number = int(re.search(week, prev_week_link).groups()[0])
        current_weak_number = prev_week_number + 1

        return current_weak_number


class Schedule:
    def __init__(self, lessons: List[Lesson]):
        self.lessons = lessons

    @staticmethod
    def get_schedule_from_html(html_content: bytes):
        page_parser = UneconParser(html_content)
        lessons = page_parser.parse_page()
        schedule = Schedule(lessons)
        return schedule

    def transform_schedule_to_str(self, is_detail_mode=False) -> str:
        day = None
        prev_lesson_time = None
        schedule_str = ""
        for lesson in self.lessons:
            if lesson.day != day or not day:
                day = lesson.day
                schedule_str += f"\n<b>{day} {lesson.day_of_week}</b>\n"

            if prev_lesson_time != lesson.time:
                if is_detail_mode:
                    schedule_str += "\n"
                schedule_str += f"<b>{lesson.time}</b>\n{lesson.name}\n"
            else:
                if is_detail_mode:
                    schedule_str += "\n"

            if is_detail_mode:
                schedule_str += f"Преподаватель: {lesson.professor}\n"
                schedule_str += f"{lesson.location}\n"

            prev_lesson_time = lesson.time

        return schedule_str

    def get_info_about_day(self, day_number: int) -> List[Lesson]:
        lessons_at_one_day = []
        day_count = 0
        day = None
        for lesson in self.lessons:
            if day != lesson.day:
                day = lesson.day
                day_count += 1

            if day_count == day_number:
                lessons_at_one_day.append(lesson)

        return lessons_at_one_day
