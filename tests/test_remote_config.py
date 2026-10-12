import copy
import os
import unittest
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models.faculty import Faculty
from core.models.group import Group
from core.repositories.remote_config_repository import RemoteConfigRepository
from core.services.app_config_service import get_app_config
from core.services.remote_config_service import (
    DEFAULT_REMOTE_CONFIG_DOCUMENT,
    MOSCOW_TIMEZONE,
    REMOTE_CONFIG_KEY,
    RemoteConfigValidationError,
    build_remote_config_context,
    evaluate_remote_config,
    validate_remote_config_document,
)
from db import Base


class RemoteConfigTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        session = self.session_factory()
        session.add(Faculty(id=7, name="Test faculty"))
        session.add(Group(id=101, name="A-2601", faculty_id=7, course=1))
        session.add(Group(id=202, name="B-2501", faculty_id=7, course=2))
        session.commit()
        session.close()

    def tearDown(self):
        self.engine.dispose()

    def _experiment_document(self):
        document = copy.deepcopy(DEFAULT_REMOTE_CONFIG_DOCUMENT)
        document["parameters"]["schedule_auto_scroll_today"]["default"] = True
        document["parameters"]["schedule_auto_scroll_today"]["rules"] = [
            {
                "id": "first-course-off",
                "conditions": [
                    {
                        "attribute": "group.course",
                        "operator": "in",
                        "value": [1],
                    }
                ],
                "value": False,
            },
            {
                "id": "morning-on",
                "conditions": [
                    {
                        "attribute": "request.time_msk",
                        "operator": "time_between",
                        "value": {"start": "09:00", "end": "12:00"},
                    }
                ],
                "value": True,
            },
        ]
        return document

    def test_rules_use_first_match_per_parameter(self):
        session = self.session_factory()
        morning = datetime(2026, 9, 16, 10, 0, tzinfo=MOSCOW_TIMEZONE)

        first_course = evaluate_remote_config(
            self._experiment_document(),
            build_remote_config_context(session, group_id=101, now=morning),
        )
        second_course = evaluate_remote_config(
            self._experiment_document(),
            build_remote_config_context(session, group_id=202, now=morning),
        )
        session.close()

        self.assertFalse(first_course.payload["schedule_auto_scroll_today"])
        self.assertEqual(
            "first-course-off",
            first_course.matched_rules["schedule_auto_scroll_today"],
        )
        self.assertTrue(second_course.payload["schedule_auto_scroll_today"])
        self.assertEqual(
            "morning-on",
            second_course.matched_rules["schedule_auto_scroll_today"],
        )

    def test_time_between_is_half_open_and_supports_overnight_ranges(self):
        document = copy.deepcopy(DEFAULT_REMOTE_CONFIG_DOCUMENT)
        document["parameters"]["schedule_auto_scroll_today"]["default"] = True
        parameter = document["parameters"]["schedule_auto_scroll_today"]
        parameter["default"] = False
        parameter["rules"] = [
            {
                "id": "overnight",
                "conditions": [
                    {
                        "attribute": "request.time_msk",
                        "operator": "time_between",
                        "value": {"start": "22:00", "end": "02:00"},
                    }
                ],
                "value": True,
            }
        ]
        session = self.session_factory()

        at_2300 = build_remote_config_context(
            session,
            now=datetime(2026, 9, 16, 23, 0, tzinfo=MOSCOW_TIMEZONE),
        )
        at_0200 = build_remote_config_context(
            session,
            now=datetime(2026, 9, 17, 2, 0, tzinfo=MOSCOW_TIMEZONE),
        )
        session.close()

        self.assertTrue(
            evaluate_remote_config(document, at_2300).payload[
                "schedule_auto_scroll_today"
            ]
        )
        self.assertFalse(
            evaluate_remote_config(document, at_0200).payload[
                "schedule_auto_scroll_today"
            ]
        )

    def test_invalid_or_unbounded_rules_are_rejected(self):
        document = self._experiment_document()
        document["parameters"]["schedule_auto_scroll_today"]["rules"][0][
            "conditions"
        ][0]["attribute"] = "user.email"
        with self.assertRaises(RemoteConfigValidationError):
            validate_remote_config_document(document)

    def test_repository_versions_every_write_and_rollback(self):
        session = self.session_factory()
        repository = RemoteConfigRepository(session)
        first = repository.set(REMOTE_CONFIG_KEY, DEFAULT_REMOTE_CONFIG_DOCUMENT)
        first_revision = first.revision
        second = repository.set(REMOTE_CONFIG_KEY, self._experiment_document())

        self.assertEqual(1, first_revision)
        self.assertEqual(2, second.revision)
        self.assertEqual([2, 1], [item.revision for item in repository.history(REMOTE_CONFIG_KEY)])

        restored = repository.rollback(REMOTE_CONFIG_KEY, 1)
        self.assertEqual(3, restored.revision)
        self.assertEqual(DEFAULT_REMOTE_CONFIG_DOCUMENT, restored.document)
        session.close()

    def test_public_app_config_uses_server_group_metadata(self):
        session = self.session_factory()
        RemoteConfigRepository(session).set(
            REMOTE_CONFIG_KEY,
            self._experiment_document(),
        )
        session.close()

        config = get_app_config(
            self.session_factory,
            group_id=101,
            now=datetime(2026, 9, 16, 10, 0, tzinfo=MOSCOW_TIMEZONE),
        )

        self.assertFalse(config.schedule_auto_scroll_today)
        self.assertEqual(1, config.revision)
        self.assertFalse(config.room_map_button_enabled)

    def test_structured_payloads_are_preserved(self):
        document = copy.deepcopy(DEFAULT_REMOTE_CONFIG_DOCUMENT)
        document["parameters"]["schedule_auto_scroll_today"]["default"] = True
        document["parameters"]["banner"] = {
            "default": {"title": "Hello", "items": [1, 2]},
            "rules": [],
        }
        session = self.session_factory()
        context = build_remote_config_context(session)
        session.close()

        result = evaluate_remote_config(document, context)
        self.assertEqual(
            {"title": "Hello", "items": [1, 2]},
            result.payload["banner"],
        )


if __name__ == "__main__":
    unittest.main()
