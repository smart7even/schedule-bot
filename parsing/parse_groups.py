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

    session = Session()
    for group in groups.find_all("a"):
        new_group = Group(id=group["href"].split("=")[-1], name=group.string, faculty_id=faculty, course=course)
        session.add(new_group)

    session.commit()
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


if __name__ == "__main__":
    fill_groups(faculty=22, course=1)
