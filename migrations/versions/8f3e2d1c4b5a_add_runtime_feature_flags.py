"""add runtime feature flags

Revision ID: 8f3e2d1c4b5a
Revises: 71d3e4f8a210
Create Date: 2026-08-24 18:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "8f3e2d1c4b5a"
down_revision = "71d3e4f8a210"
branch_labels = None
depends_on = None


def upgrade():
    feature_flags = op.create_table(
        "feature_flags",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("name"),
    )
    op.bulk_insert(
        feature_flags,
        [
            {"name": "room_map_button_enabled", "enabled": False},
            {"name": "room_map_caption_enabled", "enabled": False},
        ],
    )


def downgrade():
    op.drop_table("feature_flags")
