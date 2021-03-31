"""Create tables

Revision ID: 79c9b1a9b39d
Revises: 
Create Date: 2021-04-01 00:17:20.429320

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79c9b1a9b39d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "current_week",
        sa.Column("week", sa.Integer),
        sa.Column("date", sa.DateTime, primary_key=True)
    )

    op.create_table(
        "faculties",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String)
    )

    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("faculty_id", sa.Integer, sa.ForeignKey('faculties.id', ondelete="CASCADE")),
        sa.Column("course", sa.Integer)
    )

    op.create_table(
        "schedule_cache",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id", ondelete="CASCADE")),
        sa.Column("week", sa.Integer),
        sa.Column("text", sa.String(3000)),
        sa.Column("markup", sa.String(1000))
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id", ondelete="CASCADE"))
    )


def downgrade():
    pass
