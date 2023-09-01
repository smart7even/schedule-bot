from typing import List, Optional

from core.types.lesson import Lesson
from core.types.text_elements import (
    Bold,
    Plain,
    NewLine,
    wrap_with_new_lines,
    ElementsContainer
)


class Schedule:
    """Schedule object for processing lessons"""

    def __init__(self, lessons: List[Lesson]):
        self.lessons = lessons

    def transform_schedule_to_str(self,
                                  group_name: Optional[str] = None,
                                  week: Optional[int] = None,
                                  is_detail_mode=False) -> str:
        """
        Transforms schedule to str representation
        :param group_name: group name
        :param week: study week since the start of study year
        :param is_detail_mode: enables detailed representation
        :return: string representation of schedule
        """
        schedule_list = []
        day = None
        prev_lesson_time = None
        is_new_day = None

        if group_name:
            schedule_list.append(Bold(group_name))
            schedule_list.append(NewLine())

        if week:
            schedule_list.append(Bold(f"Неделя {week}"))
            schedule_list.append(NewLine())

        for lesson in self.lessons:
            if lesson.day != day or not day:
                day = lesson.day
                is_new_day = True
                schedule_list.append(wrap_with_new_lines(Bold(f"{day} {lesson.day_of_week}")))
            else:
                is_new_day = False

            if prev_lesson_time != lesson.time or is_new_day:
                if is_detail_mode:
                    schedule_list.append(NewLine())

                schedule_list.append(Bold(lesson.time))
                schedule_list.append(wrap_with_new_lines(Plain(lesson.name)))
                schedule_list.append(Plain(lesson.location.strip().replace('\n', '')))
            else:
                if is_detail_mode:
                    schedule_list.append(NewLine())

            if is_detail_mode:
                schedule_list.append(Plain(f"Преподаватель: {lesson.professor}"))
                schedule_list.append(wrap_with_new_lines(Plain(lesson.location)))

            prev_lesson_time = lesson.time

        elements_container = ElementsContainer(*schedule_list)

        return elements_container.to_str()

    def get_info_about_day(self, day_number: int) -> List[Lesson]:
        """
        Returns the lessons that belong to a particular day
        :param day_number: study day number from the start of the week
        :return: list of Lesson objects
        """
        lessons_at_one_day = []
        day_count = 0
        day = None
        for lesson in self.lessons:
            if day != lesson.day:
                day = lesson.day
                day_count += 1

            if day_count == day_number:
                lessons_at_one_day.append(lesson)

        return lessons_at_one_day


