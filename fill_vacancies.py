import json
import re

from typing import Optional

from datetime import datetime
from sqlalchemy.orm import sessionmaker

from core.models.vacancy import Vacancy
from db import engine

Session = sessionmaker()
Session.configure(bind=engine)


def text_to_days(text: Optional[str]) -> Optional[int]:
    if text is None:
        return None

    # Define a mapping of time units to approximate days
    time_unit_to_days = {
        "день": 1,
        "дня": 1,
        "дней": 1,
        "месяц": 30,
        "месяца": 30,
        "месяцев": 30,
        "год": 365,
        "года": 365,
        "лет": 365
    }

    # Match the number and the time unit in the text
    match = re.match(r"(\d+)\s+(\w+)", text)
    if not match:
        return None

    # Extract the number and the time unit
    number = int(match.group(1))
    time_unit = match.group(2).lower()

    # Get the equivalent days for the time unit
    if time_unit not in time_unit_to_days:
        raise ValueError(f"Unsupported time unit: {time_unit}")

    return number * time_unit_to_days[time_unit]


def populate_vacancy_table(json_data: dict, session: Session):
    """
    Populate the Vacancy table with data from the JSON.

    :param json_data: Dictionary containing the JSON data.
    :param session: SQLAlchemy Session instance.
    """
    # Extract salary details
    salary = json_data.get("salary", {}) or {}

    salary_from_dict = salary.get("from", {}) or {}
    salary_from = salary_from_dict.get("value")
    salary_from_currency = salary_from_dict.get("currency")

    salary_to_dict = salary.get("to", {}) or {}
    salary_to = salary_to_dict.get("value")
    salary_to_currency = salary_to_dict.get("currency")

    # Extract conditions
    conditions = json_data.get("conditions", {})

    # Create Vacancy instance
    vacancy = Vacancy(
        id=json_data.get("id"),
        date=datetime.fromisoformat(json_data.get("date")),
        name=json_data.get("name"),
        company=json_data.get("company"),
        application_guidelines=json_data.get("application_guidelines"),
        salary_type=salary.get("type"),
        salary_payment_frequency_type=salary.get("payment_type"),
        salary_from=salary_from,
        salary_from_currency=salary_from_currency,
        salary_to=salary_to,
        salary_to_currency=salary_to_currency,
        requirements="\n".join(json_data.get("requirements", [])),
        responsibilities="\n".join(json_data.get("responsibilities", [])),
        work_type=conditions.get("type"),
        work_schedule=conditions.get("work_schedule"),
        number_of_working_days_in_a_week=conditions.get("number_of_working_days_in_a_week"),
        number_of_working_hours_in_a_week=conditions.get("number_of_working_hours_in_a_week"),
        probation_period_days=text_to_days(conditions.get("probation_period")),
        text=json_data.get("text")
    )

    # Add the vacancy to the session
    session.add(vacancy)

    # Commit the transaction
    session.commit()


# Example usage
if __name__ == "__main__":
    json_string = open('data/response10_fixed.json').read()
    data = json.loads(json_string)

    session = Session()

    # Populate the database

    for vacancy in data:
        populate_vacancy_table(vacancy, session)
