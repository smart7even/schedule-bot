from bs4 import BeautifulSoup
import requests
from sqlalchemy.orm import sessionmaker
from models import engine, User, Group, Faculty

Session = sessionmaker()
Session.configure(bind=engine)


def fill_groups(faculty: int, course: int):
    page = requests.get("https://rasp.unecon.ru/raspisanie.php", params={"fakultet": faculty, "kurs": course})

    soup = BeautifulSoup(page.content, features="html.parser")

    groups = soup.find("div", {"class": "grps"})

    if groups:
        session = Session()
        try:
            for group in groups.find_all("a"):
                new_group = Group(id=group["href"].split("=")[-1], name=group.string, faculty_id=faculty, course=course)
                session.add(new_group)

            session.commit()
        except Exception as e:
            print(e)
        finally:
            session.close()


def fill_faculties():
    page = requests.get("https://rasp.unecon.ru")

    soup = BeautifulSoup(page.content, features="html.parser")

    faculties = soup.find("div", {"class": "fakultets"})

    session = Session()

    for faculty in faculties.find_all("a"):
        new_faculty = Faculty(id=faculty["data-fakultet_kod"], name=faculty.string)
        session.add(new_faculty)

    session.commit()
    session.close()


def get_faculty_courses(faculty_id: int):
    courses = []

    page = requests.get("https://rasp.unecon.ru", {"fakultet": faculty_id})

    soup = BeautifulSoup(page.content, features="html.parser")

    faculties = soup.find("div", {"class": "kurses"})

    for course in faculties.find_all("a"):
        courses.append(course["data-kurs"])

    return courses


def fill_all_groups():
    session = Session()

    for faculty in session.query(Faculty).all():
        faculty_courses = get_faculty_courses(faculty.id)

        for course in faculty_courses:
            fill_groups(faculty.id, course)

    session.close()


if __name__ == "__main__":
    fill_all_groups()
