from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class AcademicWeek:
    academic_year_start: int
    week: int
    period_start: date
    period_end: date


def first_study_week_start(academic_year_start: int) -> date:
    september_first = date(academic_year_start, 9, 1)
    return september_first - timedelta(days=september_first.weekday())


def academic_week_for(day: date) -> AcademicWeek:
    current_year_start = first_study_week_start(day.year)
    academic_year_start = day.year if day >= current_year_start else day.year - 1
    period_start = first_study_week_start(academic_year_start)
    week = (day - period_start).days // 7 + 1
    week_start = period_start + timedelta(days=(week - 1) * 7)
    return AcademicWeek(
        academic_year_start=academic_year_start,
        week=week,
        period_start=week_start,
        period_end=week_start + timedelta(days=6),
    )
