import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from core.services.group_usage_dimensions_service import (
    GroupUsageDimensionsCache,
)


class _Session:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class GroupUsageDimensionsCacheTest(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.sessions = []
        self.lookups = []
        self.groups = {
            101: SimpleNamespace(
                name="  БИ-2601\n",
                course=1,
                faculty_id=7,
            ),
        }

        def session_factory():
            session = _Session()
            self.sessions.append(session)
            return session

        groups = self.groups
        lookups = self.lookups

        class Repository:
            def __init__(self, session):
                self.session = session

            def get_group_by_id(self, group_id):
                lookups.append(group_id)
                return groups.get(group_id)

        self.cache = GroupUsageDimensionsCache(
            session_factory=session_factory,
            repository_factory=Repository,
            ttl_seconds=60,
            max_entries=2,
            clock=lambda: self.now,
        )

    def test_resolves_safe_snapshot_and_closes_session(self):
        self.assertEqual(
            {
                "group_name": "БИ-2601",
                "group_course": 1,
                "group_faculty_id": 7,
            },
            self.cache.resolve("101"),
        )
        self.assertEqual([101], self.lookups)
        self.assertTrue(self.sessions[0].closed)

    def test_reuses_cached_value_until_ttl_expires(self):
        first = self.cache.resolve(101)
        self.groups[101].course = 2

        self.assertEqual(first, self.cache.resolve(101))
        self.assertEqual([101], self.lookups)

        self.now += 61
        self.assertEqual(2, self.cache.resolve(101)["group_course"])
        self.assertEqual([101, 101], self.lookups)

    def test_missing_group_is_negative_cached(self):
        self.assertEqual({}, self.cache.resolve(404))
        self.assertEqual({}, self.cache.resolve(404))
        self.assertEqual([404], self.lookups)

    def test_lookup_failure_is_fail_open_and_cached(self):
        class FailingRepository:
            def __init__(self, session):
                self.session = session

            def get_group_by_id(self, group_id):
                raise RuntimeError("private datastore detail")

        cache = GroupUsageDimensionsCache(
            session_factory=lambda: _Session(),
            repository_factory=FailingRepository,
            ttl_seconds=60,
        )

        self.assertEqual({}, cache.resolve(101))

    def test_session_close_failure_is_fail_open(self):
        class CloseFailingSession:
            def close(self):
                raise RuntimeError("private close detail")

        class Repository:
            def __init__(self, session):
                self.session = session

            def get_group_by_id(self, group_id):
                return SimpleNamespace(
                    name="БИ-2601",
                    course=1,
                    faculty_id=7,
                )

        cache = GroupUsageDimensionsCache(
            session_factory=CloseFailingSession,
            repository_factory=Repository,
        )

        self.assertEqual(1, cache.resolve(101)["group_course"])

    def test_invalid_group_id_never_opens_session(self):
        self.assertEqual({}, self.cache.resolve("not-an-id"))
        self.assertEqual([], self.sessions)

    def test_cache_size_is_bounded(self):
        self.cache.resolve(101)
        self.cache.resolve(202)
        self.cache.resolve(303)
        self.cache.resolve(101)

        self.assertEqual([101, 202, 303, 101], self.lookups)


if __name__ == "__main__":
    unittest.main()
