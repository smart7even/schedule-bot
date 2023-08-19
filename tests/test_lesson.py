from core.types.lesson import Lesson


def test_lesson_sorting():
    lessons = [
        Lesson("Math", "25.08.2023", "5", "10:00-11:00", "Dr. Smith", "Room 101"),
        Lesson("English", "24.08.2023", "4", "14:00-15:00", "Dr. Brown", "Room 102"),
        Lesson("History", "23.08.2023", "3", "09:00-10:00", "Dr. White", "Room 103")
    ]

    sorted_lessons = sorted(lessons, key=lambda lesson: lesson.get_start_date())

    # Verifying the order of the sorted lessons
    assert sorted_lessons[0].name == "History"
    assert sorted_lessons[1].name == "English"
    assert sorted_lessons[2].name == "Math"
