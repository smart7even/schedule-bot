import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.repositories.feature_flag_repository import (
    FeatureFlagRepository,
    ROOM_MAP_BUTTON_ENABLED,
    ROOM_MAP_CAPTION_ENABLED,
)
from core.services.app_config_service import AppConfig, get_app_config
from core.types.lesson import Lesson
from db import Base
from server import lessons_to_dict


class FeatureFlagTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_flags_default_off_and_update_without_process_restart(self):
        first = get_app_config(self.session_factory)
        self.assertEqual(AppConfig(), first)

        session = self.session_factory()
        FeatureFlagRepository(session).set(ROOM_MAP_BUTTON_ENABLED, True)
        session.close()

        second = get_app_config(self.session_factory)
        self.assertTrue(second.room_map_button_enabled)
        self.assertFalse(second.room_map_caption_enabled)

    def test_only_allowlisted_flags_can_be_written(self):
        session = self.session_factory()
        with self.assertRaises(ValueError):
            FeatureFlagRepository(session).set("unknown", True)
        session.close()

    def test_caption_is_controlled_at_serialization_time(self):
        lesson = Lesson(
            "Иностранный язык (Практика)",
            "03.09.2025",
            "СР",
            "14:30 - 16:00",
            "Антонова Ксения Николаевна",
            "64 ауд. Грибоедова 30/32",
            None,
            105658,
            "https://staff.unecon.ru/unecon_scheme.php?initial_search=64",
            "НА СХЕМЕ ЛИНГВОБАШНИ",
        )

        hidden = lessons_to_dict([lesson], AppConfig())[0]
        visible = lessons_to_dict(
            [lesson],
            AppConfig(room_map_caption_enabled=True),
        )[0]

        self.assertNotIn("СХЕМЕ", hidden["location"])
        self.assertIn("НА СХЕМЕ ЛИНГВОБАШНИ", visible["location"])


if __name__ == "__main__":
    unittest.main()
