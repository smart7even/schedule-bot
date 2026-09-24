import unittest

from core.schedule.site_parser import UneconParser


class RoomMapParserTest(unittest.TestCase):
    @staticmethod
    def lesson_with_note(room: str, building: str, note: str) -> bytes:
        # Mirrors the university's desktop room cell and separate `prim` note.
        room_search = room.split()[0] if room else ""
        map_link = (
            f'<a href="https://staff.unecon.ru/unecon_scheme.php?initial_kind=8&amp;initial_search={room_search}">'
            '<button>НА СХЕМЕ МОСКАТЕЛЬНЫЙ</button></a>'
            if room else ""
        )
        return f"""
        <table><tr class="new_day">
          <td><span class="date">22.09.2026</span><span class="day">ВТ</span></td>
          <td><span class="time">12:50 - 14:20</span></td>
          <td class="no_768 aud marker">
            <span class="aud">{room}{map_link}</span>
            <span class="korpus">{building}</span>
          </td>
          <td class="predmet">
            <span class="predmet">Экономическая статистика (Лекция)</span>
            <span class="prepod"></span><span class="group"></span>
            <span class="prim">{note}</span>
          </td>
        </tr></table>
        """.encode("utf-8")

    def test_room_map_is_structured_and_button_caption_is_not_location(self):
        html = """
        <table><tr class="new_day">
          <td><span class="date">03.09.2025</span><span class="day">СР</span></td>
          <td><span class="time">14:30 - 16:00</span></td>
          <td class="no_768 aud marker">
            <span class="aud">64 ауд.
              <a href="https://staff.unecon.ru/unecon_scheme.php?initial_kind=2&amp;initial_search=64">
                <button><b>НА СХЕМЕ ЛИНГВОБАШНИ</b></button>
              </a>
            </span>
            <span class="korpus">Грибоедова 30/32 2 лестница</span>
          </td>
          <td class="predmet">
            <span class="predmet">Иностранный язык (Практика)</span>
            <span class="prepod"><a href="raspisanie_prepod.php?p=105658">Антонова Ксения Николаевна</a></span>
            <span class="group"></span><span class="prim"></span>
          </td>
        </tr></table>
        """.encode("utf-8")

        lesson = UneconParser(html).parse_page()[0]

        self.assertEqual(
            "64 ауд. Грибоедова 30/32 2 лестница",
            lesson.location,
        )
        self.assertNotIn("СХЕМЕ", lesson.location)
        self.assertEqual(
            "https://staff.unecon.ru/unecon_scheme.php?initial_kind=2&initial_search=64",
            lesson.room_url,
        )
        self.assertEqual("НА СХЕМЕ ЛИНГВОБАШНИ", lesson.room_map_caption)
        self.assertIsNone(lesson.note)

    def test_note_keeps_room_building_and_map_link(self):
        lesson = UneconParser(self.lesson_with_note(
            "102 ауд. ", "Москательный 4", "Чуракова И.Ю."
        )).parse_page()[0]

        self.assertEqual(
            "102 ауд. Москательный 4 · Чуракова И.Ю.", lesson.location
        )
        self.assertEqual("Чуракова И.Ю.", lesson.note)
        self.assertEqual(
            "https://staff.unecon.ru/unecon_scheme.php?initial_kind=8&initial_search=102",
            lesson.room_url,
        )
        self.assertEqual("НА СХЕМЕ МОСКАТЕЛЬНЫЙ", lesson.room_map_caption)

    def test_subgroup_note_stays_visible_with_room(self):
        lesson = UneconParser(self.lesson_with_note(
            "88 ауд. ", "Грибоедова 30/32 2 лестница",
            "испанский подгруппа 2",
        )).parse_page()[0]

        self.assertIn("88 ауд.", lesson.location)
        self.assertIn("испанский подгруппа 2", lesson.location)
        self.assertEqual("испанский подгруппа 2", lesson.note)

    def test_note_without_physical_room_is_visible_fallback(self):
        lesson = UneconParser(self.lesson_with_note(
            "", "", "Дистанционно"
        )).parse_page()[0]

        self.assertEqual("Дистанционно", lesson.location)
        self.assertEqual("Дистанционно", lesson.note)
        self.assertIsNone(lesson.room_url)


if __name__ == "__main__":
    unittest.main()
