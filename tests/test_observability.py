import asyncio
import json
import logging
import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from core.health import database_is_ready
from core.observability import (
    JsonFormatter,
    log_event,
    normalized_route,
    safe_path_dimensions,
)


class ObservabilityTest(unittest.TestCase):
    def test_json_formatter_emits_safe_structured_fields(self):
        record = logging.LogRecord(
            name="schedule-api",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="HTTP request completed",
            args=(),
            exc_info=None,
        )
        record.event = "http.request"
        record.group_id = 123
        record.details = {"must": "not leak"}

        payload = json.loads(JsonFormatter().format(record))

        self.assertEqual("http.request", payload["event"])
        self.assertEqual(123, payload["group_id"])
        self.assertNotIn("details", payload)

    def test_path_dimensions_keep_only_numeric_public_ids(self):
        self.assertEqual(
            {"group_id": 10, "faculty_id": 20},
            safe_path_dimensions({
                "group_id": "10",
                "faculty_id": 20,
                "asset_id": "private-looking-value",
                "professor_id": "not-a-number",
            }),
        )

    def test_route_uses_template_not_raw_path(self):
        route = MagicMock(path="/group/{group_id}/schedule")
        self.assertEqual(
            "/group/{group_id}/schedule",
            normalized_route({"route": route}),
        )
        self.assertEqual("/unmatched", normalized_route({}))

    def test_database_readiness_is_true_on_success(self):
        with patch("core.health.check_database"):
            self.assertTrue(asyncio.run(database_is_ready(0.1)))

    def test_database_readiness_is_false_on_failure(self):
        with patch(
            "core.health.check_database",
            side_effect=RuntimeError("database detail must stay private"),
        ):
            self.assertFalse(asyncio.run(database_is_ready(0.1)))

    def test_event_fields_do_not_collide_with_log_record_fields(self):
        logger = logging.getLogger("observability-test")
        with self.assertRaises(KeyError):
            log_event(
                logger,
                logging.INFO,
                "bad",
                "bad",
                {"created": 1},
            )
        log_event(
            logger,
            logging.INFO,
            "group_sync.success",
            "Group synchronization succeeded",
            {"groups_created": 1},
        )


if __name__ == "__main__":
    unittest.main()
