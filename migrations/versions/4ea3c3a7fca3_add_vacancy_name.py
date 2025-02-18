"""add vacancy name

Revision ID: 4ea3c3a7fca3
Revises: d165fba46af9
Create Date: 2024-12-15 01:37:25.568248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ea3c3a7fca3'
down_revision = 'd165fba46af9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vacancy', sa.Column('name', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('vacancy', 'name')
