from typing import List

from core.types.lesson import Lesson
from site_parser import UneconParser


class Schedule:
    """
    Класс расписания для обработки списка объектов Lesson
    """
    def __init__(self, lessons: List[Lesson]):
        self.lessons = lessons

    def transform_schedule_to_str(self, is_detail_mode=False) -> str:
        """
        Создает из списка объектов Lesson их строковое представление для отправки пользователю
        :param is_detail_mode: режим отображения подробной информации
        :return: строковое представление расписания
        """
        day = None
        prev_lesson_time = None
        schedule_str = ""
        for lesson in self.lessons:
            if lesson.day != day or not day:
                day = lesson.day
                schedule_str += f"\n<b>{day} {lesson.day_of_week}</b>\n"

            if prev_lesson_time != lesson.time:
                if is_detail_mode:
                    schedule_str += "\n"
                schedule_str += f"<b>{lesson.time}</b>\n{lesson.name}\n"
            else:
                if is_detail_mode:
                    schedule_str += "\n"

            if is_detail_mode:
                schedule_str += f"Преподаватель: {lesson.professor}\n"
                schedule_str += f"{lesson.location}\n"

            prev_lesson_time = lesson.time

        return schedule_str

    def get_info_about_day(self, day_number: int) -> List[Lesson]:
        """
        Формирует список объектов Lesson, относящихся к опеределенному дню
        :param day_number: день недели по счету от начала списка self.lessons
        :return: список объектов Lesson, относящихся к опеределенному дню
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
