from typing import Optional, List

from core.models.group import Group
from db import Session


class GroupRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """Gets group by id"""
        return self.session.query(Group).filter(Group.id == group_id).one_or_none()

    def get(self, faculty_id: Optional[int] = None, course: Optional[int] = None,
            name: Optional[str] = None, include_inactive: bool = False) -> List[Group]:
        """Gets group by id"""

        query_parameters = []

        if faculty_id:
            query_parameters.append(Group.faculty_id == faculty_id)

        if course:
            query_parameters.append(Group.course == course)

        if name:
            search = "%{}%".format(name)
            query_parameters.append(Group.name.like(search))

        if not include_inactive:
            query_parameters.append(Group.is_active.is_(True))

        return (
            self.session.query(Group)
            .filter(*query_parameters)
            .order_by(Group.course.asc(), Group.name.asc())
            .all()
        )

    def get_all(self, include_inactive: bool = False) -> List[Group]:
        """Gets all groups stored in db"""
        query = self.session.query(Group)
        if not include_inactive:
            query = query.filter(Group.is_active.is_(True))
        return query.order_by(Group.course.asc(), Group.name.asc()).all()

    def get_courses_in_faculty(self, faculty_id: int):
        """
        Gets courses that exist in faculty
        :param faculty_id: faculty id in the university site
        :return: courses list
        """
        session = self.session
        courses = session.query(Group.course).filter(
            Group.faculty_id == faculty_id,
            Group.is_active.is_(True),
        ).distinct().all()
        courses = list(map(lambda wrapped_list: wrapped_list[0], courses))
        courses.sort()
        return courses

    def get_groups_by_faculty_and_course(self, faculty_id: int, course: int):
        """
        Gets groups with particular faculty and course
        :param faculty_id: faculty id in the university site
        :param course: course number
        :return: list of group objects
        """
        return self.session.query(Group).filter(
            Group.faculty_id == faculty_id,
            Group.course == course,
            Group.is_active.is_(True),
        ).order_by(Group.name.asc()).all()
