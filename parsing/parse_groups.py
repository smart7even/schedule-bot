from bs4 import BeautifulSoup
import requests
from sqlalchemy.orm import sessionmaker
from db import engine
from core.models.group import Group
from core.models.faculty import Faculty

Session = sessionmaker()
Session.configure(bind=engine)


def fill_groups(faculty_id: int, course: int):
    """
    Fill db with groups in particular faculty and course
    :param faculty_id: faculty id in the university site
    :param course: course number
    """
    page = requests.get("https://rasp.unecon.ru/raspisanie.php", params={"fakultet": faculty_id, "kurs": course})

    if page.status_code == 200:
        soup = BeautifulSoup(page.content, features="html.parser")

        groups = soup.find("div", {"class": "grps"})

        if groups:
            session = Session()
            try:
                for group in groups.find_all("a"):
                    new_group = Group(
                        id=group["href"].split("=")[-1],
                        name=group.string,
                        faculty_id=faculty_id,
                        course=course
                    )
                    session.add(new_group)

                session.commit()
            except Exception as e:
                print(e)
            finally:
                session.close()
    else:
        print(f"{page.url} request failed")


def fill_faculties():
    """Fill db with faculties"""
    page = requests.get("https://rasp.unecon.ru")

    if page.status_code == 200:
        soup = BeautifulSoup(page.content, features="html.parser")

        faculties = soup.find("div", {"class": "fakultets"})

        session = Session()

        for faculty in faculties.find_all("a"):
            new_faculty = Faculty(id=faculty["data-fakultet_kod"], name=faculty.string)
            session.add(new_faculty)

        session.commit()
        session.close()
    else:
        print(f"{page.url} request failed")


def get_faculty_courses(faculty_id: int):
    """
    :param faculty_id: faculty id in the university site
    """
    courses = []

    page = requests.get("https://rasp.unecon.ru", {"fakultet": faculty_id})

    if page.status_code == 200:
        soup = BeautifulSoup(page.content, features="html.parser")

        faculties = soup.find("div", {"class": "kurses"})

        for course in faculties.find_all("a"):
            courses.append(course["data-kurs"])
    else:
        print(f"{page.url} request failed")

    return courses


def fill_all_groups():
    """Fill db with all groups"""
    session = Session()

    for faculty in session.query(Faculty).all():
        faculty_courses = get_faculty_courses(faculty.id)

        for course in faculty_courses:
            fill_groups(faculty.id, course)

    session.close()


if __name__ == "__main__":
    fill_all_groups()
