import asyncio
import importlib.util
import json
import os
from pathlib import Path
import unittest

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import server


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT
    / "migrations"
    / "versions"
    / "b47d2f9a6e31_empty_legacy_news_asset.py"
)
ARCHIVE_PATH = ROOT / "assets" / "archive" / "news_bdui_2026-08-24.json"


def _load_migration():
    spec = importlib.util.spec_from_file_location("empty_news_migration", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EmptyNewsAssetMigrationTest(unittest.TestCase):
    def setUp(self):
        self.engine = sa.create_engine("sqlite:///:memory:")
        self.metadata = sa.MetaData()
        self.asset = sa.Table(
            "asset",
            self.metadata,
            sa.Column("id", sa.Text, primary_key=True),
            sa.Column("content", sa.JSON),
        )
        self.metadata.create_all(self.engine)
        self.session_factory = sa.orm.sessionmaker(bind=self.engine)
        self.migration = _load_migration()

        archived = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
        self.archived_content = archived["content"]
        with self.engine.begin() as connection:
            connection.execute(
                self.asset.insert().values(
                    id="news",
                    content=self.archived_content,
                )
            )

    def tearDown(self):
        self.engine.dispose()

    def _run(self, migration_function):
        with self.engine.begin() as connection:
            context = MigrationContext.configure(connection)
            self.migration.op = Operations(context)
            migration_function()

    def _content(self):
        with self.engine.connect() as connection:
            return connection.execute(
                sa.select([self.asset.c.content]).where(
                    self.asset.c.id == "news"
                )
            ).scalar()

    def test_upgrade_empties_content_and_downgrade_restores_archive(self):
        self.assertEqual(
            self.archived_content,
            self.migration._LEGACY_NEWS_CONTENT,
        )

        self._run(self.migration.upgrade)
        self.assertEqual({}, self._content())

        original_session = server.Session
        server.Session = self.session_factory
        try:
            response = asyncio.run(server.get_asset("news"))
        finally:
            server.Session = original_session

        self.assertEqual("news", response.id)
        self.assertEqual({}, response.content)

        self._run(self.migration.downgrade)
        self.assertEqual(self.archived_content, self._content())


if __name__ == "__main__":
    unittest.main()
