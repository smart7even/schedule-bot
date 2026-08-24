import re
from dataclasses import dataclass
from datetime import datetime, date
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin, urlparse, parse_qs

from core.types.lesson import Lesson


@dataclass(frozen=True)
class SchedulePeriod:
    start: date
    end: date

    @property
    def academic_year_start(self) -> int:
        """Return the year whose September 1 belongs to this first week."""
        for year in range(self.start.year, self.end.year + 1):
            september_first = date(year, 9, 1)
            if self.start <= september_first <= self.end:
                return year

        # Non-first weeks do not contain September 1. The academic year starts
        # in the previous calendar year for January-August dates.
        return self.start.year if self.start.month >= 9 else self.start.year - 1


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
                    lesson_professor_id_href = lesson_professor_span.a["href"]
                    parsed_uri = urlparse(lesson_professor_id_href)
                    # Extract the query parameters
                    query_params = parse_qs(parsed_uri.query)
                    # Get the value of the 'p' parameter
                    lesson_professor_id_str = query_params.get('p', [None])[0]
                    lesson_professor_id = int(lesson_professor_id_str) if lesson_professor_id_str else None
                    # Print the value
                else:
                    lesson_professor = None
                    lesson_professor_id = None

                lesson_group_span = tr.find("span", {"class": "group"})
                if lesson_group_span:
                    lesson_group = lesson_group_span.text
                else:
                    lesson_group = None

                # The source repeats room markup for several responsive
                # breakpoints. Prefer the desktop cell because its room and
                # building spans are separate and therefore do not mix the
                # room-map button caption into the visible location.
                lesson_location_span = tr.select_one("td.no_768 span.aud")
                lesson_building_span = tr.select_one("td.no_768 span.korpus")

                lesson_location: Optional[str] = None
                lesson_room_url: Optional[str] = None
                lesson_room_map_caption: Optional[str] = None

                if lesson_location_span is not None:
                    room_link = lesson_location_span.select_one("a[href]")
                    if room_link is not None:
                        lesson_room_url = urljoin(
                            "https://rasp.unecon.ru/",
                            room_link.get("href", ""),
                        )
                        lesson_room_map_caption = room_link.get_text(
                            " ", strip=True
                        ) or None

                    # Read only the text directly owned by the room span. This
                    # intentionally excludes button text such as "НА СХЕМЕ
                    # ЛИНГВОБАШНИ".
                    room = " ".join(
                        text.strip()
                        for text in lesson_location_span.find_all(
                            string=True,
                            recursive=False,
                        )
                        if text.strip()
                    )
                    building = (
                        lesson_building_span.get_text(" ", strip=True)
                        if lesson_building_span is not None
                        else ""
                    )
                    lesson_location = " ".join(
                        part for part in (room, building) if part
                    )

                lessons_location_remote_span = tr.find("span", {"class": "prim"})

                if (
                    lessons_location_remote_span is not None
                    and lessons_location_remote_span.get_text(" ", strip=True)
                ):
                    lesson_location = lessons_location_remote_span.get_text(
                        " ", strip=True
                    )
                    lesson_room_url = None
                    lesson_room_map_caption = None

                lesson_location = lesson_location or ""

                lesson = Lesson(lesson_name, lesson_day,
                                lesson_day_of_week, lesson_time, lesson_professor,
                                lesson_location, lesson_group,
                                lesson_professor_id, lesson_room_url,
                                lesson_room_map_caption)
                lessons.append(lesson)

        return lessons

    def get_current_week_number(self) -> int:
        """
        Parses html content and extracts study week number since the start of study year
        :return:
        """
        soup = BeautifulSoup(self.html_content, features="html.parser")

        week = r"w=(\d{1,2})"

        previous = soup.select_one("span.prev a")
        if previous is None:
            return 1

        match = re.search(week, previous.get("href", ""))
        if match is None:
            raise ValueError("UNECON previous-week link is invalid")
        return int(match.group(1)) + 1

    def get_schedule_period(self) -> SchedulePeriod:
        """Parse the exact date interval displayed for the requested week."""
        soup = BeautifulSoup(self.html_content, features="html.parser")
        schedule = soup.select_one("div.rasp h1")

        if schedule is None:
            raise ValueError("Response is not a UNECON schedule page")

        match = re.search(
            r"Расписание\s+с\s+(\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})",
            schedule.get_text(" ", strip=True),
        )
        if match is None:
            raise ValueError("UNECON schedule period is missing")

        return SchedulePeriod(
            start=datetime.strptime(match.group(1), "%d.%m.%Y").date(),
            end=datetime.strptime(match.group(2), "%d.%m.%Y").date(),
        )

    def get_schedule_subject(self) -> str:
        """Return the group/professor label shown below the period heading."""
        soup = BeautifulSoup(self.html_content, features="html.parser")
        schedule = soup.select_one("div.rasp h1")
        if schedule is None:
            raise ValueError("Response is not a UNECON schedule page")

        text = schedule.get_text(" ", strip=True)
        match = re.search(
            r"Расписание\s+с\s+\d{2}\.\d{2}\.\d{4}\s+по\s+\d{2}\.\d{2}\.\d{4}\s+(.+)$",
            text,
        )
        if match is None:
            raise ValueError("UNECON schedule subject is missing")
        return match.group(1).strip()
