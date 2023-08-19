from datetime import datetime, timedelta


def get_week_start(date: datetime) -> datetime:
    return date - timedelta(days=date.weekday())


def get_date(d: datetime) -> datetime:
    return datetime(d.year, d.month, d.day)


def calculate_difference_in_days(date1: datetime, date2: datetime) -> int:
    d1 = datetime(date1.year, date1.month, date1.day)
    d2 = datetime(date2.year, date2.month, date2.day)
    return (d1 - d2).days


kSeptemberMonthNumber: int = 9
kNumberOfDaysInWeek: int = 7


def get_study_week_number(date_time: datetime, now_time: datetime) -> int:
    start_of_study_year_date = get_start_of_study_year_date(now_time)
    days = calculate_difference_in_days(date_time, start_of_study_year_date)
    return (days // kNumberOfDaysInWeek) + 1


def get_start_of_study_week(week: int, now_time: datetime) -> datetime:
    start_of_study_year_date = get_start_of_study_year_date(now_time)
    start_week_date = start_of_study_year_date + timedelta(days=(week - 1) * 7)
    return start_week_date


def get_start_of_study_year_date(now_time: datetime) -> datetime:
    if now_time.month >= kSeptemberMonthNumber:
        return get_week_start(datetime(now_time.year, kSeptemberMonthNumber, 1))
    else:
        return get_week_start(datetime(now_time.year - 1, kSeptemberMonthNumber, 1))
