import unittest

from core.schedule.site_parser import UneconParser


class RoomMapParserTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
