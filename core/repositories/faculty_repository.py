from typing import List

from core.models.faculty import Faculty
from db import Session


class FacultyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self) -> List[Faculty]:
        """Gets all faculties stored in db"""
        return self.session.query(Faculty).all()
