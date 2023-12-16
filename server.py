import re
from typing import Optional
from datetime import datetime

from fastapi import FastAPI

from core.repositories.faculty_repository import FacultyRepository
from core.repositories.group_repository import GroupRepository
from core.request import unecon_request
from core.schedule.site_parser import UneconParser
from core.types.lesson import Lesson
from core.utils.date_utils import get_study_week_number
from db import Session

app = FastAPI()


@app.get("/faculty")
async def get_faculties(name: Optional[str] = None):
    session = Session()
    faculties_repository = FacultyRepository(session)
    faculties = faculties_repository.get(name=name)

    return {"faculties": faculties}


@app.get("/faculty/{faculty_id}")
async def get_faculty_by_id(faculty_id: int):
    session = Session()
    faculties_repository = FacultyRepository(session)
    faculties = faculties_repository.get_by_id(faculty_id)

    return faculties


@app.get("/group")
async def get_groups(course: Optional[int] = None, faculty_id: Optional[int] = None, name: Optional[str] = None):
    session = Session()
    group_repository = GroupRepository(session)
    groups = group_repository.get(course=course, faculty_id=faculty_id, name=name)

    return {"groups": groups}


@app.get("/group/{group_id}")
async def get_group_by_id(group_id: int):
    session = Session()
    group_repository = GroupRepository(session)
    group = group_repository.get_group_by_id(group_id)

    return group


@app.get("/group/{group_id}/schedule")
async def get_group_schedule(group_id: int, week: Optional[int] = None):
    page = unecon_request(group_id=group_id, week=week)

    if page.status_code == 200:
        page_parser = UneconParser(page.text)
        lessons = page_parser.parse_page()
        week = page_parser.get_current_week_number()

        dict_lessons = lessons_to_dict(lessons)

        return {
            'week': week,
            'lessons': dict_lessons
        }

    return {
        'lessons': []
    }


@app.get("/group/{group_id}/lessons/next")
async def get_next_lessons(group_id: int, after_date: Optional[str] = None):
    current_date = None

    now_date = datetime.now()

    if after_date is not None:
        current_date = datetime.fromisoformat(after_date)
    else:
        current_date = now_date

    week = get_study_week_number(current_date, now_date)

    page = unecon_request(group_id=group_id, week=week)

    if page.status_code != 200:
        return {
            'lessons': []
        }

    page_parser = UneconParser(page.text)

    lessons = page_parser.parse_page()

    week = page_parser.get_current_week_number()

    lessons_after_date = get_lessons_after_date(lessons, current_date)

    print(lessons_after_date)

    if len(lessons_after_date) != 0:
        return {
            'lessons': lessons_to_dict(lessons_after_date)
        }

    page = unecon_request(group_id=group_id, week=week + 1)

    if page.status_code != 200:
        return {
            'lessons': []
        }

    page_parser = UneconParser(page.text)
    lessons = page_parser.parse_page()
    week = page_parser.get_current_week_number()

    lessons_after_date = get_lessons_after_date(lessons, current_date)

    if len(lessons_after_date) != 0:
        return {
            'lessons': lessons_to_dict(lessons_after_date)
        }

    return {
        'lessons': []
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


def get_lessons_after_date(lessons: list[Lesson], date: datetime) -> list[Lesson]:
    sorted_lessons = list(sorted(lessons, key=lambda l: l.get_start_date()))

    for i in range(len(sorted_lessons)):
        lesson = sorted_lessons[i]

        if lesson.get_start_date() > date:
            return sorted_lessons[i:]

    return []


def lessons_to_dict(lessons: list[Lesson]) -> list[dict]:
    dict_lessons = []

    for lesson in lessons:
        day = lesson.get_day_start_date()
        start_time = lesson.get_start_date()
        end_time = lesson.get_end_date()

        dict_lesson = {
            'name': lesson.name,
            'day': day.isoformat(),
            'day_of_week': lesson.day_of_week,
            'start': start_time,
            'end': end_time,
            'professor': lesson.professor,
            'location': lesson.location,
            'lesson_type': lesson.get_lesson_type(),
            'is_elective': lesson.get_is_elective()
        }

        dict_lessons.append(dict_lesson)

    return dict_lessons
