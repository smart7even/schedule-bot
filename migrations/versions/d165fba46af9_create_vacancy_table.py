"""create vacancy table

Revision ID: d165fba46af9
Revises: c1221a71b614
Create Date: 2024-12-15 00:49:58.966900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd165fba46af9'
down_revision = 'c1221a71b614'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vacancy',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('date', sa.DateTime),
        sa.Column('company', sa.Text),
        sa.Column('application_guidelines', sa.Text),
        sa.Column('salary_type', sa.Text),
        sa.Column('salary_payment_frequency_type', sa.Text),
        sa.Column('salary_from', sa.Float),
        sa.Column('salary_from_currency', sa.Text),
        sa.Column('salary_to', sa.Float),
        sa.Column('salary_to_currency', sa.Text),
        sa.Column('requirements', sa.Text),
        sa.Column('responsibilities', sa.Text),
        sa.Column('work_type', sa.Text),
        sa.Column('work_schedule', sa.Text),
        sa.Column('number_of_working_days_in_a_week', sa.Integer),
        sa.Column('number_of_working_hours_in_a_week', sa.Integer),
        sa.Column('probation_period_days', sa.Integer),
        sa.Column('text', sa.Text),
    )




def downgrade():
    op.drop_table('vacancy')
