import unittest

from core.types.lesson import Lesson
from scripts.audit_live_schedules import check_rows, choose_groups


class LiveScheduleAuditTest(unittest.TestCase):
    def test_sample_covers_faculties_and_is_reproducible(self):
        groups = [
            {"id": 1, "is_active": True, "faculty_id": 10, "course": 1},
            {"id": 2, "is_active": True, "faculty_id": 10, "course": 2},
            {"id": 3, "is_active": True, "faculty_id": 20, "course": 1},
            {"id": 4, "is_active": False, "faculty_id": 30, "course": 3},
        ]

        first = choose_groups(groups, 3, "same-seed", set())
        second = choose_groups(groups, 3, "same-seed", set())

        self.assertEqual(first, second)
        self.assertEqual({1, 2, 3}, {group["id"] for group in first})

    def test_room_loss_is_detected_independently_of_parser(self):
        lesson = Lesson(
            "Экономическая статистика (Лекция)", "22.09.2026", "ВТ",
            "12:50 - 14:20", None, "Чуракова И.Ю.", None, None,
        )

        problems = check_rows(
            [("102 ауд.", "Москательный 4", "Чуракова И.Ю.", None)],
            [lesson],
        )

        self.assertTrue(any("102 ауд." in problem for problem in problems))
        self.assertTrue(any("Москательный 4" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
