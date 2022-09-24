from typing import Optional

from fastapi import FastAPI

from core.models import group
from core.models import faculty
from core.repositories.faculty_repository import FacultyRepository
from core.repositories.group_repository import GroupRepository
from db import Session

app = FastAPI()


@app.get("/faculty")
async def get_faculties():
    session = Session()
    faculties_repository = FacultyRepository(session)
    faculties = faculties_repository.get_all()

    return {"faculties": faculties}


@app.get("/faculty/{faculty_id}")
async def get_faculty_by_id(faculty_id: int):
    session = Session()
    faculties_repository = FacultyRepository(session)
    faculty = faculties_repository.get_by_id(faculty_id)

    return faculty


@app.get("/group")
async def get_groups(course: Optional[int] = None, faculty_id: Optional[int] = None):
    session = Session()
    group_repository = GroupRepository(session)
    groups = group_repository.get(course=course, faculty_id=faculty_id)

    return {"groups": groups}


@app.get("/group/{group_id}")
async def get_group_by_id(group_id: int):
    session = Session()
    group_repository = GroupRepository(session)
    group = group_repository.get_group_by_id(group_id)

    return group


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
