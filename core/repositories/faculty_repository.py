from typing import List, Optional

from sqlalchemy.orm import joinedload

from core.models.faculty import Faculty
from core.models.group import Group
from db import Session


class FacultyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, faculty_id: int) -> Optional[Faculty]:
        """Gets faculty by id"""
        return self.session.query(Faculty).options(joinedload(Faculty.groups)).filter(Group.faculty_id == faculty_id).first()

    def get(self, name: Optional[str] = None) -> List[Faculty]:
        query_parameters = []

        if name:
            search = "%{}%".format(name)
            query_parameters.append(Faculty.name.like(search))

        return self.session.query(Faculty).filter(*query_parameters).all()

    def get_all(self) -> List[Faculty]:
        """Gets all faculties stored in db"""
        return self.session.query(Faculty).all()
