import unittest

from core.types.lesson import Lesson


class LessonTest(unittest.TestCase):
    def test_lesson_sorting(self):
        lessons = [
            Lesson("Math", "25.08.2023", "5", "10:00-11:00", "Dr. Smith", "Room 101", "", None),
            Lesson("English", "24.08.2023", "4", "14:00-15:00", "Dr. Brown", "Room 102", "", None),
            Lesson("History", "23.08.2023", "3", "09:00-10:00", "Dr. White", "Room 103", "", None),
        ]

        sorted_lessons = sorted(
            lessons, key=lambda lesson: lesson.get_start_date())
        self.assertEqual("History", sorted_lessons[0].name)
        self.assertEqual("English", sorted_lessons[1].name)
        self.assertEqual("Math", sorted_lessons[2].name)
