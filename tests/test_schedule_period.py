import asyncio
import os
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from core.schedule.site_parser import SchedulePeriod, UneconParser
from core.services import schedule_context_service
from core.utils.academic_year import academic_week_for, first_study_week_start


FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return (FIXTURES / name).read_bytes()


class FakeResponse:
    def __init__(self, content, url="https://rasp.unecon.ru/raspisanie_grp.php?g=13872&w=1"):
        self.content = content
        self.text = content.decode()
        self.url = url
        self.status_code = 200


class SchedulePeriodTest(unittest.TestCase):
    def test_period_identifies_old_academic_year(self):
        parser = UneconParser(fixture("week_1_2025.html"))
        period = parser.get_schedule_period()
        self.assertEqual(date(2025, 9, 1), period.start)
        self.assertEqual(2025, period.academic_year_start)
        self.assertEqual(1, parser.get_current_week_number())
        self.assertEqual("Группа БИ-2501", parser.get_schedule_subject())

    def test_period_identifies_new_academic_year_before_september(self):
        period = UneconParser(fixture("week_1_2026.html")).get_schedule_period()
        self.assertEqual(date(2026, 8, 31), period.start)
        self.assertEqual(2026, period.academic_year_start)

    def test_listing_is_not_accepted_as_schedule(self):
        parser = UneconParser(fixture("group_listing.html"))
        with self.assertRaises(ValueError):
            parser.get_schedule_period()

    def test_calendar_week_handles_53_and_early_new_year(self):
        self.assertEqual(53, academic_week_for(date(2025, 8, 25)).week)
        self.assertEqual(1, academic_week_for(date(2026, 8, 31)).week)
        self.assertEqual(date(2026, 8, 31), first_study_week_start(2026))

    @patch.object(schedule_context_service, "_sentinel_group_ids", return_value=[1, 2, 3])
    @patch.object(schedule_context_service, "_parse_group_page")
    def test_context_recommends_new_week_when_source_rolls_early(self, parse, _sentinels):
        old_current = SchedulePeriod(date(2026, 8, 24), date(2026, 8, 30))
        new_first = SchedulePeriod(date(2026, 8, 31), date(2026, 9, 6))

        def result(_group_id, week=None):
            return (1, new_first) if week == 1 else (52, old_current)

        parse.side_effect = result
        context = schedule_context_service.detect_schedule_context(date(2026, 8, 24))
        self.assertTrue(context["upcoming"]["published"])
        self.assertEqual(1, context["recommended"]["week"])
        self.assertEqual(2026, context["recommended"]["academic_year_start"])

    @patch.object(schedule_context_service, "_sentinel_group_ids", return_value=[1, 2, 3])
    @patch.object(schedule_context_service, "_parse_group_page")
    def test_context_keeps_week_52_before_rollover(self, parse, _sentinels):
        current = SchedulePeriod(date(2026, 8, 24), date(2026, 8, 30))
        old_first = SchedulePeriod(date(2025, 9, 1), date(2025, 9, 7))

        def result(_group_id, week=None):
            return (1, old_first) if week == 1 else (52, current)

        parse.side_effect = result
        context = schedule_context_service.detect_schedule_context(date(2026, 8, 24))
        self.assertFalse(context["upcoming"]["published"])
        self.assertEqual(52, context["recommended"]["week"])

    def test_schedule_response_keeps_legacy_fields(self):
        import server

        response = FakeResponse(fixture("week_52_2026.html"))
        with patch.object(server, "unecon_request", return_value=response):
            result = asyncio.run(server.get_group_schedule(13872, 52))

        self.assertEqual(52, result["week"])
        self.assertEqual([], result["lessons"])
        self.assertTrue(result["has_schedule_days"])
        self.assertEqual("2026-08-24", result["period_start"])
        self.assertEqual(2025, result["academic_year_start"])


if __name__ == "__main__":
    unittest.main()
