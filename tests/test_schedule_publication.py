import os
import unittest
from datetime import date
from unittest.mock import Mock, patch


os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import server
from core.request import unecon_request
from core.schedule.site_parser import SchedulePeriod


class SchedulePublicationTest(unittest.TestCase):
    def tearDown(self):
        server._group_published_through.cache_clear()
        server._professor_published_through.cache_clear()

    def test_future_empty_period_beyond_horizon_is_unpublished(self):
        period = SchedulePeriod(date(2099, 9, 21), date(2099, 9, 27))

        self.assertFalse(server._has_schedule_days(period, [], None))
        self.assertFalse(
            server._has_schedule_days(period, [], date(2099, 9, 20))
        )

    def test_empty_period_inside_horizon_is_a_published_free_week(self):
        period = SchedulePeriod(date(2099, 9, 21), date(2099, 9, 27))

        self.assertTrue(
            server._has_schedule_days(period, [], date(2099, 10, 4))
        )

    def test_past_empty_period_is_authoritative_without_horizon(self):
        period = SchedulePeriod(date(2000, 1, 3), date(2000, 1, 9))

        self.assertTrue(server._has_schedule_days(period, [], None))

    @patch.object(server, "unecon_request")
    def test_semester_horizon_probe_is_short_and_cached(self, request):
        response = Mock()
        response.status_code = 200
        response.text = (
            '<div class="rasp"><h1>'
            'Расписание с 01.09.2099 по 04.10.2099 Группа БИ-9901'
            '</h1></div>'
        )
        request.return_value = response

        first = server._group_published_through(42, 7)
        second = server._group_published_through(42, 7)

        self.assertEqual(date(2099, 10, 4), first)
        self.assertEqual(first, second)
        request.assert_called_once_with(
            group_id=42,
            semester=True,
            timeout=(2, 4),
        )

    @patch("core.request.requests.get")
    def test_semester_request_does_not_send_a_conflicting_week(self, get):
        unecon_request(42, week=7, semester=True, timeout=(2, 4))

        params = get.call_args.kwargs["params"]
        self.assertEqual({"g": 42, "semestr": 1}, params)
        self.assertEqual((2, 4), get.call_args.kwargs["timeout"])


if __name__ == "__main__":
    unittest.main()
