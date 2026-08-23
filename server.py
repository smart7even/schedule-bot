import re
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException

from core.repositories.asset_repository import AssetRepository
from core.repositories.faculty_repository import FacultyRepository
from core.repositories.group_repository import GroupRepository
from core.repositories.vacancy_repository import VacancyRepository
from core.request import unecon_professor_request, unecon_request
from core.schedule.site_parser import UneconParser
from core.services.schedule_context_service import (
    ScheduleSourceError,
    get_schedule_context,
)
from core.types.lesson import Lesson
from core.utils.date_utils import get_study_week_number
from core.utils.academic_year import academic_week_for
from db import Session

app = FastAPI()


@app.get("/health")
async def health():
    """Process-level health check that does not depend on UNECON availability."""
    return {"status": "ok"}


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
async def get_groups(course: Optional[int] = None, faculty_id: Optional[int] = None,
                     name: Optional[str] = None, include_inactive: bool = False):
    session = Session()
    group_repository = GroupRepository(session)
    groups = group_repository.get(
        course=course,
        faculty_id=faculty_id,
        name=name,
        include_inactive=include_inactive,
    )

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
        try:
            period = page_parser.get_schedule_period()
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error))
        lessons = page_parser.parse_page()
        week = page_parser.get_current_week_number()

        dict_lessons = lessons_to_dict(lessons)

        return {
            'week': week,
            'academic_year_start': period.academic_year_start,
            'period_start': period.start.isoformat(),
            'period_end': period.end.isoformat(),
            'lessons': dict_lessons
        }

    return {
        'lessons': []
    }


@app.get("/professor/{professor_id}/schedule")
def get_professor_schedule(professor_id: int, week: Optional[int] = None):
    page = unecon_professor_request(professor_id=professor_id, week=week)

    if page.status_code == 200:
        page_parser = UneconParser(page.text)
        try:
            period = page_parser.get_schedule_period()
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error))
        lessons = page_parser.parse_page()
        week = page_parser.get_current_week_number()

        dict_lessons = lessons_to_dict(lessons)

        return {
            'week': week,
            'academic_year_start': period.academic_year_start,
            'period_start': period.start.isoformat(),
            'period_end': period.end.isoformat(),
            'lessons': dict_lessons
        }

    return {
        'lessons': []
    }


@app.get("/schedule/context")
async def get_context(force_refresh: bool = False):
    try:
        return get_schedule_context(force_refresh=force_refresh)
    except ScheduleSourceError as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.get("/group/{group_id}/lessons/next")
async def get_next_lessons(group_id: int, after_date: Optional[str] = None):
    current_date = None

    now_date = datetime.now()

    if after_date is not None:
        current_date = datetime.fromisoformat(after_date)
    else:
        current_date = now_date

    try:
        context = get_schedule_context()
        if current_date.date() == now_date.date():
            week = context['recommended']['week']
        else:
            week = academic_week_for(current_date.date()).week
    except ScheduleSourceError:
        # Keep the endpoint available if the metadata probe is temporarily down.
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

    if len(lessons_after_date) != 0:
        return {
            'lessons': lessons_to_dict(lessons_after_date)
        }

    next_week = week + 1 if week < 53 else 1
    page = unecon_request(group_id=group_id, week=next_week)

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


@app.get("/asset/{asset_id}")
async def get_asset(asset_id: str):
    session = Session()

    asset_repository = AssetRepository(session)

    asset = asset_repository.get_by_id(asset_id)

    return asset


@app.get("/vacancy")
async def get_vacancies():
    session = Session()

    vacancy_repository = VacancyRepository(session)

    vacancies = vacancy_repository.get_all()

    return vacancies


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
            'is_elective': lesson.get_is_elective(),
            'group': lesson.group,
            'professor_id': lesson.professor_id,
        }

        dict_lessons.append(dict_lesson)

    return dict_lessons


if __name__ == '__main__':
    print(get_professor_schedule(8806))
