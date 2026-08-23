"""add group sync metadata

Revision ID: 71d3e4f8a210
Revises: 4ea3c3a7fca3
Create Date: 2026-08-24 00:30:00
"""
from alembic import op
import sqlalchemy as sa


revision = '71d3e4f8a210'
down_revision = '4ea3c3a7fca3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('groups', sa.Column(
        'is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('groups', sa.Column(
        'first_seen_at', sa.DateTime(), nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('groups', sa.Column(
        'last_seen_at', sa.DateTime(), nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('groups', sa.Column('missing_since', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('groups', 'missing_since')
    op.drop_column('groups', 'last_seen_at')
    op.drop_column('groups', 'first_seen_at')
    op.drop_column('groups', 'is_active')
