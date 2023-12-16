import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Lesson:
    name: str
    day: str
    day_of_week: str
    time: str
    professor: str
    location: str

    def get_start_date(self) -> datetime:
        day_pattern = '%d.%m.%Y'
        time_pattern = '%H:%M'
        datetime_pattern = f'{time_pattern} {day_pattern}'

        time: list[str] = self.time.replace(" ", "").split('-')

        start_time = datetime.strptime(f'{time[0]} {self.day}', datetime_pattern)

        return start_time

    def get_end_date(self) -> datetime:
        day_pattern = '%d.%m.%Y'
        time_pattern = '%H:%M'
        datetime_pattern = f'{time_pattern} {day_pattern}'

        time: list[str] = self.time.replace(" ", "").split('-')

        end_time = datetime.strptime(f'{time[1]} {self.day}', datetime_pattern)

        return end_time

    def get_day_start_date(self) -> datetime:
        day_pattern = '%d.%m.%Y'
        day = datetime.strptime(self.day, day_pattern)
        return day

    def get_lesson_type(self) -> Optional[str]:
        match = re.search(r'\(([^()]*)\)$', self.name)

        return match.group(1) if match else None

    def get_is_elective(self) -> Optional[bool]:
        return self.name.startswith("Выбор ")
