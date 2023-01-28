from typing import Optional
from datetime import datetime

from fastapi import FastAPI

from core.repositories.faculty_repository import FacultyRepository
from core.repositories.group_repository import GroupRepository
from core.request import unecon_request
from core.schedule.site_parser import UneconParser
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

        dict_lessons = []

        for lesson in lessons:
            day_pattern = '%d.%m.%Y'
            time_pattern = '%H:%M'
            datetime_pattern = f'{time_pattern} {day_pattern}'

            day = datetime.strptime(lesson.day, day_pattern)
            time: list[str] = lesson.time.replace(" ", "").split('-')

            start_time = datetime.strptime(f'{time[0]} {lesson.day}', datetime_pattern)
            end_time = datetime.strptime(f'{time[1]} {lesson.day}', datetime_pattern)

            dict_lesson = {
                'name': lesson.name,
                'day': day.isoformat(),
                'day_of_week': lesson.day_of_week,
                'start': start_time,
                'end': end_time,
                'professor': lesson.professor,
                'location': lesson.location,
            }

            dict_lessons.append(dict_lesson)

        return {
            'week': week,
            'lessons': dict_lessons
        }

    return {
        'lessons': []
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
