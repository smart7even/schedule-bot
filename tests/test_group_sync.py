import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from core.models.group import Group
from db import Base
from parsing import group_sync
from parsing.group_sync import FacultySnapshot, GroupSnapshot


class GroupSyncTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.faculties = [FacultySnapshot(id=1, name="Test faculty")]
        self.groups = [
            GroupSnapshot(id=101, name="A-2601", faculty_id=1, course=1),
            GroupSnapshot(id=102, name="B-2601", faculty_id=1, course=1),
        ]
        self.session_patch = patch.object(
            group_sync,
            "Session",
            self.session_factory,
        )
        self.session_patch.start()

    def tearDown(self):
        self.session_patch.stop()
        self.engine.dispose()

    def _sync(self, groups, now):
        with patch.object(
            group_sync,
            "scrape_group_snapshot",
            return_value=(self.faculties, groups),
        ):
            return group_sync.sync_groups(now=now)

    def test_sync_is_idempotent_and_deactivates_only_after_grace_period(self):
        start = datetime(2026, 8, 24, 1, 0)
        first = self._sync(self.groups, start)
        second = self._sync(self.groups, start + timedelta(hours=1))

        self.assertEqual(2, first.created)
        self.assertEqual(0, second.created)
        self.assertEqual(0, second.updated)

        missing = self._sync(self.groups[:1], start + timedelta(days=1))
        self.assertEqual(1, missing.missing)
        self.assertEqual(0, missing.deactivated)

        expired = self._sync(self.groups[:1], start + timedelta(days=8))
        self.assertEqual(1, expired.deactivated)

        session = self.session_factory()
        try:
            old_group = session.query(Group).get(102)
            self.assertFalse(old_group.is_active)
            self.assertEqual("A-2601", session.query(Group).get(101).name)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
