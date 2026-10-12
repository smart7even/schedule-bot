"""add remote config documents

Revision ID: c6a4e89d2f10
Revises: b47d2f9a6e31
Create Date: 2026-09-16
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "c6a4e89d2f10"
down_revision = "b47d2f9a6e31"
branch_labels = None
depends_on = None


DEFAULT_DOCUMENT = {
    "schema_version": 1,
    "refresh_interval_seconds": 300,
    "parameters": {
        "schedule_auto_scroll_today": {
            "description": "Start the current week at today's section on cold launch.",
            "default": True,
            "rules": [],
        }
    },
}


def upgrade():
    documents = op.create_table(
        "remote_config_documents",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )
    revisions = op.create_table(
        "remote_config_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("config_key", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["config_key"],
            ["remote_config_documents.key"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "config_key",
            "revision",
            name="uq_remote_config_revision",
        ),
    )
    serialized = json.loads(json.dumps(DEFAULT_DOCUMENT))
    op.bulk_insert(
        documents,
        [{"key": "mobile_app", "document": serialized, "revision": 1}],
    )
    op.bulk_insert(
        revisions,
        [
            {
                "config_key": "mobile_app",
                "revision": 1,
                "document": serialized,
            }
        ],
    )


def downgrade():
    op.drop_table("remote_config_revisions")
    op.drop_table("remote_config_documents")
