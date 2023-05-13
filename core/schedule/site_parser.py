import re
from bs4 import BeautifulSoup
from typing import List, Optional

from core.types.lesson import Lesson


class UneconParser:
    """Unecon schedule parser"""
    def __init__(self, html_content: bytes):
        """
        :param html_content: html content from unecon schedule page
        """
        self.html_content = html_content

    def parse_page(self) -> List[Lesson]:
        """
        Parses html and returns list of lesson objects
        """
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
                lesson_name_tr = tr.find("span", {"class": "predmet"})
                lesson_name = lesson_name_tr.text
                lesson_time = tr.find("span", {"class": "time"}).string
                lesson_professor_span = tr.find("span", {"class": "prepod"})
                if lesson_professor_span.a:
                    lesson_professor = lesson_professor_span.a.text
                else:
                    lesson_professor = None

                lesson_location_span = tr.find("span", {"class": "aud"})

                lesson_location: Optional[str] = None

                if lesson_location_span.text:
                    lesson_location = lesson_location_span.text.strip()

                lessons_location_remote_span = tr.find("span", {"class": "prim"})

                if lessons_location_remote_span.text:
                    lesson_location = lessons_location_remote_span.text

                if lesson_location:
                    lesson_location = lesson_location.replace('ПОКАЗАТЬ НА СХЕМЕ', '')

                lesson = Lesson(lesson_name, lesson_day,
                                lesson_day_of_week, lesson_time, lesson_professor, lesson_location)
                lessons.append(lesson)

        return lessons

    def get_current_week_number(self) -> int:
        """
        Parses html content and extracts study week number since the start of study year
        :return:
        """
        soup = BeautifulSoup(self.html_content, features="html.parser")

        week = r"w=(\d{1,2})"

        prev_week_link = soup.find("span", {"class": "prev"}).a["href"]
        next_week_link = soup.find("span", {"class": "next"}).a["href"]

        prev_week_number = int(re.search(week, prev_week_link).groups()[0])
        current_week_number = prev_week_number + 1

        return current_week_number
