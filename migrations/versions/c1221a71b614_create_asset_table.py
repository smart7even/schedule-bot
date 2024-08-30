"""create asset table

Revision ID: c1221a71b614
Revises: 79c9b1a9b39d
Create Date: 2024-08-30 23:43:13.031430

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1221a71b614'
down_revision = '79c9b1a9b39d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'asset',
        sa.Column('id', sa.Text, primary_key=True),
        sa.Column('content', sa.JSON),
    )


def downgrade():
    op.drop_table('asset')
