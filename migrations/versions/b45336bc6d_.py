"""empty message

Revision ID: b45336bc6d
Revises: 4a5df8c40b7
Create Date: 2015-06-13 01:03:29.441876

"""

# revision identifiers, used by Alembic.
revision = 'b45336bc6d'
down_revision = '4a5df8c40b7'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ff_plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('start_perf', sa.Float(), nullable=False),
    sa.Column('end_perf', sa.Float(), nullable=False),
    sa.Column('loads', postgresql.ARRAY(sa.Float()), nullable=False),
    sa.Column('initial_p', sa.Float(), nullable=False),
    sa.Column('k_1', sa.Float(), nullable=False),
    sa.Column('tau_1', sa.Float(), nullable=False),
    sa.Column('k_2', sa.Float(), nullable=False),
    sa.Column('tau_2', sa.Float(), nullable=False),
    sa.Column('prequel_plan', postgresql.ARRAY(sa.Float()), nullable=True),
    sa.Column('goal', sa.Float(), nullable=False),
    sa.Column('length', sa.Integer(), nullable=False),
    sa.Column('max_load', sa.Float(), nullable=False),
    sa.Column('off_weeks', postgresql.ARRAY(sa.Integer()), nullable=True),
    sa.Column('off_days', postgresql.ARRAY(sa.Integer()), nullable=True),
    sa.Column('weekly_cycle', postgresql.ARRAY(sa.Integer()), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ff_plans')
    ### end Alembic commands ###
