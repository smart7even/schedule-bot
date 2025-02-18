from typing import List

from db import Session
from core.models.vacancy import Vacancy


class VacancyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self) -> List[Vacancy]:
        """Gets all vacancies stored in db"""
        return self.session.query(Vacancy).order_by(Vacancy.id.desc()).all()
