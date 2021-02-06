from typing import List
from data_types import Lesson
from bs4 import BeautifulSoup
import re


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

                lesson = Lesson(lesson_name, lesson_day,
                                lesson_day_of_week, lesson_time, lesson_professor)
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

            if is_detail_mode:
                schedule += f"Преподаватель: {lesson.professor}\n"

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
    def get_current_week_number(html: bytes) -> int:
        soup = BeautifulSoup(html, features="html.parser")

        week = r"w=(\d{2})"

        prev_week_link = soup.find("span", {"class": "prev"}).a["href"]
        next_week_link = soup.find("span", {"class": "next"}).a["href"]

        prev_week_number = int(re.search(week, prev_week_link).groups()[0])
        current_weak_number = prev_week_number + 1

        return current_weak_number
