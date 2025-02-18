from sqlalchemy import Column, Integer, Text, Float, DateTime

from db import Base

class Vacancy(Base):
    """Vacancy model"""
    __tablename__ = "vacancy"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime())
    name = Column(Text())
    company = Column(Text())
    application_guidelines = Column(Text())
    salary_type = Column(Text())
    salary_payment_frequency_type = Column(Text())
    salary_from = Column(Float())
    salary_from_currency = Column(Text())
    salary_to = Column(Float())
    salary_to_currency = Column(Text())
    requirements = Column(Text())
    responsibilities = Column(Text())
    work_type = Column(Text())
    work_schedule = Column(Text())
    number_of_working_days_in_a_week = Column(Integer)
    number_of_working_hours_in_a_week = Column(Integer)
    probation_period_days = Column(Integer)
    text = Column(Text())