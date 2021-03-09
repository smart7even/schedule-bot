from sqlalchemy import Column, Integer, String, ForeignKey

from db import Base, Session


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey('faculties.id', ondelete="CASCADE"))
    course = Column(Integer)

    @staticmethod
    def get_group_by_id(group_id: int):
        session = Session()

        group = session.query(Group).filter(Group.id == group_id).one_or_none()

        session.close()

        return group

    @staticmethod
    def get_all():
        session = Session()

        groups = session.query(Group).all()

        session.close()

        return groups

    @staticmethod
    def get_courses_in_faculty(faculty_id: int):
        session = Session()

        courses = session.query(Group.course).filter(Group.faculty_id == faculty_id).distinct().all()

        session.close()

        courses = list(map(lambda wrapped_list: wrapped_list[0], courses))
        courses.sort()

        return courses

    @staticmethod
    def get_groups_by_faculty_and_course(faculty_id: int, course: int):
        session = Session()

        groups = session.query(Group).filter(Group.faculty_id == faculty_id, Group.course == course).all()

        session.close()

        return groups

    def __repr__(self) -> str:
        return f"Group(group_id={self.id} group_name={self.name})"